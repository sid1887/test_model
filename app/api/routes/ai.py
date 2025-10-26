"""
AI API Routes - Images, CLIP, Barcode, OCR, Text Generation, Embeddings, Voice
Implements all HuggingFace and AI model endpoints
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ai"])


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ImageAnalyzeRequest(BaseModel):
    """Request to analyze an image"""
    image_id: str
    tasks: List[str] = Field(
        default=["clip", "barcode", "ocr", "caption"],
        description="Tasks: clip, barcode, ocr, caption, objects"
    )


class CLIPCompareRequest(BaseModel):
    """Request to compare image with products"""
    image: Optional[str] = Field(None, description="Base64 image or URL")
    image_id: Optional[str] = Field(None, description="Previously uploaded image ID")
    top_k: int = Field(default=5, ge=1, le=50)


class BarcodeDecodeRequest(BaseModel):
    """Request to decode barcode"""
    image_id: str


class OCRReceiptRequest(BaseModel):
    """Request to extract text from receipt"""
    image_id: str


class TextGenerateRequest(BaseModel):
    """Request to generate text"""
    prompt: str
    max_tokens: Optional[int] = Field(default=256, ge=1, le=2048)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    model: Optional[str] = None


class TextAnalyzeRequest(BaseModel):
    """Request to analyze text"""
    text: str
    task: str = Field(..., description="Task: sentiment, ner, summarize")


class EmbeddingsRequest(BaseModel):
    """Request to get text embeddings"""
    texts: List[str]


class CaptchaSolveRequest(BaseModel):
    """Request to solve CAPTCHA"""
    site: Optional[str] = None
    image_base64: str


# ============================================
# IMAGE UPLOAD & ANALYSIS ENDPOINTS
# ============================================

@router.post("/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    source: str = Form(default="upload"),
    user_id: Optional[str] = Form(None)
):
    """
    Upload image for processing
    
    - **file**: Image file (JPEG, PNG, etc.)
    - **source**: Source type (camera, upload, url)
    - **user_id**: Optional user identifier
    
    Returns image_id and URL for further processing
    """
    try:
        from app.services.image_processor import get_image_processor
        
        # Read file
        file_bytes = await file.read()
        
        # Get processor
        processor = await get_image_processor()
        
        # Save upload
        result = await processor.save_upload(
            file_bytes=file_bytes,
            filename=file.filename,
            source=source
        )
        
        if result.get('status') == 'ok':
            return JSONResponse({
                "status": "ok",
                "image_id": result['image_id'],
                "url": result['url'],
                "size": result['size']
            })
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Upload failed'))
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/images/analyze")
async def analyze_image(request: ImageAnalyzeRequest):
    """
    Analyze uploaded image
    
    Performs requested analysis tasks:
    - **clip**: Find similar products
    - **barcode**: Detect and decode barcodes/QR codes
    - **ocr**: Extract text
    - **caption**: Generate image caption
    - **objects**: Detect objects
    
    Returns results for all requested tasks
    """
    try:
        from app.services.image_processor import get_image_processor
        
        processor = await get_image_processor()
        
        # Get image path from ID
        image_path = processor.upload_dir / f"{request.image_id}.jpg"
        
        # Try different extensions
        if not image_path.exists():
            for ext in ['.png', '.jpeg', '.webp']:
                alt_path = processor.upload_dir / f"{request.image_id}{ext}"
                if alt_path.exists():
                    image_path = alt_path
                    break
        
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Analyze
        result = await processor.analyze_image(str(image_path), request.tasks)
        
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CLIP SIMILARITY SEARCH
# ============================================

@router.post("/clip/compare")
async def clip_compare(request: CLIPCompareRequest):
    """
    Find products similar to image using CLIP
    
    - **image**: Base64 encoded image or URL
    - **image_id**: Previously uploaded image ID
    - **top_k**: Number of matches to return
    
    Returns list of matching products with scores
    """
    try:
        from app.services.clip_search import CLIPSearchService
        
        clip_service = CLIPSearchService()
        
        # Determine image source
        image_path = None
        
        if request.image_id:
            # Use uploaded image
            from app.services.image_processor import get_image_processor
            processor = await get_image_processor()
            
            for ext in ['.jpg', '.png', '.jpeg', '.webp']:
                path = processor.upload_dir / f"{request.image_id}{ext}"
                if path.exists():
                    image_path = str(path)
                    break
            
            if not image_path:
                raise HTTPException(status_code=404, detail="Image not found")
        
        elif request.image:
            # Handle base64 or URL
            if request.image.startswith('data:image'):
                # Base64 image
                import tempfile
                
                # Extract base64 data
                header, encoded = request.image.split(',', 1)
                image_bytes = base64.b64decode(encoded)
                
                # Save to temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.write(image_bytes)
                temp_file.close()
                image_path = temp_file.name
            
            elif request.image.startswith('http'):
                # URL - download image
                import aiohttp
                import tempfile
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(request.image) as response:
                        if response.status == 200:
                            image_bytes = await response.read()
                            
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                            temp_file.write(image_bytes)
                            temp_file.close()
                            image_path = temp_file.name
                        else:
                            raise HTTPException(status_code=400, detail="Failed to download image")
            else:
                raise HTTPException(status_code=400, detail="Invalid image format")
        
        else:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Search for matches
        matches = await clip_service.search_by_image(image_path, top_k=request.top_k)
        
        return JSONResponse({
            "status": "ok",
            "matches": matches,
            "count": len(matches) if matches else 0
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CLIP compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# BARCODE DETECTION
# ============================================

@router.post("/barcode/decode")
async def decode_barcode(request: BarcodeDecodeRequest):
    """
    Detect and decode barcodes/QR codes from image
    
    Returns list of detected barcodes with type and data
    """
    try:
        from app.services.image_processor import get_image_processor
        
        processor = await get_image_processor()
        
        # Get image path
        image_path = None
        for ext in ['.jpg', '.png', '.jpeg', '.webp']:
            path = processor.upload_dir / f"{request.image_id}{ext}"
            if path.exists():
                image_path = str(path)
                break
        
        if not image_path:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Detect barcodes
        barcodes = await processor._detect_barcodes(image_path)
        
        return JSONResponse({
            "status": "ok",
            "barcodes": barcodes,
            "count": len(barcodes)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Barcode decode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# OCR / RECEIPT PARSING
# ============================================

@router.post("/ocr/receipt")
async def ocr_receipt(request: OCRReceiptRequest):
    """
    Extract text from receipt image and parse items
    
    Returns extracted text and parsed line items
    """
    try:
        from app.services.image_processor import get_image_processor
        
        processor = await get_image_processor()
        
        # Get image path
        image_path = None
        for ext in ['.jpg', '.png', '.jpeg', '.webp']:
            path = processor.upload_dir / f"{request.image_id}{ext}"
            if path.exists():
                image_path = str(path)
                break
        
        if not image_path:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Extract text
        text = await processor._extract_text(image_path)
        
        # Parse receipt (basic implementation)
        items = _parse_receipt_text(text)
        
        return JSONResponse({
            "status": "ok",
            "text": text,
            "items": items
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR receipt error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _parse_receipt_text(text: str) -> List[Dict[str, Any]]:
    """Parse receipt text into line items (simplified)"""
    import re
    
    items = []
    lines = text.split('\n')
    
    # Look for price patterns
    price_pattern = r'\$?(\d+\.?\d{0,2})'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Find prices in line
        prices = re.findall(price_pattern, line)
        
        if prices:
            # Assume last price is the item price
            price = float(prices[-1])
            
            # Remove price from line to get item name
            name = re.sub(price_pattern, '', line).strip()
            
            if name and price > 0:
                items.append({
                    'name': name,
                    'price': price,
                    'qty': 1,
                    'confidence': 0.7  # Basic confidence
                })
    
    return items


# ============================================
# TEXT GENERATION & ANALYSIS
# ============================================

@router.post("/text/generate")
async def generate_text(request: TextGenerateRequest):
    """
    Generate text using HuggingFace LLM
    
    - **prompt**: Input text prompt
    - **max_tokens**: Maximum tokens to generate
    - **temperature**: Sampling temperature (0-2)
    - **model**: Optional custom model
    
    Returns generated text
    """
    try:
        from app.services.huggingface_connector import get_hf_connector
        
        hf = get_hf_connector()
        
        if not hf.is_configured():
            raise HTTPException(status_code=503, detail="HuggingFace API not configured")
        
        # Generate
        text = await hf.generate_text(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            model=request.model
        )
        
        if text:
            return JSONResponse({
                "status": "ok",
                "text": text
            })
        else:
            raise HTTPException(status_code=500, detail="Text generation failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text/analyze")
async def analyze_text(request: TextAnalyzeRequest):
    """
    Analyze text (sentiment, NER, summarize)
    
    - **text**: Input text
    - **task**: Analysis task (sentiment, ner, summarize)
    
    Returns task-specific analysis results
    """
    try:
        from app.services.huggingface_connector import get_hf_connector
        
        hf = get_hf_connector()
        
        if not hf.is_configured():
            raise HTTPException(status_code=503, detail="HuggingFace API not configured")
        
        result = None
        
        if request.task == 'sentiment':
            result = await hf.analyze_sentiment(request.text)
            
        elif request.task == 'ner':
            result = await hf.extract_entities(request.text)
            
        elif request.task == 'summarize':
            result = await hf.summarize_text(request.text)
            result = {'summary': result}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown task: {request.task}")
        
        if result:
            return JSONResponse({
                "status": "ok",
                "task": request.task,
                "result": result
            })
        else:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# EMBEDDINGS
# ============================================

@router.post("/embeddings")
async def get_embeddings(request: EmbeddingsRequest):
    """
    Get text embeddings for similarity search
    
    - **texts**: List of texts to embed
    
    Returns embedding vectors
    """
    try:
        from app.services.huggingface_connector import get_hf_connector
        
        hf = get_hf_connector()
        
        if not hf.is_configured():
            raise HTTPException(status_code=503, detail="HuggingFace API not configured")
        
        embeddings = await hf.get_embeddings(request.texts)
        
        if embeddings:
            return JSONResponse({
                "status": "ok",
                "embeddings": embeddings,
                "count": len(embeddings)
            })
        else:
            raise HTTPException(status_code=500, detail="Embedding generation failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embeddings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# VOICE / SPEECH-TO-TEXT
# ============================================

@router.post("/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Transcribe audio to text
    
    - **file**: Audio file (WAV, MP3, etc.)
    - **language**: Optional language code (e.g., 'en')
    
    Returns transcript and metadata
    """
    try:
        from app.services.voice_stt import get_stt_service
        
        stt = await get_stt_service()
        
        # Read audio file
        audio_bytes = await file.read()
        
        # Transcribe
        result = await stt.transcribe(
            audio_bytes=audio_bytes,
            language=language
        )
        
        if result:
            return JSONResponse({
                "status": "ok",
                "transcript": result.get('transcript', ''),
                "language": result.get('language', language or 'en'),
                "processing_time": result.get('processing_time', 0)
            })
        else:
            raise HTTPException(status_code=500, detail="Transcription failed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CAPTCHA SOLVING
# ============================================

@router.post("/captcha/solve")
async def solve_captcha(request: CaptchaSolveRequest):
    """
    Solve CAPTCHA using self-hosted service
    
    - **site**: Optional site URL
    - **image_base64**: Base64 encoded CAPTCHA image
    
    Returns solved CAPTCHA text
    """
    try:
        import aiohttp
        import os
        
        captcha_url = os.getenv('CAPTCHA_SERVICE_URL', 'http://localhost:9001')
        
        # Decode base64 image
        if request.image_base64.startswith('data:image'):
            header, encoded = request.image_base64.split(',', 1)
            image_data = encoded
        else:
            image_data = request.image_base64
        
        # Call 2captcha-compatible API
        async with aiohttp.ClientSession() as session:
            # Submit CAPTCHA
            async with session.post(
                f"{captcha_url}/in.php",
                data={
                    'method': 'base64',
                    'body': image_data
                }
            ) as response:
                submit_result = await response.json()
                
                if submit_result.get('status') != 1:
                    raise HTTPException(status_code=500, detail="CAPTCHA submission failed")
                
                task_id = submit_result.get('request')
            
            # Poll for result
            import asyncio
            max_attempts = 30
            
            for attempt in range(max_attempts):
                await asyncio.sleep(2)
                
                async with session.get(
                    f"{captcha_url}/res.php",
                    params={
                        'action': 'get',
                        'id': task_id
                    }
                ) as response:
                    result = await response.json()
                    
                    if result.get('status') == 1:
                        # Success
                        return JSONResponse({
                            "status": "ok",
                            "solution": result.get('request', '')
                        })
                    elif result.get('error'):
                        # Error
                        raise HTTPException(status_code=500, detail=result.get('error'))
            
            # Timeout
            raise HTTPException(status_code=408, detail="CAPTCHA solving timeout")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CAPTCHA solve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
