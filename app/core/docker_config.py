"""
Secure Configuration Loader for Docker Environment
Handles secrets, environment variables, and configuration validation
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator

logger = logging.getLogger(__name__)

class DockerSecureSettings(BaseSettings):
    """
    Secure settings class that reads from Docker secrets and environment variables
    Following testdriven.io best practices for production deployment
    """
    
    # Application Settings
    app_name: str = Field(default="Cumpair", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # Database Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="compair", env="POSTGRES_DB")
    postgres_user: str = Field(default="compair", env="POSTGRES_USER")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    
    # Service URLs
    proxy_service_url: str = Field(default="http://localhost:8001", env="PROXY_SERVICE_URL")
    captcha_service_url: str = Field(default="http://localhost:9001", env="CAPTCHA_SERVICE_URL")
    scraper_service_url: str = Field(default="http://localhost:3000", env="SCRAPER_SERVICE_URL")
    
    # File Configuration
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    models_dir: str = Field(default="models", env="MODELS_DIR")
    
    # AI Model Configuration
    clip_model_name: str = Field(default="ViT-B/32", env="CLIP_MODEL_NAME")
    yolo_model_path: str = Field(default="models/yolov8n.pt", env="YOLO_MODEL_PATH")
    
    # Docker Mode Detection
    docker_mode: bool = Field(default=False, env="CUMPAIR_DOCKER_MODE")
    
    # Secret file paths (Docker secrets)
    secret_key_file: Optional[str] = Field(default=None, env="SECRET_KEY_FILE")
    database_password_file: Optional[str] = Field(default=None, env="DATABASE_PASSWORD_FILE")
    redis_password_file: Optional[str] = Field(default=None, env="REDIS_PASSWORD_FILE")
    
    # Fallback secrets (for development)
    secret_key: Optional[str] = Field(default=None, env="SECRET_KEY")
    database_password: Optional[str] = Field(default=None, env="DATABASE_PASSWORD")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_secrets()
        self._validate_configuration()
    
    def _load_secrets(self):
        """Load secrets from Docker secret files or environment variables"""
        
        # Load secret key
        if self.secret_key_file and Path(self.secret_key_file).exists():
            with open(self.secret_key_file, 'r') as f:
                self.secret_key = f.read().strip()
            logger.info("✅ Secret key loaded from Docker secret")
        elif not self.secret_key:
            if self.docker_mode:
                logger.error("❌ SECRET_KEY_FILE not found in Docker mode")
                raise ValueError("Secret key file required in Docker mode")
            else:
                logger.warning("⚠️ Using default secret key for development")
                self.secret_key = "dev-secret-key-change-in-production"
        
        # Load database password
        if self.database_password_file and Path(self.database_password_file).exists():
            with open(self.database_password_file, 'r') as f:
                self.database_password = f.read().strip()
            logger.info("✅ Database password loaded from Docker secret")
        elif not self.database_password:
            if self.docker_mode:
                logger.error("❌ DATABASE_PASSWORD_FILE not found in Docker mode")
                raise ValueError("Database password file required in Docker mode")
            else:
                logger.warning("⚠️ Using default database password for development")
                self.database_password = "compair123"
        
        # Load Redis password
        if self.redis_password_file and Path(self.redis_password_file).exists():
            with open(self.redis_password_file, 'r') as f:
                self.redis_password = f.read().strip()
            logger.info("✅ Redis password loaded from Docker secret")
        elif not self.redis_password:
            if self.docker_mode:
                logger.warning("⚠️ Redis password not configured, using no authentication")
                self.redis_password = ""
            else:
                self.redis_password = ""
    
    def _validate_configuration(self):
        """Validate configuration for security and completeness"""
        
        if self.environment == "production":
            # Production security checks
            if self.secret_key == "dev-secret-key-change-in-production":
                raise ValueError("Must set secure SECRET_KEY in production")
            
            if len(self.secret_key) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            
            if self.debug:
                logger.warning("⚠️ DEBUG mode enabled in production environment")
        
        logger.info(f"✅ Configuration validated for {self.environment} environment")
    
    @property
    def database_url(self) -> str:
        """Construct database URL with loaded password"""
        return f"postgresql://{self.postgres_user}:{self.database_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL with loaded password"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}"
    
    @property
    def celery_broker_url(self) -> str:
        """Celery broker URL (Redis)"""
        return f"{self.redis_url}/0"
    
    @property
    def celery_result_backend(self) -> str:
        """Celery result backend URL (Redis)"""
        return f"{self.redis_url}/0"
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging (without sensitive data)"""
        return {
            "app_name": self.app_name,
            "environment": self.environment,
            "debug": self.debug,
            "log_level": self.log_level,
            "docker_mode": self.docker_mode,
            "database_host": self.postgres_host,
            "database_port": self.postgres_port,
            "database_name": self.postgres_db,
            "redis_host": self.redis_host,
            "redis_port": self.redis_port,
            "proxy_service": self.proxy_service_url,
            "captcha_service": self.captcha_service_url,
            "clip_model": self.clip_model_name,
            "secrets_loaded": {
                "secret_key": bool(self.secret_key),
                "database_password": bool(self.database_password),
                "redis_password": bool(self.redis_password)
            }
        }

# Factory function to create settings based on environment
def create_settings() -> DockerSecureSettings:
    """Create settings instance with proper configuration"""
    try:
        settings = DockerSecureSettings()
        
        # Log configuration summary
        config_summary = settings.get_config_summary()
        logger.info("🔧 Application Configuration:")
        for key, value in config_summary.items():
            if key != "secrets_loaded":
                logger.info(f"   {key}: {value}")
        
        # Log secrets status
        secrets = config_summary["secrets_loaded"]
        logger.info("🔐 Secrets Status:")
        for secret, loaded in secrets.items():
            status = "✅ Loaded" if loaded else "❌ Missing"
            logger.info(f"   {secret}: {status}")
        
        return settings
        
    except Exception as e:
        logger.error(f"❌ Configuration loading failed: {e}")
        raise

# Global settings instance
settings = create_settings()
