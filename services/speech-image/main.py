"""
Speech & Image Processing Microservice
Voice STT (faster-whisper), OCR (EasyOCR), Image processing
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import logging
from typing import Optional
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Speech & Image Processing Service",
    description="Voice STT, OCR, image preprocessing",
    version="1.0.0"
)

# Global service cache
services_cache = {}

# ============================================================================
# INITIALIZATION
# ============================================================================

async def load_services():
    """Load services on startup"""
    logger.info("🚀 Loading speech & image services...")

    try:
        # Voice STT - OpenAI Whisper
        import whisper
        services_cache['whisper'] = whisper.load_model("base", device="cpu")
        logger.info("✓ Whisper loaded")
    except Exception as e:
        logger.warning(f"⚠️ Whisper load failed: {e}")

    try:
        # OCR - EasyOCR
        import easyocr
        services_cache['ocr_reader'] = easyocr.Reader(['en'], gpu=False)
        logger.info("✓ EasyOCR loaded")
    except Exception as e:
        logger.warning(f"⚠️ EasyOCR load failed: {e}")

    logger.info("✅ Speech & Image services initialization complete")


@app.on_event("startup")
async def startup():
    """FastAPI startup event"""
    await load_services()


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/media/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "speech-image",
        "port": 8003,
        "services_loaded": len(services_cache),
        "timestamp": time.time()
    }


@app.post("/api/media/voice-to-text")
async def voice_to_text(audio: UploadFile = File(...), language: str = "en"):
    """
    Convert audio to text using Whisper

    Args:
        audio: Audio file (MP3, WAV, M4A, OGG, etc.)
        language: Language code (default: 'en' for English)

    Returns:
        Transcribed text
    """
    try:
        if 'whisper' not in services_cache:
            raise HTTPException(status_code=503, detail="Whisper model not loaded")

        import tempfile

        # Save uploaded file
        contents = await audio.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            model = services_cache['whisper']
            result = model.transcribe(tmp_path, language=language)

            # Extract text from result
            text = result.get('text', '')

            return {
                "text": text,
                "timestamp": time.time()
            }
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Voice to text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/media/ocr")
async def ocr_image(image: UploadFile = File(...)):
    """
    Extract text from image using EasyOCR

    Args:
        image: Image file (JPG, PNG, etc.)

    Returns:
        Extracted text and bounding boxes
    """
    try:
        if 'ocr_reader' not in services_cache:
            raise HTTPException(status_code=503, detail="OCR model not loaded")

        from PIL import Image
        from io import BytesIO
        import tempfile

        # Save image temporarily (EasyOCR needs file path)
        contents = await image.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            reader = services_cache['ocr_reader']
            results = reader.readtext(tmp_path)

            # Format results
            text_blocks = []
            full_text = []

            for (bbox, text, confidence) in results:
                text_blocks.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bbox": [[float(p[0]), float(p[1])] for p in bbox]
                })
                full_text.append(text)

            return {
                "full_text": " ".join(full_text),
                "text_blocks": text_blocks,
                "block_count": len(text_blocks),
                "timestamp": time.time()
            }
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/media/process-image")
async def process_image(image: UploadFile = File(...), operation: str = "resize"):
    """
    Process image (resize, rotate, etc.)

    Args:
        image: Image file
        operation: 'resize', 'rotate', 'enhance', etc.

    Returns:
        Processed image metadata
    """
    try:
        from PIL import Image, ImageEnhance
        from io import BytesIO
        import base64

        # Read image
        contents = await image.read()
        img = Image.open(BytesIO(contents))

        # Get original dimensions
        original_size = img.size

        # Apply operation
        if operation == "resize":
            img = img.resize((640, 480))
        elif operation == "rotate":
            img = img.rotate(90)
        elif operation == "enhance":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
        elif operation == "blur":
            img = img.filter(Image.BLUR)

        # Convert back to base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {
            "operation": operation,
            "original_size": original_size,
            "new_size": img.size,
            "format": img.format,
            "image_base64": f"data:image/jpeg;base64,{img_str[:100]}..." # Truncated for response
        }

    except Exception as e:
        logger.error(f"Image processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8003))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
