"""
Core configuration settings for Compair application
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, List, Union
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # App Configuration
    app_name: str = "Compair"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database Configuration
    database_url: str = "postgresql://compair:compair123@localhost:5432/compair"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
      # Proxy Configuration
    rota_url: str = "http://localhost:8001"    # File Upload Configuration
    upload_dir: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: str = ".jpg,.jpeg,.png,.webp,.bmp"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as a list"""
        return [ext.strip() for ext in self.allowed_extensions.split(',')]
    
    # AI Model Configuration
    models_dir: str = "models"
    yolo_model_path: str = "models/yolov8n.pt"
    efficientnet_model_path: str = "models/spec_extractor.h5"
    clip_model_name: str = "ViT-B/32"
    clip_cache_dir: str = "models/clip_cache"
    
    # Scraper Service Configuration
    scraper_service_url: str = "http://localhost:3001"
    max_concurrent_requests: int = 100
    download_delay: float = 0.25
    user_agents_file: str = "config/user_agents.txt"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
      # Monitoring
    enable_prometheus: bool = True
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env without validation errors

# Global settings instance
settings = Settings()
