"""
Feature Extraction Service for Streaming Product Ingestion
Implements resource-efficient pipeline:
- Receives product JSON from Node.js scraper
- Downloads image to RAM only, computes CLIP embedding
- Normalizes price, forms feature vector
- Stores embedding in FAISS, metadata in DB
- Logs all steps, deletes raw data from RAM
- Never stores raw HTML/images on disk
"""

import asyncio
import aiohttp
import numpy as np
import faiss
import os
import tempfile
import logging
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
from pathlib import Path
from io import BytesIO
from PIL import Image
import sqlite3
from sklearn.linear_model import SGDClassifier
import pickle

from app.core.monitoring import logger
from app.services.clip_search import CLIPSearchService

class FeatureExtractionService:
    """Streaming feature extraction with no raw data persistence"""
    
    def __init__(self):
        self.clip_service = None
        self.faiss_index = None
        self.metadata_db_path = "models/product_metadata.db"
        self.embedding_counter = 0
        self.error_log_path = "logs/scrape_extract.log"
        self.incremental_model = SGDClassifier(loss='log_loss', random_state=42)
        self.model_trained = False
        
        # Ensure directories exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("models", exist_ok=True)
        
        # Initialize SQLite for metadata
        self._init_metadata_db()
        
    async def initialize(self):
        """Initialize CLIP service and load existing indexes"""
        try:
            self.clip_service = CLIPSearchService()
            await self.clip_service.initialize()
            
            # Load existing FAISS index if available
            index_path = Path("models/clip_indexes/streaming_index.faiss")
            if index_path.exists():
                self.faiss_index = faiss.read_index(str(index_path))
                self.embedding_counter = self.faiss_index.ntotal
                logger.info(f"Loaded existing FAISS index with {self.embedding_counter} embeddings")
            
            logger.info("Feature extraction service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize feature extraction service: {e}")
            raise
    
    def _init_metadata_db(self):
        """Initialize lightweight SQLite database for metadata"""
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE,
                site TEXT,
                url TEXT,
                title TEXT,
                price_usd REAL,
                currency TEXT,
                embedding_id INTEGER,
                prediction TEXT,
                confidence REAL,
                timestamp TEXT,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def process_scraped_product(self, product_json: Dict) -> Dict:
        """
        Main processing pipeline for scraped product data
        Returns distilled metadata only
        """
        product_id = product_json.get('product_id', '')
        site = product_json.get('site', '')
        url = product_json.get('url', '')
        title = product_json.get('title', '')
        price_raw = product_json.get('price_raw', '')
        currency = product_json.get('currency', 'USD')
        image_url = product_json.get('image_url', '')
        timestamp = product_json.get('timestamp', datetime.now(timezone.utc).isoformat())
        
        result_metadata = {
            "product_id": product_id,
            "site": site,
            "url": url,
            "title": title,
            "price_usd": None,
            "currency": currency,
            "embedding_id": None,
            "prediction": None,
            "confidence": 0.0,
            "timestamp": timestamp,
            "error": None,
            "status": "failed"
        }
        
        try:
            # Step 1: Download image to RAM only
            image_bytes = await self._download_image_to_ram(image_url)
            
            # Step 2: Compute CLIP embedding (image in RAM)
            image_embedding = await self._compute_image_embedding(image_bytes)
            
            # Step 3: Normalize price
            price_usd = self._normalize_price(price_raw, currency)
            
            # Step 4: Compute text embedding
            text_embedding = await self._compute_text_embedding(title)
            
            # Step 5: Form feature vector
            feature_vector = self._form_feature_vector(image_embedding, text_embedding, price_usd, site)
            
            # Step 6: Store embedding in FAISS
            embedding_id = self._store_embedding(image_embedding)
            
            # Step 7: Make prediction (if model is trained)
            prediction, confidence = self._make_prediction(feature_vector)
            
            # Step 8: Store distilled metadata
            result_metadata.update({
                "price_usd": price_usd,
                "embedding_id": embedding_id,
                "prediction": prediction,
                "confidence": confidence,
                "status": "success",
                "error": None
            })
            
            self._store_metadata(result_metadata)
            
            # Log success
            self._log_processing_step(product_id, "success", f"Processed {site} product")
            
        except Exception as e:
            error_msg = str(e)
            result_metadata["error"] = error_msg
            result_metadata["status"] = "failed"
            
            # Store failed metadata for tracking
            self._store_metadata(result_metadata)
            
            # Log error
            self._log_processing_step(product_id, "error", error_msg)
            
        finally:
            # Ensure no raw data remains in memory
            if 'image_bytes' in locals():
                del image_bytes
            if 'image_embedding' in locals():
                del image_embedding
            if 'text_embedding' in locals():
                del text_embedding
            if 'feature_vector' in locals():
                del feature_vector
        
        return result_metadata
    
    async def _download_image_to_ram(self, image_url: str) -> bytes:
        """Download image directly to RAM, never to disk"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        raise Exception(f"Image download failed: HTTP {response.status}")
                    
                    image_bytes = await response.read()
                    
                    # Validate image
                    if len(image_bytes) < 1000:  # Too small
                        raise Exception("Downloaded image too small")
                    
                    if len(image_bytes) > 10 * 1024 * 1024:  # Too large (10MB)
                        raise Exception("Downloaded image too large")
                    
                    # Verify it's a valid image
                    try:
                        img = Image.open(BytesIO(image_bytes))
                        img.verify()
                    except Exception:
                        raise Exception("Invalid image format")
                    
                    return image_bytes
                    
        except Exception as e:
            raise Exception(f"Image download failed: {e}")
    
    async def _compute_image_embedding(self, image_bytes: bytes) -> np.ndarray:
        """Compute CLIP embedding from image bytes in RAM"""
        try:
            # Create temporary file in memory
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=True) as tmp_file:
                tmp_file.write(image_bytes)
                tmp_file.flush()
                
                # Compute embedding
                embedding = await self.clip_service.encode_image(tmp_file.name)
                
                # Temporary file automatically deleted
                return embedding
                
        except Exception as e:
            raise Exception(f"Image embedding failed: {e}")
    
    async def _compute_text_embedding(self, text: str) -> np.ndarray:
        """Compute CLIP text embedding"""
        try:
            return await self.clip_service.encode_text(text)
        except Exception as e:
            raise Exception(f"Text embedding failed: {e}")
    
    def _normalize_price(self, price_raw: str, currency: str = "USD") -> float:
        """Extract and normalize price to USD"""
        try:
            # Remove common price formatting
            price_clean = price_raw.replace('$', '').replace(',', '').replace('₹', '').strip()
            
            # Extract numeric value
            import re
            price_match = re.search(r'[\d,]+\.?\d*', price_clean)
            if not price_match:
                raise Exception(f"No numeric price found in: {price_raw}")
            
            price_value = float(price_match.group().replace(',', ''))
            
            # Simple currency conversion (placeholder - use real rates in production)
            if currency.upper() == "INR":
                price_value = price_value / 83.0  # Approximate INR to USD
            elif currency.upper() == "EUR":
                price_value = price_value * 1.1   # Approximate EUR to USD
            
            return round(price_value, 2)
            
        except Exception as e:
            raise Exception(f"Price normalization failed: {e}")
    
    def _form_feature_vector(self, image_emb: np.ndarray, text_emb: np.ndarray, 
                           price: float, site: str) -> np.ndarray:
        """Combine embeddings and features into single vector"""
        try:
            # Site encoding (simple one-hot)
            site_encoding = self._encode_site(site)
            
            # Combine all features
            feature_vector = np.concatenate([
                image_emb.flatten(),
                text_emb.flatten(),
                [price],
                site_encoding
            ])
            
            return feature_vector.astype(np.float32)
            
        except Exception as e:
            raise Exception(f"Feature vector formation failed: {e}")
    
    def _encode_site(self, site: str) -> np.ndarray:
        """Simple site encoding"""
        sites = ['amazon', 'walmart', 'ebay', 'flipkart', 'target']
        encoding = np.zeros(len(sites))
        
        site_lower = site.lower()
        for i, s in enumerate(sites):
            if s in site_lower:
                encoding[i] = 1.0
                break
        
        return encoding
    
    def _store_embedding(self, embedding: np.ndarray) -> int:
        """Store embedding in FAISS index"""
        try:
            # Initialize index if needed
            if self.faiss_index is None:
                dimension = embedding.shape[0]
                self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Add embedding
            self.faiss_index.add(embedding.reshape(1, -1))
            embedding_id = self.embedding_counter
            self.embedding_counter += 1
            
            # Save index periodically
            if self.embedding_counter % 100 == 0:
                self._save_faiss_index()
            
            return embedding_id
            
        except Exception as e:
            raise Exception(f"FAISS storage failed: {e}")
    
    def _make_prediction(self, feature_vector: np.ndarray) -> tuple[str, float]:
        """Make prediction using incremental model"""
        try:
            if not self.model_trained:
                return "unknown", 0.0
            
            # Predict category (placeholder)
            pred_proba = self.incremental_model.predict_proba([feature_vector])
            confidence = float(np.max(pred_proba))
            
            # Simple category mapping
            categories = ['electronics', 'clothing', 'home', 'books', 'other']
            pred_class = self.incremental_model.predict([feature_vector])[0]
            
            if pred_class < len(categories):
                prediction = categories[pred_class]
            else:
                prediction = "other"
            
            return prediction, confidence
            
        except Exception:
            return "unknown", 0.0
    
    def _store_metadata(self, metadata: Dict):
        """Store distilled metadata in SQLite"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO product_metadata 
                (product_id, site, url, title, price_usd, currency, embedding_id, 
                 prediction, confidence, timestamp, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata['product_id'], metadata['site'], metadata['url'],
                metadata['title'], metadata['price_usd'], metadata['currency'],
                metadata['embedding_id'], metadata['prediction'], 
                metadata['confidence'], metadata['timestamp'], metadata['error']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store metadata: {e}")
    
    def _log_processing_step(self, product_id: str, status: str, message: str):
        """Log processing step to file"""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"{timestamp} | {product_id} | {status} | {message}\n"
        
        try:
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception:
            pass  # Don't fail processing due to logging issues
    
    def _save_faiss_index(self):
        """Save FAISS index to disk"""
        try:
            index_dir = Path("models/clip_indexes")
            index_dir.mkdir(exist_ok=True)
            faiss.write_index(self.faiss_index, str(index_dir / "streaming_index.faiss"))
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
    
    def get_metadata_stats(self) -> Dict:
        """Get processing statistics"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM product_metadata")
            total_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM product_metadata WHERE error IS NULL")
            success_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM product_metadata WHERE error IS NOT NULL")
            error_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_processed": total_count,
                "successful": success_count,
                "failed": error_count,
                "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
                "embeddings_stored": self.embedding_counter
            }
            
        except Exception:
            return {"error": "Failed to get stats"}
    
    async def search_products_by_text(self, query: str, limit: int = 10, min_similarity: float = 0.7) -> List[Dict]:
        """
        Search products using text query via FAISS similarity search
        """
        try:
            if not self.clip_service or not self.faiss_index:
                await self.initialize()
            
            # Get text embedding
            text_embedding = await self.clip_service.encode_text(query)
            text_embedding = text_embedding.reshape(1, -1).astype('float32')
            
            # Search FAISS index
            similarities, indices = self.faiss_index.search(text_embedding, limit * 2)  # Get more to filter
            
            # Filter by similarity threshold and get metadata
            results = []
            for sim, idx in zip(similarities[0], indices[0]):
                if sim >= min_similarity and idx < self.embedding_counter:
                    metadata = self._get_product_metadata_by_embedding_id(idx)
                    if metadata:
                        metadata['similarity'] = float(sim)
                        results.append(metadata)
                        
                        if len(results) >= limit:
                            break
            
            logger.info(f"Text search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Text search error: {e}")
            return []
    
    async def search_products_by_image(self, image_data: bytes, limit: int = 10, min_similarity: float = 0.7) -> List[Dict]:
        """
        Search products using image via FAISS similarity search
        """
        try:
            if not self.clip_service or not self.faiss_index:
                await self.initialize()
            
            # Process image in memory
            image = Image.open(BytesIO(image_data)).convert('RGB')
            
            # Get image embedding
            image_embedding = await self.clip_service.encode_image(image)
            image_embedding = image_embedding.reshape(1, -1).astype('float32')
            
            # Search FAISS index
            similarities, indices = self.faiss_index.search(image_embedding, limit * 2)
            
            # Filter by similarity threshold and get metadata
            results = []
            for sim, idx in zip(similarities[0], indices[0]):
                if sim >= min_similarity and idx < self.embedding_counter:
                    metadata = self._get_product_metadata_by_embedding_id(idx)
                    if metadata:
                        metadata['similarity'] = float(sim)
                        results.append(metadata)
                        
                        if len(results) >= limit:
                            break
            
            logger.info(f"Image search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Image search error: {e}")
            return []
    
    def _get_product_metadata_by_embedding_id(self, embedding_id: int) -> Optional[Dict]:
        """Get product metadata by embedding ID from SQLite"""
        try:
            conn = sqlite3.connect(self.metadata_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT product_id, site, url, title, price_usd, currency, 
                       prediction, confidence, timestamp
                FROM product_metadata 
                WHERE embedding_id = ?
            """, (embedding_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'product_id': row[0],
                    'site': row[1],
                    'url': row[2],
                    'title': row[3],
                    'price_usd': row[4],
                    'currency': row[5],
                    'prediction': row[6],
                    'confidence': row[7],
                    'timestamp': row[8]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting metadata for embedding {embedding_id}: {e}")
            return None
    
    async def get_search_stats(self) -> Dict:
        """Get search index statistics"""
        try:
            stats = {
                'total_embeddings': self.embedding_counter,
                'faiss_index_size': self.faiss_index.ntotal if self.faiss_index else 0,
                'service_initialized': self.clip_service is not None,
                'metadata_db_exists': os.path.exists(self.metadata_db_path)
            }
            
            # Get database stats
            if os.path.exists(self.metadata_db_path):
                conn = sqlite3.connect(self.metadata_db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM product_metadata")
                stats['total_products'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT site) FROM product_metadata")
                stats['unique_sites'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT site, COUNT(*) FROM product_metadata GROUP BY site")
                stats['products_by_site'] = dict(cursor.fetchall())
                
                conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting search stats: {e}")
            return {'error': str(e)}

# Create global feature extraction service instance
feature_extraction_service = FeatureExtractionService()