const request = require('supertest');
const ScraperAPI = require('../src/api/server');
const redisClient = require('../src/utils/redis');

describe('Scraper API', () => {
  let app;
  let server;

  beforeAll(async () => {
    // Create API instance for testing
    const api = new ScraperAPI();
    app = api.app;

    // Connect to Redis for testing
    await redisClient.connect();

    // Start server on test port
    server = app.listen(0); // Use random available port
  });

  afterAll(async () => {
    if (server) {
      server.close();
    }
    await redisClient.disconnect();
  });

  beforeEach(async () => {
    // Clear test data before each test
    await redisClient.flushAll();
  });

  describe('GET /health', () => {
    it('should return health status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('uptime');
      expect(response.body).toHaveProperty('redis');
      expect(response.body).toHaveProperty('scraper');
    });
  });

  describe('GET /', () => {
    it('should return API information', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.body).toHaveProperty('message', 'Web Scraper API');
      expect(response.body).toHaveProperty('endpoints');
      expect(response.body.endpoints).toHaveProperty('POST /api/scrape');
    });
  });

  describe('POST /api/scrape', () => {
    it('should scrape a valid URL', async () => {
      const testUrl = 'https://httpbin.org/html';

      const response = await request(app)
        .post('/api/scrape')
        .send({
          url: testUrl,
          options: {
            usePuppeteer: false,
            selectors: {
              title: 'title'
            }
          }
        })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('url', testUrl);
      expect(response.body).toHaveProperty('data');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body.data).toHaveProperty('title');
    }, 30000); // 30 second timeout for scraping

    it('should return error for missing URL', async () => {
      const response = await request(app)
        .post('/api/scrape')
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('error', 'URL is required');
    });

    it('should return error for invalid URL', async () => {
      const response = await request(app)
        .post('/api/scrape')
        .send({ url: 'not-a-valid-url' })
        .expect(400);

      expect(response.body).toHaveProperty('error', 'Invalid URL format');
    });

    it('should use cached result when available', async () => {
      const testUrl = 'https://httpbin.org/html';

      // First request - should scrape and cache
      const firstResponse = await request(app)
        .post('/api/scrape')
        .send({
          url: testUrl,
          options: { cache: true }
        })
        .expect(200);

      expect(firstResponse.body).toHaveProperty('success', true);
      expect(firstResponse.body).not.toHaveProperty('cached');

      // Second request - should return cached result
      const secondResponse = await request(app)
        .post('/api/scrape')
        .send({
          url: testUrl,
          options: { cache: true }
        })
        .expect(200);

      expect(secondResponse.body).toHaveProperty('cached', true);
    }, 45000);
  });

  describe('POST /api/scrape/batch', () => {
    it('should scrape multiple URLs', async () => {
      const urls = [
        'https://httpbin.org/html',
        'https://httpbin.org/json'
      ];

      const response = await request(app)
        .post('/api/scrape/batch')
        .send({
          urls,
          options: {
            usePuppeteer: false,
            selectors: {
              title: 'title'
            }
          }
        })
        .expect(200);

      expect(response.body).toHaveProperty('results');
      expect(response.body).toHaveProperty('summary');
      expect(response.body.summary).toHaveProperty('total', 2);
      expect(Array.isArray(response.body.results)).toBe(true);
    }, 60000);

    it('should return error for missing URLs', async () => {
      const response = await request(app)
        .post('/api/scrape/batch')
        .send({})
        .expect(400);

      expect(response.body).toHaveProperty('error', 'URLs array is required');
    });

    it('should return error for too many URLs', async () => {
      const urls = new Array(51).fill('https://httpbin.org/html');

      const response = await request(app)
        .post('/api/scrape/batch')
        .send({ urls })
        .expect(400);

      expect(response.body).toHaveProperty('error', 'Maximum 50 URLs allowed per batch');
    });
  });

  describe('GET /api/stats', () => {
    it('should return scraper statistics', async () => {
      const response = await request(app)
        .get('/api/stats')
        .expect(200);

      expect(response.body).toHaveProperty('totalRequests');
      expect(response.body).toHaveProperty('successfulRequests');
      expect(response.body).toHaveProperty('failedRequests');
      expect(response.body).toHaveProperty('successRate');
      expect(response.body).toHaveProperty('uptime');
    });
  });

  describe('Cache endpoints', () => {
    it('should return 404 for non-existent cache key', async () => {
      const response = await request(app)
        .get('/api/cache/nonexistent')
        .expect(404);

      expect(response.body).toHaveProperty('error', 'Data not found in cache');
    });

    it('should clear cache', async () => {
      // Add some test data to cache
      await redisClient.set('scraper:test', { test: 'data' });

      const response = await request(app)
        .delete('/api/cache')
        .expect(200);

      expect(response.body).toHaveProperty('message');
      expect(response.body.message).toMatch(/Cleared \d+ cache entries/);
    });
  });

  describe('Error handling', () => {
    it('should return 404 for non-existent endpoints', async () => {
      const response = await request(app)
        .get('/non-existent-endpoint')
        .expect(404);

      expect(response.body).toHaveProperty('error', 'Endpoint not found');
    });
  });
});
