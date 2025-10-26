"""
Environment Configuration
Centralized access to environment variables with type safety and defaults
"""
import os
from typing import Optional
from functools import lru_cache


class Config:
    """Application configuration loaded from environment variables"""
    
    # Service Configuration
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "cumpair")
    APP_NAME: str = os.getenv("APP_NAME", "Cumpair")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Feature Flags
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # Database Configuration
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "compair")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "compair")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Web Application
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))
    
    # API Configuration
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:8080"
    ).split(",")
    
    # AI Model Configuration
    CLIP_MODEL_NAME: str = os.getenv("CLIP_MODEL_NAME", "ViT-B/32")
    
    @classmethod
    def is_demo_mode(cls) -> bool:
        """Check if application is running in demo mode"""
        return cls.DEMO_MODE
    
    @classmethod
    def get_service_name(cls) -> str:
        """Get the service name for metrics and logging"""
        return cls.SERVICE_NAME
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get the database connection URL"""
        password = f":{cls.POSTGRES_PASSWORD}" if cls.POSTGRES_PASSWORD else ""
        return (
            f"postgresql://{cls.POSTGRES_USER}{password}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get the Redis connection URL"""
        password = f":{cls.REDIS_PASSWORD}@" if cls.REDIS_PASSWORD else ""
        return f"redis://{password}{cls.REDIS_HOST}:{cls.REDIS_PORT}/0"


@lru_cache()
def get_config() -> Config:
    """Get cached configuration instance"""
    return Config()


# Export convenience functions
def is_demo_mode() -> bool:
    """Check if running in demo mode"""
    return get_config().is_demo_mode()


def get_service_name() -> str:
    """Get the service name"""
    return get_config().get_service_name()


# Log configuration on import (only in debug mode)
if Config.DEBUG:
    print(f"[Config] Environment configuration loaded:")
    print(f"  - Service Name: {Config.SERVICE_NAME}")
    print(f"  - Demo Mode: {Config.DEMO_MODE}")
    print(f"  - Environment: {Config.ENVIRONMENT}")
    print(f"  - Debug: {Config.DEBUG}")
