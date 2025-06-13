# Cumpair Proxy Management Service

A self-hosted proxy management service with HAProxy integration, health monitoring, and automatic free proxy sourcing.

## Features

- **HAProxy Integration**: Dynamic proxy pool management with load balancing

- **Redis Persistence**: Proxy health and performance tracking

- **Automatic Health Checks**: Continuous monitoring of proxy availability

- **Free Proxy Sources**: Automatic discovery and integration of free proxies

- **REST API**: Full control over proxy pool management

- **Statistics Dashboard**: Real-time metrics and performance data

## Quick Start

1. **Start the service:**

```text
powershell
docker-compose up -d

```text

2. **Check service health:**

```text
bash
curl http://localhost:8001/health

```text

3. **Get available proxies:**

```text
bash
curl http://localhost:8001/proxies

```text

4. **Get the best proxy:**

```text
bash
curl http://localhost:8001/proxies/best

```text

## API Endpoints

### Proxy Management

- `GET /proxies` - List all proxies

- `GET /proxies/best` - Get the best available proxy

- `POST /proxies` - Add a new proxy

- `DELETE /proxies/{proxy_url}` - Remove a proxy

- `POST /proxies/{proxy_url}/report-failure` - Report proxy failure

### System Management

- `GET /health` - Service health check

- `GET /stats` - Proxy pool statistics

- `POST /proxies/refresh` - Manually refresh free proxies

### HAProxy Stats

- Access HAProxy statistics at: http://localhost:8081/stats

## Configuration

Environment variables:

- `REDIS_URL`: Redis connection string (default: redis://localhost:6380)

- `HAPROXY_STATS_URL`: HAProxy stats URL

- `PROXY_HEALTH_CHECK_INTERVAL`: Health check interval in seconds (default: 60)

- `FREE_PROXY_SOURCES`: Enable free proxy sourcing (default: true)

## Integration with Cumpair

The service integrates seamlessly with the main Cumpair application:

```text
python
# In your scraping service

proxy_manager = ProxyManager()
proxy_manager.rota_client_url = "http://localhost:8001"

# Get best proxy

proxy = await proxy_manager.get_proxy()

```text

## Architecture

```text

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cumpair App   │────│  Proxy Manager  │────│     HAProxy     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │      Redis      │    │   Proxy Pool    │
                       └─────────────────┘    └─────────────────┘

```text

## Health Monitoring

The service automatically:

1. Checks proxy health every 60 seconds

2. Updates HAProxy configuration with healthy proxies

3. Removes failed proxies after 3 consecutive failures

4. Maintains success rate and latency metrics

## Free Proxy Sources

Automatically fetches proxies from:

- proxy-list.download

- proxyscrape.com

- Additional sources can be added in the `refresh_free_proxies` method

## Performance

- Batched health checks (10 proxies per batch)

- Intelligent proxy scoring (success_rate / latency)

- HAProxy load balancing with backup servers

- Redis-based persistence for quick recovery
