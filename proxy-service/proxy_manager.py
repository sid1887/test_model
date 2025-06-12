"""
Self-Hosted Proxy Management Service with HAProxy Integration
Manages proxy pools, health checks, and rotation with Redis persistence
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import aiohttp
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from fake_useragent import UserAgent
import subprocess
import os
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
HAPROXY_CONFIG_PATH = "/app/haproxy.cfg"
HAPROXY_STATS_URL = os.getenv("HAPROXY_STATS_URL", "http://localhost:8081/stats")
PROXY_HEALTH_CHECK_INTERVAL = int(os.getenv("PROXY_HEALTH_CHECK_INTERVAL", "60"))
FREE_PROXY_SOURCES = os.getenv("FREE_PROXY_SOURCES", "true").lower() == "true"

# Pydantic models
class ProxyServer(BaseModel):
    url: str
    type: str = "http"  # http, https, socks4, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    latency: Optional[float] = None
    success_rate: float = 1.0
    last_check: Optional[datetime] = None
    failures: int = 0
    is_active: bool = True

class ProxyHealthCheck(BaseModel):
    proxy_url: str
    status: str  # "healthy", "unhealthy", "timeout"
    latency: float
    timestamp: datetime
    error_message: Optional[str] = None

class ProxyStats(BaseModel):
    total_proxies: int
    healthy_proxies: int
    unhealthy_proxies: int
    average_latency: float
    success_rate: float

# FastAPI app
app = FastAPI(title="Cumpair Proxy Manager", version="1.0.0")

class ProxyManager:
    """Enhanced proxy manager with Redis persistence and HAProxy integration"""
    
    def __init__(self):
        self.redis_client = None
        self.ua = UserAgent()
        self.health_check_running = False
        
    async def initialize(self):
        """Initialize Redis connection and start background tasks"""
        try:
            self.redis_client = redis.from_url(REDIS_URL)
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis")
            
            # Start background tasks
            if not self.health_check_running:
                asyncio.create_task(self.continuous_health_check())
                asyncio.create_task(self.auto_refresh_free_proxies())
                self.health_check_running = True
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def add_proxy(self, proxy: ProxyServer) -> bool:
        """Add a new proxy to the pool"""
        try:
            proxy_key = f"proxy:{proxy.url}"
            proxy_data = proxy.model_dump_json()
            
            await self.redis_client.hset("proxies", proxy.url, proxy_data)
            await self.redis_client.sadd("proxy_urls", proxy.url)
            
            # Add to HAProxy configuration
            await self._update_haproxy_config()
            
            logger.info(f"✅ Added proxy: {proxy.url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add proxy {proxy.url}: {e}")
            return False
    
    async def remove_proxy(self, proxy_url: str) -> bool:
        """Remove a proxy from the pool"""
        try:
            await self.redis_client.hdel("proxies", proxy_url)
            await self.redis_client.srem("proxy_urls", proxy_url)
            
            # Update HAProxy configuration
            await self._update_haproxy_config()
            
            logger.info(f"✅ Removed proxy: {proxy_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to remove proxy {proxy_url}: {e}")
            return False
    
    async def get_best_proxy(self) -> Optional[ProxyServer]:
        """Get the best available proxy based on success rate and latency"""
        try:
            proxy_urls = await self.redis_client.smembers("proxy_urls")
            
            if not proxy_urls:
                return None
            
            best_proxy = None
            best_score = -1
            
            for proxy_url in proxy_urls:
                proxy_data = await self.redis_client.hget("proxies", proxy_url)
                if proxy_data:
                    proxy = ProxyServer.model_validate_json(proxy_data)
                    
                    if not proxy.is_active:
                        continue
                    
                    # Calculate score: success_rate / (latency + 1)
                    latency = proxy.latency or 1.0
                    score = proxy.success_rate / (latency + 1)
                    
                    if score > best_score:
                        best_score = score
                        best_proxy = proxy
            
            return best_proxy
            
        except Exception as e:
            logger.error(f"❌ Failed to get best proxy: {e}")
            return None
    
    async def get_all_proxies(self) -> List[ProxyServer]:
        """Get all proxies in the pool"""
        try:
            proxy_urls = await self.redis_client.smembers("proxy_urls")
            proxies = []
            
            for proxy_url in proxy_urls:
                proxy_data = await self.redis_client.hget("proxies", proxy_url)
                if proxy_data:
                    proxy = ProxyServer.model_validate_json(proxy_data)
                    proxies.append(proxy)
            
            return proxies
            
        except Exception as e:
            logger.error(f"❌ Failed to get all proxies: {e}")
            return []
    
    async def check_proxy_health(self, proxy: ProxyServer) -> ProxyHealthCheck:
        """Check the health of a single proxy"""
        start_time = time.time()
        
        try:
            proxy_config = {
                'http': proxy.url,
                'https': proxy.url
            }
            
            if proxy.username and proxy.password:
                # Handle authenticated proxies
                auth_url = proxy.url.replace('://', f'://{proxy.username}:{proxy.password}@')
                proxy_config = {'http': auth_url, 'https': auth_url}
            
            # Test with a simple GET request
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://httpbin.org/ip",
                    proxy=proxy.url if not (proxy.username and proxy.password) else auth_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    latency = time.time() - start_time
                    
                    if response.status == 200:
                        return ProxyHealthCheck(
                            proxy_url=proxy.url,
                            status="healthy",
                            latency=latency,
                            timestamp=datetime.now()
                        )
                    else:
                        return ProxyHealthCheck(
                            proxy_url=proxy.url,
                            status="unhealthy",
                            latency=latency,
                            timestamp=datetime.now(),
                            error_message=f"HTTP {response.status}"
                        )
                        
        except asyncio.TimeoutError:
            return ProxyHealthCheck(
                proxy_url=proxy.url,
                status="timeout",
                latency=time.time() - start_time,
                timestamp=datetime.now(),
                error_message="Connection timeout"
            )
        except Exception as e:
            return ProxyHealthCheck(
                proxy_url=proxy.url,
                status="unhealthy",
                latency=time.time() - start_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    async def update_proxy_health(self, proxy_url: str, health_check: ProxyHealthCheck):
        """Update proxy health status in Redis"""
        try:
            proxy_data = await self.redis_client.hget("proxies", proxy_url)
            if proxy_data:
                proxy = ProxyServer.model_validate_json(proxy_data)
                
                # Update metrics
                proxy.latency = health_check.latency
                proxy.last_check = health_check.timestamp
                
                if health_check.status == "healthy":
                    proxy.failures = 0
                    proxy.is_active = True
                    # Improve success rate gradually
                    proxy.success_rate = min(1.0, proxy.success_rate + 0.1)
                else:
                    proxy.failures += 1
                    # Degrade success rate
                    proxy.success_rate = max(0.0, proxy.success_rate - 0.2)
                    
                    # Deactivate if too many failures
                    if proxy.failures >= 3:
                        proxy.is_active = False
                
                # Save updated proxy
                await self.redis_client.hset("proxies", proxy_url, proxy.model_dump_json())
                
        except Exception as e:
            logger.error(f"❌ Failed to update proxy health for {proxy_url}: {e}")
    
    async def continuous_health_check(self):
        """Continuously check proxy health in the background"""
        while True:
            try:
                proxies = await self.get_all_proxies()
                logger.info(f"🔍 Checking health of {len(proxies)} proxies...")
                
                # Check proxies in batches to avoid overwhelming
                batch_size = 10
                for i in range(0, len(proxies), batch_size):
                    batch = proxies[i:i + batch_size]
                    
                    # Check batch concurrently
                    tasks = [self.check_proxy_health(proxy) for proxy in batch]
                    health_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Update health status
                    for proxy, health_result in zip(batch, health_results):
                        if isinstance(health_result, ProxyHealthCheck):
                            await self.update_proxy_health(proxy.url, health_result)
                    
                    # Small delay between batches
                    await asyncio.sleep(1)
                
                # Update HAProxy configuration after health checks
                await self._update_haproxy_config()
                
                logger.info(f"✅ Health check completed")
                
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
            
            # Wait before next health check
            await asyncio.sleep(PROXY_HEALTH_CHECK_INTERVAL)
    
    async def auto_refresh_free_proxies(self):
        """Automatically refresh free proxies every hour"""
        while True:
            try:
                if FREE_PROXY_SOURCES:
                    await self.refresh_free_proxies()
                
                # Wait 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"❌ Auto refresh error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes on error
    
    async def refresh_free_proxies(self):
        """Fetch new free proxies from various sources"""
        logger.info("🔄 Refreshing free proxies...")
        
        try:
            # Free proxy sources
            sources = [
                "https://www.proxy-list.download/api/v1/get?type=http",
                "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all",
            ]
            
            new_proxies = []
            
            async with aiohttp.ClientSession() as session:
                for source_url in sources:
                    try:
                        async with session.get(source_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            if response.status == 200:
                                proxy_list = await response.text()
                                
                                # Parse proxy list (format: ip:port)
                                for line in proxy_list.strip().split('\n'):
                                    if ':' in line and line.count('.') == 3:
                                        proxy_url = f"http://{line.strip()}"
                                        
                                        # Check if proxy already exists
                                        exists = await self.redis_client.hexists("proxies", proxy_url)
                                        if not exists:
                                            proxy = ProxyServer(
                                                url=proxy_url,
                                                type="http",
                                                country="unknown",
                                                success_rate=0.5  # Start with neutral rating
                                            )
                                            new_proxies.append(proxy)
                                            
                    except Exception as e:
                        logger.warning(f"Failed to fetch from {source_url}: {e}")
            
            # Add new proxies
            added_count = 0
            for proxy in new_proxies[:50]:  # Limit to 50 new proxies per refresh
                if await self.add_proxy(proxy):
                    added_count += 1
            
            logger.info(f"✅ Added {added_count} new free proxies")
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh free proxies: {e}")
    
    async def _update_haproxy_config(self):
        """Update HAProxy configuration with current proxy pool"""
        try:
            proxies = await self.get_all_proxies()
            healthy_proxies = [p for p in proxies if p.is_active and p.success_rate > 0.3]
            
            # Generate HAProxy backend configuration
            backend_config = []
            backend_config.append("backend proxy_pool")
            backend_config.append("    balance roundrobin")
            backend_config.append("    option httpchk GET /")
            
            for i, proxy in enumerate(healthy_proxies):
                server_name = f"proxy{i+1}"
                proxy_host = proxy.url.replace("http://", "").replace("https://", "")
                
                # Add server line
                server_line = f"    server {server_name} {proxy_host} check"
                if proxy.success_rate < 0.7:
                    server_line += " backup"  # Mark low success rate proxies as backup
                    
                backend_config.append(server_line)
            
            # Read current HAProxy config
            with open(HAPROXY_CONFIG_PATH, 'r') as f:
                current_config = f.read()
            
            # Replace backend section
            config_lines = current_config.split('\n')
            new_config_lines = []
            in_backend = False
            
            for line in config_lines:
                if line.startswith('backend proxy_pool'):
                    in_backend = True
                    new_config_lines.extend(backend_config)
                elif in_backend and line.startswith('backend '):
                    in_backend = False
                    new_config_lines.append(line)
                elif not in_backend:
                    new_config_lines.append(line)
            
            # Write updated config to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cfg') as temp_file:
                temp_file.write('\n'.join(new_config_lines))
                temp_config_path = temp_file.name
            
            # Validate configuration
            result = subprocess.run(
                ['haproxy', '-c', '-f', temp_config_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Configuration is valid, replace the current one
                os.replace(temp_config_path, HAPROXY_CONFIG_PATH)
                
                # Reload HAProxy (send SIGHUP)
                subprocess.run(['pkill', '-HUP', 'haproxy'])
                
                logger.info(f"✅ Updated HAProxy config with {len(healthy_proxies)} healthy proxies")
            else:
                logger.error(f"❌ HAProxy config validation failed: {result.stderr}")
                os.unlink(temp_config_path)
                
        except Exception as e:
            logger.error(f"❌ Failed to update HAProxy config: {e}")
    
    async def get_stats(self) -> ProxyStats:
        """Get proxy pool statistics"""
        try:
            proxies = await self.get_all_proxies()
            
            if not proxies:
                return ProxyStats(
                    total_proxies=0,
                    healthy_proxies=0,
                    unhealthy_proxies=0,
                    average_latency=0.0,
                    success_rate=0.0
                )
            
            healthy = [p for p in proxies if p.is_active]
            total_latency = sum(p.latency or 0 for p in proxies if p.latency)
            total_success_rate = sum(p.success_rate for p in proxies)
            
            return ProxyStats(
                total_proxies=len(proxies),
                healthy_proxies=len(healthy),
                unhealthy_proxies=len(proxies) - len(healthy),
                average_latency=total_latency / len(proxies) if proxies else 0.0,
                success_rate=total_success_rate / len(proxies) if proxies else 0.0
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return ProxyStats(
                total_proxies=0,
                healthy_proxies=0,
                unhealthy_proxies=0,
                average_latency=0.0,
                success_rate=0.0
            )

# Global proxy manager instance
proxy_manager = ProxyManager()

# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize the proxy manager on startup"""
    await proxy_manager.initialize()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/proxies", response_model=List[ProxyServer])
