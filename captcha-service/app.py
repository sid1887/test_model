"""
Self-Hosted 2captcha-Compatible Captcha Solving Service
Implements the 2captcha API for local captcha solving using multiple OCR engines
"""

import os
import uuid
import time
import base64
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from flask import Flask, request, jsonify
import redis
from PIL import Image, ImageFilter, ImageEnhance
import pytesseract
import cv2
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Redis for task queue
redis_client = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)

# Configuration
TEMP_DIR = Path("/app/temp")
TEMP_DIR.mkdir(exist_ok=True)

# OCR engines initialization
OCR_ENGINES = {}

def init_ocr_engines():
    """Initialize available OCR engines"""
    # Tesseract is always available in the container
    OCR_ENGINES['tesseract'] = True
    logger.info("Tesseract OCR initialized")
    
    # Try to initialize EasyOCR
    try:
        import easyocr
        OCR_ENGINES['easyocr'] = easyocr.Reader(['en'], gpu=False)
        logger.info("EasyOCR initialized successfully")
    except Exception as e:
        logger.warning(f"EasyOCR initialization failed: {e}")

class CaptchaSolver:
    """Enhanced captcha solver with multiple methods"""
    
    def __init__(self):
        self.methods = [
            self._solve_with_easyocr,
            self._solve_with_tesseract_enhanced,
            self._solve_with_tesseract_basic
        ]
    
    def solve_captcha(self, image_path: str, captcha_type: str = "text") -> Optional[str]:
        """Solve captcha using best available method"""
        for method in self.methods:
            try:
                result = method(image_path)
                if result and len(result) >= 3:  # Minimum length check
                    logger.info(f"Captcha solved with {method.__name__}: {result}")
                    return result
            except Exception as e:
                logger.debug(f"Method {method.__name__} failed: {e}")
                continue
        
        logger.warning("All captcha solving methods failed")
        return None
    
    def _solve_with_easyocr(self, image_path: str) -> Optional[str]:
        """Solve using EasyOCR"""
        if 'easyocr' not in OCR_ENGINES:
            return None
        
        try:
            reader = OCR_ENGINES['easyocr']
            results = reader.readtext(image_path)
            
            if results:
                # Extract text with highest confidence
                text = ' '.join([result[1] for result in results if result[2] > 0.6])
                text = ''.join(c for c in text if c.isalnum())
                return text if len(text) >= 3 else None
        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
        
        return None
    
    def _solve_with_tesseract_enhanced(self, image_path: str) -> Optional[str]:
        """Enhanced Tesseract with preprocessing"""
        try:
            # Load and preprocess image
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Multiple preprocessing techniques
            preprocessed_images = []
            
            # 1. Gaussian blur + threshold
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh1 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            preprocessed_images.append(thresh1)
            
            # 2. Morphological operations
            kernel = np.ones((3, 3), np.uint8)
            opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            _, thresh2 = cv2.threshold(opened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            preprocessed_images.append(thresh2)
            
            # 3. Erosion + dilation
            eroded = cv2.erode(gray, kernel, iterations=1)
            dilated = cv2.dilate(eroded, kernel, iterations=1)
            preprocessed_images.append(dilated)
            
            # Try OCR on each preprocessed image
            configs = [
                '--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                '--psm 6',
                '--psm 13'
            ]
            
            for img in preprocessed_images:
                for config in configs:
                    text = pytesseract.image_to_string(img, config=config)
                    text = ''.join(c for c in text.strip() if c.isalnum())
                    if text and len(text) >= 3:
                        return text
        
        except Exception as e:
            logger.error(f"Enhanced Tesseract failed: {e}")
        
        return None
    
    def _solve_with_tesseract_basic(self, image_path: str) -> Optional[str]:
        """Basic Tesseract OCR"""
        try:
            # Simple preprocessing
            img = Image.open(image_path).convert('L')
            img = img.filter(ImageFilter.SHARPEN)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.0)
            
            # OCR
            text = pytesseract.image_to_string(img, config='--psm 8')
            text = ''.join(c for c in text.strip() if c.isalnum())
            
            return text if len(text) >= 3 else None
            
        except Exception as e:
            logger.error(f"Basic Tesseract failed: {e}")
            return None

# Initialize solver
captcha_solver = CaptchaSolver()

