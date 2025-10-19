# 🚀 Quick Start Guide

## Prerequisites Check

Before starting, ensure you have:
- ✅ Docker Desktop installed and **running**
- ✅ At least 4GB RAM available
- ✅ At least 10GB disk space free

## Starting Cumpair (First Time)

### Option 1: Automated (Recommended)

```powershell
# Windows PowerShell
.\quickstart.ps1
```

```bash
# Linux/Mac
bash quickstart.sh
```

### Option 2: Manual

```powershell
# 1. Create environment file (if not exists)
if (!(Test-Path .env)) { Copy-Item .env.example .env }

# 2. Start all services
docker-compose -f docker-compose.dev.yml up -d

# 3. Wait for services to be ready (30-60 seconds)
Start-Sleep -Seconds 30

# 4. Check status
docker-compose -f docker-compose.dev.yml ps

# 5. Run database migrations
docker-compose -f docker-compose.dev.yml exec web alembic upgrade head
```

## Verify Everything Works

### Check Service Health

```powershell
# Web API health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","version":"1.0.0",...}
```

### Access API Documentation

Open in browser: http://localhost:8000/docs

You should see the Swagger UI with all available endpoints.

### Check Database Connection

```powershell
docker-compose -f docker-compose.dev.yml exec web python -c "from app.core.database import engine; print('✅ Database connected!')"
```

### Check Redis Connection

```powershell
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
# Should respond: PONG
```

## Common Commands

### View Logs

```powershell
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f web
docker-compose -f docker-compose.dev.yml logs -f worker
docker-compose -f docker-compose.dev.yml logs -f scraper
```

### Restart Services

```powershell
# Restart all
docker-compose -f docker-compose.dev.yml restart

# Restart specific service
docker-compose -f docker-compose.dev.yml restart web
```

### Stop Services

```powershell
# Stop all (keeps data)
docker-compose -f docker-compose.dev.yml down

# Stop all and remove volumes (DELETES DATA!)
docker-compose -f docker-compose.dev.yml down -v
```

### Rebuild After Code Changes

```powershell
# Rebuild and restart specific service
docker-compose -f docker-compose.dev.yml up -d --build web

# Rebuild everything
docker-compose -f docker-compose.dev.yml up -d --build
```

## Testing the API

### Search Products

```powershell
curl -X GET "http://localhost:8000/api/v1/search?q=iPhone+15" `
  -H "Content-Type: application/json"
```

### Health Check

```powershell
curl http://localhost:8000/api/v1/health
```

### Upload Image for Analysis

```powershell
curl -X POST "http://localhost:8000/api/v1/analyze" `
  -F "file=@path/to/image.jpg"
```

## Troubleshooting

### Services Won't Start

```powershell
# Check Docker is running
docker info

# Check disk space
Get-PSDrive C

# Check for port conflicts
Get-NetTCPConnection -LocalPort 8000,5432,6379,3001
```

### Database Connection Errors

```powershell
# Check Postgres is healthy
docker-compose -f docker-compose.dev.yml ps postgres

# View Postgres logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart Postgres
docker-compose -f docker-compose.dev.yml restart postgres
```

### Out of Memory

```powershell
# Check Docker memory usage
docker stats

# Stop some services
docker-compose -f docker-compose.dev.yml stop worker scraper

# Restart with more memory
# Increase Docker Desktop memory limit in Settings > Resources
```

### Clean Slate (Nuclear Option)

```powershell
# Stop everything
docker-compose -f docker-compose.dev.yml down -v

# Remove all Cumpair images
docker images | Select-String "test_model" | ForEach-Object { docker rmi ($_ -split '\s+')[2] }

# Rebuild from scratch
docker-compose -f docker-compose.dev.yml up --build -d
```

## Next Steps

Once everything is running:

1. **Explore the API**: http://localhost:8000/docs
2. **Read the Architecture**: `docs/architecture.md`
3. **Set up local scraper**: Follow `docs/deploy.md` section on local scraping
4. **Configure AI models**: Place model files in `models/` directory
5. **Start building features**: Check the 12-month roadmap in the handoff doc

## Need Help?

- **Logs**: Always check logs first (`docker-compose logs -f [service]`)
- **Documentation**: See `docs/` folder
- **Architecture**: `docs/architecture.md`
- **Deployment**: `docs/deploy.md`

---

**You're all set! Happy coding! 🎉**
