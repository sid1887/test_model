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

    // Service URLs
    this.proxyServiceUrl = process.env.PROXY_SERVICE_URL || 'http://proxy-api:8001';
    this.haproxyUrl = process.env.HAPROXY_URL || 'http://cumpair-proxy-manager:8080';
    this.captchaServiceUrl = process.env.CAPTCHA_SERVICE_URL || 'http://captcha-solver:9001';

    // Proxy rotation settings
    this.useProxyRotation = process.env.USE_PROXY_ROTATION !== 'false';
    this.currentProxy = null;
    this.proxyPool = [];
    this.proxyRotationInterval = 5; // Rotate proxy every 5 requests
    this.requestsSinceProxyRotation = 0;

    // Rate limiter - 5 requests per second per domain (increased from 1 for performance)
    this.rateLimiter = new RateLimiterMemory({
      points: 5,
      duration: 1000
    });

    this.activeBrowsers = new Set();
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      startTime: Date.now(),
      proxiesUsed: 0,
      captchasSolved: 0
    };

    // Initialize proxy pool
    this.initializeProxyPool().catch(err =>
      logger.warn('Proxy pool initialization failed, continuing without proxies:', err.message)
    );
  }

  async initializeProxyPool() {
    try {
      // Try to get proxies from proxy service
      const response = await axios.get(`${this.proxyServiceUrl}/api/v1/proxies/list`, {
        timeout: 3000
      });

      if (response.data && response.data.proxies) {
        this.proxyPool = response.data.proxies.slice(0, 10); // Use top 10 proxies
        logger.info(`Initialized proxy pool with ${this.proxyPool.length} proxies`);
      }
    } catch (error) {
      logger.warn(`Could not initialize proxy pool: ${error.message}`);
    }
  }

  async getNextProxy() {
    // Rotate to next proxy if needed
    if (this.proxyPool.length === 0) {
      return null;
    }

    this.requestsSinceProxyRotation++;

    if (this.requestsSinceProxyRotation >= this.proxyRotationInterval || !this.currentProxy) {
      const randomIndex = Math.floor(Math.random() * this.proxyPool.length);
      this.currentProxy = this.proxyPool[randomIndex];
      this.requestsSinceProxyRotation = 0;
      this.stats.proxiesUsed++;
      logger.info(`Rotated to proxy: ${this.currentProxy.host}:${this.currentProxy.port}`);
    }

    return this.currentProxy;
  }

  async solveCaptcha(imageData, type = 'image') {
    try {
      logger.info('Attempting to solve CAPTCHA...');

      const response = await axios.post(`${this.captchaServiceUrl}/api/v1/solve`, {
        image: imageData,
        type
      }, {
        timeout: 30000 // 30 second timeout for captcha solving
      });

      if (response.data && response.data.solution) {
        this.stats.captchasSolved++;
        logger.info('CAPTCHA solved successfully');
        return response.data.solution;
      }

      throw new Error('No solution in captcha response');
    } catch (error) {
      logger.error(`CAPTCHA solving failed: ${error.message}`);
      return null;
    }
  }

  async createBrowser(useProxy = false) {
    try {
      const launchOptions = {
        headless: 'new', // Use new headless mode to avoid deprecation warning
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu',
          '--disable-blink-features=AutomationControlled'
        ],
        defaultViewport: {
          width: 1366,
          height: 768
        }
      };

      // Add proxy configuration if requested and available
      if (useProxy && this.useProxyRotation) {
        const proxy = await this.getNextProxy();
        if (proxy) {
          launchOptions.args.push(`--proxy-server=${proxy.host}:${proxy.port}`);
          logger.info(`Browser launching with proxy: ${proxy.host}:${proxy.port}`);
        }
      }

      const browser = await puppeteer.launch(launchOptions);

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

      // Use proxy for e-commerce sites to avoid blocking
      const useProxy = options.useProxy !== false && this.useProxyRotation;
      browser = await this.createBrowser(useProxy);
      page = await browser.newPage();

      // Set user agent with rotation
      const userAgents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      ];
      const randomUA = userAgents[Math.floor(Math.random() * userAgents.length)];
      await page.setUserAgent(randomUA);

      // Set extra headers if provided
      if (options.headers) {
        await page.setExtraHTTPHeaders(options.headers);
      }

      // Navigate to the page
      await page.goto(url, {
        waitUntil: options.waitUntil || 'domcontentloaded',
        timeout: this.timeout
      });

      // Check for CAPTCHA and solve if detected
      const hasCaptcha = await page.evaluate(() => {
        const captchaIndicators = [
          'g-recaptcha',
          'h-captcha',
          'captcha-container',
          'recaptcha',
          'hcaptcha'
        ];
        return captchaIndicators.some(indicator =>
          document.querySelector(`[class*="${indicator}"]`) ||
          document.querySelector(`[id*="${indicator}"]`)
        );
      });

      if (hasCaptcha) {
        logger.warn('CAPTCHA detected on page, attempting to solve...');
        try {
          // Take screenshot of captcha
          const captchaScreenshot = await page.screenshot({ encoding: 'base64' });

          // Attempt to solve
          const solution = await this.solveCaptcha(captchaScreenshot, 'image');

          if (solution) {
            // Try to input solution (this is simplified, real implementation would be more complex)
            await page.evaluate((sol) => {
              const input = document.querySelector('input[name="captcha"]') ||
                           document.querySelector('input[type="text"]');
              if (input) input.value = sol;
            }, solution);

            logger.info('CAPTCHA solution applied');
          } else {
            logger.warn('CAPTCHA solving failed, continuing anyway...');
          }
        } catch (captchaError) {
          logger.error('Error handling CAPTCHA:', captchaError);
        }
      }

      // Wait for specific selector if provided
      if (options.waitForSelector) {
        await page.waitForSelector(options.waitForSelector, { timeout: this.timeout });
      }

      // If selectors are provided, wait for the products selector
      if (options.selectors && options.selectors.products) {
        try {
          await page.waitForSelector(options.selectors.products, { timeout: 10000 });
          logger.info(`Products selector found: ${options.selectors.products}`);

          // Scroll to load lazy images
          await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight / 2);
          });
          await new Promise(resolve => setTimeout(resolve, 1000));

        } catch (waitError) {
          logger.warn(`Products selector not found within 10s: ${options.selectors.products}`);
        }
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
        // ALWAYS include HTML for downstream processing
        data.html = content;

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
        `${((this.stats.successfulRequests / this.stats.totalRequests) * 100).toFixed(2)}%` : '0%',
      requestsPerMinute: this.stats.totalRequests > 0 ?
        Math.round((this.stats.totalRequests / uptime) * 60000) : 0,
      activeBrowsers: this.activeBrowsers.size,
      proxyPoolSize: this.proxyPool.length,
      proxiesRotated: this.stats.proxiesUsed,
      captchasSolved: this.stats.captchasSolved,
      services: {
        proxyService: this.proxyServiceUrl,
        captchaService: this.captchaServiceUrl,
        haproxy: this.haproxyUrl,
        proxyRotationEnabled: this.useProxyRotation
      }
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
