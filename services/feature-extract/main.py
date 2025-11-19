"""
Feature Extraction Microservice
Semantic embeddings, FAISS vector indexing, similarity search
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from typing import List, Optional
import os
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Feature Extraction Service",
    description="Embeddings generation and vector search",
    version="1.0.0"
)

# Global service cache
services_cache = {}
vector_index = None
indexed_texts = {}

# ============================================================================
# MODELS
# ============================================================================

class EmbedRequest(BaseModel):
    texts: List[str]

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class IndexAddRequest(BaseModel):
    doc_id: str
    text: str

# ============================================================================
# INITIALIZATION
# ============================================================================

async def load_services():
    """Load services on startup"""
    logger.info("🚀 Loading feature extraction services...")

    try:
        from sentence_transformers import SentenceTransformer
        services_cache['embedder'] = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✓ Sentence Transformers loaded")
    except Exception as e:
        logger.warning(f"⚠️ Sentence Transformers load failed: {e}")

    logger.info("✅ Feature extraction services initialization complete")
@app.on_event("startup")
async def startup():
    """FastAPI startup event"""
    await load_services()


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/features/health")
async def health_check():
    """Health check endpoint"""
    global vector_index
    return {
        "status": "healthy",
        "service": "feature-extract",
        "port": 8004,
        "services_loaded": len(services_cache),
        "indexed_documents": len(indexed_texts),
        "has_index": services_cache.get('faiss_index') is not None,
        "timestamp": time.time()
    }


@app.post("/api/features/embed")
async def generate_embeddings(request: EmbedRequest):
    """
    Generate embeddings for texts

    Args:
        texts: List of text strings to embed

    Returns:
        Embeddings vectors
    """
    try:
        if 'embedder' not in services_cache:
            raise HTTPException(status_code=503, detail="Embedder not loaded")

        model = services_cache['embedder']
        embeddings = model.encode(request.texts, convert_to_tensor=False)

        return {
            "embeddings": embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings,
            "count": len(request.texts),
            "embedding_dim": len(embeddings[0]) if len(embeddings) > 0 else 0,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/features/index-add")
async def add_to_index(request: IndexAddRequest):
    """
    Add document to embeddings store

    Args:
        doc_id: Document identifier
        text: Document text

    Returns:
        Index status
    """
    try:
        if 'embedder' not in services_cache:
            raise HTTPException(status_code=503, detail="Embedder not loaded")

        model = services_cache['embedder']
        embedding = model.encode([request.text], convert_to_tensor=False)[0]

        # Store text and embedding
        indexed_texts[request.doc_id] = {
            'text': request.text,
            'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        }

        return {
            "doc_id": request.doc_id,
            "added": True,
            "total_indexed": len(indexed_texts),
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Index add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/features/search")
async def search_index(request: SearchRequest):
    """
    Search indexed documents

    Args:
        query: Search query text
        top_k: Number of results to return

    Returns:
        Most similar documents
    """
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        if 'embedder' not in services_cache:
            raise HTTPException(status_code=503, detail="Embedder not loaded")

        if len(indexed_texts) == 0:
            return {
                "query": request.query,
                "results": [],
                "message": "Index is empty"
            }

        model = services_cache['embedder']

        # Encode query
        query_embedding = model.encode([request.query], convert_to_tensor=False)[0]

        # Calculate similarity scores
        results = []
        for doc_id, doc_data in indexed_texts.items():
            doc_embedding = np.array(doc_data['embedding'])
            similarity = float(cosine_similarity(
                [query_embedding],
                [doc_embedding]
            )[0][0])

            text = doc_data['text']
            results.append({
                "doc_id": doc_id,
                "text": text[:200] + "..." if len(text) > 200 else text,
                "similarity": similarity
            })

        # Sort by similarity (descending) and return top-k
        results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:request.top_k]

        return {
            "query": request.query,
            "results": results,
            "count": len(results),
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/features/index-stats")
async def index_stats():
    """Get index statistics"""
    return {
        "indexed_documents": len(indexed_texts),
        "timestamp": time.time()
    }


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", 8004))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
