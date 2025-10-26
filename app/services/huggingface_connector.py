"""
HuggingFace Inference API Connector
Handles text generation, sentiment analysis, embeddings, image captioning via HF API
"""

import os
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import base64
import logging

logger = logging.getLogger(__name__)


class HuggingFaceConnector:
    """Client for HuggingFace Inference API with retry logic and rate limiting"""
    
    def __init__(self):
        self.api_key = os.getenv('HF_API_KEY', '')
        self.base_url = os.getenv('HF_INFERENCE_ENDPOINT', 'https://api-inference.huggingface.co/models')
        self.timeout = int(os.getenv('HF_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('HF_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('HF_RETRY_DELAY', '2'))
        
        # Model configurations
        self.models = {
            'text_gen': os.getenv('HF_TEXT_MODEL', 'meta-llama/Llama-2-7b-chat-hf'),
            'sentiment': os.getenv('HF_SENTIMENT_MODEL', 'distilbert-base-uncased-finetuned-sst-2-english'),
            'embeddings': os.getenv('HF_EMBEDDINGS_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
            'ner': os.getenv('HF_NER_MODEL', 'dbmdz/bert-large-cased-finetuned-conll03-english'),
            'caption': os.getenv('HF_IMAGE_CAPTION_MODEL', 'Salesforce/blip-image-captioning-large'),
        }
        
        self.text_max_tokens = int(os.getenv('HF_TEXT_MAX_TOKENS', '256'))
        self.text_temperature = float(os.getenv('HF_TEXT_TEMPERATURE', '0.7'))
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Track metrics
        self.request_count = 0
        self.error_count = 0
        self.total_latency = 0.0
        
        logger.info(f"🤗 HuggingFace Connector initialized")
        logger.info(f"   Models: {list(self.models.keys())}")
        
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key and self.api_key.startswith('hf_'))
    
    async def _make_request(
        self,
        model: str,
        payload: Dict[str, Any],
        retry_count: int = 0
    ) -> Optional[Any]:
        """Make HTTP request to HF API with retry logic"""
        
        if not self.is_configured():
            logger.error("HuggingFace API key not configured")
            return None
        
        url = f"{self.base_url}/{model}"
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    self.request_count += 1
                    latency = time.time() - start_time
                    self.total_latency += latency
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.debug(f"HF request successful: {model} ({latency:.2f}s)")
                        return result
                    
                    elif response.status == 503:
                        # Model is loading
                        error_data = await response.json()
                        estimated_time = error_data.get('estimated_time', 20)
                        
                        if retry_count < self.max_retries:
                            logger.warning(f"Model loading, retrying in {estimated_time}s...")
                            await asyncio.sleep(estimated_time)
                            return await self._make_request(model, payload, retry_count + 1)
                        else:
                            logger.error(f"Model failed to load after {self.max_retries} retries")
                            self.error_count += 1
                            return None
                    
                    elif response.status == 429:
                        # Rate limit
                        if retry_count < self.max_retries:
                            wait_time = self.retry_delay * (2 ** retry_count)
                            logger.warning(f"Rate limited, retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            return await self._make_request(model, payload, retry_count + 1)
                        else:
                            logger.error("Rate limit exceeded, max retries reached")
                            self.error_count += 1
                            return None
                    
                    else:
                        error_text = await response.text()
                        logger.error(f"HF API error {response.status}: {error_text}")
                        self.error_count += 1
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"HF request timeout for model: {model}")
            self.error_count += 1
            
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_delay)
                return await self._make_request(model, payload, retry_count + 1)
            return None
            
        except Exception as e:
            logger.error(f"HF request exception: {e}")
            self.error_count += 1
            return None
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate text using HuggingFace text generation model
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            model: Optional custom model name
            
        Returns:
            Generated text or None
        """
        model_name = model or self.models['text_gen']
        max_tokens = max_tokens or self.text_max_tokens
        temperature = temperature or self.text_temperature
        
        payload = {
            'inputs': prompt,
            'parameters': {
                'max_new_tokens': max_tokens,
                'temperature': temperature,
                'return_full_text': False
            }
        }
        
        result = await self._make_request(model_name, payload)
        
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', '').strip()
        
        return None
    
    async def analyze_sentiment(
        self,
        text: str,
        model: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment of text
        
        Args:
            text: Input text to analyze
            model: Optional custom model name
            
        Returns:
            Dict with label and score, or None
        """
        model_name = model or self.models['sentiment']
        
        payload = {'inputs': text}
        result = await self._make_request(model_name, payload)
        
        if result and isinstance(result, list) and len(result) > 0:
            # Get highest score prediction
            predictions = result[0]
            if isinstance(predictions, list):
                best = max(predictions, key=lambda x: x.get('score', 0))
                return {
                    'label': best.get('label', 'UNKNOWN'),
                    'score': best.get('score', 0.0),
                    'all_predictions': predictions
                }
        
        return None
    
    async def extract_entities(
        self,
        text: str,
        model: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Extract named entities from text
        
        Args:
            text: Input text
            model: Optional custom model name
            
        Returns:
            List of entities with type and confidence
        """
        model_name = model or self.models['ner']
        
        payload = {'inputs': text}
        result = await self._make_request(model_name, payload)
        
        if result and isinstance(result, list):
            return result
        
        return None
    
    async def get_embeddings(
        self,
        texts: Union[str, List[str]],
        model: Optional[str] = None
    ) -> Optional[List[List[float]]]:
        """
        Get text embeddings for similarity search
        
        Args:
            texts: Single text or list of texts
            model: Optional custom model name
            
        Returns:
            List of embedding vectors or None
        """
        model_name = model or self.models['embeddings']
        
        if isinstance(texts, str):
            texts = [texts]
        
        # Note: Some embedding models need special handling
        # Sentence-transformers models return embeddings directly
        payload = {'inputs': texts}
        result = await self._make_request(model_name, payload)
        
        if result:
            # Handle different response formats
            if isinstance(result, list):
                # Check if it's already a list of embeddings
                if all(isinstance(item, list) for item in result):
                    return result
                # Or if it's a single embedding
                elif all(isinstance(item, (int, float)) for item in result):
                    return [result]
        
        return None
    
    async def caption_image(
        self,
        image_path: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate caption for image
        
        Args:
            image_path: Path to image file
            image_bytes: Raw image bytes
            model: Optional custom model name
            
        Returns:
            Caption text or None
        """
        model_name = model or self.models['caption']
        
        # Read image if path provided
        if image_path:
            try:
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()
            except Exception as e:
                logger.error(f"Failed to read image: {e}")
                return None
        
        if not image_bytes:
            logger.error("No image data provided")
            return None
        
        # For image captioning, send raw bytes
        url = f"{self.base_url}/{model_name}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    data=image_bytes,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        if isinstance(result, list) and len(result) > 0:
                            return result[0].get('generated_text', '')
                    else:
                        error_text = await response.text()
                        logger.error(f"Caption API error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Caption request exception: {e}")
        
        return None
    
    async def summarize_text(
        self,
        text: str,
        max_length: int = 130,
        min_length: int = 30
    ) -> Optional[str]:
        """
        Summarize long text
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
            
        Returns:
            Summary text or None
        """
        # Use text generation model for summarization
        prompt = f"Summarize the following text concisely:\n\n{text}\n\nSummary:"
        
        return await self.generate_text(
            prompt=prompt,
            max_tokens=max_length
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        avg_latency = (
            self.total_latency / self.request_count 
            if self.request_count > 0 
            else 0.0
        )
        
        return {
            'configured': self.is_configured(),
            'requests_total': self.request_count,
            'errors_total': self.error_count,
            'avg_latency_seconds': round(avg_latency, 3),
            'models': self.models
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if HF API is accessible"""
        if not self.is_configured():
            return {
                'status': 'unconfigured',
                'message': 'HF_API_KEY not set',
                'healthy': False
            }
        
        try:
            # Try a simple sentiment check
            result = await self.analyze_sentiment("test", model=self.models['sentiment'])
            
            if result:
                return {
                    'status': 'healthy',
                    'message': 'HF API accessible',
                    'healthy': True,
                    'stats': self.get_stats()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'HF API request failed',
                    'healthy': False
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'healthy': False
            }


# Singleton instance
_hf_connector: Optional[HuggingFaceConnector] = None


def get_hf_connector() -> HuggingFaceConnector:
    """Get or create HuggingFace connector singleton"""
    global _hf_connector
    if _hf_connector is None:
        _hf_connector = HuggingFaceConnector()
    return _hf_connector
