/**
 * Enhanced Cumpair Scraping Microservice
 * Node.js + Puppeteer-based e-commerce scraper supporting 15+ retailers
 * Anti-bot measures and enhanced reliability
 */

const express = require('express');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const AdblockerPlugin = require('puppeteer-extra-plugin-adblocker');
const UserAgent = require('user-agents');
const axios = require('axios');
const cors = require('cors');
const helmet = require('helmet');
const { RateLimiterMemory } = require('rate-limiter-flexible');
const winston = require('winston');
require('dotenv').config();

// Configure Puppeteer with stealth
puppeteer.use(StealthPlugin());
puppeteer.use(AdblockerPlugin({ blockTrackers: true }));

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'scraper.log' })
  ]
});

const app = express();
const PORT = process.env.SCRAPER_PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Rate limiting
const rateLimiter = new RateLimiterMemory({
  keyResolver: (req) => req.ip,
  points: 10, // 10 requests
  duration: 60 // per 60 seconds
});

// Rate limiter middleware
const rateLimiterMiddleware = async (req, res, next) => {
  try {
    await rateLimiter.consume(req.ip);
    next();
  } catch (rejRes) {
    res.status(429).send('Too Many Requests');
  }
};

// Enhanced scrapers supporting 15+ retailers
const scrapers = {
  // TIER 1: Major US Retailers (High Priority)
  amazon: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.setViewport({ width: 1366, height: 768 });

        await page.evaluateOnNewDocument(() => {
          Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        });

        await page.goto(`https://www.amazon.com/s?k=${encodeURIComponent(query)}`, {
          waitUntil: 'domcontentloaded',
          timeout: 45000
        });

        await page.waitForTimeout(2000);

        const products = await page.evaluate(() => {
          const selectors = [
            '[data-component-type="s-search-result"]',
            '.s-result-item',
            '.sg-col-inner .s-card-container',
            '[data-asin]:not([data-asin=""])'
          ];

          let items = [];
          for (const selector of selectors) {
            items = Array.from(document.querySelectorAll(selector));
            if (items.length > 0) break;
          }

          return items.slice(0, 5).map(item => {
            const titleSelectors = ['h2 a span', '.a-link-normal .a-text-normal', '[data-cy="title-recipe-title"]'];
            const priceSelectors = ['.a-price .a-offscreen', '.a-price-whole', '.a-price-fraction'];

            let titleEl = null;
            for (const selector of titleSelectors) {
              titleEl = item.querySelector(selector);
              if (titleEl) break;
            }

            let priceEl = null;
            for (const selector of priceSelectors) {
              priceEl = item.querySelector(selector);
              if (priceEl) break;
            }

            const imageEl = item.querySelector('img');
            const linkEl = item.querySelector('h2 a') || item.querySelector('.a-link-normal');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.amazon.com${linkEl.getAttribute('href')}` : '',
              site: 'amazon'
            };
          }).filter(item => item.title && item.title.length > 0);
        });

        logger.info(`Amazon scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Amazon scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  walmart: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.walmart.com/search?q=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('[data-automation-id="product-title"]'));
          return items.slice(0, 5).map(item => {
            const container = item.closest('[data-item-id]');
            const titleEl = container?.querySelector('[data-automation-id="product-title"]');
            const priceEl = container?.querySelector('[itemprop="price"]') || container?.querySelector('.price-current');
            const imageEl = container?.querySelector('img');
            const linkEl = container?.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.walmart.com${linkEl.getAttribute('href')}` : '',
              site: 'walmart'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Walmart scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Walmart scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  target: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.target.com/s?searchTerm=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('[data-test="product-card"], .ProductCard'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('[data-test="product-title"], .ProductCard__title, h3');
            const priceEl = item.querySelector('[data-test="product-price"], .Price, .price');
            const imageEl = item.querySelector('[data-test="product-image"], .ProductCard__image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.target.com${linkEl.getAttribute('href')}` : '',
              site: 'target'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Target scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Target scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  bestbuy: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.bestbuy.com/site/searchpage.jsp?st=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.sku-item, .product-item'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.sku-title h1, .v-fw-regular, .sku-title');
            const priceEl = item.querySelector('.priceView-hero-price span, .priceView-customer-price span, .sr-only');
            const imageEl = item.querySelector('.primary-image, .media-wrapper img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.bestbuy.com${linkEl.getAttribute('href')}` : '',
              site: 'bestbuy'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Best Buy scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Best Buy scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  ebay: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.ebay.com/sch/i.html?_nkw=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.s-item'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.s-item__title');
            const priceEl = item.querySelector('.s-item__price');
            const imageEl = item.querySelector('.s-item__image img');
            const linkEl = item.querySelector('.s-item__link');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl?.getAttribute('href') || '',
              site: 'ebay'
            };
          }).filter(item => item.title && item.price && !item.title.includes('Shop on eBay'));
        });

        logger.info(`eBay scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`eBay scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  // TIER 2: Major Specialized Retailers
  costco: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.costco.com/CatalogSearch?keyword=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.product-tile, .product'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.description, .product-title, h1');
            const priceEl = item.querySelector('.price, .product-price');
            const imageEl = item.querySelector('img.product-image, .product-img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.costco.com${linkEl.getAttribute('href')}` : '',
              site: 'costco'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Costco scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Costco scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  homedepot: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.homedepot.com/s/${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.plp-pod, .product-pod'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.product-title, .pod-plp__title');
            const priceEl = item.querySelector('.price, .price-format__main-price');
            const imageEl = item.querySelector('.product-image, .product-pod__image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.homedepot.com${linkEl.getAttribute('href')}` : '',
              site: 'homedepot'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Home Depot scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Home Depot scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  lowes: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.lowes.com/search?searchTerm=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.plp-tile, .product-tile'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.product-title, .art-pd-title');
            const priceEl = item.querySelector('.price, .price-current');
            const imageEl = item.querySelector('.product-image img, .art-pd-image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.lowes.com${linkEl.getAttribute('href')}` : '',
              site: 'lowes'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Lowe's scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Lowe's scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  newegg: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.newegg.com/p/pl?d=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.item-cell, .item-container'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.item-title, .item-brand');
            const priceEl = item.querySelector('.price-current, .price-current-num');
            const imageEl = item.querySelector('.item-img img, .product-image');
            const linkEl = item.querySelector('.item-title a, a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.newegg.com${linkEl.getAttribute('href')}` : '',
              site: 'newegg'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Newegg scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Newegg scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  macys: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.macys.com/shop/search?keyword=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.productThumbnail, .product-thumbnail'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.product-title, .productDescription');
            const priceEl = item.querySelector('.price, .product-price');
            const imageEl = item.querySelector('.product-image img, .productThumbnailImage');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.macys.com${linkEl.getAttribute('href')}` : '',
              site: 'macys'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Macy's scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Macy's scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  // TIER 3: Specialized Online Retailers
  overstock: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.overstock.com/search?keywords=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('.product-item, .product'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('.product-title, .product-name');
            const priceEl = item.querySelector('.price, .product-price');
            const imageEl = item.querySelector('.product-image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.overstock.com${linkEl.getAttribute('href')}` : '',
              site: 'overstock'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Overstock scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Overstock scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  wayfair: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.wayfair.com/keyword.php?keyword=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('[data-testid="ProductCard"], .ProductCard'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('[data-testid="ProductName"], .ProductCard__name');
            const priceEl = item.querySelector('[data-testid="PrimaryPrice"], .ProductCard__price');
            const imageEl = item.querySelector('[data-testid="ProductCardImage"], .ProductCard__image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.wayfair.com${linkEl.getAttribute('href')}` : '',
              site: 'wayfair'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Wayfair scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Wayfair scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  zappos: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.zappos.com/search?term=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('[data-testid="product-grid-item"], .product'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('[data-testid="product-name"], .product-name');
            const priceEl = item.querySelector('[data-testid="product-price"], .product-price');
            const imageEl = item.querySelector('[data-testid="product-image"], .product-image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.zappos.com${linkEl.getAttribute('href')}` : '',
              site: 'zappos'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Zappos scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Zappos scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  bhphotovideo: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.bhphotovideo.com/c/search?Ntt=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('[data-selenium="itemInner"], .js-item-container'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('[data-selenium="itemTitle"], .item-title');
            const priceEl = item.querySelector('[data-selenium="itemPrice"], .price');
            const imageEl = item.querySelector('[data-selenium="itemImage"], .item-image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.bhphotovideo.com${linkEl.getAttribute('href')}` : '',
              site: 'bhphotovideo'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`B&H Photo scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`B&H Photo scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  },

  nordstrom: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.nordstrom.com/sr?keyword=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('[data-testid="product-module"], .product-module'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('[data-testid="product-title"], .product-title');
            const priceEl = item.querySelector('[data-testid="product-price"], .product-price');
            const imageEl = item.querySelector('[data-testid="product-image"], .product-image img');
            const linkEl = item.querySelector('a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.nordstrom.com${linkEl.getAttribute('href')}` : '',
              site: 'nordstrom'
            };
          }).filter(item => item.title && item.price);
        });

        logger.info(`Nordstrom scraper found ${products.length} products for query: ${query}`);
        return products;
      } catch (error) {
        logger.error(`Nordstrom scraper error: ${error.message}`);
        return [];
      } finally {
        await page.close();
      }
    }
  }
};

