"""
CLIP-based Image Search Service
Implements zero-shot image-to-product matching using OpenAI CLIP
Enhanced with automatic persistence, concurrency handling, and scalability optimizations
"""

import torch
import clip
import numpy as np
from PIL import Image
import faiss
import pickle
import os
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import asyncio
import threading
import time
from sentence_transformers import SentenceTransformer
import json

from app.core.config import settings
from app.core.monitoring import logger

class CLIPSearchService:
    """Enhanced CLIP-based semantic search with automatic persistence and optimization"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model = None
        self.clip_preprocess = None
        self.sentence_model = None
        self.image_index = None
        self.text_index = None
        self.product_metadata = {}
        self.index_path = Path(settings.models_dir) / "clip_indexes"
        self.index_path.mkdir(exist_ok=True)
        
        # Enhanced features
        self._index_lock = threading.RLock()  # For concurrent access
        self._last_save_time = 0
        self._save_interval = 300  # Auto-save every 5 minutes
        self._pending_saves = 0
        self._max_index_size = 100000  # Switch to IVFPQ after this
        self._auto_save_enabled = True
        
        # Performance tracking
        self._stats = {
            'total_products': 0,
            'last_save_time': None,
            'index_type': 'FlatIP',
            'search_count': 0,
            'avg_search_time': 0.0        }
    
    async def initialize(self):
        """Initialize CLIP models and load existing indexes"""
        try:
            # Load CLIP model with device optimization
            logger.info(f"Loading CLIP model: {settings.clip_model_name}")
            self.clip_model, self.clip_preprocess = clip.load(
                settings.clip_model_name, 
                device=self.device
            )
            
            # Load sentence transformer for text embeddings
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Load existing indexes if available
            await self._load_indexes()
            
            # Start auto-save background task
            if self._auto_save_enabled:
                asyncio.create_task(self._auto_save_loop())
            
            logger.info("Enhanced CLIP search service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CLIP service: {e}")
            raise
    
    async def encode_image(self, image_path: str) -> np.ndarray:
        """Encode image to CLIP embedding"""
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.clip_preprocess(image).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                image_features = self.clip_model.encode_image(image_tensor)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
            return image_features.cpu().numpy().flatten()
            
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            raise
    
    async def encode_text(self, text: str) -> np.ndarray:
        """Encode text to CLIP embedding"""
        try:
            text_token = clip.tokenize([text]).to(self.device)
            
            with torch.no_grad():
                text_features = self.clip_model.encode_text(text_token)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                
            return text_features.cpu().numpy().flatten()
            
        except Exception as e:
            logger.error(f"Failed to encode text '{text}': {e}")
            raise
      
    async def encode_text_sentence_transformer(self, text: str) -> np.ndarray:
        """Alternative text encoding using sentence transformers"""
        try:
            embedding = self.sentence_model.encode([text])
            return embedding.flatten()
        except Exception as e:
            logger.error(f"Failed to encode text with sentence transformer: {e}")
            raise
    
    async def add_product_to_index(self, product_id: int, image_path: str, 
                                 title: str, description: str = ""):
        """Add a product to the search indexes with enhanced concurrency handling"""
        async with asyncio.Lock():  # Prevent concurrent modifications
            try:
                # Validate inputs
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Image not found: {image_path}")
                
                # Check for duplicates
                for metadata in self.product_metadata.values():
                    if metadata['product_id'] == product_id:
                        logger.debug(f"Product {product_id} already in index")
                        return
                
                # Encode image with proper preprocessing
                image_embedding = await self.encode_image(image_path)
                
                # Encode text (title + description)
                text_content = f"{title} {description}".strip()
                text_embedding = await self.encode_text(text_content)
                
                with self._index_lock:
                    # Initialize indexes if they don't exist
                    if self.image_index is None:
                        dimension = image_embedding.shape[0]
                        self.image_index = faiss.IndexFlatIP(dimension)
                        self.text_index = faiss.IndexFlatIP(text_embedding.shape[0])
                        logger.info(f"Initialized FAISS indexes with dimension {dimension}")
                    
                    # Add to indexes
                    self.image_index.add(image_embedding.reshape(1, -1))
                    self.text_index.add(text_embedding.reshape(1, -1))
                    
                    # Store metadata
                    index_id = self.image_index.ntotal - 1
                    self.product_metadata[index_id] = {
                        'product_id': product_id,
                        'title': title,
                        'description': description,
                        'image_path': image_path,
                        'added_time': time.time()
                    }
                    
                    # Update stats
                    self._stats['total_products'] = len(self.product_metadata)
                    self._pending_saves += 1
                
                # Check if we should upgrade index
                if self._should_upgrade_index():
                    asyncio.create_task(self._upgrade_to_ivfpq())
                
                logger.info(f"Added product {product_id} to CLIP indexes (total: {self._stats['total_products']})")
                
            except Exception as e:
                logger.error(f"Failed to add product {product_id} to index: {e}")
                raise
    
    async def search_by_image(self, query_image_path: str, 
                            top_k: int = 10) -> List[Dict]:
        """Search for similar products using an image query"""
        try:
            if self.image_index is None or self.image_index.ntotal == 0:
                return []
              # Encode query image
            query_embedding = await self.encode_image(query_image_path)
            
            # Search
            scores, indices = self.image_index.search(
                query_embedding.reshape(1, -1), top_k * 2  # Get more results to allow for deduplication
            )
            
            # Format results with deduplication by product_id
            results = []
            seen_product_ids = set()
            
            for score, idx in zip(scores[0], indices[0]):
                if idx in self.product_metadata:
                    product_id = self.product_metadata[idx]['product_id']
                    
                    # Skip if we've already seen this product
                    if product_id in seen_product_ids:
                        continue
                    
                    seen_product_ids.add(product_id)
                    result = self.product_metadata[idx].copy()
                    result['similarity_score'] = float(score)
                    results.append(result)
                    
                    # Stop if we have enough unique results
                    if len(results) >= top_k:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            raise
    
    async def search_by_text(self, query_text: str, 
                           top_k: int = 10) -> List[Dict]:
        """Search for products using text query"""
        try:
            if self.text_index is None or self.text_index.ntotal == 0:
                return []
              # Encode query text
            query_embedding = await self.encode_text(query_text)
            
            # Search
            scores, indices = self.text_index.search(
                query_embedding.reshape(1, -1), top_k * 2  # Get more results to allow for deduplication
            )
            
            # Format results with deduplication by product_id
            results = []
            seen_product_ids = set()
            
            for score, idx in zip(scores[0], indices[0]):
                if idx in self.product_metadata:
                    product_id = self.product_metadata[idx]['product_id']
                    
                    # Skip if we've already seen this product
                    if product_id in seen_product_ids:
                        continue
                    
                    seen_product_ids.add(product_id)
                    result = self.product_metadata[idx].copy()
                    result['similarity_score'] = float(score)
                    results.append(result)
                    
                    # Stop if we have enough unique results
                    if len(results) >= top_k:
                        break
            
            return results
            
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            raise
    
    async def hybrid_search(self, query_text: str = None, 
                          query_image_path: str = None,
                          top_k: int = 10, 
                          text_weight: float = 0.5) -> List[Dict]:
        """Perform hybrid text + image search"""
        try:
            if query_text is None and query_image_path is None:
                raise ValueError("At least one of query_text or query_image_path must be provided")
            
            text_results = []
            image_results = []
            
            # Get text results
            if query_text:
                text_results = await self.search_by_text(query_text, top_k * 2)
            
            # Get image results
            if query_image_path:
                image_results = await self.search_by_image(query_image_path, top_k * 2)
            
            # Combine results
            if not text_results:
                return image_results[:top_k]
            elif not image_results:
                return text_results[:top_k]
            
            # Hybrid scoring
            combined_scores = {}
            
            # Add text scores
            for result in text_results:
                product_id = result['product_id']
                combined_scores[product_id] = {
                    'text_score': result['similarity_score'] * text_weight,
                    'image_score': 0,
                    'metadata': result
                }
            
            # Add image scores
            for result in image_results:
                product_id = result['product_id']
                if product_id in combined_scores:
                    combined_scores[product_id]['image_score'] = \
                        result['similarity_score'] * (1 - text_weight)
                else:
                    combined_scores[product_id] = {
                        'text_score': 0,
                        'image_score': result['similarity_score'] * (1 - text_weight),
                        'metadata': result
                    }
            
            # Calculate final scores and sort
            final_results = []
            for product_id, scores in combined_scores.items():
                final_score = scores['text_score'] + scores['image_score']
                result = scores['metadata'].copy()
                result['hybrid_score'] = final_score
                result['text_component'] = scores['text_score']
                result['image_component'] = scores['image_score']
                final_results.append(result)
            
            # Sort by hybrid score and return top_k
            final_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            return final_results[:top_k]
              except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise
    
    async def save_indexes(self):
        """Enhanced save with atomic operations and backup creation"""
        if not self.image_index or self.image_index.ntotal == 0:
            logger.debug("No indexes to save")
            return
            
        save_start_time = time.time()
        
        with self._index_lock:
            try:
                # Create temporary files for atomic save
                temp_suffix = f".tmp_{int(time.time())}"
                image_temp_path = self.index_path / f"image_index{temp_suffix}.faiss"
                text_temp_path = self.index_path / f"text_index{temp_suffix}.faiss"
                metadata_temp_path = self.index_path / f"metadata{temp_suffix}.pkl"
                stats_temp_path = self.index_path / f"stats{temp_suffix}.json"
                
                # Save to temporary files first
                if self.image_index is not None:
                    faiss.write_index(self.image_index, str(image_temp_path))
                
                if self.text_index is not None:
                    faiss.write_index(self.text_index, str(text_temp_path))
                
                # Save metadata with additional info
                enhanced_metadata = {
                    'product_metadata': self.product_metadata,
                    'save_time': time.time(),
                    'total_products': len(self.product_metadata),
                    'index_type': self._stats['index_type'],
                    'version': '2.0'  # Enhanced version
                }
                
                with open(metadata_temp_path, 'wb') as f:
                    pickle.dump(enhanced_metadata, f)
                
                # Save stats
                current_stats = await self.get_stats()
                with open(stats_temp_path, 'w') as f:
                    json.dump(current_stats, f, indent=2)
                
                # Create backups of existing files
                backup_dir = self.index_path / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_timestamp = int(time.time())
                
                existing_files = [
                    ("image_index.faiss", image_temp_path),
                    ("text_index.faiss", text_temp_path),
                    ("metadata.pkl", metadata_temp_path),
                    ("stats.json", stats_temp_path)
                ]
                
                for filename, temp_path in existing_files:
                    final_path = self.index_path / filename
                    backup_path = backup_dir / f"{backup_timestamp}_{filename}"
                    
                    # Backup existing file if it exists
                    if final_path.exists():
                        final_path.replace(backup_path)
                    
                    # Move temp file to final location (atomic operation)
                    temp_path.replace(final_path)
                
                # Update stats
                self._last_save_time = time.time()
                self._pending_saves = 0
                self._stats['last_save_time'] = self._last_save_time
                
                save_duration = time.time() - save_start_time
                logger.info(f"CLIP indexes saved successfully in {save_duration:.2f}s "
                           f"({len(self.product_metadata)} products)")
                
                # Clean old backups (keep last 5)
                await self._cleanup_old_backups(backup_dir, keep_count=5)
                
            except Exception as e:
                # Clean up temp files on error
                for temp_file in [image_temp_path, text_temp_path, metadata_temp_path, stats_temp_path]:
                    if temp_file.exists():
                        temp_file.unlink()
                
                logger.error(f"Failed to save indexes: {e}")
                raise
    
    async def _cleanup_old_backups(self, backup_dir: Path, keep_count: int = 5):
        """Clean up old backup files to save disk space"""
        try:
            backup_files = list(backup_dir.glob("*_*.faiss"))
            backup_files.extend(backup_dir.glob("*_*.pkl"))
            backup_files.extend(backup_dir.glob("*_*.json"))
            
            # Group by file type and sort by timestamp
            file_groups = {}
            for file_path in backup_files:
                parts = file_path.name.split('_', 1)
                if len(parts) == 2:
                    timestamp, filename = parts
                    if filename not in file_groups:
                        file_groups[filename] = []
                    file_groups[filename].append((int(timestamp), file_path))
            
            # Keep only the latest backups for each file type
            for filename, files in file_groups.items():
                files.sort(reverse=True)  # Latest first
                for _, file_path in files[keep_count:]:
                    file_path.unlink()
                    logger.debug(f"Cleaned up old backup: {file_path.name}")
                    
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
      async def _load_indexes(self):
        """Enhanced loading with fallback and version compatibility"""
        try:
            image_index_path = self.index_path / "image_index.faiss"
            text_index_path = self.index_path / "text_index.faiss"
            metadata_path = self.index_path / "metadata.pkl"
            stats_path = self.index_path / "stats.json"
            
            # Load indexes
            if image_index_path.exists():
                self.image_index = faiss.read_index(str(image_index_path))
                logger.info(f"Loaded image index with {self.image_index.ntotal} vectors")
                
                # Detect index type
                if hasattr(self.image_index, 'nlist'):
                    self._stats['index_type'] = 'IVFPQ'
                else:
                    self._stats['index_type'] = 'FlatIP'
            
            if text_index_path.exists():
                self.text_index = faiss.read_index(str(text_index_path))
                logger.info(f"Loaded text index with {self.text_index.ntotal} vectors")
            
            # Load metadata with version compatibility
            if metadata_path.exists():
                with open(metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                
                # Handle both old and new metadata formats
                if isinstance(metadata, dict) and 'product_metadata' in metadata:
                    # New enhanced format
                    self.product_metadata = metadata['product_metadata']
                    self._stats.update({
                        'total_products': metadata.get('total_products', len(self.product_metadata)),
                        'index_type': metadata.get('index_type', 'FlatIP')
                    })
                    logger.info(f"Loaded enhanced metadata (v{metadata.get('version', '2.0')}) "
                               f"for {len(self.product_metadata)} products")
                else:
                    # Legacy format
                    self.product_metadata = metadata
                    self._stats['total_products'] = len(self.product_metadata)
                    logger.info(f"Loaded legacy metadata for {len(self.product_metadata)} products")
            
            # Load stats if available
            if stats_path.exists():
                with open(stats_path, 'r') as f:
                    saved_stats = json.load(f)
                    self._stats.update(saved_stats)
                    logger.debug("Loaded saved statistics")
            
            # Validate consistency
            if self.image_index and len(self.product_metadata) != self.image_index.ntotal:
                logger.warning(f"Index/metadata mismatch: {self.image_index.ntotal} vectors, "
                             f"{len(self.product_metadata)} metadata entries")
            
            self._last_save_time = time.time()
            
        except Exception as e:
            logger.warning(f"Could not load existing indexes: {e}")
            # Try to recover from backup
            await self._try_backup_recovery()

    async def _auto_save_loop(self):
        """Background task for automatic index persistence"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                current_time = time.time()
                
                # Save if interval elapsed and there are pending changes
                if (current_time - self._last_save_time > self._save_interval and 
                    self._pending_saves > 0):
                    await self.save_indexes()
                    logger.debug("Auto-saved CLIP indexes")
                    
            except Exception as e:
                logger.error(f"Auto-save loop error: {e}")
                await asyncio.sleep(60)  # Continue trying
    
    def _should_upgrade_index(self) -> bool:
        """Check if we should upgrade from FlatIP to IVFPQ for better performance"""
        if self.image_index is None:
            return False
        return (self.image_index.ntotal > self._max_index_size and 
                self._stats['index_type'] == 'FlatIP')
    
    async def _upgrade_to_ivfpq(self):
        """Upgrade indexes from FlatIP to IVFPQ for better scalability"""
        if not self._should_upgrade_index():
            return
            
        logger.info("Upgrading CLIP indexes to IVFPQ for better performance...")
        
        with self._index_lock:
            try:
                # Backup current indexes
                await self.save_indexes()
                
                # Create IVFPQ indexes
                dimension = self.image_index.d
                nlist = min(4096, int(np.sqrt(self.image_index.ntotal)))  # Number of clusters
                
                # Upgrade image index
                quantizer = faiss.IndexFlatIP(dimension)
                new_image_index = faiss.IndexIVFPQ(quantizer, dimension, nlist, 8, 8)
                
                # Train and populate new index
                if self.image_index.ntotal > 1000:  # Need enough data to train
                    # Get all vectors for training
                    all_vectors = np.zeros((self.image_index.ntotal, dimension), dtype=np.float32)
                    for i in range(self.image_index.ntotal):
                        all_vectors[i] = self.image_index.reconstruct(i)
                    
                    new_image_index.train(all_vectors)
                    new_image_index.add(all_vectors)
                    
                    # Replace old index
                    self.image_index = new_image_index
                    
                    # Same for text index
                    new_text_index = faiss.IndexIVFPQ(quantizer, dimension, nlist, 8, 8)
                    text_vectors = np.zeros((self.text_index.ntotal, dimension), dtype=np.float32)
                    for i in range(self.text_index.ntotal):
                        text_vectors[i] = self.text_index.reconstruct(i)
                    
                    new_text_index.train(text_vectors)
                    new_text_index.add(text_vectors)
                    self.text_index = new_text_index
                    
                    self._stats['index_type'] = 'IVFPQ'
                    await self.save_indexes()
                    
                    logger.info(f"Successfully upgraded indexes to IVFPQ (nlist={nlist})")
                
            except Exception as e:
                logger.error(f"Failed to upgrade indexes: {e}")
    
    async def get_stats(self) -> Dict:
        """Get comprehensive statistics about the search service"""
        stats = self._stats.copy()
        
        if self.image_index:
            stats.update({
                'image_index_size': self.image_index.ntotal,
                'text_index_size': self.text_index.ntotal if self.text_index else 0,
                'metadata_count': len(self.product_metadata),
                'last_save_time': self._last_save_time,
                'pending_saves': self._pending_saves,
                'auto_save_enabled': self._auto_save_enabled,
                'device': self.device,
                'index_path': str(self.index_path)
            })
        
        return stats

    async def _try_backup_recovery(self):
        """Try to recover from the latest backup"""
        try:
            backup_dir = self.index_path / "backups"
            if not backup_dir.exists():
                return
            
            # Find the latest backup timestamp
            backup_files = list(backup_dir.glob("*_image_index.faiss"))
            if not backup_files:
                return
            
            # Extract timestamps and find the latest
            timestamps = []
            for file_path in backup_files:
                try:
                    timestamp = int(file_path.name.split('_')[0])
                    timestamps.append(timestamp)
                except (ValueError, IndexError):
                    continue
            
            if not timestamps:
                return
            
            latest_timestamp = max(timestamps)
            logger.info(f"Attempting recovery from backup {latest_timestamp}")
            
            # Load backup files
            backup_files = {
                'image_index': backup_dir / f"{latest_timestamp}_image_index.faiss",
                'text_index': backup_dir / f"{latest_timestamp}_text_index.faiss",
                'metadata': backup_dir / f"{latest_timestamp}_metadata.pkl"
            }
            
            # Verify all backup files exist
            missing_files = [name for name, path in backup_files.items() if not path.exists()]
            if missing_files:
                logger.warning(f"Backup recovery failed: missing files {missing_files}")
                return
            
            # Load from backup
            self.image_index = faiss.read_index(str(backup_files['image_index']))
            self.text_index = faiss.read_index(str(backup_files['text_index']))
            
            with open(backup_files['metadata'], 'rb') as f:
                metadata = pickle.load(f)
                if isinstance(metadata, dict) and 'product_metadata' in metadata:
                    self.product_metadata = metadata['product_metadata']
                else:
                    self.product_metadata = metadata
            
            logger.info(f"Successfully recovered from backup: {len(self.product_metadata)} products")
            
        except Exception as e:
            logger.error(f"Backup recovery failed: {e}")
    
    async def force_save(self):
        """Force immediate save regardless of pending changes"""
        logger.info("Forcing immediate index save...")
        await self.save_indexes()
    
    async def optimize_for_search(self):
        """Optimize indexes for better search performance"""
        if not self.image_index or self.image_index.ntotal == 0:
            return
        
        logger.info("Optimizing indexes for search performance...")
        
        try:
            # Set optimal search parameters for IVFPQ
            if hasattr(self.image_index, 'nprobe'):
                # Balance between speed and accuracy
                optimal_nprobe = min(32, max(1, self.image_index.nlist // 8))
                self.image_index.nprobe = optimal_nprobe
                self.text_index.nprobe = optimal_nprobe
                logger.info(f"Set nprobe to {optimal_nprobe} for optimal search")
            
        except Exception as e:
            logger.warning(f"Index optimization failed: {e}")
    
    async def get_health_status(self) -> Dict:
        """Get comprehensive health status of the search service"""
        health = {
            'status': 'healthy',
            'warnings': [],
            'metrics': await self.get_stats()
        }
        
        try:
            # Check index consistency
            if self.image_index and self.text_index:
                if self.image_index.ntotal != self.text_index.ntotal:
                    health['status'] = 'warning'
                    health['warnings'].append("Image and text index sizes don't match")
            
            # Check metadata consistency
            if self.image_index and len(self.product_metadata) != self.image_index.ntotal:
                health['status'] = 'warning'
                health['warnings'].append("Metadata count doesn't match index size")
            
            # Check disk space
            index_size_mb = sum(
                f.stat().st_size for f in self.index_path.glob("*.faiss")
                if f.exists()
            ) / (1024 * 1024)
            
            health['metrics']['index_size_mb'] = round(index_size_mb, 2)
            
            if index_size_mb > 1000:  # > 1GB
                health['warnings'].append(f"Large index size: {index_size_mb:.1f}MB")
            
            # Check last save time
            if self._pending_saves > 100:
                health['status'] = 'warning'
                health['warnings'].append(f"{self._pending_saves} pending saves")
            
        except Exception as e:
            health['status'] = 'error'
            health['warnings'].append(f"Health check failed: {e}")
        
        return health
# Global instance
clip_service = CLIPSearchService()
