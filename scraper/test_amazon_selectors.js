const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

// Configure Puppeteer with stealth
puppeteer.use(StealthPlugin());

async function testAmazonSelectors() {
    console.log('Testing Amazon selectors...');
    
    const browser = await puppeteer.launch({
        headless: false, // Show browser for debugging
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage'
        ]
    });

    const page = await browser.newPage();
    
    try {
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        console.log('Navigating to Amazon search...');
        await page.goto('https://www.amazon.com/s?k=laptop', {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Wait a bit for dynamic content
        await page.waitForTimeout(3000);

        // Test current selectors
        console.log('Testing current selectors...');
        const currentResults = await page.evaluate(() => {
            const items = Array.from(document.querySelectorAll('[data-component-type="s-search-result"]'));
            console.log(`Found ${items.length} items with current selector`);
            return items.length;
        });

        // Test alternative selectors
        console.log('Testing alternative selectors...');
        const altResults = await page.evaluate(() => {
            const selectors = [
                '[data-component-type="s-search-result"]',
                '.s-result-item',
                '.s-card-container',
                '[data-asin]',
                '.a-section.a-spacing-base'
            ];
            
            const results = {};
            selectors.forEach(selector => {
                const items = document.querySelectorAll(selector);
                results[selector] = items.length;
                console.log(`Selector "${selector}": ${items.length} results`);
            });
            
            return results;
        });

        console.log('Alternative selector results:', altResults);

        // Test extracting data with working selector
        const bestSelector = Object.entries(altResults).reduce((a, b) => altResults[a[0]] > altResults[b[0]] ? a : b)[0];
        console.log(`Best selector: ${bestSelector} with ${altResults[bestSelector]} results`);

        if (altResults[bestSelector] > 0) {
            const sampleData = await page.evaluate((selector) => {
                const items = Array.from(document.querySelectorAll(selector));
                return items.slice(0, 3).map((item, index) => {
                    // Try multiple title selectors
                    const titleSelectors = [
                        'h2 a span',
                        '.a-link-normal .a-text-normal',
                        '[data-cy="title-recipe-title"]',
                        '.s-link-style a span',
                        'h2 span'
                    ];
                    
                    let title = '';
                    for (const sel of titleSelectors) {
                        const titleEl = item.querySelector(sel);
                        if (titleEl && titleEl.textContent.trim()) {
                            title = titleEl.textContent.trim();
                            break;
                        }
                    }

                    // Try multiple price selectors
                    const priceSelectors = [
                        '.a-price .a-offscreen',
                        '.a-price-whole',
                        '.a-price .a-price-range .a-price-whole'
                    ];
                    
                    let price = '';
                    for (const sel of priceSelectors) {
                        const priceEl = item.querySelector(sel);
                        if (priceEl && priceEl.textContent.trim()) {
                            price = priceEl.textContent.trim();
                            break;
                        }
                    }

                    const imageEl = item.querySelector('img');
                    const linkEl = item.querySelector('h2 a') || item.querySelector('a');

                    return {
                        index,
                        title: title || 'NO TITLE FOUND',
                        price: price || 'NO PRICE FOUND',
                        hasImage: !!imageEl,
                        hasLink: !!linkEl,
                        itemHtml: item.innerHTML.substring(0, 500) + '...'
                    };
                });
            }, bestSelector);

            console.log('Sample extracted data:');
            sampleData.forEach(item => {
                console.log(`\n${item.index + 1}. Title: ${item.title}`);
                console.log(`   Price: ${item.price}`);
                console.log(`   Has Image: ${item.hasImage}`);
                console.log(`   Has Link: ${item.hasLink}`);
            });
        }

        // Take a screenshot for manual inspection
        await page.screenshot({ path: 'd:/dev_packages/test_model/amazon_debug.png', fullPage: true });
        console.log('Screenshot saved as amazon_debug.png');

    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

testAmazonSelectors();
