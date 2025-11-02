"""
Complete HuggingFace API Integration
Text generation, sentiment analysis, NER, embeddings, image classification
"""

from typing import Dict, List, Optional, Any
import aiohttp
import asyncio
from app.core.config import settings
from app.core.metrics import metrics
from app.core.cache import cached, CacheLevel
import logging
import time

logger = logging.getLogger(__name__)


class HuggingFaceClient:
    """Complete HuggingFace API client with all AI models"""
    
    def __init__(self):
        self.api_key = settings.hf_api_key
        self.base_url = "https://api-inference.huggingface.co/models"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Model endpoints
        self.models = {
            "text_generation": "gpt2",
            "sentiment": "distilbert-base-uncased-finetuned-sst-2-english",
            "ner": "dslim/bert-base-NER",
            "embeddings": "sentence-transformers/all-MiniLM-L6-v2",
            "zero_shot": "facebook/bart-large-mnli",
            "summarization": "facebook/bart-large-cnn",
            "translation": "Helsinki-NLP/opus-mt-en-es",
            "question_answering": "deepset/roberta-base-squad2",
            "image_classification": "google/vit-base-patch16-224",
            "object_detection": "facebook/detr-resnet-50"
        }
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self.session
    
    async def close(self):
        """Close session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _request(
        self,
        model: str,
        payload: Dict[str, Any],
        retry_count: int = 3
    ) -> Any:
        """Make request to HuggingFace API with retries"""
        url = f"{self.base_url}/{model}"
        session = await self.get_session()
        
        for attempt in range(retry_count):
            try:
                start_time = time.time()
                
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    duration = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        metrics.track_ai_inference(model, duration, "success")
                        return result
                    elif response.status == 503:
                        # Model loading, wait and retry
                        logger.warning(f"Model {model} loading, waiting...")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error(f"HF API error {response.status}: {error_text}")
                        metrics.track_ai_inference(model, duration, "error")
                        raise Exception(f"HF API error: {response.status}")
                        
            except asyncio.TimeoutError:
                logger.error(f"HF API timeout for {model}")
                if attempt == retry_count - 1:
                    raise
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"HF API request failed: {e}")
                if attempt == retry_count - 1:
                    raise
                await asyncio.sleep(1)
        
        raise Exception(f"Failed after {retry_count} retries")
    
    @cached("hf_text_gen", ttl=300)
    async def generate_text(
        self,
        prompt: str,
        max_length: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """Generate text completion"""
        result = await self._request(
            self.models["text_generation"],
            {
                "inputs": prompt,
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "return_full_text": False
                }
            }
        )
        
        return result[0]["generated_text"] if result else ""
    
    @cached("hf_sentiment", ttl=3600)
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        result = await self._request(
            self.models["sentiment"],
            {"inputs": text}
        )
        
        if result and len(result) > 0:
            return {
                "label": result[0][0]["label"],
                "score": result[0][0]["score"]
            }
        
        return {"label": "NEUTRAL", "score": 0.5}
    
    @cached("hf_ner", ttl=3600)
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text"""
        result = await self._request(
            self.models["ner"],
            {"inputs": text}
        )
        
        entities = []
        for entity in result:
            entities.append({
                "entity": entity["entity_group"],
                "word": entity["word"],
                "score": entity["score"]
            })
        
        return entities
    
    @cached("hf_embeddings", ttl=86400, levels=[CacheLevel.L2])
    async def compute_embeddings(self, text: str) -> List[float]:
        """Compute text embeddings"""
        result = await self._request(
            self.models["embeddings"],
            {"inputs": text}
        )
        
        return result
    
    async def zero_shot_classify(
        self,
        text: str,
        candidate_labels: List[str]
    ) -> Dict[str, Any]:
        """Zero-shot classification"""
        result = await self._request(
            self.models["zero_shot"],
            {
                "inputs": text,
                "parameters": {"candidate_labels": candidate_labels}
            }
        )
        
        return {
            "labels": result["labels"],
            "scores": result["scores"]
        }
    
    @cached("hf_summary", ttl=3600)
    async def summarize(self, text: str, max_length: int = 130) -> str:
        """Summarize text"""
        result = await self._request(
            self.models["summarization"],
            {
                "inputs": text,
                "parameters": {"max_length": max_length}
            }
        )
        
        return result[0]["summary_text"] if result else ""
    
    async def translate(self, text: str, source_lang: str = "en", target_lang: str = "es") -> str:
        """Translate text"""
        model = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
        
        result = await self._request(
            model,
            {"inputs": text}
        )
        
        return result[0]["translation_text"] if result else ""
    
    async def answer_question(self, question: str, context: str) -> Dict[str, Any]:
        """Answer question based on context"""
        result = await self._request(
            self.models["question_answering"],
            {
                "inputs": {
                    "question": question,
                    "context": context
                }
            }
        )
        
        return {
            "answer": result["answer"],
            "score": result["score"]
        }
    
    async def classify_image(self, image_url: str) -> List[Dict[str, Any]]:
        """Classify image using Vision Transformer"""
        result = await self._request(
            self.models["image_classification"],
            {"inputs": image_url}
        )
        
        return [{"label": item["label"], "score": item["score"]} for item in result]
    
    async def detect_objects(self, image_url: str) -> List[Dict[str, Any]]:
        """Detect objects in image"""
        result = await self._request(
            self.models["object_detection"],
            {"inputs": image_url}
        )
        
        return result
    
    async def batch_compute_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Batch compute embeddings for efficiency"""
        tasks = [self.compute_embeddings(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    async def enhance_product_description(self, description: str) -> Dict[str, Any]:
        """
        Enhance product description with AI analysis
        Returns: sentiment, entities, summary, key features
        """
        tasks = [
            self.analyze_sentiment(description),
            self.extract_entities(description),
            self.summarize(description) if len(description) > 200 else None,
            self.zero_shot_classify(
                description,
                ["electronics", "clothing", "food", "books", "toys", "home", "sports"]
            )
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "sentiment": results[0] if not isinstance(results[0], Exception) else None,
            "entities": results[1] if not isinstance(results[1], Exception) else None,
            "summary": results[2] if not isinstance(results[2], Exception) else description[:200],
            "category": results[3] if not isinstance(results[3], Exception) else None
        }


# Global client instance
hf_client = HuggingFaceClient()
