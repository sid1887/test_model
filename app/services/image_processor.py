"""
Enhanced Image Processor
Integrates YOLO, CLIP, OCR, Barcode Detection, and Image Captioning
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import uuid
import json

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Unified image processing service"""
    
    def __init__(self):
        self.yolo_model = None
        self.clip_service = None
        self.hf_connector = None
        self.ocr_engine = None
        
        # Processing metrics
        self.processed_count = 0
        self.total_processing_time = 0.0
        self.error_count = 0
        
        # Upload directory
        self.upload_dir = Path(os.getenv('UPLOAD_DIR', 'uploads'))
        self.upload_dir.mkdir(exist_ok=True)
        
        logger.info("🖼️  Image Processor initialized")
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing image processing components...")
        
        # Initialize YOLO
        await self._init_yolo()
        
        # Initialize CLIP
        await self._init_clip()
        
        # Initialize OCR
        await self._init_ocr()
        
        # Initialize HF connector for captioning
        await self._init_hf()
        
        logger.info("✅ Image Processor ready")
    
    async def _init_yolo(self):
        """Initialize YOLO model"""
        try:
            from ultralytics import YOLO
            
            model_path = os.getenv('YOLO_MODEL_PATH', 'yolov8n.pt')
            
            loop = asyncio.get_event_loop()
            self.yolo_model = await loop.run_in_executor(
                None,
                lambda: YOLO(model_path)
            )
            
            logger.info(f"✅ YOLO model loaded: {model_path}")
            
        except Exception as e:
            logger.warning(f"YOLO initialization failed: {e}")
            self.yolo_model = None
    
    async def _init_clip(self):
        """Initialize CLIP service"""
        try:
            from app.services.clip_search import CLIPSearchService
            
            self.clip_service = CLIPSearchService()
            await self.clip_service.initialize()
            
            logger.info("✅ CLIP service ready")
            
        except Exception as e:
            logger.warning(f"CLIP initialization failed: {e}")
            self.clip_service = None
    
    async def _init_ocr(self):
        """Initialize OCR engine"""
        try:
            import easyocr
            
            loop = asyncio.get_event_loop()
            self.ocr_engine = await loop.run_in_executor(
                None,
                lambda: easyocr.Reader(['en'], gpu=False)
            )
            
            logger.info("✅ EasyOCR initialized")
            
        except ImportError:
            # Fallback to Tesseract
            try:
                import pytesseract
                self.ocr_engine = 'tesseract'
                logger.info("✅ Tesseract OCR ready")
            except ImportError:
                logger.warning("No OCR engine available")
                self.ocr_engine = None
                
        except Exception as e:
            logger.warning(f"OCR initialization failed: {e}")
            self.ocr_engine = None
    
    async def _init_hf(self):
        """Initialize HuggingFace connector"""
        try:
            from app.services.huggingface_connector import get_hf_connector
            
            self.hf_connector = get_hf_connector()
            logger.info("✅ HF connector ready for captioning")
            
        except Exception as e:
            logger.warning(f"HF connector initialization failed: {e}")
            self.hf_connector = None
    
    async def save_upload(
        self,
        file_bytes: bytes,
        filename: str,
        source: str = 'upload'
    ) -> Dict[str, Any]:
        """
        Save uploaded image and return metadata
        
        Args:
            file_bytes: Image file bytes
            filename: Original filename
            source: Source type (camera, upload, url)
            
        Returns:
            Dict with image_id, url, and metadata
        """
        try:
            # Generate unique ID
            image_id = str(uuid.uuid4())
            ext = Path(filename).suffix or '.jpg'
            new_filename = f"{image_id}{ext}"
            
            # Save file
            file_path = self.upload_dir / new_filename
            file_path.write_bytes(file_bytes)
            
            # Get file size
            file_size = len(file_bytes)
            
            logger.info(f"Saved image: {new_filename} ({file_size} bytes)")
            
            return {
                'status': 'ok',
                'image_id': image_id,
                'url': f'/uploads/{new_filename}',
                'filename': filename,
                'source': source,
                'size': file_size,
                'path': str(file_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to save upload: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def analyze_image(
        self,
        image_path: str,
        tasks: List[str]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive image analysis
        
        Args:
            image_path: Path to image file
            tasks: List of analysis tasks ['clip', 'barcode', 'ocr', 'caption', 'objects']
            
        Returns:
            Dict with results for each task
        """
        start_time = time.time()
        results = {}
        
        try:
            # Run tasks in parallel where possible
            async_tasks = []
            
            if 'clip' in tasks and self.clip_service:
                async_tasks.append(('clip', self._run_clip_analysis(image_path)))
            
            if 'barcode' in tasks and self.yolo_model:
                async_tasks.append(('barcode', self._detect_barcodes(image_path)))
            
            if 'ocr' in tasks and self.ocr_engine:
                async_tasks.append(('ocr', self._extract_text(image_path)))
            
            if 'caption' in tasks and self.hf_connector:
                async_tasks.append(('caption', self._generate_caption(image_path)))
            
            if 'objects' in tasks and self.yolo_model:
                async_tasks.append(('objects', self._detect_objects(image_path)))
            
            # Execute all tasks
            if async_tasks:
                task_results = await asyncio.gather(
                    *[task[1] for task in async_tasks],
                    return_exceptions=True
                )
                
                for (task_name, _), result in zip(async_tasks, task_results):
                    if isinstance(result, Exception):
                        results[task_name] = {'error': str(result)}
                    else:
                        results[task_name] = result
            
            # Update metrics
            processing_time = time.time() - start_time
            self.processed_count += 1
            self.total_processing_time += processing_time
            
            return {
                'status': 'ok',
                'results': results,
                'processing_time': round(processing_time, 3)
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            self.error_count += 1
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _run_clip_analysis(self, image_path: str) -> Dict[str, Any]:
        """Run CLIP similarity search"""
        try:
            if not self.clip_service:
                return {'error': 'CLIP service not available'}
            
            # Get similar products
            matches = await self.clip_service.search_by_image(image_path, top_k=5)
            
            return {
                'matches': matches,
                'count': len(matches) if matches else 0
            }
            
        except Exception as e:
            logger.error(f"CLIP analysis error: {e}")
            return {'error': str(e)}
    
    async def _detect_barcodes(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect and decode barcodes/QR codes"""
        try:
            import cv2
            from pyzbar import pyzbar
            
            # Read image
            image = cv2.imread(image_path)
            
            # Detect barcodes
            loop = asyncio.get_event_loop()
            barcodes = await loop.run_in_executor(
                None,
                lambda: pyzbar.decode(image)
            )
            
            results = []
            for barcode in barcodes:
                results.append({
                    'type': barcode.type,
                    'data': barcode.data.decode('utf-8'),
                    'rect': {
                        'x': barcode.rect.left,
                        'y': barcode.rect.top,
                        'width': barcode.rect.width,
                        'height': barcode.rect.height
                    }
                })
            
            return results
            
        except ImportError:
            logger.warning("pyzbar not installed, using YOLO for detection")
            return await self._detect_barcodes_yolo(image_path)
        except Exception as e:
            logger.error(f"Barcode detection error: {e}")
            return []
    
    async def _detect_barcodes_yolo(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect barcodes using YOLO (no decoding)"""
        try:
            if not self.yolo_model:
                return []
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.yolo_model(image_path)
            )
            
            barcodes = []
            for result in results:
                for box in result.boxes:
                    # Look for barcode/QR-like objects
                    # This is a simplified version
                    barcodes.append({
                        'type': 'detected',
                        'confidence': float(box.conf),
                        'bbox': box.xyxy.tolist()[0]
                    })
            
            return barcodes
            
        except Exception as e:
            logger.error(f"YOLO barcode detection error: {e}")
            return []
    
    async def _extract_text(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            if self.ocr_engine == 'tesseract':
                import pytesseract
                from PIL import Image
                
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    lambda: pytesseract.image_to_string(Image.open(image_path))
                )
                
                return text.strip()
            
            elif self.ocr_engine:  # EasyOCR
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    lambda: self.ocr_engine.readtext(image_path)
                )
                
                text_parts = [result[1] for result in results]
                return ' '.join(text_parts)
            
            else:
                return ''
                
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ''
    
    async def _generate_caption(self, image_path: str) -> str:
        """Generate image caption using HuggingFace"""
        try:
            if not self.hf_connector:
                return ''
            
            caption = await self.hf_connector.caption_image(image_path=image_path)
            return caption or ''
            
        except Exception as e:
            logger.error(f"Captioning error: {e}")
            return ''
    
    async def _detect_objects(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect objects using YOLO"""
        try:
            if not self.yolo_model:
                return []
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.yolo_model(image_path)
            )
            
            objects = []
            for result in results:
                for box in result.boxes:
                    objects.append({
                        'class': result.names[int(box.cls)],
                        'confidence': float(box.conf),
                        'bbox': box.xyxy.tolist()[0]
                    })
            
            return objects
            
        except Exception as e:
            logger.error(f"Object detection error: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics"""
        avg_time = (
            self.total_processing_time / self.processed_count
            if self.processed_count > 0
            else 0.0
        )
        
        return {
            'images_processed': self.processed_count,
            'errors_total': self.error_count,
            'avg_processing_time': round(avg_time, 3),
            'components': {
                'yolo': self.yolo_model is not None,
                'clip': self.clip_service is not None,
                'ocr': self.ocr_engine is not None,
                'captioning': self.hf_connector is not None
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check all components"""
        components = {}
        
        # Check YOLO
        components['yolo'] = {
            'available': self.yolo_model is not None,
            'status': 'ready' if self.yolo_model else 'unavailable'
        }
        
        # Check CLIP
        components['clip'] = {
            'available': self.clip_service is not None,
            'status': 'ready' if self.clip_service else 'unavailable'
        }
        
        # Check OCR
        components['ocr'] = {
            'available': self.ocr_engine is not None,
            'status': 'ready' if self.ocr_engine else 'unavailable'
        }
        
        # Check HF
        components['captioning'] = {
            'available': self.hf_connector is not None,
            'status': 'ready' if self.hf_connector else 'unavailable'
        }
        
        healthy = any(c['available'] for c in components.values())
        
        return {
            'status': 'healthy' if healthy else 'degraded',
            'components': components,
            'healthy': healthy
        }


# Singleton instance
_image_processor: Optional[ImageProcessor] = None


async def get_image_processor() -> ImageProcessor:
    """Get or create image processor singleton"""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
        await _image_processor.initialize()
    return _image_processor
