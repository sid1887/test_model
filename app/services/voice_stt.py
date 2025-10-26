"""
Voice Speech-to-Text Service
Supports both HuggingFace Whisper API and local faster-whisper
"""

import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class VoiceSTTService:
    """Speech-to-Text service with HF and local Whisper support"""
    
    def __init__(self):
        self.provider = os.getenv('VOICE_STT_PROVIDER', 'local').lower()
        self.model_name = os.getenv('VOICE_STT_MODEL', 'openai/whisper-large-v2')
        self.language = os.getenv('VOICE_STT_LANGUAGE', 'en')
        self.device = os.getenv('VOICE_STT_DEVICE', 'cpu')
        
        # Local Whisper settings
        self.whisper_model_size = os.getenv('WHISPER_MODEL_SIZE', 'base')
        self.whisper_compute_type = os.getenv('WHISPER_COMPUTE_TYPE', 'int8')
        self.whisper_beam_size = int(os.getenv('WHISPER_BEAM_SIZE', '5'))
        
        self.whisper_model = None
        self.hf_connector = None
        
        # Metrics
        self.transcription_count = 0
        self.total_duration = 0.0
        self.error_count = 0
        
        logger.info(f"🎤 Voice STT Service initialized (provider: {self.provider})")
        
    async def initialize(self):
        """Initialize the STT provider"""
        if self.provider == 'local':
            await self._init_local_whisper()
        elif self.provider == 'hf':
            await self._init_hf_whisper()
        else:
            logger.warning(f"Unknown STT provider: {self.provider}, defaulting to local")
            await self._init_local_whisper()
    
    async def _init_local_whisper(self):
        """Initialize local faster-whisper model"""
        try:
            from faster_whisper import WhisperModel
            
            logger.info(f"Loading faster-whisper model: {self.whisper_model_size}")
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self.whisper_model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    self.whisper_model_size,
                    device=self.device,
                    compute_type=self.whisper_compute_type
                )
            )
            
            logger.info("✅ Faster-whisper model loaded successfully")
            
        except ImportError:
            logger.error("faster-whisper not installed. Install with: pip install faster-whisper")
            self.whisper_model = None
        except Exception as e:
            logger.error(f"Failed to load faster-whisper: {e}")
            self.whisper_model = None
    
    async def _init_hf_whisper(self):
        """Initialize HuggingFace Whisper connector"""
        try:
            from app.services.huggingface_connector import get_hf_connector
            
            self.hf_connector = get_hf_connector()
            
            if self.hf_connector.is_configured():
                logger.info("✅ HuggingFace Whisper connector ready")
            else:
                logger.error("HF_API_KEY not configured, falling back to local")
                await self._init_local_whisper()
                
        except Exception as e:
            logger.error(f"Failed to initialize HF connector: {e}")
            await self._init_local_whisper()
    
    async def transcribe(
        self,
        audio_path: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio to text
        
        Args:
            audio_path: Path to audio file
            audio_bytes: Raw audio bytes
            language: Language code (optional)
            
        Returns:
            Dict with transcript and metadata
        """
        start_time = time.time()
        
        try:
            # Save bytes to temp file if needed
            temp_file = None
            if audio_bytes and not audio_path:
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.wav'
                )
                temp_file.write(audio_bytes)
                temp_file.close()
                audio_path = temp_file.name
            
            if not audio_path:
                logger.error("No audio data provided")
                return None
            
            # Transcribe based on provider
            if self.provider == 'local' and self.whisper_model:
                result = await self._transcribe_local(audio_path, language)
            elif self.provider == 'hf' and self.hf_connector:
                result = await self._transcribe_hf(audio_path, language)
            else:
                logger.error("No STT provider available")
                result = None
            
            # Clean up temp file
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            
            # Update metrics
            duration = time.time() - start_time
            if result:
                self.transcription_count += 1
                self.total_duration += duration
                
                # Add metadata
                result['processing_time'] = round(duration, 3)
                result['provider'] = self.provider
            else:
                self.error_count += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            self.error_count += 1
            return None
    
    async def _transcribe_local(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Transcribe using local faster-whisper"""
        if not self.whisper_model:
            logger.error("Whisper model not loaded")
            return None
        
        try:
            lang = language or self.language
            
            # Run transcription in executor
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,
                lambda: self.whisper_model.transcribe(
                    audio_path,
                    language=lang,
                    beam_size=self.whisper_beam_size
                )
            )
            
            # Collect segments
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text)
            
            transcript = ' '.join(transcript_parts).strip()
            
            return {
                'transcript': transcript,
                'language': info.language,
                'language_probability': info.language_probability,
                'duration': info.duration
            }
            
        except Exception as e:
            logger.error(f"Local transcription error: {e}")
            return None
    
    async def _transcribe_hf(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Transcribe using HuggingFace API"""
        try:
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Call HF API (custom implementation for audio)
            import aiohttp
            
            url = f"{self.hf_connector.base_url}/{self.model_name}"
            headers = {
                'Authorization': f'Bearer {self.hf_connector.api_key}'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    data=audio_bytes,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        if isinstance(result, dict) and 'text' in result:
                            return {
                                'transcript': result['text'],
                                'language': language or self.language
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"HF STT error {response.status}: {error_text}")
            
            return None
            
        except Exception as e:
            logger.error(f"HF transcription error: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        avg_duration = (
            self.total_duration / self.transcription_count
            if self.transcription_count > 0
            else 0.0
        )
        
        return {
            'provider': self.provider,
            'model': self.whisper_model_size if self.provider == 'local' else self.model_name,
            'transcriptions_total': self.transcription_count,
            'errors_total': self.error_count,
            'avg_processing_time': round(avg_duration, 3)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        if self.provider == 'local':
            if self.whisper_model:
                return {
                    'status': 'healthy',
                    'provider': 'local',
                    'model': self.whisper_model_size,
                    'healthy': True
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Whisper model not loaded',
                    'healthy': False
                }
        
        elif self.provider == 'hf':
            if self.hf_connector and self.hf_connector.is_configured():
                return {
                    'status': 'healthy',
                    'provider': 'hf',
                    'model': self.model_name,
                    'healthy': True
                }
            else:
                return {
                    'status': 'unconfigured',
                    'message': 'HF API key not set',
                    'healthy': False
                }
        
        return {
            'status': 'error',
            'message': 'Unknown provider',
            'healthy': False
        }


# Singleton instance
_stt_service: Optional[VoiceSTTService] = None


async def get_stt_service() -> VoiceSTTService:
    """Get or create STT service singleton"""
    global _stt_service
    if _stt_service is None:
        _stt_service = VoiceSTTService()
        await _stt_service.initialize()
    return _stt_service