async def get_proxies():
    """Get all proxies in the pool"""
    return await proxy_manager.get_all_proxies()

@app.get("/proxies/best", response_model=ProxyServer)
async def get_best_proxy():
    """Get the best available proxy"""
    proxy = await proxy_manager.get_best_proxy()
    if not proxy:
        raise HTTPException(status_code=404, detail="No healthy proxies available")
    return proxy

@app.post("/proxies", response_model=dict)
async def add_proxy(proxy: ProxyServer):
    """Add a new proxy to the pool"""
    success = await proxy_manager.add_proxy(proxy)
    if success:
        return {"message": f"Proxy {proxy.url} added successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to add proxy")

@app.delete("/proxies/{proxy_url:path}")
async def remove_proxy(proxy_url: str):
    """Remove a proxy from the pool"""
    success = await proxy_manager.remove_proxy(proxy_url)
    if success:
        return {"message": f"Proxy {proxy_url} removed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Proxy not found")

@app.post("/proxies/refresh")
async def refresh_proxies(background_tasks: BackgroundTasks):
    """Manually refresh free proxies"""
    background_tasks.add_task(proxy_manager.refresh_free_proxies)
    return {"message": "Proxy refresh initiated"}

@app.get("/stats", response_model=ProxyStats)
async def get_proxy_stats():
    """Get proxy pool statistics"""
    return await proxy_manager.get_stats()

@app.post("/proxies/{proxy_url:path}/report-failure")
async def report_proxy_failure(proxy_url: str):
    """Report a proxy failure"""
    try:
        proxy_data = await proxy_manager.redis_client.hget("proxies", proxy_url)
        if proxy_data:
            proxy = ProxyServer.model_validate_json(proxy_data)
            proxy.failures += 1
            proxy.success_rate = max(0.0, proxy.success_rate - 0.3)
            
            if proxy.failures >= 2:
                proxy.is_active = False
            
            await proxy_manager.redis_client.hset("proxies", proxy_url, proxy.model_dump_json())
            return {"message": f"Failure reported for {proxy_url}"}
        else:
            raise HTTPException(status_code=404, detail="Proxy not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "proxy_manager:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )
