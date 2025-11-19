"""
AI Models Microservice - YOLO, EfficientNet, CLIP
Serves computer vision models for object detection, classification, and embeddings
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import logging
from typing import List, Optional
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Models Service",
    description="YOLO, EfficientNet, CLIP object detection and embeddings",
    version="1.0.0"
)

# Global model cache
models_cache = {}

# ============================================================================
# INITIALIZATION
# ============================================================================

async def load_models():
    """Load all models on startup"""
    logger.info("🚀 Loading AI models...")

    try:
        # YOLO
        from ultralytics import YOLO
        models_cache['yolo'] = YOLO('yolov8n.pt')
        logger.info("✓ YOLO loaded")
    except Exception as e:
        logger.warning(f"⚠️ YOLO load failed: {e}")

    try:
        # CLIP
        import clip
        device = "cpu"
        models_cache['clip_model'], models_cache['clip_preprocess'] = clip.load("ViT-B/32", device=device)
        logger.info("✓ CLIP loaded")
    except Exception as e:
        logger.warning(f"⚠️ CLIP load failed: {e}")

    try:
        # Sentence Transformers
        from sentence_transformers import SentenceTransformer
        models_cache['sentence_transformer'] = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Sentence Transformers loaded")
    except Exception as e:
        logger.warning(f"⚠️ Sentence Transformers load failed: {e}")

    logger.info("✅ Model initialization complete")


@app.on_event("startup")
async def startup():
    """FastAPI startup event"""
    await load_models()


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/models/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-models",
        "port": 8001,
        "models_loaded": len(models_cache),
        "timestamp": time.time()
    }


@app.post("/api/models/yolo-detect")
async def yolo_detect(image: UploadFile = File(...), confidence: float = 0.5):
    """
    YOLO object detection on uploaded image

    Args:
        image: Image file (JPG, PNG, etc.)
        confidence: Detection confidence threshold (0-1)

    Returns:
        Detections with bounding boxes and labels
    """
    try:
        if 'yolo' not in models_cache:
            raise HTTPException(status_code=503, detail="YOLO model not loaded")

        # Read image
        contents = await image.read()
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            # Run detection
            results = models_cache['yolo'](tmp_path, conf=confidence, verbose=False)

            detections = []
            for r in results:
                for box in r.boxes:
                    detections.append({
                        'class': r.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': [float(x) for x in box.xyxy[0].tolist()]
                    })

            return {"detections": detections, "count": len(detections)}
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"YOLO detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/clip-encode-text")
async def clip_encode_text(texts: List[str]):
    """
    CLIP text encoding

    Args:
        texts: List of text strings to encode

    Returns:
        Text embeddings (768-dim vectors)
    """
    try:
        if 'clip_model' not in models_cache:
            raise HTTPException(status_code=503, detail="CLIP model not loaded")

        import torch
        import clip

        model = models_cache['clip_model']
        device = next(model.parameters()).device

        with torch.no_grad():
            text_tokens = clip.tokenize(texts).to(device)
            embeddings = model.encode_text(text_tokens)
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)

        return {
            "embeddings": embeddings.cpu().tolist(),
            "count": len(texts),
            "embedding_dim": len(embeddings[0])
        }

    except Exception as e:
        logger.error(f"CLIP text encoding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/clip-encode-image")
async def clip_encode_image(image: UploadFile = File(...)):
    """
    CLIP image encoding

    Args:
        image: Image file to encode

    Returns:
        Image embedding (768-dim vector)
    """
    try:
        if 'clip_model' not in models_cache:
            raise HTTPException(status_code=503, detail="CLIP model not loaded")

        import torch
        import clip
        from PIL import Image
        from io import BytesIO

        model = models_cache['clip_model']
        preprocess = models_cache['clip_preprocess']
        device = next(model.parameters()).device

        # Read and preprocess image
        contents = await image.read()
        img = Image.open(BytesIO(contents)).convert('RGB')
        img_tensor = preprocess(img).unsqueeze(0).to(device)

        with torch.no_grad():
            embedding = model.encode_image(img_tensor)
            embedding = embedding / embedding.norm(dim=-1, keepdim=True)

        return {
            "embedding": embedding.cpu().squeeze().tolist(),
            "embedding_dim": len(embedding[0])
        }

    except Exception as e:
        logger.error(f"CLIP image encoding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/models/sentence-embed")
async def sentence_embed(texts: List[str]):
    """
    Sentence embedding using Sentence Transformers

    Args:
        texts: List of text strings

    Returns:
        Text embeddings (384-dim vectors)
    """
    try:
        if 'sentence_transformer' not in models_cache:
            raise HTTPException(status_code=503, detail="Sentence Transformer not loaded")

        model = models_cache['sentence_transformer']
        embeddings = model.encode(texts, convert_to_tensor=False)

        return {
            "embeddings": embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings,
            "count": len(texts),
            "embedding_dim": len(embeddings[0]) if len(embeddings) > 0 else 0
        }

    except Exception as e:
        logger.error(f"Sentence embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8001))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
