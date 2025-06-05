const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const { RateLimiterRedis } = require('rate-limiter-flexible');
require('dotenv').config();

const logger = require('../utils/logger');
const redisClient = require('../utils/redis');
const WebScraper = require('../scraper/WebScraper');

class ScraperAPI {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3000;
    this.scraper = new WebScraper();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet());
    
    // CORS
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(',') : '*',
      methods: ['GET', 'POST'],
      allowedHeaders: ['Content-Type', 'Authorization']
    }));

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 60000,
      max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
      message: {
        error: 'Too many requests from this IP, please try again later.',
        retryAfter: Math.ceil((parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 60000) / 1000)
      },
      standardHeaders: true,
      legacyHeaders: false,
    });

    this.app.use('/api/', limiter);

    // Request logging
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path} - ${req.ip}`);
      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', async (req, res) => {
      try {
        const redisStatus = redisClient.getStatus();
        const scraperStats = this.scraper.getStats();
        
        res.json({
          status: 'healthy',
          timestamp: new Date().toISOString(),
          version: process.env.npm_package_version || '1.0.0',
          uptime: process.uptime(),
          redis: redisStatus,
          scraper: scraperStats,
          memory: process.memoryUsage(),
          cpu: process.cpuUsage()
        });
      } catch (error) {
        logger.error('Health check failed:', error);
        res.status(500).json({
          status: 'unhealthy',
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Single URL scraping endpoint
    this.app.post('/api/scrape', async (req, res) => {
      try {
        const { url, options = {} } = req.body;

        if (!url) {
          return res.status(400).json({
            error: 'URL is required',
            timestamp: new Date().toISOString()
          });
        }

        // Validate URL
        try {
          new URL(url);
        } catch (error) {
          return res.status(400).json({
            error: 'Invalid URL format',
            timestamp: new Date().toISOString()
          });
        }

        // Check cache first if caching is enabled
        if (options.cache !== false) {
          const cachedResult = await this.scraper.getCachedResult(url);
          if (cachedResult) {
            logger.info(`Returning cached result for ${url}`);
            return res.json({
              ...cachedResult,
              cached: true,
              timestamp: new Date().toISOString()
            });
          }
        }

        // Scrape the URL
        const result = await this.scraper.scrapeWithRetry(url, {
          ...options,
          cache: options.cache !== false
        });

        res.json(result);
      } catch (error) {
        logger.error('Scraping failed:', error);
        res.status(500).json({
          error: error.message,
          url: req.body.url,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Batch scraping endpoint
    this.app.post('/api/scrape/batch', async (req, res) => {
      try {
        const { urls, options = {} } = req.body;

        if (!urls || !Array.isArray(urls) || urls.length === 0) {
          return res.status(400).json({
            error: 'URLs array is required',
            timestamp: new Date().toISOString()
          });
        }

        if (urls.length > 50) {
          return res.status(400).json({
            error: 'Maximum 50 URLs allowed per batch',
            timestamp: new Date().toISOString()
          });
        }

        // Validate URLs
        for (const url of urls) {
          try {
            new URL(url);
          } catch (error) {
            return res.status(400).json({
              error: `Invalid URL format: ${url}`,
              timestamp: new Date().toISOString()
            });
          }
        }

        const result = await this.scraper.scrapeConcurrently(urls, {
          ...options,
          cache: options.cache !== false
        });

        res.json({
          ...result,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        logger.error('Batch scraping failed:', error);
        res.status(500).json({
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Get scraper statistics
    this.app.get('/api/stats', (req, res) => {
      try {
        const stats = this.scraper.getStats();
        res.json({
          ...stats,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        logger.error('Failed to get stats:', error);
        res.status(500).json({
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Get cached data
    this.app.get('/api/cache/:key', async (req, res) => {
      try {
        const { key } = req.params;
        const data = await redisClient.get(`scraper:${key}`);
        
        if (!data) {
          return res.status(404).json({
            error: 'Data not found in cache',
            timestamp: new Date().toISOString()
          });
        }

        res.json({
          data,
          cached: true,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        logger.error('Failed to get cached data:', error);
        res.status(500).json({
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Clear cache
    this.app.delete('/api/cache', async (req, res) => {
      try {
        const { pattern = 'scraper:*' } = req.query;
        const keys = await redisClient.getKeys(pattern);
        
        if (keys.length > 0) {
          for (const key of keys) {
            await redisClient.del(key);
          }
        }

        res.json({
          message: `Cleared ${keys.length} cache entries`,
          pattern,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        logger.error('Failed to clear cache:', error);
        res.status(500).json({
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Default route
    this.app.get('/', (req, res) => {
      res.json({
        message: 'Web Scraper API',
        version: process.env.npm_package_version || '1.0.0',
        documentation: '/api/docs',
        health: '/health',
        endpoints: {
          'POST /api/scrape': 'Scrape a single URL',
          'POST /api/scrape/batch': 'Scrape multiple URLs',
          'GET /api/stats': 'Get scraper statistics',
          'GET /api/cache/:key': 'Get cached data',
          'DELETE /api/cache': 'Clear cache'
        }
      });
    });
  }

  setupErrorHandling() {
    // 404 handler
    this.app.use((req, res) => {
      res.status(404).json({
        error: 'Endpoint not found',
        path: req.path,
        method: req.method,
        timestamp: new Date().toISOString()
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      logger.error('Unhandled error:', error);
      
      res.status(error.status || 500).json({
        error: error.message || 'Internal server error',
        timestamp: new Date().toISOString(),
        ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
      });
    });
  }

  async start() {
    try {
      // Connect to Redis
      await redisClient.connect();
      
      // Start the server
      this.server = this.app.listen(this.port, () => {
        logger.info(`Scraper API server running on port ${this.port}`);
        logger.info(`Health check: http://localhost:${this.port}/health`);
        logger.info(`API Documentation: http://localhost:${this.port}/`);
      });

      // Graceful shutdown handling
      process.on('SIGTERM', this.shutdown.bind(this));
      process.on('SIGINT', this.shutdown.bind(this));
      process.on('uncaughtException', (error) => {
        logger.error('Uncaught exception:', error);
        this.shutdown();
      });
      process.on('unhandledRejection', (reason, promise) => {
        logger.error('Unhandled rejection at:', promise, 'reason:', reason);
        this.shutdown();
      });

    } catch (error) {
      logger.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  async shutdown() {
    logger.info('Shutting down server...');
    
    try {
      // Close HTTP server
      if (this.server) {
        await new Promise((resolve) => {
          this.server.close(resolve);
        });
        logger.info('HTTP server closed');
      }

      // Cleanup scraper
      await this.scraper.cleanup();

      // Disconnect from Redis
      await redisClient.disconnect();

      logger.info('Graceful shutdown completed');
      process.exit(0);
    } catch (error) {
      logger.error('Error during shutdown:', error);
      process.exit(1);
    }
  }
}

// Start the server if this file is run directly
if (require.main === module) {
  const api = new ScraperAPI();
  api.start();
}

module.exports = ScraperAPI;
