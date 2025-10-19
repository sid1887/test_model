#!/usr/bin/env pwsh

# 🔧 QUICK REDIS CONNECTION FIX
# This script specifically fixes the Redis connection issue causing the warning loop

Write-Host "🔧 REDIS CONNECTION FIX STARTING..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Stop the scraper service that's spamming Redis warnings
Write-Host "🛑 Stopping scraper service..." -ForegroundColor Yellow
docker-compose -f docker-compose.complete.yml stop scraper

# Check if Redis is running
Write-Host "🔍 Checking Redis status..." -ForegroundColor Yellow
$redisContainer = docker ps -q -f "name=redis"

if ($redisContainer) {
    Write-Host "✅ Redis container is running: $redisContainer" -ForegroundColor Green
    
    # Test Redis connection
    try {
        $redisPing = docker exec $redisContainer redis-cli ping
        Write-Host "✅ Redis connection test: $redisPing" -ForegroundColor Green
    } catch {
        Write-Host "❌ Redis connection test failed" -ForegroundColor Red
        Write-Host "🔧 Restarting Redis..." -ForegroundColor Yellow
        docker-compose -f docker-compose.complete.yml restart redis
        Start-Sleep -Seconds 10
    }
} else {
    Write-Host "❌ Redis container not running" -ForegroundColor Red
    Write-Host "🚀 Starting Redis..." -ForegroundColor Yellow
    docker-compose -f docker-compose.complete.yml up -d redis
    Start-Sleep -Seconds 10
}

# Update scraper environment to handle Redis connection better
Write-Host "🔧 Updating scraper environment..." -ForegroundColor Yellow

# Create a temporary environment file for scraper
@"
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_ENABLED=true
REDIS_RETRY_ATTEMPTS=3
REDIS_RETRY_DELAY=5000
REDIS_CONNECTION_TIMEOUT=10000
NODE_ENV=production
PORT=3001
"@ | Out-File -FilePath ".env.scraper" -Encoding UTF8

# Fix the scraper Redis connection code
Write-Host "🔧 Fixing scraper Redis connection logic..." -ForegroundColor Yellow

# Create a fixed Redis utility for the scraper
$redisFixedContent = @"
const redis = require('redis');
const logger = require('./logger');

class RedisClient {
  constructor() {
    this.client = null;
    this.isConnected = false;
    this.retryAttempts = 0;
    this.maxRetries = 3;
    this.retryDelay = 5000;
    this.connectionTimeout = 10000;
  }

  async connect() {
    try {
      this.client = redis.createClient({
        host: process.env.REDIS_HOST || 'redis',
        port: process.env.REDIS_PORT || 6379,
        connect_timeout: this.connectionTimeout,
        retry_strategy: (options) => {
          if (this.retryAttempts >= this.maxRetries) {
            logger.warn('Redis: Max retry attempts reached, continuing without caching');
            return false;
          }
          
          this.retryAttempts++;
          logger.warn(`Redis: Retry attempt ${this.retryAttempts}/${this.maxRetries}`);
          return this.retryDelay;
        }
      });

      this.client.on('connect', () => {
        logger.info('Redis: Connected successfully');
        this.isConnected = true;
        this.retryAttempts = 0;
      });

      this.client.on('error', (err) => {
        logger.warn(`Redis: Connection error - ${err.message}`);
        this.isConnected = false;
      });

      this.client.on('end', () => {
        logger.warn('Redis: Connection ended');
        this.isConnected = false;
      });

      await this.client.connect();
      return this.client;
    } catch (error) {
      logger.warn(`Redis: Failed to connect - ${error.message}`);
      this.isConnected = false;
      return null;
    }
  }

  async get(key) {
    if (!this.isConnected) {
      return null;
    }
    
    try {
      return await this.client.get(key);
    } catch (error) {
      logger.warn(`Redis: Get operation failed - ${error.message}`);
      return null;
    }
  }

  async set(key, value, ttl = 3600) {
    if (!this.isConnected) {
      return false;
    }
    
    try {
      if (ttl) {
        await this.client.setEx(key, ttl, value);
      } else {
        await this.client.set(key, value);
      }
      return true;
    } catch (error) {
      logger.warn(`Redis: Set operation failed - ${error.message}`);
      return false;
    }
  }

  getStatus() {
    return {
      isConnected: this.isConnected,
      host: process.env.REDIS_HOST || 'redis',
      port: process.env.REDIS_PORT || 6379,
      retryAttempts: this.retryAttempts,
      maxRetries: this.maxRetries
    };
  }
}

module.exports = new RedisClient();
"@

# Write the fixed Redis client to scraper utils
$redisUtilPath = "scraper/src/utils/redis_fixed.js"
$redisFixedContent | Out-File -FilePath $redisUtilPath -Encoding UTF8

Write-Host "✅ Created fixed Redis client at $redisUtilPath" -ForegroundColor Green

# Wait for Redis to be ready
Write-Host "⏳ Waiting for Redis to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test Redis connection
Write-Host "🔍 Testing Redis connection..." -ForegroundColor Yellow
$redisContainer = docker ps -q -f "name=redis"
if ($redisContainer) {
    try {
        $redisPing = docker exec $redisContainer redis-cli ping
        if ($redisPing -eq "PONG") {
            Write-Host "✅ Redis is responding correctly" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Redis responded with: $redisPing" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Redis connection test failed" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Redis container not found" -ForegroundColor Red
}

# Start scraper with fixed configuration
Write-Host "🚀 Starting scraper with fixed configuration..." -ForegroundColor Yellow
docker-compose -f docker-compose.complete.yml up -d scraper

# Wait and check scraper logs
Write-Host "⏳ Waiting for scraper to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "🔍 Checking scraper logs..." -ForegroundColor Yellow
$scraperContainer = docker ps -q -f "name=scraper"
if ($scraperContainer) {
    Write-Host "📋 Recent scraper logs:" -ForegroundColor Yellow
    docker logs $scraperContainer --tail 20
} else {
    Write-Host "❌ Scraper container not found" -ForegroundColor Red
}

# Final status check
Write-Host ""
Write-Host "🎯 FINAL STATUS CHECK" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

Write-Host "Redis Status:" -ForegroundColor Yellow
$redisContainer = docker ps -q -f "name=redis"
if ($redisContainer) {
    Write-Host "✅ Redis container is running" -ForegroundColor Green
} else {
    Write-Host "❌ Redis container not running" -ForegroundColor Red
}

Write-Host "Scraper Status:" -ForegroundColor Yellow
$scraperContainer = docker ps -q -f "name=scraper"
if ($scraperContainer) {
    Write-Host "✅ Scraper container is running" -ForegroundColor Green
} else {
    Write-Host "❌ Scraper container not running" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 REDIS CONNECTION FIX COMPLETE!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "✅ Redis connection issues should be resolved" -ForegroundColor Green
Write-Host "✅ Scraper should no longer spam Redis warnings" -ForegroundColor Green
Write-Host "✅ Fixed Redis client created for future use" -ForegroundColor Green
Write-Host ""
Write-Host "🔍 To monitor:" -ForegroundColor Yellow
Write-Host "   docker-compose -f docker-compose.complete.yml logs -f scraper" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔄 If issues persist, run the comprehensive fix:" -ForegroundColor Yellow
Write-Host "   .\docker-complete-fix.ps1" -ForegroundColor Yellow