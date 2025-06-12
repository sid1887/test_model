#!/usr/bin/env python3
"""
AI Model Manager for Cumpair - Handles YOLO, EfficientNet, and CLIP models
"""

import asyncio
import torch
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import time
from datetime import datetime

# Core ML Libraries
from ultralytics import YOLO
import clip
from transformers import AutoProcessor, AutoModel
from PIL import Image
import torchvision.transforms as transforms

# Database imports
from app.models.product import Product
from app.models.analysis import Analysis
from app.core.database import get_db_session
from app.core.gpu_memory import managed_inference, get_optimal_device, get_memory_manager


class ModelManager:
    """Central manager for all AI models used in product analysis."""
    
    def __init__(self):
        self.yolo_model = None
        self.clip_model = None
        self.clip_processor = None
        self.efficientnet_model = None
        # Start with CPU for stability, GPU will be used dynamically
        self.device = "cpu"  
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Log GPU availability
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"🔥 AI Model Manager initialized - Primary: CPU, GPU Available: {gpu_name} ({gpu_memory:.1f}GB)")
        else:
            print(f"🔥 AI Model Manager initialized - CPU only mode")
    
    async def initialize_models(self) -> bool:
        """Initialize all AI models asynchronously."""
        print("🚀 Initializing AI models...")
        
        try:
            # Initialize YOLO for object detection
            await self._load_yolo_model()
            
            # Initialize CLIP for image-text matching
            await self._load_clip_model()
              # Initialize EfficientNet for specification extraction
            await self._load_efficientnet_model()
            
            print("✅ All AI models initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Model initialization failed: {e}")
            return False
            
    async def _load_yolo_model(self):
        """Load YOLO model for object detection with production optimizations."""
        from app.core.monitoring import logger
        
        try:
            yolo_path = self.models_dir / "yolov8n.pt"
            
            # Download YOLO if not exists
            if not yolo_path.exists():
                logger.info("⬇️ Downloading YOLOv8n model...")
                # Disable verbose output during download for production
                import os
                os.environ['YOLO_VERBOSE'] = 'False'
                # Disable ultralytics telemetry in production
                os.environ['YOLO_DISABLE_TELEMETRY'] = 'True'
                self.yolo_model = YOLO('yolov8n.pt')  # This will auto-download
                # Move to models directory
                import shutil
                shutil.move('yolov8n.pt', yolo_path)
            else:                self.yolo_model = YOLO(str(yolo_path))
            
            # Load model on CPU first for stability
            self.yolo_model.to("cpu")
            
            # Production optimizations for YOLO
            if hasattr(self.yolo_model.model, 'eval'):
                self.yolo_model.model.eval()  # Set to evaluation mode
            
            # Configure for production performance
            self.yolo_model.overrides = {
                'verbose': False,  # Disable verbose logging
                'save': False,     # Don't save prediction images
                'show': False,     # Don't show images
                'conf': 0.25,      # Default confidence threshold
                'iou': 0.45,       # IoU threshold for NMS
                'max_det': 300,    # Maximum detections per image
                'half': torch.cuda.is_available(),  # Use FP16 if GPU available
                'device': self.device,
                'workers': 1,      # Single worker for API usage
                'batch': 1,        # Single batch processing
                'imgsz': 640,      # Standard input size
                'augment': False,  # Disable TTA for speed
                'agnostic_nms': False,  # Class-specific NMS
                'retina_masks': False,  # Disable for speed
            }
            
            # Additional memory optimizations for production
            if torch.cuda.is_available():
                torch.cuda.empty_cache()  # Clear GPU cache
                # Enable memory-efficient attention if available
                try:
                    torch.backends.cuda.matmul.allow_tf32 = True
                    torch.backends.cudnn.allow_tf32 = True
                except:
                    pass
            
            # Warm up the model with a test prediction
            test_input = np.zeros((640, 640, 3), dtype=np.uint8)
            warmup_result = self.yolo_model.predict(
                source=test_input, 
                verbose=False,
                save=False,
                show=False
            )
            
            logger.info(f"✅ YOLO model loaded and optimized - Classes: {len(self.yolo_model.names)}")
            logger.info(f"🔧 Production settings applied - Device: {self.device}")
            
        except Exception as e:
            logger.error(f"❌ YOLO loading failed: {e}")
            logger.error(f"🔍 Error context - Path: {yolo_path}, Device: {self.device}")
            raise RuntimeError(f"Failed to initialize YOLO model: {str(e)}") from e
    
    async def _load_clip_model(self):
        """Load CLIP model for image-text matching."""
        print("🔗 Loading CLIP model...")
        
        try:
            model_name = "ViT-B/32"
            self.clip_model, self.clip_processor = clip.load(model_name, device=self.device)
            
            # Test the model
            test_image = torch.randn(1, 3, 224, 224).to(self.device)
            test_text = clip.tokenize(["test"]).to(self.device)
            
            with torch.no_grad():
                _ = self.clip_model.encode_image(test_image)
                _ = self.clip_model.encode_text(test_text)
            
            print(f"✅ CLIP model loaded successfully - Model: {model_name}")
            
        except Exception as e:
            print(f"❌ CLIP loading failed: {e}")
            raise
    
    async def _load_efficientnet_model(self):
        """Load EfficientNet model for specification extraction."""
        print("🧠 Loading EfficientNet model...")
        
        try:
            # For now, we'll create a placeholder
            # In production, this would load a custom-trained model
            self.efficientnet_model = None
            print("⚠️ EfficientNet placeholder loaded (custom model needed)")
            
        except Exception as e:
            print(f"❌ EfficientNet loading failed: {e}")
            raise


