const WebScraper = require('./src/scraper/WebScraper');
const redisClient = require('./src/utils/redis');
const logger = require('./src/utils/logger');
require('dotenv').config();

// Example usage of the Web Scraper
async function demonstrateWebScraper() {
  const scraper = new WebScraper();

  try {
    logger.info('=== Web Scraper Demonstration ===');

    // Example 1: Simple scraping with Cheerio
    logger.info('\n1. Simple scraping with Cheerio');
    const simpleResult = await scraper.scrapeWithRetry('https://httpbin.org/html', {
      usePuppeteer: false,
      selectors: {
        title: 'title',
        headings: { selector: 'h1', multiple: true },
        firstParagraph: 'p:first-of-type'
      },
      cache: true
    });
    logger.info('Simple scraping result:', JSON.stringify(simpleResult, null, 2));

    // Example 2: Scraping with Puppeteer for dynamic content
    logger.info('\n2. Scraping with Puppeteer');
    const puppeteerResult = await scraper.scrapeWithRetry('https://httpbin.org/html', {
      usePuppeteer: true,
      selectors: {
        title: 'title',
        body: 'body'
      },
      waitUntil: 'networkidle0',
      cache: true
    });
    logger.info('Puppeteer scraping result keys:', Object.keys(puppeteerResult.data));

    // Example 3: Batch scraping
    logger.info('\n3. Batch scraping multiple URLs');
    const urls = [
      'https://httpbin.org/json',
      'https://httpbin.org/xml',
      'https://httpbin.org/html'
    ];

    const batchResult = await scraper.scrapeConcurrently(urls, {
      usePuppeteer: false,
      cache: true,
      selectors: {
        title: 'title',
        content: 'body'
      }
    });

    logger.info('Batch scraping summary:', batchResult.summary);

    // Example 4: Check cache
    logger.info('\n4. Checking cached results');
    const cachedResult = await scraper.getCachedResult('https://httpbin.org/html');
    if (cachedResult) {
      logger.info('Found cached result for httpbin.org/html');
    } else {
      logger.info('No cached result found');
    }

    // Example 5: Get scraper statistics
    logger.info('\n5. Scraper statistics');
    const stats = scraper.getStats();
    logger.info('Scraper stats:', stats);

  } catch (error) {
    logger.error('Demonstration failed:', error);
  } finally {
    // Cleanup
    await scraper.cleanup();
    await redisClient.disconnect();
  }
}

// Example usage of specific scraping scenarios
async function demonstrateAdvancedScraping() {
  const scraper = new WebScraper();

  try {
    logger.info('\n=== Advanced Scraping Examples ===');

    // E-commerce product scraping example
    const ecommerceSelectors = {
      title: 'h1.product-title, .product-name, [data-testid="product-title"]',
      price: '.price, .product-price, [data-testid="price"]',
      description: '.product-description, .description',
      images: {
        selector: '.product-images img, .gallery img',
        attribute: 'src',
        multiple: true
      },
      availability: '.availability, .stock-status',
      rating: '.rating, .stars, [data-testid="rating"]'
    };

    // News article scraping example
    const newsSelectors = {
      headline: 'h1, .headline, .article-title',
      author: '.author, .byline, [data-testid="author"]',
      publishDate: '.publish-date, .date, time[datetime]',
      content: '.article-content, .story-body, .content',
      tags: {
        selector: '.tags a, .categories a',
        multiple: true
      }
    };

    // Social media post scraping example (be mindful of terms of service)
    const socialSelectors = {
      username: '.username, .handle, [data-testid="username"]',
      content: '.post-content, .tweet-text, .post-body',
      timestamp: '.timestamp, .date, time',
      likes: '.likes-count, .favorite-count',
      shares: '.shares-count, .retweet-count'
    };

    logger.info('Advanced selectors configured for different content types');
    logger.info('E-commerce selectors:', Object.keys(ecommerceSelectors));
    logger.info('News selectors:', Object.keys(newsSelectors));
    logger.info('Social media selectors:', Object.keys(socialSelectors));

  } catch (error) {
    logger.error('Advanced demonstration failed:', error);
  } finally {
    await scraper.cleanup();
  }
}

// Run demonstrations if this file is executed directly
if (require.main === module) {
  (async () => {
    await demonstrateWebScraper();
    await demonstrateAdvancedScraping();
  })();
}

module.exports = {
  WebScraper,
  demonstrateWebScraper,
  demonstrateAdvancedScraping
};
