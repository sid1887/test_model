const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const cheerio = require('cheerio');
const axios = require('axios');
const { RateLimiterMemory } = require('rate-limiter-flexible');
const logger = require('../utils/logger');
const redisClient = require('../utils/redis');

// Use stealth plugin to avoid detection
puppeteer.use(StealthPlugin());

class WebScraper {
  constructor(options = {}) {
    this.maxConcurrent = options.maxConcurrent || parseInt(process.env.MAX_CONCURRENT_SCRAPERS) || 5;
    this.timeout = options.timeout || parseInt(process.env.DEFAULT_TIMEOUT) || 30000;
    this.retryAttempts = options.retryAttempts || parseInt(process.env.RETRY_ATTEMPTS) || 3;
    this.retryDelay = options.retryDelay || parseInt(process.env.RETRY_DELAY) || 1000;
    this.headless = options.headless !== undefined ? options.headless : process.env.HEADLESS !== 'false';
    
    // Rate limiter - 1 request per second per domain
    this.rateLimiter = new RateLimiterMemory({
      points: 1,
      duration: 1000,
    });

    this.activeBrowsers = new Set();
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      startTime: Date.now()
    };
  }

  async createBrowser() {
    try {
      const browser = await puppeteer.launch({
        headless: this.headless,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu'
        ],
        defaultViewport: {
          width: 1366,
          height: 768
        }
      });

      this.activeBrowsers.add(browser);
      
      browser.on('disconnected', () => {
        this.activeBrowsers.delete(browser);
      });

      return browser;
    } catch (error) {
      logger.error('Failed to create browser:', error);
      throw error;
    }
  }

  async scrapeWithPuppeteer(url, options = {}) {
    let browser;
    let page;
    const startTime = Date.now();

    try {
      // Apply rate limiting
      await this.rateLimiter.consume(new URL(url).hostname);

      browser = await this.createBrowser();
      page = await browser.newPage();

      // Set user agent
      await page.setUserAgent(process.env.USER_AGENT || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

      // Set extra headers if provided
      if (options.headers) {
        await page.setExtraHTTPHeaders(options.headers);
      }

      // Navigate to the page
      await page.goto(url, {
        waitUntil: options.waitUntil || 'networkidle0',
        timeout: this.timeout
      });

      // Wait for specific selector if provided
      if (options.waitForSelector) {
        await page.waitForSelector(options.waitForSelector, { timeout: this.timeout });
      }

      // Execute custom JavaScript if provided
      if (options.evaluate) {
        await page.evaluate(options.evaluate);
      }

      // Get page content
      const content = await page.content();
      const $ = cheerio.load(content);

      // Extract data based on selectors
      let data = {};
      if (options.selectors) {
        for (const [key, selector] of Object.entries(options.selectors)) {
          if (typeof selector === 'string') {
            data[key] = $(selector).text().trim();
          } else if (selector.multiple) {
            data[key] = [];
            $(selector.selector).each((i, elem) => {
              data[key].push($(elem).text().trim());
            });
          } else if (selector.attribute) {
            data[key] = $(selector.selector).attr(selector.attribute);
          } else {
            data[key] = $(selector.selector).text().trim();
          }
        }
      } else {
        // Return full page content if no selectors specified
        data = {
          title: $('title').text(),
          content: $('body').text().trim(),
          html: content
        };
      }

      // Take screenshot if requested
      if (options.screenshot) {
        data.screenshot = await page.screenshot({
          type: 'png',
          fullPage: options.screenshotFullPage || false
        });
      }

      const responseTime = Date.now() - startTime;
      this.updateStats(true, responseTime);

      logger.info(`Successfully scraped ${url} in ${responseTime}ms`);
      return {
        success: true,
        url,
        data,
        timestamp: new Date().toISOString(),
        responseTime
      };

    } catch (error) {
      const responseTime = Date.now() - startTime;
      this.updateStats(false, responseTime);
      
      logger.error(`Failed to scrape ${url}:`, error);
      throw error;
    } finally {
      if (page) await page.close();
      if (browser) await browser.close();
    }
  }

  async scrapeWithCheerio(url, options = {}) {
    const startTime = Date.now();

    try {
      // Apply rate limiting
      await this.rateLimiter.consume(new URL(url).hostname);

      const response = await axios.get(url, {
        timeout: this.timeout,
        headers: {
          'User-Agent': process.env.USER_AGENT || 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          ...options.headers
        }
      });

      const $ = cheerio.load(response.data);
      let data = {};

      if (options.selectors) {
        for (const [key, selector] of Object.entries(options.selectors)) {
          if (typeof selector === 'string') {
            data[key] = $(selector).text().trim();
          } else if (selector.multiple) {
            data[key] = [];
            $(selector.selector).each((i, elem) => {
              data[key].push($(elem).text().trim());
            });
          } else if (selector.attribute) {
            data[key] = $(selector.selector).attr(selector.attribute);
          } else {
            data[key] = $(selector.selector).text().trim();
          }
        }
      } else {
        data = {
          title: $('title').text(),
          content: $('body').text().trim(),
          html: response.data
        };
      }

      const responseTime = Date.now() - startTime;
      this.updateStats(true, responseTime);

      logger.info(`Successfully scraped ${url} with Cheerio in ${responseTime}ms`);
      return {
        success: true,
        url,
        data,
        timestamp: new Date().toISOString(),
        responseTime
      };

    } catch (error) {
      const responseTime = Date.now() - startTime;
      this.updateStats(false, responseTime);
      
      logger.error(`Failed to scrape ${url} with Cheerio:`, error);
      throw error;
    }
  }

  async scrapeWithRetry(url, options = {}) {
    let lastError;
    
    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const method = options.usePuppeteer ? 'scrapeWithPuppeteer' : 'scrapeWithCheerio';
        const result = await this[method](url, options);
        
        // Cache the result in Redis
        if (options.cache) {
          const cacheKey = `scraper:${Buffer.from(url).toString('base64')}`;
          await redisClient.set(cacheKey, result, options.cacheTTL || 3600);
        }
        
        return result;
      } catch (error) {
        lastError = error;
        logger.warn(`Scraping attempt ${attempt} failed for ${url}: ${error.message}`);
        
        if (attempt < this.retryAttempts) {
          const delay = this.retryDelay * Math.pow(2, attempt - 1); // Exponential backoff
          logger.info(`Retrying in ${delay}ms...`);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    
    throw new Error(`Failed to scrape ${url} after ${this.retryAttempts} attempts. Last error: ${lastError.message}`);
  }

  async scrapeConcurrently(urls, options = {}) {
    const results = [];
    const errors = [];
    const semaphore = new Array(this.maxConcurrent).fill(null);
    
    const processUrl = async (url, index) => {
      try {
        const result = await this.scrapeWithRetry(url, options);
        results[index] = result;
      } catch (error) {
        errors[index] = { url, error: error.message };
        logger.error(`Failed to scrape ${url}:`, error);
      }
    };

    // Process URLs in batches
    for (let i = 0; i < urls.length; i += this.maxConcurrent) {
      const batch = urls.slice(i, i + this.maxConcurrent);
      const promises = batch.map((url, batchIndex) => 
        processUrl(url, i + batchIndex)
      );
      
      await Promise.all(promises);
      logger.info(`Completed batch ${Math.floor(i / this.maxConcurrent) + 1}`);
    }

    return {
      results: results.filter(r => r),
      errors: errors.filter(e => e),
      summary: {
        total: urls.length,
        successful: results.filter(r => r).length,
        failed: errors.filter(e => e).length
      }
    };
  }

  async getCachedResult(url) {
    try {
      const cacheKey = `scraper:${Buffer.from(url).toString('base64')}`;
      return await redisClient.get(cacheKey);
    } catch (error) {
      logger.error(`Failed to get cached result for ${url}:`, error);
      return null;
    }
  }

  updateStats(success, responseTime) {
    this.stats.totalRequests++;
    if (success) {
      this.stats.successfulRequests++;
    } else {
      this.stats.failedRequests++;
    }
    
    // Update average response time
    const totalTime = this.stats.averageResponseTime * (this.stats.totalRequests - 1) + responseTime;
    this.stats.averageResponseTime = Math.round(totalTime / this.stats.totalRequests);
  }

  getStats() {
    const uptime = Date.now() - this.stats.startTime;
    return {
      ...this.stats,
      uptime,
      successRate: this.stats.totalRequests > 0 ? 
        ((this.stats.successfulRequests / this.stats.totalRequests) * 100).toFixed(2) + '%' : '0%',
      requestsPerMinute: this.stats.totalRequests > 0 ? 
        Math.round((this.stats.totalRequests / uptime) * 60000) : 0,
      activeBrowsers: this.activeBrowsers.size
    };
  }

  async cleanup() {
    logger.info('Cleaning up web scraper...');
    
    // Close all active browsers
    const browserPromises = Array.from(this.activeBrowsers).map(browser => 
      browser.close().catch(error => logger.error('Error closing browser:', error))
    );
    
    await Promise.all(browserPromises);
    this.activeBrowsers.clear();
    
    logger.info('Web scraper cleanup completed');
  }
}

module.exports = WebScraper;