class ProductAnalyzer:
    """Main class for analyzing product images using AI models."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.product_categories = {
            # Electronics
            'cell phone': 'Electronics',
            'laptop': 'Electronics', 
            'tablet': 'Electronics',
            'camera': 'Electronics',
            'tv': 'Electronics',
            'headphones': 'Electronics',
            'mouse': 'Electronics',
            'keyboard': 'Electronics',
            
            # Clothing & Fashion
            'person': 'Fashion',  # Often contains clothing
            'tie': 'Fashion',
            'handbag': 'Fashion',
            'suitcase': 'Fashion',
            
            # Home & Garden
            'chair': 'Furniture',
            'couch': 'Furniture',
            'bed': 'Furniture',
            'dining table': 'Furniture',
            'toilet': 'Home & Garden',
            'sink': 'Home & Garden',
            
            # Sports & Outdoors
            'bicycle': 'Sports',
            'motorcycle': 'Automotive',
            'car': 'Automotive',
            'truck': 'Automotive',
            'boat': 'Sports',
            'surfboard': 'Sports',
            'tennis racket': 'Sports',
            'baseball bat': 'Sports',
            'skateboard': 'Sports',
            'skis': 'Sports',
            
            # Kitchen & Dining
            'bottle': 'Kitchen',
            'wine glass': 'Kitchen',
            'cup': 'Kitchen',
            'fork': 'Kitchen',
            'knife': 'Kitchen',
            'spoon': 'Kitchen',
            'bowl': 'Kitchen',
            'banana': 'Food',
            'apple': 'Food',
            'orange': 'Food',
            'broccoli': 'Food',
            'carrot': 'Food',
            'pizza': 'Food',
            'donut': 'Food',
            'cake': 'Food',
        }
    
    async def analyze_product_image(self, image_path: str, product_id: int) -> Dict[str, Any]:
        """
        Complete product analysis pipeline.
        
        Args:
            image_path: Path to the product image
            product_id: Database ID of the product
            
        Returns:
            Dictionary containing all analysis results
        """
        print(f"🔍 Starting analysis for product {product_id}: {image_path}")
        start_time = time.time()
        
        try:
            # Load image
            image = self._load_image(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Run all analysis steps
            analysis_results = {}
            
            # 1. Object Detection with YOLO
            print("🎯 Running object detection...")
            detection_results = await self._detect_objects(image)
            analysis_results['object_detection'] = detection_results
            
            # 2. Category Classification
            print("📂 Classifying product category...")
            category_results = await self._classify_category(image, detection_results)
            analysis_results['category_classification'] = category_results
            
            # 3. Brand Recognition with CLIP
            print("🏷️ Recognizing brand...")
            brand_results = await self._recognize_brand(image)
            analysis_results['brand_recognition'] = brand_results
            
            # 4. Specification Extraction
            print("📋 Extracting specifications...")
            spec_results = await self._extract_specifications(image, category_results)
            analysis_results['specification_extraction'] = spec_results
            
            # 5. Quality Assessment
            print("⭐ Assessing image quality...")
            quality_results = await self._assess_image_quality(image)
            analysis_results['quality_assessment'] = quality_results
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(analysis_results)
            analysis_results['overall_confidence'] = overall_confidence
            
            processing_time = time.time() - start_time
            analysis_results['processing_time'] = processing_time
              # Save to database
            await self._save_analysis_to_db(product_id, analysis_results, processing_time)
            print(f"✅ Analysis completed in {processing_time:.2f}s - Confidence: {overall_confidence:.2f}")
            return analysis_results
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            # Save error to database
            await self._save_error_to_db(product_id, str(e), time.time() - start_time)
            raise
    
    def _load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load and preprocess image."""
        try:
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
            else:
                image = np.array(image_path)
            
            if image is None:
                return None
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image
            
        except Exception as e:
            print(f"❌ Image loading failed: {e}")
            return None
    
    async def _detect_objects(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect objects in the image using YOLO with production optimizations."""
        from app.core.monitoring import logger, ANALYSIS_COUNT
        import time
        
        start_time = time.time()
        
        try:
            # Validate input
            if image is None or image.size == 0:
                raise ValueError("Invalid image input: empty or None")
            
            # Ensure image is in correct format
            if len(image.shape) != 3 or image.shape[2] != 3:
                raise ValueError(f"Invalid image shape: {image.shape}. Expected (H, W, 3)")
            
            # Memory optimization for large images
            max_size = 1280  # Limit max dimension for performance
            h, w = image.shape[:2]
            if max(h, w) > max_size:
                scale = max_size / max(h, w)
                new_h, new_w = int(h * scale), int(w * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                logger.info(f"🔄 Image resized from {w}x{h} to {new_w}x{new_h} for performance")            # Run YOLO inference with hybrid CPU/GPU selection
            with managed_inference("YOLO_Detection", "yolo", 700) as device:
                with torch.inference_mode():  # Use inference_mode for better performance
                    results = self.model_manager.yolo_model.predict(
                        source=image,
                        verbose=False,
                        save=False,
                        show=False,
                        conf=0.25,  # Confidence threshold
                        iou=0.45,   # IoU threshold for NMS
                        max_det=300,  # Maximum detections
                        half=(device == "cuda"),  # Use FP16 only on GPU
                        device=device,  # Use the optimal device selected
                        augment=False,  # Disable test-time augmentation for speed
                        agnostic_nms=False,  # Use class-specific NMS
                    )
            
            detections = []
            total_confidence = 0.0
            
            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        try:
                            # Extract detection info with validation
                            xyxy = box.xyxy[0].cpu().numpy()
                            conf = float(box.conf[0].cpu().numpy())
                            cls = int(box.cls[0].cpu().numpy())
                            
                            # Validate detection data
                            if conf < 0.0 or conf > 1.0:
                                logger.warning(f"Invalid confidence score: {conf}")
                                continue
                                
                            if cls < 0 or cls >= len(self.model_manager.yolo_model.names):
                                logger.warning(f"Invalid class ID: {cls}")
                                continue
                            
                            class_name = self.model_manager.yolo_model.names[cls]
                            total_confidence += conf
                            
                            detection = {
                                'class': class_name,
                                'confidence': round(conf, 4),
                                'bbox': [round(float(x), 2) for x in xyxy.tolist()],
                                'class_id': cls,
                                'area': float((xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1]))
                            }
                            detections.append(detection)
                            
                        except Exception as box_error:
                            logger.warning(f"Failed to process detection box: {box_error}")
                            continue
            
            # Sort by confidence (highest first)
            detections.sort(key=lambda x: x['confidence'], reverse=True)
            
            processing_time = time.time() - start_time
            detection_count = len(detections)
            max_confidence = max([d['confidence'] for d in detections]) if detections else 0.0
            avg_confidence = (total_confidence / detection_count) if detection_count > 0 else 0.0
            
            # Determine primary object with confidence filtering
            primary_object = 'unknown'
            if detections and detections[0]['confidence'] >= 0.5:
                primary_object = detections[0]['class']
            elif detections and detections[0]['confidence'] >= 0.25:
                primary_object = f"{detections[0]['class']}_low_conf"
            
            result = {
                'detections': detections,
                'primary_object': primary_object,
                'detection_count': detection_count,
                'max_confidence': round(max_confidence, 4),
                'avg_confidence': round(avg_confidence, 4),
                'processing_time': round(processing_time, 4),
                'model_version': 'yolov8n_optimized_v2',
                'status': 'success',
                'image_size': f"{image.shape[1]}x{image.shape[0]}"
            }
              # Log performance metrics
            ANALYSIS_COUNT.labels(status='success').inc()
            logger.info(f"Object detection completed: {detection_count} objects in {processing_time:.3f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Object detection failed: {str(e)}"
              # Log the error with context
            logger.error(f"{error_msg} (processing_time: {processing_time:.3f}s)")
            ANALYSIS_COUNT.labels(status='error').inc()
            
            # Return structured error response instead of empty result
            return {
                'detections': [],
                'primary_object': 'unknown',
                'detection_count': 0,
                'max_confidence': 0.0,
                'avg_confidence': 0.0,
                'processing_time': round(processing_time, 4),
                'model_version': 'yolov8n_optimized_v2',
                'status': 'error',
                'error': error_msg,
                'error_type': type(e).__name__,
                'image_size': f"{image.shape[1]}x{image.shape[0]}" if image is not None and len(image.shape) >= 2 else "unknown"
            }
    
    async def _classify_category(self, image: np.ndarray, detection_results: Dict) -> Dict[str, Any]:
        """Classify product category based on detected objects."""
        try:
            primary_object = detection_results.get('primary_object', 'unknown')
            category = self.product_categories.get(primary_object, 'Other')
            
            # Additional logic for better categorization
            detections = detection_results.get('detections', [])
            
            # Look for electronics indicators
            electronics_objects = ['cell phone', 'laptop', 'tv', 'camera', 'mouse', 'keyboard']
            if any(d['class'] in electronics_objects for d in detections):
                category = 'Electronics'
            
            # Look for fashion indicators  
            fashion_objects = ['person', 'tie', 'handbag', 'suitcase']
            if any(d['class'] in fashion_objects for d in detections):
                category = 'Fashion'
            
            confidence = detection_results.get('max_confidence', 0.0)
            
            return {
                'category': category,
                'confidence': confidence,
                'reasoning': f"Based on detected object: {primary_object}",
                'alternative_categories': self._get_alternative_categories(detections)
            }
            
        except Exception as e:
            print(f"❌ Category classification failed: {e}")
            return {'category': 'Other', 'confidence': 0.0, 'reasoning': 'Classification failed'}
    
    def _get_alternative_categories(self, detections: List[Dict]) -> List[str]:
        """Get alternative category suggestions."""
        categories = set()
        for detection in detections[:3]:  # Top 3 detections
            obj_class = detection['class']
            if obj_class in self.product_categories:
                categories.add(self.product_categories[obj_class])
        return list(categories)
    
    async def _recognize_brand(self, image: np.ndarray) -> Dict[str, Any]:
        """Recognize brand using CLIP model."""
        try:
            # Convert image to PIL
            pil_image = Image.fromarray(image)
            
            # Common brand names to search for
            brand_queries = [
                "Apple logo", "Samsung logo", "Nike logo", "Adidas logo",
                "Sony logo", "Microsoft logo", "Google logo", "Amazon logo",
                "Dell logo", "HP logo", "Lenovo logo", "ASUS logo",
                "Canon logo", "Nikon logo", "iPhone", "Galaxy phone",
                "MacBook", "Surface laptop", "iPad", "no brand visible"
            ]
            
            # Preprocess image for CLIP
            image_input = self.model_manager.clip_processor(pil_image).unsqueeze(0).to(self.model_manager.device)
            text_inputs = clip.tokenize(brand_queries).to(self.model_manager.device)
            
            # Get similarities
            with torch.no_grad():
                image_features = self.model_manager.clip_model.encode_image(image_input)
                text_features = self.model_manager.clip_model.encode_text(text_inputs)
                
                # Calculate similarities
                similarities = torch.cosine_similarity(image_features, text_features, dim=1)
                similarities = similarities.cpu().numpy()
            
            # Get top matches
            top_indices = np.argsort(similarities)[::-1][:3]
            
            brand_results = []
            for idx in top_indices:
                brand_results.append({
                    'brand': brand_queries[idx],
                    'confidence': float(similarities[idx]),
                    'score': float(similarities[idx])
                })
            
            # Extract likely brand name
            top_match = brand_results[0]
            brand_name = self._extract_brand_name(top_match['brand'])
            
            return {
                'detected_brand': brand_name,
                'confidence': top_match['confidence'],
                'all_matches': brand_results,
                'method': 'CLIP similarity'
            }
            
        except Exception as e:
            print(f"❌ Brand recognition failed: {e}")
            return {'detected_brand': 'Unknown', 'confidence': 0.0, 'method': 'Failed'}
    
    def _extract_brand_name(self, brand_query: str) -> str:
        """Extract clean brand name from query."""
        # Remove common words
        brand = brand_query.replace(' logo', '').replace(' phone', '').replace(' laptop', '')
        
        # Map specific cases
        brand_mapping = {
            'iPhone': 'Apple',
            'MacBook': 'Apple', 
            'iPad': 'Apple',
            'Galaxy phone': 'Samsung',
            'Surface laptop': 'Microsoft',
            'no brand visible': 'Unknown'
        }
        
        return brand_mapping.get(brand, brand.title())
    
    async def _extract_specifications(self, image: np.ndarray, category_results: Dict) -> Dict[str, Any]:
        """Extract product specifications based on category."""
        try:
            category = category_results.get('category', 'Other')
            
            # For now, we'll use rule-based extraction
            # In production, this would use a trained EfficientNet model
            
            specs = {}
            confidence = 0.5  # Placeholder confidence
            
            if category == 'Electronics':
                specs = await self._extract_electronics_specs(image)
            elif category == 'Fashion':
                specs = await self._extract_fashion_specs(image)
            elif category == 'Furniture':
                specs = await self._extract_furniture_specs(image)
            else:
                specs = await self._extract_general_specs(image)
            
            return {
                'specifications': specs,
                'confidence': confidence,
                'category': category,
                'extraction_method': 'rule_based_placeholder'
            }
            
        except Exception as e:
            print(f"❌ Specification extraction failed: {e}")
            return {'specifications': {}, 'confidence': 0.0, 'category': 'Unknown'}
    
    async def _extract_electronics_specs(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract electronics-specific specifications."""
        # Placeholder implementation
        height, width = image.shape[:2]
        aspect_ratio = width / height
        
        return {
            'estimated_size': 'medium' if 0.7 < aspect_ratio < 1.3 else 'rectangular',
            'color_analysis': self._analyze_dominant_colors(image),
            'form_factor': 'portrait' if aspect_ratio < 0.8 else 'landscape' if aspect_ratio > 1.2 else 'square'
        }
    
    async def _extract_fashion_specs(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract fashion-specific specifications."""
        return {
            'color_analysis': self._analyze_dominant_colors(image),
            'estimated_type': 'clothing_item'
        }
    
    async def _extract_furniture_specs(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract furniture-specific specifications."""
        return {
            'color_analysis': self._analyze_dominant_colors(image),
            'estimated_material': 'mixed'
        }
    
    async def _extract_general_specs(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract general specifications."""
        return {
            'color_analysis': self._analyze_dominant_colors(image)
        }
    
    def _analyze_dominant_colors(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze dominant colors in the image."""
        try:
            # Reshape image to list of pixels
            pixels = image.reshape(-1, 3)
            
            # Use k-means clustering to find dominant colors
            from sklearn.cluster import KMeans
            
            # Reduce number of pixels for faster processing
            if len(pixels) > 10000:
                indices = np.random.choice(len(pixels), 10000, replace=False)
                pixels = pixels[indices]
            
            # Find 3 dominant colors
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            kmeans.fit(pixels)
            
            colors = kmeans.cluster_centers_.astype(int)
            
            # Convert to color names (simplified)
            color_names = []
            for color in colors:
                color_name = self._rgb_to_color_name(color)
                color_names.append(color_name)
            
            return {
                'dominant_colors': color_names,
                'rgb_values': colors.tolist()
            }
            
        except Exception as e:
            print(f"❌ Color analysis failed: {e}")
            return {'dominant_colors': ['unknown'], 'rgb_values': []}
    
    def _rgb_to_color_name(self, rgb: np.ndarray) -> str:
        """Convert RGB values to approximate color name."""
        r, g, b = rgb
        
        # Simple color mapping
        if r > 200 and g > 200 and b > 200:
            return 'white'
        elif r < 50 and g < 50 and b < 50:
            return 'black'
        elif r > g and r > b:
            return 'red'
        elif g > r and g > b:
            return 'green'
        elif b > r and b > g:
            return 'blue'
        elif r > 150 and g > 150 and b < 100:
            return 'yellow'
        elif r > 150 and g < 100 and b > 150:
            return 'purple'
        elif r < 100 and g > 150 and b > 150:
            return 'cyan'
        else:
            return 'mixed'
    
    async def _assess_image_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Assess the quality of the image for analysis."""
        try:
            height, width = image.shape[:2]
            
            # Resolution assessment
            total_pixels = height * width
            resolution_score = min(total_pixels / (1920 * 1080), 1.0)  # Normalize to 1080p
            
            # Blur assessment (using Laplacian variance)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_normalized = min(blur_score / 1000, 1.0)  # Normalize
            
            # Brightness assessment
            brightness = np.mean(gray)
            brightness_score = 1.0 - abs(brightness - 127) / 127  # Optimal around 127
            
            # Overall quality score
            quality_score = (resolution_score * 0.3 + blur_normalized * 0.4 + brightness_score * 0.3)
            
            return {
                'quality_score': float(quality_score),
                'resolution': {'width': width, 'height': height, 'score': float(resolution_score)},
                'sharpness': {'score': float(blur_normalized), 'variance': float(blur_score)},
                'brightness': {'score': float(brightness_score), 'mean': float(brightness)},
                'recommendation': 'good' if quality_score > 0.7 else 'acceptable' if quality_score > 0.5 else 'poor'
            }
            
        except Exception as e:
            print(f"❌ Quality assessment failed: {e}")
            return {'quality_score': 0.5, 'recommendation': 'unknown'}
    
    def _calculate_overall_confidence(self, analysis_results: Dict) -> float:
        """Calculate overall confidence score from all analysis components."""
        try:
            # Weight different components
            weights = {
                'object_detection': 0.3,
                'category_classification': 0.25,
                'brand_recognition': 0.2,
                'specification_extraction': 0.15,
                'quality_assessment': 0.1
            }
            
            total_confidence = 0.0
            total_weight = 0.0
            
            for component, weight in weights.items():
                if component in analysis_results:
                    component_confidence = self._extract_component_confidence(analysis_results[component])
                    total_confidence += component_confidence * weight
                    total_weight += weight
            
            return total_confidence / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            print(f"❌ Confidence calculation failed: {e}")
            return 0.0
    
    def _extract_component_confidence(self, component_result: Dict) -> float:
        """Extract confidence score from component result."""
        if 'confidence' in component_result:
            return float(component_result['confidence'])
        elif 'max_confidence' in component_result:
            return float(component_result['max_confidence'])
        elif 'quality_score' in component_result:
            return float(component_result['quality_score'])
        else:
            return 0.5  # Default confidence
    
    async def _save_analysis_to_db(self, product_id: int, analysis_results: Dict, processing_time: float):
        """Save analysis results to database."""
        try:
            async with get_db_session() as session:
                analysis = Analysis(
                    product_id=product_id,
                    analysis_type="complete_vision_analysis",
                    raw_results=analysis_results,
                    processed_results={
                        'category': analysis_results.get('category_classification', {}).get('category', 'Unknown'),
                        'brand': analysis_results.get('brand_recognition', {}).get('detected_brand', 'Unknown'),
                        'specifications': analysis_results.get('specification_extraction', {}).get('specifications', {}),
                        'primary_object': analysis_results.get('object_detection', {}).get('primary_object', 'unknown')
                    },
                    confidence_score=analysis_results.get('overall_confidence', 0.0),
                    processing_time=processing_time,
                    model_version="yolo8n+clip+custom-v1.0",
                    status="completed"
                )
                
                session.add(analysis)
                await session.commit()
                print(f"💾 Analysis saved to database for product {product_id}")
                
        except Exception as e:
            print(f"❌ Failed to save analysis to database: {e}")
    
    async def _save_error_to_db(self, product_id: int, error_message: str, processing_time: float):
        """Save analysis error to database."""
        try:
            async with get_db_session() as session:
                analysis = Analysis(
                    product_id=product_id,
                    analysis_type="complete_vision_analysis",
                    raw_results={},
                    processed_results={},
                    confidence_score=0.0,
                    processing_time=processing_time,
                    model_version="yolo8n+clip+custom-v1.0",
                    status="failed",
                    error_message=error_message
                )
                
                session.add(analysis)
                await session.commit()
                print(f"💾 Error saved to database for product {product_id}")
                
        except Exception as e:
            print(f"❌ Failed to save error to database: {e}")


# Global model manager instance
model_manager = ModelManager()
product_analyzer = ProductAnalyzer(model_manager)


async def initialize_ai_system():
    """Initialize the complete AI system."""
    print("🔥 Initializing Cumpair AI System...")
    success = await model_manager.initialize_models()
    if success:
        print("🚀 AI System ready for product analysis!")
    else:
        print("❌ AI System initialization failed!")
    return success


if __name__ == "__main__":
    # Test the AI system
    asyncio.run(initialize_ai_system())