@app.route('/in.php', methods=['POST'])
def submit_captcha():
    """Submit captcha for solving (2captcha API compatible)"""
    try:
        method = request.form.get('method')
        
        if method == 'base64':
            # Handle base64 image
            body = request.form.get('body')
            if not body:
                return jsonify({'status': 0, 'error': 'NO_IMAGE'})
            
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            
            # Decode and save image
            try:
                image_data = base64.b64decode(body)
                image_path = TEMP_DIR / f"{task_id}.png"
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                # Store task in Redis
                task_data = {
                    'id': task_id,
                    'method': method,
                    'image_path': str(image_path),
                    'status': 'processing',
                    'created_at': time.time()
                }
                
                redis_client.hset(f"task:{task_id}", mapping=task_data)
                
                # Start solving in background (or solve immediately for demo)
                result = captcha_solver.solve_captcha(str(image_path))
                
                if result:
                    redis_client.hset(f"task:{task_id}", 'status', 'ready')
                    redis_client.hset(f"task:{task_id}", 'result', result)
                else:
                    redis_client.hset(f"task:{task_id}", 'status', 'error')
                    redis_client.hset(f"task:{task_id}", 'error', 'CAPTCHA_UNSOLVABLE')
                
                return jsonify({'status': 1, 'request': task_id})
                
            except Exception as e:
                logger.error(f"Image processing failed: {e}")
                return jsonify({'status': 0, 'error': 'ERROR_IMAGE_TYPE'})
        
        elif method == 'userrecaptcha':
            # Handle reCAPTCHA (placeholder)
            return jsonify({'status': 0, 'error': 'ERROR_RECAPTCHA_NOT_SUPPORTED'})
        
        else:
            return jsonify({'status': 0, 'error': 'ERROR_WRONG_METHOD'})
    
    except Exception as e:
        logger.error(f"Submit captcha error: {e}")
        return jsonify({'status': 0, 'error': 'ERROR_INTERNAL'})

@app.route('/res.php', methods=['GET'])
def get_result():
    """Get captcha solving result (2captcha API compatible)"""
    try:
        action = request.args.get('action')
        task_id = request.args.get('id')
        
        if action == 'get' and task_id:
            # Get task from Redis
            task_data = redis_client.hgetall(f"task:{task_id}")
            
            if not task_data:
                return jsonify({'status': 0, 'error': 'ERROR_CAPTCHA_UNSOLVABLE'})
            
            status = task_data.get('status', 'processing')
            
            if status == 'ready':
                result = task_data.get('result', '')
                # Clean up
                redis_client.delete(f"task:{task_id}")
                try:
                    os.remove(task_data.get('image_path', ''))
                except:
                    pass
                
                return jsonify({'status': 1, 'request': result})
            
            elif status == 'error':
                error = task_data.get('error', 'CAPTCHA_UNSOLVABLE')
                # Clean up
                redis_client.delete(f"task:{task_id}")
                try:
                    os.remove(task_data.get('image_path', ''))
                except:
                    pass
                
                return jsonify({'status': 0, 'error': error})
            
            else:
                return jsonify({'status': 0, 'request': 'CAPCHA_NOT_READY'})
        
        elif action == 'getbalance':
            # Return dummy balance
            return jsonify({'status': 1, 'request': '999.99'})
        
        else:
            return jsonify({'status': 0, 'error': 'ERROR_WRONG_ID_FORMAT'})
    
    except Exception as e:
        logger.error(f"Get result error: {e}")
        return jsonify({'status': 0, 'error': 'ERROR_INTERNAL'})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()
        
        # Test OCR engines
        ocr_status = {}
        for engine, available in OCR_ENGINES.items():
            if engine == 'tesseract':
                ocr_status[engine] = True
            elif engine == 'easyocr':
                ocr_status[engine] = available is not None
        
        return jsonify({
            'status': 'healthy',
            'ocr_engines': ocr_status,
            'redis': 'connected',
            'temp_dir': str(TEMP_DIR),
            'version': '1.0.0'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get service statistics"""
    try:
        # Count active tasks
        keys = redis_client.keys("task:*")
        active_tasks = len(keys)
        
        # Get tasks by status
        stats = {
            'active_tasks': active_tasks,
            'ocr_engines': list(OCR_ENGINES.keys()),
            'supported_methods': ['base64'],
            'temp_dir_size': sum(f.stat().st_size for f in TEMP_DIR.glob('*') if f.is_file()),
            'uptime': time.time()  # Simple uptime
        }
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize OCR engines
    init_ocr_engines()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=9001, debug=False)
