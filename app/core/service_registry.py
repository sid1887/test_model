"""
Service Registry - Central service discovery and health management
All services register here for inter-service communication
"""

from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime
from pydantic import BaseModel
import asyncio
import httpx


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    # Core Services
    WEB_API = "web_api"
    SCRAPER = "scraper"
    WORKER = "worker"
    
    # Data Services
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    SEARCH = "search"
    
    # AI/ML Services
    CLIP = "clip"
    HUGGINGFACE = "huggingface"
    VISION = "vision"
    OCR = "ocr"
    BARCODE = "barcode"
    
    # Real-time Services
    STOCK_FEED = "stock_feed"
    CRYPTO_FEED = "crypto_feed"
    NEWS_FEED = "news_feed"
    TICKET_FEED = "ticket_feed"
    
    # External Services
    PROXY_MANAGER = "proxy_manager"
    CAPTCHA_SOLVER = "captcha_solver"


class ServiceInfo(BaseModel):
    name: str
    service_type: ServiceType
    host: str
    port: int
    health_endpoint: Optional[str] = None
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: Optional[datetime] = None
    metadata: Dict = {}
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ServiceRegistry:
    """Central registry for all microservices"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Register all known services"""
        
        # Core Services
        self.register(ServiceInfo(
            name="web_api",
            service_type=ServiceType.WEB_API,
            host="web",
            port=8000,
            health_endpoint="/health/services"
        ))
        
        self.register(ServiceInfo(
            name="scraper",
            service_type=ServiceType.SCRAPER,
            host="scraper",
            port=3001,
            health_endpoint="/health"
        ))
        
        # Data Services
        self.register(ServiceInfo(
            name="postgres",
            service_type=ServiceType.DATABASE,
            host="postgres",
            port=5432
        ))
        
        self.register(ServiceInfo(
            name="redis_main",
            service_type=ServiceType.CACHE,
            host="redis",
            port=6379,
            metadata={"purpose": "main_cache"}
        ))
        
        self.register(ServiceInfo(
            name="redis_captcha",
            service_type=ServiceType.CACHE,
            host="redis-captcha",
            port=6379,
            metadata={"purpose": "captcha_queue"}
        ))
        
        self.register(ServiceInfo(
            name="redis_proxy",
            service_type=ServiceType.CACHE,
            host="redis-proxy",
            port=6379,
            metadata={"purpose": "proxy_pool"}
        ))
        
        # External Services
        self.register(ServiceInfo(
            name="captcha_solver",
            service_type=ServiceType.CAPTCHA_SOLVER,
            host="captcha-solver",
            port=5000,
            health_endpoint="/health"
        ))
        
        self.register(ServiceInfo(
            name="proxy_api",
            service_type=ServiceType.PROXY_MANAGER,
            host="proxy-api",
            port=5001,
            health_endpoint="/health"
        ))
    
    def register(self, service: ServiceInfo):
        """Register a service"""
        self.services[service.name] = service
    
    def get(self, name: str) -> Optional[ServiceInfo]:
        """Get service by name"""
        return self.services.get(name)
    
    def get_by_type(self, service_type: ServiceType) -> List[ServiceInfo]:
        """Get all services of a specific type"""
        return [s for s in self.services.values() if s.service_type == service_type]
    
    async def check_health(self, service_name: str) -> ServiceStatus:
        """Check health of a specific service"""
        service = self.get(service_name)
        if not service:
            return ServiceStatus.UNKNOWN
        
        if not service.health_endpoint:
            # Services without health endpoint assumed healthy if registered
            return ServiceStatus.HEALTHY
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service.url}{service.health_endpoint}")
                if response.status_code == 200:
                    service.status = ServiceStatus.HEALTHY
                else:
                    service.status = ServiceStatus.DEGRADED
        except Exception:
            service.status = ServiceStatus.UNHEALTHY
        
        service.last_check = datetime.utcnow()
        return service.status
    
    async def check_all_health(self) -> Dict[str, ServiceStatus]:
        """Check health of all services"""
        tasks = [self.check_health(name) for name in self.services.keys()]
        statuses = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            name: status if not isinstance(status, Exception) else ServiceStatus.UNHEALTHY
            for name, status in zip(self.services.keys(), statuses)
        }
    
    def get_healthy_services(self) -> List[ServiceInfo]:
        """Get all healthy services"""
        return [s for s in self.services.values() if s.status == ServiceStatus.HEALTHY]
    
    def get_service_url(self, name: str) -> Optional[str]:
        """Get service URL by name"""
        service = self.get(name)
        return service.url if service else None


# Global registry instance
registry = ServiceRegistry()
