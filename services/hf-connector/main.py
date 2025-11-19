"""
HuggingFace Connector Microservice
Text generation, sentiment analysis, NER, zero-shot classification, image captioning
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
    title="HuggingFace Connector Service",
    description="Text generation, sentiment, NER, classification, captioning",
    version="1.0.0"
)

# Global model cache
models_cache = {}

# ============================================================================
# INITIALIZATION
# ============================================================================

async def load_models():
    """Load HuggingFace models on startup"""
    logger.info("🚀 Loading HuggingFace models...")

    try:
        # Sentiment analysis
        from transformers import pipeline
        models_cache['sentiment'] = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        logger.info("✓ Sentiment analysis loaded")
    except Exception as e:
        logger.warning(f"⚠️ Sentiment load failed: {e}")

    try:
        # Zero-shot classification
        from transformers import pipeline
        models_cache['zero_shot'] = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        logger.info("✓ Zero-shot classification loaded")
    except Exception as e:
        logger.warning(f"⚠️ Zero-shot load failed: {e}")

    try:
        # Named Entity Recognition
        from transformers import pipeline
        models_cache['ner'] = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", aggregation_strategy="simple")
        logger.info("✓ NER loaded")
    except Exception as e:
        logger.warning(f"⚠️ NER load failed: {e}")

    try:
        # Image captioning
        from transformers import pipeline
        models_cache['image_caption'] = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
        logger.info("✓ Image captioning loaded")
    except Exception as e:
        logger.warning(f"⚠️ Image captioning load failed: {e}")

    try:
        # Text generation
        from transformers import pipeline
        models_cache['text_generation'] = pipeline("text-generation", model="gpt2")
        logger.info("✓ Text generation loaded")
    except Exception as e:
        logger.warning(f"⚠️ Text generation load failed: {e}")

    logger.info("✅ HuggingFace model initialization complete")


@app.on_event("startup")
async def startup():
    """FastAPI startup event"""
    await load_models()


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/hf/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "hf-connector",
        "port": 8002,
        "models_loaded": len(models_cache),
        "timestamp": time.time()
    }


@app.post("/api/hf/sentiment")
async def sentiment_analysis(texts: List[str]):
    """
    Sentiment analysis on text

    Args:
        texts: List of text strings to analyze

    Returns:
        Sentiment labels and scores
    """
    try:
        if 'sentiment' not in models_cache:
            raise HTTPException(status_code=503, detail="Sentiment model not loaded")

        model = models_cache['sentiment']
        results = []
        for text in texts:
            result = model(text)[0]
            results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "label": result['label'],
                "score": float(result['score'])
            })

        return {"results": results, "count": len(results)}

    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hf/zero-shot")
async def zero_shot_classify(text: str, labels: List[str]):
    """
    Zero-shot classification

    Args:
        text: Text to classify
        labels: Candidate labels

    Returns:
        Classification scores for each label
    """
    try:
        if 'zero_shot' not in models_cache:
            raise HTTPException(status_code=503, detail="Zero-shot model not loaded")

        model = models_cache['zero_shot']
        result = model(text, labels)

        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "labels": result['labels'],
            "scores": [float(s) for s in result['scores']],
            "top_label": result['labels'][0]
        }

    except Exception as e:
        logger.error(f"Zero-shot classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hf/ner")
async def named_entity_recognition(text: str):
    """
    Named Entity Recognition

    Args:
        text: Text to extract entities from

    Returns:
        Named entities with types and scores
    """
    try:
        if 'ner' not in models_cache:
            raise HTTPException(status_code=503, detail="NER model not loaded")

        model = models_cache['ner']
        entities = model(text)

        return {
            "text": text,
            "entities": [
                {
                    "entity": e['entity_group'],
                    "word": e['word'],
                    "score": float(e['score'])
                }
                for e in entities
            ],
            "count": len(entities)
        }

    except Exception as e:
        logger.error(f"NER error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hf/caption-image")
async def caption_image(image: UploadFile = File(...)):
    """
    Generate image caption

    Args:
        image: Image file to caption

    Returns:
        Generated caption text
    """
    try:
        if 'image_caption' not in models_cache:
            raise HTTPException(status_code=503, detail="Image captioning model not loaded")

        from PIL import Image
        from io import BytesIO

        model = models_cache['image_caption']

        # Read image
        contents = await image.read()
        img = Image.open(BytesIO(contents)).convert('RGB')

        # Generate caption
        result = model(img)
        caption = result[0]['generated_text'] if result else "No caption generated"

        return {
            "caption": caption,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Image captioning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hf/generate-text")
async def generate_text(prompt: str, max_length: int = 50):
    """
    Text generation

    Args:
        prompt: Starting text prompt
        max_length: Maximum length of generated text

    Returns:
        Generated text continuation
    """
    try:
        if 'text_generation' not in models_cache:
            raise HTTPException(status_code=503, detail="Text generation model not loaded")

        model = models_cache['text_generation']
        result = model(prompt, max_length=max_length, num_return_sequences=1)[0]

        return {
            "prompt": prompt,
            "generated": result['generated_text'],
            "length": len(result['generated_text'])
        }

    except Exception as e:
        logger.error(f"Text generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8002))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
