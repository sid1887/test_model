# Cumpair Scraper Service - Node.js/Playwright

🕷️ **Cumpair Scraper Service** is a robust, production-ready web scraping system built with Node.js and Playwright that provides comprehensive e-commerce data extraction capabilities.

## 🚀 Features

### 🌐 Multi-Platform Support

- **Amazon** - Product details, prices, ratings, reviews

- **eBay** - Auction and Buy-It-Now listings

- **Walmart** - Product information and pricing

- **Best Buy** - Electronics and tech products

- **Target** - General merchandise

- **15+ Retailers** - Easily extensible architecture

### 🔧 Advanced Scraping Capabilities

- **Playwright Browser Automation** - Handle dynamic content and JavaScript

- **Cheerio HTML Parsing** - Fast static content extraction

- **Anti-Detection Features** - User-agent rotation, proxy support

- **CAPTCHA Handling** - Integration with captcha-service

- **Rate Limiting** - Respect website policies and avoid blocks

### ⚡ Performance & Reliability

- **Concurrent Processing** - Multiple URLs simultaneously

- **Redis Caching** - Intelligent caching to avoid redundant requests

- **Retry Mechanisms** - Automatic retry with exponential backoff

- **Error Recovery** - Robust error handling and logging

- **Health Monitoring** - Comprehensive statistics and metrics

## 🏗️ Architecture

### Port Configuration

- **Development**: Port 3001 (standardized)

- **Docker**: Port 3001 (container and host)

- **API Base**: `http://localhost:3001`

### Integration Points

- **FastAPI Backend**: Receives scraping requests on port 8000

- **Redis Cache**: Shared caching layer on port 6379

- **Captcha Service**: CAPTCHA solving on dedicated service

- **Proxy Service**: Proxy rotation management

## 🚀 Quick Start

### Prerequisites

- Node.js 18+

- Redis (optional, falls back to memory)

- Docker (for containerized deployment)

### Installation

```text
bash
# Install dependencies

npm install

# Install Playwright browsers

npx playwright install chromium

# Start the service

npm start

```text

### Environment Variables

Create a `.env` file:

```text
env
PORT=3001
REDIS_URL=redis://localhost:6379
CAPTCHA_SERVICE_URL=http://localhost:8081
LOG_LEVEL=info
CONCURRENT_LIMIT=5
REQUEST_TIMEOUT=30000

```text

## API Endpoints

### Health Check

```text
http
GET /health

```text

Returns server health status, Redis connection, and scraper statistics.

### Single URL Scraping

```text
http
POST /api/scrape
Content-Type: application/json

{
  "url": "https://example.com",
  "options": {
    "usePuppeteer": false,
    "cache": true,
    "selectors": {
      "title": "title",
      "headings": { "selector": "h1", "multiple": true },
      "links": { "selector": "a", "attribute": "href", "multiple": true }
    }
  }
}

```text

### Batch Scraping

```text
http
POST /api/scrape/batch
Content-Type: application/json

{
  "urls": [
    "https://example1.com",
    "https://example2.com"
  ],
  "options": {
    "usePuppeteer": false,
    "cache": true,
    "selectors": {
      "title": "title",
      "content": "body"
    }
  }
}

```text

### Get Statistics

```text
http
GET /api/stats

```text

### Cache Management

```text
http
GET /api/cache/:key
DELETE /api/cache?pattern=scraper:*

```text

## Configuration

Environment variables (`.env` file):

```text
env
# Server Configuration

NODE_ENV=development
PORT=3000

# Redis Configuration

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Rate Limiting

RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100

# Scraping Configuration

MAX_CONCURRENT_SCRAPERS=5
DEFAULT_TIMEOUT=30000
RETRY_ATTEMPTS=3
RETRY_DELAY=1000

# Puppeteer Configuration

HEADLESS=true
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36

# Logging

LOG_LEVEL=info
LOG_FILE=logs/scraper.log

```text

## Usage Examples

### Basic Web Scraping

```text
javascript
const WebScraper = require('./src/scraper/WebScraper');

const scraper = new WebScraper();

// Simple scraping
const result = await scraper.scrapeWithRetry('https://example.com', {
  selectors: {
    title: 'title',
    description: 'meta[name="description"]'
  }
});

console.log(result.data);

```text

### E-commerce Product Scraping

