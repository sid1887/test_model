# Cumpair Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment (DigitalOcean)](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Migrations](#database-migrations)
6. [Monitoring Setup](#monitoring-setup)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- Docker 20.10+ and Docker Compose 2.0+
- Git
- (Local only) Python 3.11+ or Node.js 18+ for local development

### Required Accounts

- GitHub account (for code + CI/CD)
- DigitalOcean account (GitHub Education Pack for $200 credit)
- Neon account (free PostgreSQL hosting)
- Upstash account (free Redis hosting)
- Grafana Cloud account (free monitoring)

---

## Local Development Setup

### 1. Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/cumpair.git
cd cumpair

# Copy environment template
cp .env.example .env

# Edit .env with your local values
nano .env
```

### 2. Start Development Environment

```bash
# Build and start all services
docker-compose -f docker-compose.dev.yml up --build

# Or start specific services
docker-compose -f docker-compose.dev.yml up postgres redis web
```

### 3. Verify Services

```bash
# Check all services are running
docker-compose -f docker-compose.dev.yml ps

# Test API health
curl http://localhost:8000/api/v1/health

# Test scraper health
curl http://localhost:3001/health
```

### 4. Run Database Migrations

```bash
# Inside web container or locally
docker-compose -f docker-compose.dev.yml exec web alembic upgrade head

# Or create new migration
docker-compose -f docker-compose.dev.yml exec web alembic revision --autogenerate -m "description"
```

### 5. Access Services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Scraper**: http://localhost:3001
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## Production Deployment

### Phase 1: Managed Services Setup

#### 1.1. Setup Neon (PostgreSQL)

```bash
# 1. Go to https://neon.tech
# 2. Create new project "cumpair-prod"
# 3. Copy connection string
# Example: postgresql://user:pass@ep-cool-name-123456.us-east-2.aws.neon.tech/cumpair
```

#### 1.2. Setup Upstash (Redis)

```bash
# 1. Go to https://upstash.com
# 2. Create Redis database "cumpair-prod"
# 3. Copy connection string
# Example: redis://default:pass@usw1-good-name-12345.upstash.io:6379
```

#### 1.3. Setup Grafana Cloud

```bash
# 1. Go to https://grafana.com/auth/sign-up/create-user
# 2. Create free account
# 3. Note your Grafana endpoint and API key
```

### Phase 2: DigitalOcean Droplet Setup

#### 2.1. Create Droplet

```bash
# Via DigitalOcean dashboard:
# - Choose: Ubuntu 22.04 LTS
# - Plan: Basic $12/month (2GB RAM, 1 vCPU, 50GB SSD)
# - Region: Choose closest to your users
# - Add SSH key
# - Enable monitoring
```

#### 2.2. Initial Server Setup

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Create non-root user
adduser cumpair
usermod -aG sudo cumpair
usermod -aG docker cumpair

# Switch to user
su - cumpair
```

#### 2.3. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version
docker-compose --version
```

#### 2.4. Setup Swap (for 2GB droplet stability)

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Phase 3: Application Deployment

#### 3.1. Clone and Configure

```bash
# Clone repository
cd /home/cumpair
git clone https://github.com/yourusername/cumpair.git
cd cumpair

# Create production .env
cp .env.example .env
nano .env
```

**Critical .env values for production:**

```bash
# MUST CHANGE THESE
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-random-32-char-key
DATABASE_URL=your-neon-postgres-url
REDIS_URL=your-upstash-redis-url
REDIS_PASSWORD=your-redis-password
HAPROXY_ADMIN_PASSWORD=your-secure-admin-password

# Domain configuration
DOMAIN=api.cumpair.tech
ENABLE_TLS=true
LETSENCRYPT_EMAIL=your-email@example.com
```

#### 3.2. Deploy with Docker Compose

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### 3.3. Run Initial Migrations

```bash
docker-compose -f docker-compose.prod.yml exec web alembic upgrade head
```

#### 3.4. Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo snap install certbot --classic

# Get certificate
sudo certbot certonly --standalone -d api.cumpair.tech

# Certificate will be at: /etc/letsencrypt/live/api.cumpair.tech/

# Copy to HAProxy directory
sudo cp /etc/letsencrypt/live/api.cumpair.tech/fullchain.pem /home/cumpair/cumpair/haproxy_certs/
sudo cp /etc/letsencrypt/live/api.cumpair.tech/privkey.pem /home/cumpair/cumpair/haproxy_certs/

# Combine for HAProxy
sudo cat /home/cumpair/cumpair/haproxy_certs/fullchain.pem /home/cumpair/cumpair/haproxy_certs/privkey.pem > /home/cumpair/cumpair/haproxy_certs/cert.pem
sudo chown cumpair:cumpair /home/cumpair/cumpair/haproxy_certs/cert.pem

# Restart HAProxy
docker-compose -f docker-compose.prod.yml restart haproxy
```

### Phase 4: Firewall Configuration

```bash
# Setup UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8404/tcp  # HAProxy stats (restrict to your IP later)
sudo ufw enable

# Verify
sudo ufw status verbose
```

---

## Environment Configuration

### Development .env

```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://compair:compair123@postgres:5432/compair
REDIS_URL=redis://redis:6379
SECRET_KEY=dev-key-not-for-production
```

### Production .env

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@neon-host/compair
REDIS_URL=redis://:pass@upstash-host:6379
SECRET_KEY=secure-32-char-minimum-key
CORS_ORIGINS=https://cumpair.tech,https://app.cumpair.tech
```

---

## Database Migrations

### Create New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add new table"

# Create empty migration
alembic revision -m "Add custom index"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade by 1 step
alembic upgrade +1

# Downgrade by 1 step
alembic downgrade -1

# Check current version
alembic current
```

---

## Monitoring Setup

### Prometheus Metrics

1. Add to `monitoring/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'cumpair-web'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    
  - job_name: 'haproxy'
    static_configs:
      - targets: ['haproxy:8404']
    metrics_path: '/metrics'
```

2. Restart Prometheus:

```bash
docker-compose -f docker-compose.prod.yml restart prometheus
```

### Grafana Cloud Integration

1. Get your Grafana Cloud Prometheus endpoint
2. Configure Prometheus remote write
3. Import Cumpair dashboards

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs service-name

# Check disk space
df -h

# Check memory
free -h

# Restart specific service
docker-compose -f docker-compose.prod.yml restart service-name
```

### Database Connection Errors

```bash
# Test database connectivity
docker-compose -f docker-compose.prod.yml exec web python -c "from app.core.database import engine; print('DB OK')"

# Check migrations
docker-compose -f docker-compose.prod.yml exec web alembic current
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Restart memory-heavy services
docker-compose -f docker-compose.prod.yml restart web worker

# Check swap usage
free -h
```

### SSL Certificate Issues

```bash
# Renew certificate
sudo certbot renew

# Test renewal (dry run)
sudo certbot renew --dry-run

# Setup auto-renewal cron
sudo crontab -e
# Add: 0 0 * * * certbot renew --quiet && docker-compose -f /home/cumpair/cumpair/docker-compose.prod.yml restart haproxy
```

---

## GitHub Actions CI/CD

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to DigitalOcean
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.DO_HOST }}
          username: cumpair
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            cd /home/cumpair/cumpair
            git pull
            docker-compose -f docker-compose.prod.yml build
            docker-compose -f docker-compose.prod.yml up -d
            docker-compose -f docker-compose.prod.yml exec -T web alembic upgrade head
```

---

## Local Scraper Setup

### Running Scrapers Locally

```bash
# On your development machine
cd scraper

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit REDIS_URL to point to cloud Redis

# Run scraper
npm start
```

### Scraper as Systemd Service (Optional)

```bash
# Create service file
sudo nano /etc/systemd/system/cumpair-scraper.service

# Content:
[Unit]
Description=Cumpair Scraper Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/cumpair/scraper
ExecStart=/usr/bin/node src/api/server.js
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable cumpair-scraper
sudo systemctl start cumpair-scraper
```

---

## Backup and Recovery

### Database Backups

```bash
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20251018.sql
```

### Automated Backups

```bash
# Add to crontab
0 2 * * * pg_dump $DATABASE_URL > /backups/cumpair_$(date +\%Y\%m\%d).sql
```

---

## Scaling Checklist

### When to Scale

- CPU usage consistently > 70%
- Memory usage > 80%
- API response times > 1s
- Queue length consistently > 100

### How to Scale

1. **Vertical**: Upgrade droplet size
2. **Horizontal**: Add more web workers
3. **Database**: Upgrade Neon plan or use read replicas
4. **Cache**: Upgrade Redis or add Redis cluster

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f service-name`
- Review documentation in `/docs`
- Open GitHub issue

---

**Last Updated**: October 2025
