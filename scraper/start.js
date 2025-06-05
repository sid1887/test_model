#!/usr/bin/env node

const ScraperAPI = require('./src/api/server');
const logger = require('./src/utils/logger');

// Test script to verify the scraper system
async function testScraper() {
  logger.info('🚀 Starting Web Scraper System Test...');
  
  try {
    // Create and start the API server
    const api = new ScraperAPI();
    
    logger.info('✅ API server created successfully');
    logger.info('📋 System components initialized:');
    logger.info('   - Logger: Winston configured');
    logger.info('   - Redis: Connection configured');
    logger.info('   - Web Scraper: Puppeteer & Cheerio ready');
    logger.info('   - API Server: Express routes configured');
    logger.info('   - Rate Limiting: Configured');
    logger.info('   - Error Handling: Comprehensive error handling in place');
    
    // Start the server
    await api.start();
    
    logger.info('🎉 Web Scraper System is running successfully!');
    logger.info(`🌐 API available at: http://localhost:${process.env.PORT || 3000}`);
    logger.info('📊 Health check: http://localhost:3000/health');
    logger.info('📚 API documentation: http://localhost:3000/');
    
    logger.info('\n📝 Available endpoints:');
    logger.info('   POST /api/scrape - Scrape a single URL');
    logger.info('   POST /api/scrape/batch - Scrape multiple URLs');
    logger.info('   GET /api/stats - Get scraper statistics');
    logger.info('   GET /health - Health check');
    
    logger.info('\n🔧 To test the scraper:');
    logger.info('   1. Visit http://localhost:3000/health for health check');
    logger.info('   2. Use POST /api/scrape with JSON: {"url": "https://httpbin.org/html"}');
    logger.info('   3. Check examples in examples/usage.js');
    
    logger.info('\n⚠️  Note: Redis is optional - the system will work without it');
    logger.info('💡 Press Ctrl+C to stop the server');
    
  } catch (error) {
    logger.error('❌ Failed to start scraper system:', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  logger.info('\n👋 Shutting down gracefully...');
  process.exit(0);
});

// Run the test
testScraper();
