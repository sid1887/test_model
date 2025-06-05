# Comprehensive Web Scraper

A robust, production-ready web scraping system built with Node.js that provides comprehensive scraping capabilities with rate limiting, caching, concurrent processing, and a RESTful API.

## Features

- 🚀 **Multiple Scraping Methods**: Puppeteer for dynamic content and Cheerio for static HTML
- 🔄 **Concurrent Scraping**: Process multiple URLs simultaneously with configurable concurrency limits
- ⚡ **Redis Caching**: Intelligent caching system to avoid redundant requests
- 🛡️ **Rate Limiting**: Built-in rate limiting to respect website policies
- 🔄 **Retry Mechanisms**: Automatic retry with exponential backoff for failed requests
- 📊 **Monitoring & Stats**: Comprehensive statistics and health monitoring
- 🌐 **RESTful API**: Easy-to-use HTTP API for scraping operations
- 🔧 **Error Handling**: Robust error handling and logging
- 🧪 **Testing**: Comprehensive test suite with Jest
- 📝 **Logging**: Detailed logging with Winston

## Installation

1. Clone or download the project
2. Install dependencies:
```bash
npm install
```

3. Set up Redis (optional, falls back to memory if not available)
4. Configure environment variables by copying `.env` file and adjusting values

## Quick Start

### Start the API Server
```bash
npm start
```

### Development Mode (with auto-restart)
```bash
npm run dev
```

### Run Example Usage
```bash
npm run example
```

## API Endpoints

### Health Check
```http
GET /health
```
Returns server health status, Redis connection, and scraper statistics.

### Single URL Scraping
```http
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
```

### Batch Scraping
```http
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
```

### Get Statistics
```http
GET /api/stats
```

### Cache Management
```http
GET /api/cache/:key
DELETE /api/cache?pattern=scraper:*
```

## Configuration

Environment variables (`.env` file):

```env
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
```

## Usage Examples

### Basic Web Scraping

```javascript
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
```

### E-commerce Product Scraping

```javascript
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
```

### Concurrent Scraping

```javascript
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
```

## Selector Configuration

The scraper supports flexible selector configurations:

```javascript
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
```

## Error Handling

The scraper includes comprehensive error handling:

- **Network Errors**: Automatic retries with exponential backoff
- **Rate Limiting**: Built-in rate limiting to prevent being blocked
- **Invalid URLs**: Validation and proper error responses
- **Timeouts**: Configurable timeouts for requests
- **Parsing Errors**: Graceful handling of malformed HTML

## Monitoring and Statistics

Access comprehensive statistics through the API:

```javascript
const stats = scraper.getStats();
console.log({
  totalRequests: stats.totalRequests,
  successRate: stats.successRate,
  averageResponseTime: stats.averageResponseTime,
  uptime: stats.uptime
});
```

## Testing

Run the test suite:

```bash
# Run all tests
npm test

# Watch mode for development
npm run test:watch

# Generate coverage report
npm run test:coverage
```

## API Client Examples

### Python Client Example

```python
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
```

### JavaScript/Node.js Client Example

```javascript
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
```

### cURL Examples

```bash
# Single URL scraping
curl -X POST http://localhost:3000/api/scrape \
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
curl -X POST http://localhost:3000/api/scrape/batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example1.com", "https://example2.com"],
    "options": {
      "selectors": {
        "title": "title"
      }
    }
  }'
```

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
```env
LOG_LEVEL=debug
```

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
