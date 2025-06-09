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
    });    // Get scraper statistics
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

    // Product search endpoint - compatible with FastAPI backend
    this.app.post('/api/search', async (req, res) => {
      try {
        const { query, sites = ['amazon', 'walmart', 'ebay'] } = req.body;

        if (!query) {
          return res.status(400).json({
            error: 'Query parameter is required',
            timestamp: new Date().toISOString()
          });
        }

        // Generate search URLs for different sites
        const searchUrls = [];
        const siteUrlGenerators = {
          amazon: (q) => `https://www.amazon.com/s?k=${encodeURIComponent(q)}`,
          walmart: (q) => `https://www.walmart.com/search?q=${encodeURIComponent(q)}`,
          ebay: (q) => `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(q)}`
        };

        for (const site of sites) {
          if (siteUrlGenerators[site]) {
            searchUrls.push({
              site,
              url: siteUrlGenerators[site](query)
            });
          }
        }

        // Scrape all URLs concurrently
        const scrapingPromises = searchUrls.map(async ({ site, url }) => {
          try {
            const result = await this.scraper.scrapeWithRetry(url, {
              selectors: this.getSelectorsForSite(site),
              usePuppeteer: true, // Use headless browser for e-commerce sites
              cache: true
            });

            if (result.success) {
              return {
                site,
                url,
                products: this.extractProductsFromData(result.data, site),
                timestamp: result.timestamp
              };
            } else {
              logger.warn(`Failed to scrape ${site}: ${result.error}`);
              return { site, url, products: [], error: result.error };
            }
          } catch (error) {
            logger.error(`Error scraping ${site}:`, error);
            return { site, url, products: [], error: error.message };
          }
        });

        const results = await Promise.all(scrapingPromises);
        
        // Flatten and format results
        const allProducts = [];
        const metadata = {
          query,
          sites_searched: sites,
          successful_sites: 0,
          failed_sites: 0,
          timestamp: new Date().toISOString()
        };

        results.forEach(result => {
          if (result.products && result.products.length > 0) {
            allProducts.push(...result.products);
            metadata.successful_sites++;
          } else {
            metadata.failed_sites++;
          }
        });

        res.json({
          query,
          results: allProducts,
          metadata: {
            ...metadata,
            total_results: allProducts.length
          }
        });

      } catch (error) {
        logger.error('Product search failed:', error);
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
        health: '/health',        endpoints: {
          'POST /api/scrape': 'Scrape a single URL',
          'POST /api/scrape/batch': 'Scrape multiple URLs',
          'POST /api/search': 'Search products across e-commerce sites',
          'GET /api/stats': 'Get scraper statistics',
          'GET /api/cache/:key': 'Get cached data',
          'DELETE /api/cache': 'Clear cache'
        }
      });
    });
  }

  // Helper method to get selectors for different e-commerce sites
  getSelectorsForSite(site) {
    const selectors = {
      amazon: {
        products: '[data-component-type="s-search-result"], .s-result-item',
        title: 'h2 a span, .a-link-normal .a-text-normal',
        price: '.a-price .a-offscreen, .a-price-whole',
        image: 'img',
        link: 'h2 a, .a-link-normal'
      },
      walmart: {
        products: '[data-automation-id="product-title"]',
        title: '[data-automation-id="product-title"]',
        price: '[itemprop="price"]',
        image: 'img',
        link: 'a'
      },
      ebay: {
        products: '.s-item',
        title: '.s-item__title',
        price: '.s-item__price',
        image: '.s-item__image img',
        link: '.s-item__link'
      }
    };

    return selectors[site] || {
      products: '.product, .item',
      title: 'h1, h2, h3, .title',
      price: '.price, .cost',
      image: 'img',
      link: 'a'
    };
  }

  // Helper method to extract products from scraped data
  extractProductsFromData(data, site) {
    const products = [];
    
    try {
      // If we have HTML content, parse it with Cheerio
      if (data.html) {
        const cheerio = require('cheerio');
        const $ = cheerio.load(data.html);
        const selectors = this.getSelectorsForSite(site);
        
        $(selectors.products).each((i, element) => {
          if (i >= 10) return false; // Limit to 10 products per site
          
          const $item = $(element);
          const title = $item.find(selectors.title).first().text().trim();
          const priceText = $item.find(selectors.price).first().text().trim();
          const imageUrl = $item.find(selectors.image).first().attr('src') || '';
          const link = $item.find(selectors.link).first().attr('href') || '';
          
          if (title && priceText) {            products.push({
              title,
              price: priceText,
              image: imageUrl,
              link: this.normalizeUrl(link, site),
              site,
              timestamp: new Date().toISOString()
            });
          }
        });
      }
    } catch (error) {
      logger.error(`Error extracting products for ${site}:`, error);
    }
    
    return products;
  }

  // Helper method to normalize URLs
  normalizeUrl(url, site) {
    if (!url) return '';
    
    if (url.startsWith('http')) {
      return url;
    }
    
    const baseDomains = {
      amazon: 'https://www.amazon.com',
      walmart: 'https://www.walmart.com',
      ebay: 'https://www.ebay.com'
    };
      const baseDomain = baseDomains[site] || '';
    return url.startsWith('/') ? `${baseDomain}${url}` : `${baseDomain}/${url}`;
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
