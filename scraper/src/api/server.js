const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const cheerio = require('cheerio');
// const { RateLimiterRedis } = require('rate-limiter-flexible'); // TODO: Implement Redis rate limiting
require('dotenv').config();

const logger = require('../utils/logger');
const redisClient = require('../utils/redis');
const WebScraper = require('../scraper/WebScraper');

class ScraperAPI {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3001;
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
      legacyHeaders: false
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

    // Status endpoint (alias for health)
    this.app.get('/status', async (req, res) => {
      try {
        const redisStatus = redisClient.getStatus();
        const scraperStats = this.scraper.getStats();

        res.json({
          status: 'healthy',
          service: 'scraper',
          timestamp: new Date().toISOString(),
          version: process.env.npm_package_version || '1.0.0',
          uptime: process.uptime(),
          redis: redisStatus,
          scraper: scraperStats
        });
      } catch (error) {
        logger.error('Status check failed:', error);
        res.status(500).json({
          status: 'unhealthy',
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Debug endpoint to inspect HTML and test selectors
    this.app.post('/api/debug/selectors', async (req, res) => {
      try {
        const { url, site } = req.body;

        if (!url) {
          return res.status(400).json({
            error: 'URL is required',
            timestamp: new Date().toISOString()
          });
        }

        // Scrape the page
        const result = await this.scraper.scrapeWithPuppeteer(url, {
          usePuppeteer: true,
          selectors: this.getSelectorsForSite(site)
        });

        if (!result.success) {
          return res.status(500).json({
            error: result.error,
            timestamp: new Date().toISOString()
          });
        }

        const $ = cheerio.load(result.data.html);

        // Test each selector
        const selectors = this.getSelectorsForSite(site);
        const debugInfo = {
          site,
          url,
          htmlLength: result.data.html.length,
          selectors: {}
        };

        for (const [key, selector] of Object.entries(selectors)) {
          if (typeof selector === 'string') {
            const elements = $(selector);
            debugInfo.selectors[key] = {
              selector,
              found: elements.length,
              firstElement: elements.length > 0 ? $(elements[0]).html().substring(0, 200) : null,
              allClasses: elements.length > 0 ? Array.from(new Set(
                Array.from(elements).map(el => $(el).attr('class')).filter(c => c)
              )).slice(0, 5) : [],
              allIds: elements.length > 0 ? Array.from(new Set(
                Array.from(elements).map(el => $(el).attr('id')).filter(c => c)
              )).slice(0, 5) : []
            };
          }
        }

        res.json(debugInfo);
      } catch (error) {
        logger.error('Debug selector check failed:', error);
        res.status(500).json({
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
        const { query, sites = ['amazon', 'walmart', 'ebay', 'target', 'bestbuy'] } = req.body;

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
          ebay: (q) => `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(q)}`,
          target: (q) => `https://www.target.com/s?searchTerm=${encodeURIComponent(q)}`,
          bestbuy: (q) => `https://www.bestbuy.com/site/searchpage.jsp?st=${encodeURIComponent(q)}`,
          newegg: (q) => `https://www.newegg.com/p/pl?d=${encodeURIComponent(q)}`
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
            logger.info(`Starting scrape for ${site}: ${url}`);
            const result = await this.scraper.scrapeWithRetry(url, {
              selectors: this.getSelectorsForSite(site),
              usePuppeteer: true, // Use headless browser for e-commerce sites
              cache: true
            });

            logger.info(`Scrape result for ${site} - success: ${result.success}, status: ${result.status}`);

            if (result.success) {
              logger.info(`Scrape successful for ${site}, extracting products...`);
              logger.info(`Result data keys: ${Object.keys(result.data).join(', ')}`);
              logger.info(`Has HTML: ${!!result.data.html}, HTML length: ${result.data.html ? result.data.html.length : 0}`);

              const products = this.extractProductsFromData(result.data, site);
              return {
                site,
                url,
                products,
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

    // High-performance parallel search across ALL retailers
    this.app.post('/api/search/parallel', async (req, res) => {
      try {
        const { query, max_results_per_site = 10 } = req.body;

        if (!query) {
          return res.status(400).json({
            error: 'Query parameter is required',
            timestamp: new Date().toISOString()
          });
        }

        const startTime = Date.now();

        // All available retailers (15+)
        const allSites = [
          'amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg',
          'flipkart', 'shopclues', 'jabong', 'snapdeal', 'myntra',
          'aliexpress', 'alibaba'
        ];

        const siteUrlGenerators = {
          amazon: (q) => `https://www.amazon.com/s?k=${encodeURIComponent(q)}`,
          walmart: (q) => `https://www.walmart.com/search?q=${encodeURIComponent(q)}`,
          ebay: (q) => `https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(q)}`,
          target: (q) => `https://www.target.com/s?searchTerm=${encodeURIComponent(q)}`,
          bestbuy: (q) => `https://www.bestbuy.com/site/searchpage.jsp?st=${encodeURIComponent(q)}`,
          newegg: (q) => `https://www.newegg.com/p/pl?d=${encodeURIComponent(q)}`,
          flipkart: (q) => `https://www.flipkart.com/search?q=${encodeURIComponent(q)}`,
          shopclues: (q) => `https://www.shopclues.com/search?q=${encodeURIComponent(q)}`,
          jabong: (q) => `https://www.jabong.com/search?q=${encodeURIComponent(q)}`,
          snapdeal: (q) => `https://www.snapdeal.com/search?keyword=${encodeURIComponent(q)}`,
          myntra: (q) => `https://www.myntra.com/search/${encodeURIComponent(q)}`,
          aliexpress: (q) => `https://www.aliexpress.com/wholesale?SearchText=${encodeURIComponent(q)}`,
          alibaba: (q) => `https://www.alibaba.com/trade/search?SearchText=${encodeURIComponent(q)}`
        };

        // Generate all URLs
        const searchTasks = allSites.map(site => ({
          site,
          url: siteUrlGenerators[site](query)
        }));

        // Scrape with controlled concurrency (max 3 at a time)
        const maxConcurrent = 3;
        const results = [];

        for (let i = 0; i < searchTasks.length; i += maxConcurrent) {
          const batch = searchTasks.slice(i, i + maxConcurrent);
          logger.info(`Processing batch ${Math.ceil(i / maxConcurrent) + 1}/${Math.ceil(searchTasks.length / maxConcurrent)}`);

          const batchResults = await Promise.allSettled(
            batch.map(async ({ site, url }) => {
              try {
                logger.info(`Starting scrape for ${site}: ${url}`);
                const result = await this.scraper.scrapeWithRetry(url, {
                  selectors: this.getSelectorsForSite(site),
                  usePuppeteer: true,
                  useProxy: true,
                  cache: true,
                  cacheTTL: 300 // 5 minutes cache
                });

                if (result.success) {
                  const products = this.extractProductsFromData(result.data, site);
                  logger.info(`Successfully scraped ${site}: ${products.length} products`);
                  return {
                    site,
                    url,
                    products: products.slice(0, max_results_per_site),
                    count: products.length,
                    status: 'success'
                  };
                } else {
                  logger.warn(`Scrape failed for ${site}: ${result.error}`);
                  return { site, url, products: [], count: 0, status: 'failed', error: result.error };
                }
              } catch (error) {
                logger.error(`Parallel search error for ${site}:`, error.message);
                return { site, url, products: [], count: 0, status: 'error', error: error.message };
              }
            })
          );

          results.push(...batchResults);
        }

        // Process results
        const allProducts = [];
        const siteResults = {};
        let successCount = 0;
        let failCount = 0;

        results.forEach((result, index) => {
          const site = searchTasks[index]?.site;
          if (result.status === 'fulfilled' && result.value.status === 'success') {
            allProducts.push(...result.value.products);
            siteResults[site] = {
              status: 'success',
              count: result.value.count,
              products: result.value.products.length
            };
            successCount++;
          } else {
            siteResults[site] = {
              status: 'failed',
              error: result.reason || result.value?.error || 'Unknown error'
            };
            failCount++;
          }
        });

        const executionTime = Date.now() - startTime;

        res.json({
          query,
          execution_time_ms: executionTime,
          results: allProducts,
          metadata: {
            total_products: allProducts.length,
            sites_searched: allSites.length,
            successful_sites: successCount,
            failed_sites: failCount,
            average_time_per_site_ms: Math.round(executionTime / allSites.length),
            site_results: siteResults,
            scraper_stats: this.scraper.getStats(),
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        logger.error('Parallel search failed:', error);
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
        title: 'h2 span, .a-size-mini, .a-size-base',
        price: '.a-price, .a-price-whole, [data-a-color="price"]',
        image: 'img.s-image, img.s-mobile-badge-image',
        link: 'h2 a, .a-link-normal'
      },
      walmart: {
        products: 'li[role="listitem"], [class*="ProductCard"], [data-item-id], div[class*="tile"]',
        title: 'a, span, h2, h3, [class*="title"]',
        price: 'span, [class*="price"], div[class*="Price"]',
        image: 'img',
        link: 'a[href*="/product"], a[href*="/ip/"]'
      },
      ebay: {
        products: 'li.s-item, div[class*="s-item"], li[role="listitem"], div[class*="item"]',
        title: 'h2, h3, span, a, .s-item__title',
        price: 'span, div, .BOLD, [class*="price"]',
        image: 'img',
        link: 'a[href*="/itm/"], a.BOLD, a[href]'
      },
      target: {
        products: '[data-test*="productCard"], .Card, .product, [class*="ProductCard"]',
        title: '[data-test="product-title"], .ProductCardDescription__name, h2[class*="title"]',
        price: '[data-test*="price"], .ProductPrice__current, [class*="price"]',
        image: 'img[data-test], img[class*="ProductImage"]',
        link: 'a[href*="/p/"], [class*="ProductCard__link"]'
      },
      bestbuy: {
        products: 'li.sku-item, div[class*="productContainer"], li[role="listitem"], [class*="sku-item"]',
        title: 'h2, h3, span, a, .sku-title, [class*="title"]',
        price: 'span, div, [class*="price"], .priceView',
        image: 'img',
        link: 'a[href*="/sku/"], a[href*="/product"], .sku-title a'
      },
      newegg: {
        products: 'div.item-cell, li[class*="product"], div[role="listitem"], [class*="product-item"]',
        title: 'h2, h3, span, a, .item-title, [class*="title"]',
        price: 'span, div, [class*="price"], .price-current',
        image: 'img',
        link: 'a[href*="/product"], a[href*="/items"], .item-title a'
      },
      flipkart: {
        products: 'div[data-component-type], ._2kHMtA, div[class*="productGrid"]',
        title: 'a._2r_T1i, ._4rR01T, [class*="productTitle"]',
        price: '._30jeq3, ._2Kzpj-',
        image: 'img._396cs4, img[class*="productImage"]',
        link: 'a._2r_T1i, a[class*="productLink"]'
      },
      shopclues: {
        products: '.productCont, .product-item, [class*="productContainer"]',
        title: '.p_name, .product-title, h2',
        price: '.p_discountedprice, .prod-price, [class*="price"]',
        image: 'img.productThumbImage, img[class*="productImage"]',
        link: 'a.productCardImg, a.product-link'
      },
      jabong: {
        products: '.productCardContainer, .product-item, [data-component="productCard"]',
        title: '.productCardName, .product-title, h2',
        price: '.productCardPrice, .prod-price, [class*="price"]',
        image: 'img.productCardImage, img[class*="productImage"]',
        link: 'a.productCardLink, .product-link'
      },
      snapdeal: {
        products: '.productCardImg, .productContainer, [class*="productCard"]',
        title: '.productCardBody, .productTitle, h2',
        price: '.discountedPriceText, .productCardPrice, [class*="price"]',
        image: 'img.productImage, img[class*="product"]',
        link: 'a.productCardImg, .productCardLink'
      },
      myntra: {
        products: '.productCardImg, .productContainer, [class*="productCard"]',
        title: '.productBrand, .productTitle, h3',
        price: '.productDiscountedPriceText, [class*="price"]',
        image: 'img.productCardImg, img[class*="productImage"]',
        link: 'a.productCardImg, .productCardLink'
      },
      aliexpress: {
        products: '.organic-list-offer, .search-item-card-wrapper',
        title: '.organic-list-offer-title, h2[class*="title"]',
        price: '.search-item-price, ._3c6Seb',
        image: 'img, [class*="productImage"]',
        link: 'a[href*="/item/"], .search-item-card-wrapper a'
      },
      alibaba: {
        products: '.organic-list-offer, .search-item, [class*="productItem"]',
        title: 'a.search-item-link-title, h2, [class*="title"]',
        price: '.organic-list-offer-price, [class*="price"]',
        image: 'img, [class*="productImage"]',
        link: 'a.search-item-link-title, .product-link'
      }
    };

    return selectors[site] || {
      products: '.product, .item, [data-testid*="product"], [class*="product"], li[data-product]',
      title: 'h1, h2, h3, .title, .name, [class*="title"], [class*="name"]',
      price: '.price, .cost, [class*="price"], [data-testid*="price"]',
      image: 'img[src], img[data-src]',
      link: 'a[href]'
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

        const productElements = $(selectors.products);
        logger.info(`Found ${productElements.length} product elements for ${site} using selector: ${selectors.products}`);

        $(selectors.products).each((i, element) => {
          if (i >= 10) return false; // Limit to 10 products per site

          const $item = $(element);

          // Extract title - be selective to avoid UI text
          let title = '';

          // Try specific title selectors
          const titleSelectors = [selectors.title, 'h2 a span', 'h2 span', 'a h2', 'h2 a', 'h1', '.product-name', '.product-title', 'a[href*="product"]'];
          for (const sel of titleSelectors) {
            const foundTitle = $item.find(sel).first().text().trim();
            if (foundTitle && foundTitle.length > 15 && !foundTitle.includes('Check') && !foundTitle.includes('highlighted')) {
              title = foundTitle;
              break;
            }
          }

          // Fallback: look for longest reasonable text content in major containers
          if (!title || title.length < 10) {
            const allText = $item.find('h2, h3, a, .title, .name, span[class*="title"]').map((idx, el) => $(el).text().trim()).get();
            const candidateTitles = allText.filter(t => t.length > 10 && t.length < 200 && !t.includes('Check') && !t.includes('highlighted') && !t.includes('Overall'));
            if (candidateTitles.length > 0) {
              title = candidateTitles[0];
            }
          }

          // Try to find price
          let priceText = $item.find(selectors.price).first().text().trim();
          if (!priceText) {
            priceText = $item.find('.price, .prod-price, [class*="price"]').first().text().trim();
          }
          if (!priceText) {
            // Try to find any price-like text
            const allText = $item.text();
            const priceMatch = allText.match(/\$[\d.,]+|₹[\d.,]+|€[\d.,]+/);
            priceText = priceMatch ? priceMatch[0] : '';
          }

          // Get image URL
          let imageUrl = $item.find(selectors.image).first().attr('src');
          if (!imageUrl) imageUrl = $item.find(selectors.image).first().attr('data-src');
          if (!imageUrl) imageUrl = $item.find(selectors.image).first().attr('data-lazy-src');
          if (!imageUrl) imageUrl = $item.find('img').first().attr('src');
          imageUrl = imageUrl || '';

          // Get link
          let link = $item.find(selectors.link).first().attr('href');
          if (!link) link = $item.filter('a').attr('href');
          if (!link) link = $item.closest('a').attr('href');
          if (!link) link = $item.find('a[href]').first().attr('href');
          link = link || '';

          if (i < 3) {
            logger.info(`Product ${i} for ${site}:`);
            logger.info(`  Title: ${title.substring(0, 60)}`);
            logger.info(`  Price: ${priceText}`);
          }

          // Only add if we have a reasonable title (10+ chars, not junk)
          if (title && title.length >= 10 && !title.includes('Check') && !title.includes('highlighted') && !title.includes('Overall') && !title.includes('undefined')) {
            products.push({
              title: title.substring(0, 300), // Limit title length
              price: priceText || 'N/A',
              image: imageUrl,
              link: this.normalizeUrl(link, site),
              site,
              timestamp: new Date().toISOString()
            });
          }
        });

        logger.info(`Extracted ${products.length} products from ${site}`);
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
      ebay: 'https://www.ebay.com',
      target: 'https://www.target.com',
      bestbuy: 'https://www.bestbuy.com',
      newegg: 'https://www.newegg.com'
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
    });    // Global error handler
    this.app.use((error, req, res, _next) => {
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
