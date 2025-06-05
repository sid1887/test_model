const WebScraper = require('../src/scraper/WebScraper');
const redisClient = require('../src/utils/redis');

describe('WebScraper', () => {
  let scraper;

  beforeAll(async () => {
    await redisClient.connect();
  });

  afterAll(async () => {
    await redisClient.disconnect();
  });

  beforeEach(() => {
    scraper = new WebScraper({
      maxConcurrent: 2,
      timeout: 10000,
      retryAttempts: 2
    });
  });

  afterEach(async () => {
    if (scraper) {
      await scraper.cleanup();
    }
  });

  describe('Constructor', () => {
    it('should initialize with default options', () => {
      const defaultScraper = new WebScraper();
      const stats = defaultScraper.getStats();
      
      expect(stats).toHaveProperty('totalRequests', 0);
      expect(stats).toHaveProperty('successfulRequests', 0);
      expect(stats).toHaveProperty('failedRequests', 0);
    });

    it('should initialize with custom options', () => {
      const customScraper = new WebScraper({
        maxConcurrent: 10,
        timeout: 5000
      });
      
      expect(customScraper.maxConcurrent).toBe(10);
      expect(customScraper.timeout).toBe(5000);
    });
  });

  describe('scrapeWithCheerio', () => {
    it('should scrape a simple HTML page', async () => {
      const result = await scraper.scrapeWithCheerio('https://httpbin.org/html');
      
      expect(result).toHaveProperty('success', true);
      expect(result).toHaveProperty('url', 'https://httpbin.org/html');
      expect(result).toHaveProperty('data');
      expect(result.data).toHaveProperty('title');
      expect(result.data).toHaveProperty('content');
    }, 15000);

    it('should extract data using selectors', async () => {
      const result = await scraper.scrapeWithCheerio('https://httpbin.org/html', {
        selectors: {
          title: 'title',
          heading: 'h1'
        }
      });
      
      expect(result.data).toHaveProperty('title');
      expect(result.data).toHaveProperty('heading');
      expect(typeof result.data.title).toBe('string');
    }, 15000);

    it('should handle multiple elements', async () => {
      const result = await scraper.scrapeWithCheerio('https://httpbin.org/html', {
        selectors: {
          paragraphs: { 
            selector: 'p', 
            multiple: true 
          }
        }
      });
      
      expect(Array.isArray(result.data.paragraphs)).toBe(true);
    }, 15000);

    it('should handle attributes', async () => {
      const result = await scraper.scrapeWithCheerio('https://httpbin.org/html', {
        selectors: {
          links: { 
            selector: 'a', 
            attribute: 'href',
            multiple: true 
          }
        }
      });
      
      expect(Array.isArray(result.data.links)).toBe(true);
    }, 15000);
  });

  describe('scrapeWithPuppeteer', () => {
    it('should scrape a page with Puppeteer', async () => {
      const result = await scraper.scrapeWithPuppeteer('https://httpbin.org/html', {
        selectors: {
          title: 'title'
        }
      });
      
      expect(result).toHaveProperty('success', true);
      expect(result).toHaveProperty('url', 'https://httpbin.org/html');
      expect(result.data).toHaveProperty('title');
    }, 30000);

    it('should wait for specific selector', async () => {
      const result = await scraper.scrapeWithPuppeteer('https://httpbin.org/html', {
        waitForSelector: 'body',
        selectors: {
          title: 'title'
        }
      });
      
      expect(result).toHaveProperty('success', true);
      expect(result.data).toHaveProperty('title');
    }, 30000);
  });

  describe('scrapeWithRetry', () => {
    it('should succeed on first attempt', async () => {
      const result = await scraper.scrapeWithRetry('https://httpbin.org/html', {
        usePuppeteer: false,
        selectors: {
          title: 'title'
        }
      });
      
      expect(result).toHaveProperty('success', true);
      expect(result.data).toHaveProperty('title');
    }, 20000);

    it('should fail after max retries for invalid URL', async () => {
      await expect(
        scraper.scrapeWithRetry('https://definitely-not-a-real-url-12345.com')
      ).rejects.toThrow(/Failed to scrape.*after.*attempts/);
    }, 15000);
  });

  describe('scrapeConcurrently', () => {
    it('should scrape multiple URLs concurrently', async () => {
      const urls = [
        'https://httpbin.org/html',
        'https://httpbin.org/json'
      ];
      
      const result = await scraper.scrapeConcurrently(urls, {
        usePuppeteer: false,
        selectors: {
          title: 'title'
        }
      });
      
      expect(result).toHaveProperty('results');
      expect(result).toHaveProperty('summary');
      expect(result.summary.total).toBe(2);
      expect(Array.isArray(result.results)).toBe(true);
    }, 30000);

    it('should handle mixed success and failure', async () => {
      const urls = [
        'https://httpbin.org/html',
        'https://definitely-not-a-real-url-12345.com'
      ];
      
      const result = await scraper.scrapeConcurrently(urls, {
        usePuppeteer: false
      });
      
      expect(result.summary.total).toBe(2);
      expect(result.summary.successful).toBeGreaterThan(0);
      expect(result.summary.failed).toBeGreaterThan(0);
      expect(result.errors.length).toBeGreaterThan(0);
    }, 30000);
  });

  describe('Caching', () => {
    beforeEach(async () => {
      // Clear cache before each test
      await redisClient.flushAll();
    });

    it('should cache scraped results', async () => {
      const url = 'https://httpbin.org/html';
      
      // First scrape - should cache
      await scraper.scrapeWithRetry(url, {
        cache: true,
        usePuppeteer: false
      });
      
      // Check if result is cached
      const cachedResult = await scraper.getCachedResult(url);
      expect(cachedResult).not.toBeNull();
      expect(cachedResult).toHaveProperty('success', true);
    }, 20000);

    it('should retrieve cached results', async () => {
      const url = 'https://httpbin.org/html';
      const testData = { test: 'cached data' };
      
      // Manually set cache
      const cacheKey = `scraper:${Buffer.from(url).toString('base64')}`;
      await redisClient.set(cacheKey, testData);
      
      // Retrieve cached result
      const cachedResult = await scraper.getCachedResult(url);
      expect(cachedResult).toEqual(testData);
    });
  });

  describe('Statistics', () => {
    it('should track statistics correctly', async () => {
      const initialStats = scraper.getStats();
      expect(initialStats.totalRequests).toBe(0);
      
      // Perform a successful scrape
      await scraper.scrapeWithRetry('https://httpbin.org/html', {
        usePuppeteer: false
      });
      
      const finalStats = scraper.getStats();
      expect(finalStats.totalRequests).toBe(1);
      expect(finalStats.successfulRequests).toBe(1);
      expect(finalStats.failedRequests).toBe(0);
      expect(finalStats.successRate).toBe('100.00%');
    }, 20000);

    it('should track failed requests', async () => {
      try {
        await scraper.scrapeWithRetry('https://definitely-not-a-real-url-12345.com');
      } catch (error) {
        // Expected to fail
      }
      
      const stats = scraper.getStats();
      expect(stats.failedRequests).toBeGreaterThan(0);
    }, 15000);
  });

  describe('Rate Limiting', () => {
    it('should apply rate limiting', async () => {
      const startTime = Date.now();
      
      // Make two requests to the same domain
      const promises = [
        scraper.scrapeWithCheerio('https://httpbin.org/html'),
        scraper.scrapeWithCheerio('https://httpbin.org/json')
      ];
      
      await Promise.all(promises);
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      
      // Should take at least 1 second due to rate limiting
      expect(duration).toBeGreaterThan(1000);
    }, 25000);
  });

  describe('Error Handling', () => {
    it('should handle invalid URLs gracefully', async () => {
      await expect(
        scraper.scrapeWithCheerio('not-a-url')
      ).rejects.toThrow();
    });

    it('should handle network timeouts', async () => {
      const timeoutScraper = new WebScraper({ timeout: 1 }); // 1ms timeout
      
      await expect(
        timeoutScraper.scrapeWithCheerio('https://httpbin.org/delay/5')
      ).rejects.toThrow();
      
      await timeoutScraper.cleanup();
    }, 10000);
  });
});