```text
javascript
const productSelectors = {
  title: 'h1.product-title, .product-name',
  price: '.price, .product-price',
  description: '.product-description',
  images: {
    selector: '.product-images img',
    attribute: 'src',
    multiple: true
  },
  availability: '.availability, .stock-status'
};

const result = await scraper.scrapeWithRetry(productUrl, {
  selectors: productSelectors,
  usePuppeteer: true, // For dynamic content
  cache: true
});

```text

### Concurrent Scraping

```text
javascript
const urls = [
  'https://site1.com',
  'https://site2.com',
  'https://site3.com'
];

const results = await scraper.scrapeConcurrently(urls, {
  selectors: {
    title: 'title',
    content: 'body'
  }
});

console.log(`Scraped ${results.summary.successful} out of ${results.summary.total} URLs`);

```text

## Selector Configuration

The scraper supports flexible selector configurations:

```text
javascript
{
  // Simple text extraction
  "title": "h1",

  // Multiple elements
  "headings": {
    "selector": "h1, h2, h3",
    "multiple": true
  },

  // Attribute extraction
  "links": {
    "selector": "a",
    "attribute": "href",
    "multiple": true
  },

  // Complex selectors
  "metadata": {
    "selector": "meta[property^='og:']",
    "attribute": "content",
    "multiple": true
  }
}

```text

## Error Handling

The scraper includes comprehensive error handling:

- **Network Errors**: Automatic retries with exponential backoff

- **Rate Limiting**: Built-in rate limiting to prevent being blocked

- **Invalid URLs**: Validation and proper error responses

- **Timeouts**: Configurable timeouts for requests

- **Parsing Errors**: Graceful handling of malformed HTML

## Monitoring and Statistics

Access comprehensive statistics through the API:

```text
javascript
const stats = scraper.getStats();
console.log({
  totalRequests: stats.totalRequests,
  successRate: stats.successRate,
  averageResponseTime: stats.averageResponseTime,
  uptime: stats.uptime
});

```text

## Testing

Run the test suite:

```text
bash
# Run all tests

npm test

# Watch mode for development

npm run test:watch

# Generate coverage report

npm run test:coverage

```text

## API Client Examples

### Python Client Example

```text
python
import requests

# Single URL scraping

response = requests.post('http://localhost:3000/api/scrape', json={
    'url': 'https://example.com',
    'options': {
        'selectors': {
            'title': 'title',
            'headings': {'selector': 'h1', 'multiple': True}
        }
    }
})

data = response.json()
print(data['data'])

```text

### JavaScript/Node.js Client Example

```text
javascript
const axios = require('axios');

const scrapeUrl = async (url) => {
  try {
    const response = await axios.post('http://localhost:3000/api/scrape', {
      url: url,
      options: {
        selectors: {
          title: 'title',
          content: 'p'
        }
      }
    });

    return response.data;
  } catch (error) {
    console.error('Scraping failed:', error.response?.data || error.message);
  }
};

```text

### cURL Examples

```text
bash
# Single URL scraping

curl -X POST http://localhost:3001/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "options": {
      "selectors": {
        "title": "title"
      }
    }
  }'

# Batch scraping

curl -X POST http://localhost:3001/api/scrape/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example1.com", "https://example2.com"],
    "options": {
      "selectors": {
        "title": "title"
      }
    }
  }'

```text

## Best Practices

1. **Respect robots.txt**: Always check and respect website robots.txt files

2. **Rate Limiting**: Use appropriate delays between requests

3. **User Agents**: Use realistic user agent strings

4. **Caching**: Enable caching to avoid redundant requests

5. **Error Handling**: Implement proper error handling in your applications

6. **Monitoring**: Monitor scraper performance and success rates

7. **Legal Compliance**: Ensure compliance with website terms of service and applicable laws

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**: Ensure Redis is running or disable caching

2. **Puppeteer Installation Issues**: Install additional dependencies for your OS

3. **Rate Limiting**: Adjust rate limiting settings if getting blocked

4. **Memory Issues**: Monitor memory usage for large-scale scraping

### Debugging

Enable debug logging:

```text
env
LOG_LEVEL=debug

```text

Check logs in the `logs/` directory for detailed information.

## Contributing

1. Fork the repository

2. Create a feature branch

3. Make changes with tests

4. Run the test suite

5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool is for educational and legitimate use cases only. Always respect website terms of service, robots.txt files, and applicable laws. The developers are not responsible for misuse of this software.
