/**
 * Compair Scraping Microservice
 * Node.js + Puppeteer-based e-commerce scraper with anti-bot measures
 */

const express = require('express');
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const AdblockerPlugin = require('puppeteer-extra-plugin-adblocker');
const UserAgent = require('user-agents');
const axios = require('axios');
const cheerio = require('cheerio');
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
  duration: 60, // per 60 seconds
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

// Site-specific scrapers
const scrapers = {
  amazon: {
    search: async (query, browser) => {
      const page = await browser.newPage();
      try {
        await page.setUserAgent(new UserAgent().toString());
        await page.goto(`https://www.amazon.com/s?k=${encodeURIComponent(query)}`, {
          waitUntil: 'networkidle0',
          timeout: 30000
        });

        const products = await page.evaluate(() => {
          const items = Array.from(document.querySelectorAll('[data-component-type="s-search-result"]'));
          return items.slice(0, 5).map(item => {
            const titleEl = item.querySelector('h2 a span');
            const priceEl = item.querySelector('.a-price .a-offscreen');
            const imageEl = item.querySelector('img');
            const linkEl = item.querySelector('h2 a');

            return {
              title: titleEl?.textContent?.trim() || '',
              price: priceEl?.textContent?.trim() || '',
              image: imageEl?.src || '',
              link: linkEl ? `https://www.amazon.com${linkEl.getAttribute('href')}` : '',
              site: 'amazon'
            };
          }).filter(item => item.title && item.price);
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
            const priceEl = container?.querySelector('[itemprop="price"]');
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

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.post('/scrape', rateLimiterMiddleware, async (req, res) => {
  const { query, sites = ['amazon', 'walmart', 'ebay'] } = req.body;

  if (!query) {
    return res.status(400).json({ error: 'Query parameter is required' });
  }

  try {
    const browser = await getBrowser();
    const results = [];

    // Run scrapers in parallel
    const scrapingPromises = sites.map(async (site) => {
      if (scrapers[site]) {
        try {
          const siteResults = await scrapers[site].search(query, browser);
          return siteResults;
        } catch (error) {
          logger.error(`Error scraping ${site}: ${error.message}`);
          return [];
        }
      }
      return [];
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

    logger.info(`Scraping completed for query: ${query}, found ${results.length} total products`);

    res.json({
      query,
      results,
      metadata: {
        total_results: results.length,
        sites_scraped: sites,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    logger.error(`Scraping error: ${error.message}`);
    res.status(500).json({ error: 'Internal scraping error' });
  }
});

app.post('/scrape-single', rateLimiterMiddleware, async (req, res) => {
  const { query, site } = req.body;

  if (!query || !site) {
    return res.status(400).json({ error: 'Query and site parameters are required' });
  }

  if (!scrapers[site]) {
    return res.status(400).json({ error: `Unsupported site: ${site}` });
  }

  try {
    const browser = await getBrowser();
    const results = await scrapers[site].search(query, browser);

    res.json({
      query,
      site,
      results,
      metadata: {
        total_results: results.length,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    logger.error(`Single site scraping error: ${error.message}`);
    res.status(500).json({ error: 'Internal scraping error' });
  }
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
  logger.info(`Scraper service running on port ${PORT}`);
});

module.exports = app;
