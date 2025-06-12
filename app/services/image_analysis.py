"""
Image Analysis Service - Core component for product detection and specification extraction
Implements YOLOv8 for object detection and EfficientNet for spec extraction
"""

import cv2
import numpy as np
from PIL import Image, ImageFilter
import torch
import torchvision.transforms as transforms
from ultralytics import YOLO
import tensorflow as tf
import hashlib
import logging
from typing import Dict, List, Tuple, Optional
import json
import time

from app.core.config import settings
from app.core.monitoring import ANALYSIS_COUNT, logger

class ObjectDetector:
    """YOLOv8-based object detection for products"""
    
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load YOLOv8 model"""
        try:
            self.model = YOLO(settings.yolo_model_path)
            logger.info("YOLOv8 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            # Download default model if not found
            self.model = YOLO('yolov8n.pt')
            logger.info("Downloaded and loaded default YOLOv8n model")
    
    def detect_products(self, image_path: str, confidence: float = 0.5) -> Dict:
        """
        Detect products in image using YOLOv8
        
        Args:
            image_path: Path to the image file
            confidence: Confidence threshold for detection
            
        Returns:
            Dictionary containing detection results
        """
        start_time = time.time()
        
        try:
            # Run inference
            results = self.model.predict(
                source=image_path,
                conf=confidence,
                save=False,
                verbose=False
            )
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        detection = {
                            'class_id': int(box.cls.item()),
                            'class_name': self.model.names[int(box.cls.item())],
                            'confidence': float(box.conf.item()),
                            'bbox': box.xyxy.tolist()[0],  # [x1, y1, x2, y2]
                        }
                        detections.append(detection)
            
            processing_time = time.time() - start_time
            
            # Save cropped product images if detected
            cropped_paths = []
            if detections:
                cropped_paths = self._save_cropped_products(image_path, detections)
            
            result_data = {
                'detections': detections,
                'processing_time': processing_time,
                'cropped_paths': cropped_paths,
                'model_version': 'yolov8n',
                'status': 'success'
            }
            
            ANALYSIS_COUNT.labels(status='success').inc()
            logger.info(f"Object detection completed in {processing_time:.2f}s")
            
            return result_data
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            ANALYSIS_COUNT.labels(status='error').inc()
            return {
                'detections': [],
                'error': str(e),
                'status': 'error'
            }
    
    def _save_cropped_products(self, image_path: str, detections: List[Dict]) -> List[str]:
        """Save cropped product regions"""
        cropped_paths = []
        
        try:
            image = cv2.imread(image_path)
            
            for i, detection in enumerate(detections):
                bbox = detection['bbox']
                x1, y1, x2, y2 = map(int, bbox)
                
                # Crop the image
                cropped = image[y1:y2, x1:x2]
                
                # Generate unique filename
                crop_filename = f"{image_path.split('/')[-1].split('.')[0]}_crop_{i}.jpg"
                crop_path = f"{settings.upload_dir}/{crop_filename}"
                
                # Save cropped image
                cv2.imwrite(crop_path, cropped)
                cropped_paths.append(crop_path)
                
        except Exception as e:
            logger.error(f"Failed to save cropped products: {e}")
            
        return cropped_paths

class SpecificationExtractor:
    """Enhanced EfficientNet-based specification extraction with OCR integration"""
    
    def __init__(self):
        self.model = None
        self.ocr_model = None
        self.load_model()
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # Enhanced features
        self._spec_patterns = self._load_specification_patterns()
        self._color_detector = self._init_color_detector()
        self._text_processor = self._init_text_processor()
    
    def _load_specification_patterns(self) -> Dict:
        """Load regex patterns for common specifications"""
        return {
            'dimensions': [
                r'(\d+\.?\d*)\s*[x×]\s*(\d+\.?\d*)\s*[x×]\s*(\d+\.?\d*)\s*(cm|mm|inch|in)',
                r'(\d+\.?\d*)\s*(cm|mm|inch|in)\s*[x×]\s*(\d+\.?\d*)\s*(cm|mm|inch|in)',
                r'Size:\s*(\d+\.?\d*)\s*[x×]\s*(\d+\.?\d*)\s*(cm|mm|inch|in)'
            ],
            'weight': [
                r'(\d+\.?\d*)\s*(kg|g|lbs|oz|pounds)',
                r'Weight:\s*(\d+\.?\d*)\s*(kg|g|lbs|oz)',
                r'(\d+\.?\d*)\s*(kilograms|grams)'
            ],
            'material': [
                r'(?:Material|Made of|Fabric):\s*([A-Za-z\s]+)',
                r'(\d+)%\s*([A-Za-z]+)',
                r'(Cotton|Polyester|Wool|Silk|Leather|Metal|Plastic|Wood|Glass)'
            ],
            'color': [
                r'Color:\s*([A-Za-z\s]+)',
                r'Available in:\s*([A-Za-z\s,]+)',
                r'(Black|White|Red|Blue|Green|Yellow|Pink|Purple|Orange|Brown|Gray|Grey)'
            ],
            'brand': [
                r'Brand:\s*([A-Za-z\s&]+)',
                r'by\s+([A-Za-z\s&]+)',
                r'®\s*([A-Za-z\s&]+)'
            ],
            'model': [
                r'Model:\s*([A-Za-z0-9\-\s]+)',
                r'Model\s+#?\s*([A-Za-z0-9\-\s]+)',
                r'SKU:\s*([A-Za-z0-9\-\s]+)'
            ]
        }
    
    def _init_color_detector(self):
        """Initialize color detection using computer vision"""
        try:
            import cv2
            return cv2
        except ImportError:
            logger.warning("OpenCV not available for color detection")
            return None
            
    def _init_text_processor(self):
        """Initialize OCR processor"""
        ocr_engines = {}
        
        # Try Tesseract
        try:
            import pytesseract
            ocr_engines['tesseract'] = pytesseract
            logger.info("Tesseract OCR initialized")
        except ImportError:
            logger.warning("Tesseract not available")
        
        # Try EasyOCR
        try:
            import easyocr
            ocr_engines['easyocr'] = easyocr.Reader(['en'], gpu=torch.cuda.is_available())
            logger.info("EasyOCR initialized successfully")
        except ImportError:
            logger.info("EasyOCR not available")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {e}")
        
        return ocr_engines if ocr_engines else None
    
    def load_model(self):
        """Load specification extraction model"""
        try:
            # Try to load custom trained model
            if settings.efficientnet_model_path:
                self.model = tf.keras.models.load_model(settings.efficientnet_model_path)
                logger.info("Custom specification model loaded")
            else:
                # Use pre-trained EfficientNet as fallback
                self.model = tf.keras.applications.EfficientNetB0(
                    weights='imagenet',
                    include_top=False,
                    pooling='avg'
                )
                logger.info("Using pre-trained EfficientNet-B0 for specifications")
                
        except Exception as e:
            logger.error(f"Failed to load specification model: {e}")
            self.model = None
    
    def extract_specifications(self, image_path: str) -> Dict:
        """
        Extract product specifications from image
        
        Args:
            image_path: Path to product image (usually cropped)
            
        Returns:
            Dictionary containing extracted specifications
        """
        start_time = time.time()
        
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            
            # Basic image analysis for text/specs
            specs = self._analyze_image_content(image)
            
            # If custom model is available, use it for feature extraction
            if self.model:
                features = self._extract_features(image)
                specs['features'] = features.tolist() if features is not None else []
            
            processing_time = time.time() - start_time
            
            result = {
                'specifications': specs,
                'processing_time': processing_time,
                'confidence': 0.8,  # Placeholder confidence
                'status': 'success'
            }
            
            logger.info(f"Specification extraction completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Specification extraction failed: {e}")
            return {
                'specifications': {},
                'error': str(e),
                'status': 'error'
            }
    
    def _analyze_image_content(self, image: Image.Image) -> Dict:
        """Analyze image for basic specifications"""
        specs = {}
        
        # Image properties
        specs['image_size'] = f"{image.width}x{image.height}"
        specs['color_mode'] = image.mode
        
        # Color analysis
        colors = image.getcolors(maxcolors=256*256*256)
        if colors:
            dominant_color = max(colors, key=lambda x: x[0])[1]
            specs['dominant_color'] = dominant_color
        
        # Basic content analysis (placeholder for OCR/text detection)
        # In production, you would use Tesseract or similar for text extraction
        specs['detected_text'] = []  # Placeholder for OCR results
        
        return specs
    
    def _extract_features(self, image: Image.Image) -> Optional[np.ndarray]:
        """Extract features using the loaded model"""
        try:
            # Preprocess image
            img_array = np.array(image.resize((224, 224)))
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array.astype('float32') / 255.0
            
            # Extract features
            features = self.model.predict(img_array, verbose=0)
            return features[0]
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None

class ImageAnalysisService:
    """Main service for image analysis combining detection and specification extraction"""
    
    def __init__(self):
        self.detector = ObjectDetector()
        self.spec_extractor = SpecificationExtractor()
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Complete image analysis pipeline
        
        Args:
            image_path: Path to the uploaded image
            
        Returns:
            Complete analysis results
        """
        start_time = time.time()
        
        # Generate image hash for deduplication
        image_hash = self._generate_image_hash(image_path)
        
        # Step 1: Object Detection
        detection_results = self.detector.detect_products(image_path)
        
        # Step 2: Specification Extraction
        spec_results = {}
        if detection_results.get('cropped_paths'):
            # Extract specs from the first detected product
            main_crop = detection_results['cropped_paths'][0]
            spec_results = self.spec_extractor.extract_specifications(main_crop)
        else:
            # Extract specs from original image if no products detected
            spec_results = self.spec_extractor.extract_specifications(image_path)
        
        total_time = time.time() - start_time
        
        # Combine results
        analysis_result = {
            'image_hash': image_hash,
            'object_detection': detection_results,
            'specification_extraction': spec_results,
            'total_processing_time': total_time,
            'timestamp': time.time(),
            'status': 'completed' if detection_results.get('status') == 'success' else 'partial'
        }
        
        logger.info(f"Complete image analysis finished in {total_time:.2f}s")
        return analysis_result
    
    def _generate_image_hash(self, image_path: str) -> str:
        """Generate hash for image deduplication"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return hashlib.sha256(image_data).hexdigest()
        except Exception as e:
            logger.error(f"Failed to generate image hash: {e}")
            return ""

# Global service instance
image_analysis_service = ImageAnalysisService()
