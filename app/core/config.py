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
    app_name: str = "Cumpair"
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
    rota_url: str = "http://localhost:8001"
      # File Upload Configuration
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
    
    # Captcha Service Configuration
    captcha_service_url: str = "http://localhost:9001"  # Self-hosted 2captcha-compatible service
    captcha_api_key: str = ""  # Optional API key for the service
    captcha_timeout: int = 120  # Maximum time to wait for captcha solution (seconds)
    captcha_retry_attempts: int = 3  # Number of retry attempts for failed captchas
    
    # Enhanced Proxy Management Configuration
    proxy_service_url: str = "http://localhost:8001"  # Self-hosted proxy manager
    proxy_health_check_interval: int = 60  # seconds
    proxy_max_failures: int = 3
    proxy_rotation_strategy: str = "health_based"  # health_based, round_robin, random
    
    # Advanced Scraping Configuration
    scraping_max_concurrent: int = 5  # Max concurrent scraping sessions
    scraping_rate_limit: float = 2.0  # Minimum seconds between requests per domain
    scraping_user_agent_rotation: bool = True
    scraping_stealth_mode: bool = True
    scraping_captcha_auto_solve: bool = True
    
    # Browser Configuration
    browser_headless: bool = True
    browser_max_pages: int = 10  # Max pages per browser instance
    browser_timeout: int = 30  # Page load timeout in seconds
    browser_viewport_width: int = 1920
    browser_viewport_height: int = 1080
    
    # Anti-Detection Settings
    enable_request_delays: bool = True
    min_request_delay: float = 0.5
    max_request_delay: float = 3.0
    enable_mouse_simulation: bool = True
    enable_scroll_simulation: bool = True
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if v == "your-secret-key-change-in-production":
            import os
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError("Must set a secure SECRET_KEY in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgresql+asyncpg://')):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @field_validator('redis_url')
    @classmethod
    def validate_redis_url(cls, v):
        if not v.startswith('redis://'):
            raise ValueError("REDIS_URL must be a valid Redis connection string")
        return v
    
    @field_validator('max_file_size')
    @classmethod
    def validate_max_file_size(cls, v):
        if v <= 0 or v > 100 * 1024 * 1024:  # Max 100MB
            raise ValueError("MAX_FILE_SIZE must be between 1 byte and 100MB")
        return v
    
    @field_validator('max_file_size')
    @classmethod
    def validate_max_file_size(cls, v):
        if v <= 0 or v > 100 * 1024 * 1024:  # Max 100MB
            raise ValueError("MAX_FILE_SIZE must be between 1 byte and 100MB")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env without validation errors

# Global settings instance
settings = Settings()
