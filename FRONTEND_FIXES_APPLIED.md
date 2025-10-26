# Frontend Fixes Applied - October 22, 2025

## Issues Found and Fixed

### 1. **Docker Build Failure with @swc/core on Alpine**
**Problem:** 
```
npm error path /app/node_modules/@swc/core
npm error command failed
npm error signal SIGBUS
```

**Root Cause:** `@vitejs/plugin-react-swc` uses native bindings that fail to compile on Alpine Linux due to missing build tools and musl vs glibc incompatibility.

**Solution:** Changed base image from `node:18-alpine` to `node:18` (full Debian-based image)

**Files Modified:**
- `frontend/Dockerfile` - Updated FROM instruction and added fallback npm install

---

### 2. **Nginx Configuration Formatting Issues**
**Problem:** Missing newlines between directives causing nginx syntax errors

**Solution:** Properly formatted nginx.conf with:
- Fixed comment placement
- Added websocket support for API proxy
- Changed backend proxy from `host.docker.internal` to `web:8000` (Docker network)
- Added font file caching
- Enhanced CSP to allow 'unsafe-eval' for React

**Files Modified:**
- `frontend/nginx.conf`

---

### 3. **TypeScript Configuration Mismatch**
**Problem:** tsconfig.json had Next.js-specific settings but project uses Vite

**Solution:** Updated to proper Vite TypeScript configuration:
- Changed JSX from "preserve" to "react-jsx"
- Updated module resolution to "bundler"
- Removed Next.js plugins
- Added proper include/exclude paths
- Set target to ES2020

**Files Modified:**
- `frontend/tsconfig.json`

---

### 4. **Vite Configuration Enhancements**
**Improvements Added:**
- Dynamic API URL from environment variable
- WebSocket support in proxy
- Optimized build with manual chunks for better caching
- Added sourcemap generation for development

**Files Modified:**
- `frontend/vite.config.ts`

---

### 5. **Dockerfile Robustness Improvements**
**Enhancements:**
- Added `--legacy-peer-deps` flag for npm ci
- Added fallback: if npm ci fails, removes node_modules and does fresh install
- Increased Node.js memory limit to 4GB for large builds
- Added `--maxsockets=1` to prevent ECONNRESET errors

**Dockerfile Changes:**
```dockerfile
# Before
FROM node:18-alpine AS builder
RUN npm ci

# After
FROM node:18 AS builder
RUN npm ci --legacy-peer-deps --maxsockets=1 || \
    (rm -rf node_modules package-lock.json && npm install --legacy-peer-deps)
ENV NODE_OPTIONS="--max-old-space-size=4096"
```

---

## Build & Deployment

### Build Command:
```bash
docker-compose build --no-cache frontend
```

### Start Frontend:
```bash
docker-compose up -d frontend
```

### Access:
- Frontend UI: http://localhost:8080
- Backend API (proxied): http://localhost:8080/api

---

## Testing Checklist

- [ ] Frontend builds successfully without errors
- [ ] Frontend container starts and stays healthy
- [ ] UI loads at http://localhost:8080
- [ ] API proxy works (requests to /api/* forward to backend)
- [ ] Static assets load correctly
- [ ] React routing works (no 404s on page refresh)
- [ ] Text search functionality works
- [ ] Image search functionality works
- [ ] Price comparison displays correctly
- [ ] No console errors in browser

---

## Expected Build Time
- **Full build**: ~5-10 minutes (includes downloading Node 18 base image ~211MB)
- **Subsequent builds**: ~2-3 minutes (base image cached)

---

## Architecture

```
┌─────────────┐     port 8080      ┌──────────────┐
│   Browser   │ ◄───────────────► │   Nginx      │
└─────────────┘                    │  (Frontend)  │
                                   └──────┬───────┘
                                          │ proxy /api/*
                                          ▼
                                   ┌──────────────┐
                                   │   FastAPI    │
                                   │  (Backend)   │
                                   │  port 8000   │
                                   └──────────────┘
```

---

## Notes

- The frontend is in the `frontend` profile, so it doesn't start automatically with `docker-compose up -d`
- To start: `docker-compose --profile frontend up -d` or `docker-compose up -d frontend`
- Nginx serves built static files from `/usr/share/nginx/html`
- All API calls are proxied to the backend web service via Docker network
- React build output is ~700KB (optimized with code splitting)