// Browser instance management
let browserInstance = null;

const getBrowser = async () => {
  if (!browserInstance) {
    browserInstance = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--no-first-run',
        '--no-zygote',
        '--disable-gpu'
      ]
    });
  }
  return browserInstance;
};

// Python service integration
const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:8000';

async function postToPythonService(productData) {
  try {
    const response = await axios.post(`${PYTHON_SERVICE_URL}/analysis/ingest-scraped-product`, {
      product_id: productData.id,
      site: productData.site,
      url: productData.link,
      title: productData.title,
      price_raw: productData.price,
      currency: 'USD',
      image_url: productData.image,
      timestamp: new Date().toISOString()
    }, {
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    logger.info(`Successfully posted product ${productData.id} to Python service`);
    return response.data;
  } catch (error) {
    logger.error(`Failed to post product ${productData.id} to Python service: ${error.message}`);
    throw error;
  }
}

// Routes
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    supported_retailers: Object.keys(scrapers).length,
    retailers: Object.keys(scrapers)
  });
});

app.post('/scrape', rateLimiterMiddleware, async (req, res) => {
  const { query, sites = Object.keys(scrapers) } = req.body;

  if (!query) {
    return res.status(400).json({ error: 'Query parameter is required' });
  }

  try {
    const browser = await getBrowser();
    const results = [];
    const pythonServiceResults = [];

    // Filter requested sites to only supported ones
    const supportedSites = sites.filter(site => scrapers[site]);
    
    logger.info(`Starting scraping for query: ${query} across ${supportedSites.length} sites`);

    // Run scrapers in parallel with controlled concurrency
    const scrapingPromises = supportedSites.map(async (site) => {
      try {
        const siteResults = await scrapers[site].search(query, browser);

        // Process each result through Python service
        for (const product of siteResults) {
          product.id = `${site}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

          try {
            const pythonResult = await postToPythonService(product);
            pythonServiceResults.push({
              product,
              processing: pythonResult
            });
          } catch (error) {
            logger.error(`Python service failed for product ${product.id}: ${error.message}`);
          }
        }

        return siteResults;
      } catch (error) {
        logger.error(`Error scraping ${site}: ${error.message}`);
        return [];
      }
    });

    const scrapingResults = await Promise.all(scrapingPromises);

    // Flatten results
    scrapingResults.forEach(siteResults => {
      results.push(...siteResults);
    });

    // Sort by price (extract numeric value)
    results.sort((a, b) => {
      const priceA = parseFloat(a.price.replace(/[^0-9.]/g, '')) || Infinity;
      const priceB = parseFloat(b.price.replace(/[^0-9.]/g, '')) || Infinity;
      return priceA - priceB;
    });

    logger.info(`Scraping completed for query: ${query}, found ${results.length} total products across ${supportedSites.length} sites`);

    res.json({
      query,
      results,
      python_service_processed: pythonServiceResults.length,
      metadata: {
        total_results: results.length,
        sites_scraped: supportedSites,
        sites_requested: sites,
        timestamp: new Date().toISOString(),
        feature_extraction_enabled: true,
        total_retailers_supported: Object.keys(scrapers).length
      }
    });
  } catch (error) {
    logger.error(`Scraping error: ${error.message}`);
    res.status(500).json({ error: 'Internal scraping error' });
  }
});

// API endpoint compatible with FastAPI backend
app.post('/api/search', rateLimiterMiddleware, async (req, res) => {
  const { query, sites = ['amazon', 'walmart', 'ebay', 'target', 'bestbuy'] } = req.body;

  if (!query) {
    return res.status(400).json({
      error: 'Query parameter is required',
      timestamp: new Date().toISOString()
    });
  }

  try {
    const browser = await getBrowser();
    const results = [];

    // Filter to only supported sites
    const supportedSites = sites.filter(site => scrapers[site]);

    logger.info(`API search for: ${query} across ${supportedSites.length} retailers`);

    // Run scrapers with enhanced error handling
    const scrapingPromises = supportedSites.map(async (site) => {
      try {
        const siteResults = await scrapers[site].search(query, browser);
        return {
          site,
          products: siteResults,
          status: 'success',
          count: siteResults.length
        };
      } catch (error) {
        logger.error(`Error scraping ${site}: ${error.message}`);
        return {
          site,
          products: [],
          status: 'error',
          error: error.message,
          count: 0
        };
      }
    });

    const scrapingResults = await Promise.all(scrapingPromises);

    // Collect all products and metadata
    const metadata = {
      query,
      sites_searched: supportedSites,
      successful_sites: 0,
      failed_sites: 0,
      timestamp: new Date().toISOString(),
      total_retailers_available: Object.keys(scrapers).length
    };

    scrapingResults.forEach(result => {
      if (result.status === 'success' && result.products.length > 0) {
        results.push(...result.products);
        metadata.successful_sites++;
      } else {
        metadata.failed_sites++;
      }
    });

    res.json({
      query,
      results,
      metadata: {
        ...metadata,
        total_results: results.length
      }
    });

  } catch (error) {
    logger.error('API search failed:', error);
    res.status(500).json({
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Get supported retailers endpoint
app.get('/api/retailers', (req, res) => {
  const retailers = Object.keys(scrapers).map(key => ({
    key,
    name: key.charAt(0).toUpperCase() + key.slice(1),
    status: 'active'
  }));

  res.json({
    total_retailers: retailers.length,
    retailers,
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  logger.error('Unhandled error:', error);
  res.status(500).json({
    error: 'Internal server error',
    timestamp: new Date().toISOString()
  });
});

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down scraper service...');
  if (browserInstance) {
    await browserInstance.close();
  }
  process.exit(0);
});

app.listen(PORT, () => {
  logger.info(`🚀 Enhanced Cumpair Scraper running on port ${PORT}`);
  logger.info(`📊 Supporting ${Object.keys(scrapers).length} retailers: ${Object.keys(scrapers).join(', ')}`);
});

module.exports = app;
