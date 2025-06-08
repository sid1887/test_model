const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const UserAgent = require('user-agents');

puppeteer.use(StealthPlugin());

async function debugAmazonResponse() {
  console.log('🔍 Debugging Amazon Response...');
  
  const browser = await puppeteer.launch({
    headless: false, // Show browser for debugging
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

  const page = await browser.newPage();
  
  try {
    // Set user agent and viewport
    await page.setUserAgent(new UserAgent().toString());
    await page.setViewport({ width: 1366, height: 768 });
    
    console.log('📱 Navigating to Amazon search...');
    await page.goto('https://www.amazon.com/s?k=laptop', {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait a bit for page to fully load
    await page.waitForTimeout(3000);

    // Check what we actually received
    const title = await page.title();
    console.log(`📄 Page title: ${title}`);

    // Check if we got blocked
    const content = await page.content();
    if (content.includes('Robot or human') || content.includes('captcha') || content.includes('blocked')) {
      console.log('🚫 Detected blocking/captcha page');
    }

    // Check for different possible selectors
    const selectors = [
      '[data-component-type="s-search-result"]',
      '.s-result-item',
      '.s-card-container',
      '[data-asin]',
      '.a-section.a-spacing-base',
      '.sg-col-inner',
      '[data-cy="title-recipe-title"]',
      'h2 a span'
    ];

    console.log('🔍 Testing selectors:');
    for (const selector of selectors) {
      const count = await page.$$eval(selector, elements => elements.length);
      console.log(`  ${selector}: ${count} elements`);
    }

    // Get sample HTML to understand structure
    const sampleHTML = await page.evaluate(() => {
      const firstResult = document.querySelector('[data-component-type="s-search-result"]') || 
                          document.querySelector('.s-result-item') ||
                          document.querySelector('.sg-col-inner');
      return firstResult ? firstResult.outerHTML.substring(0, 500) + '...' : 'No results found';
    });

    console.log('📝 Sample HTML structure:');
    console.log(sampleHTML);

    // Take screenshot
    await page.screenshot({ path: 'amazon_response_debug.png', fullPage: false });
    console.log('📸 Screenshot saved as amazon_response_debug.png');

    // Wait to see the page
    console.log('⏳ Waiting 10 seconds to observe the page...');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
  } finally {
    await browser.close();
  }
}

debugAmazonResponse().catch(console.error);
