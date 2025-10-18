# Archive Log - Phase 2 Consolidation

**Date:** October 18, 2025  
**Purpose:** Consolidate configurations and reduce file sprawl

---

## Archived Dockerfiles

**Location:** `archive/dockerfiles/`

| File | Reason | Notes |
|------|--------|-------|
| `Dockerfile.fix` | Legacy variant | Experimental fix attempt |
| `Dockerfile.fixed` | Legacy variant | Superseded by main Dockerfile |
| `Dockerfile.new` | Legacy variant | Development version |
| `Dockerfile.production` | Legacy variant | Merged into main Dockerfile |
| `Dockerfile.robust` | Legacy variant | Experimental version |

**Kept:** `Dockerfile` (main, production-ready)

---

## Archived Docker Compose Files

**Location:** `archive/compose-files/`

| File | Reason | Notes |
|------|--------|-------|
| `docker-compose.override.yml` | Legacy override | Now using dev/prod split |
| `docker-compose.complete.yml` | Legacy variant | Superseded by prod |
| `docker-compose.fix.yml` | Experimental fix | No longer needed |
| `docker-compose.universal.yml` | Legacy variant | Consolidated into dev/prod |
| `docker-compose.secure.yml` | Referenced in scripts | Replaced by prod with HAProxy |

**Kept:** 
- `docker-compose.yml` (original/base)
- `docker-compose.dev.yml` (local development)
- `docker-compose.prod.yml` (production with HAProxy)

---

## Archived Startup Scripts

**Location:** `archive/startup-scripts/`

| File | Type | Reason |
|------|------|--------|
| `adaptive_startup.sh` | Bash | Legacy startup method |
| `direct_start.sh` | Bash | Old direct start |
| `new_start.sh` | Bash | Experimental |
| `fixed_start.sh` | Bash | Fix attempt |
| `final_simple_fix.sh` | Bash | Legacy fix |
| `docker-start.ps1` | PowerShell | Old Windows start |
| `docker-start-secure.ps1` | PowerShell | Old secure start |
| `docker-emergency-fix.ps1` | PowerShell | Emergency fix script |

**Kept:** 
- `docker-start-secure-fixed.ps1` (current primary for Windows)
- `docker/entrypoints/` (new standardized entrypoints)
- `quickstart.ps1` / `quickstart.sh` (simplified startup)

---

## Current Configuration Strategy

### Dockerfiles

**Primary:** `Dockerfile`
- Multi-stage build (base → builder → production)
- Auto package installation
- Entrypoint scripts included
- Non-root user
- Healthchecks

### Docker Compose

**Development:** `docker-compose.dev.yml`
```bash
docker-compose -f docker-compose.dev.yml up --build
```

**Features:**
- Hot reload volumes
- Debug ports exposed
- Local PostgreSQL + Redis
- No ingress layer

**Production:** `docker-compose.prod.yml`
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Features:**
- HAProxy ingress (ports 80, 443, 8404)
- Resource limits
- Restart policies
- Internal network
- Health monitoring

### Startup Method

**Recommended Approach:** Docker entrypoints with docker-compose

**Windows:**
```powershell
# Development
docker-compose -f docker-compose.dev.yml up --build

# Production
docker-compose -f docker-compose.prod.yml up -d
```

**Linux:**
```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Production  
docker-compose -f docker-compose.prod.yml up -d
```

---

## Migration Notes

### If You Need Old Configurations

All archived files are preserved in `archive/` subdirectories. They can be restored if needed, but current configurations are preferred.

### Port Standardization

Current port allocation:
- FastAPI: 8000
- Scraper: 3001
- Captcha: 9001
- Redis: 6379
- Redis (Captcha): 6380
- PostgreSQL: 5432
- HAProxy: 80, 443, 8404

All services now use environment variables for ports (see `.env.example`).

---

### Recent file moves (Phase 2 Service Consolidation)

- `app/services/price_comparison_backup.py` → `archive/services/price_comparison_backup.py` (archived)
- `app/services/clip_search_backup.py` → `archive/services/clip_search_backup.py` (archived)

**Removed empty placeholder files:**
- `app/services/price_comparison_updated.py` (empty placeholder)
- `app/services/clip_search_fixed.py` (empty placeholder)
- `app/services/clip_search.py.backup` (old backup)
- `app/services/price_comparison_backup.py` (duplicate)


## Restoration Instructions

If you need to restore archived configurations:

```powershell
# Restore specific Dockerfile
Copy-Item -Path "archive/dockerfiles/Dockerfile.production" -Destination "." -Force

# Restore specific compose file
Copy-Item -Path "archive/compose-files/docker-compose.secure.yml" -Destination "." -Force

# Restore startup script
Copy-Item -Path "archive/startup-scripts/adaptive_startup.sh" -Destination "." -Force
```

---

## Next Steps

1. ✅ Archive legacy configurations (COMPLETE)
2. ⏳ Consolidate duplicate services (IN PROGRESS)
3. ⏳ Implement /metrics endpoint
4. ⏳ Products API database integration
5. ⏳ Port configuration audit

---

**Status:** Phase 2 archival complete - Configuration sprawl reduced from 25+ files to 3 primary configs
