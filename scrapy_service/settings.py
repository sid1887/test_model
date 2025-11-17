# Scrapy settings for ecommerce_scraper project

BOT_NAME = 'ecommerce_scraper'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

# Crawl responsibly by identifying yourself
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS_PER_IP = 2

# Delay between requests (milliseconds)
DOWNLOAD_DELAY = 0.5

# Timeout settings
DOWNLOAD_TIMEOUT = 30

# Disable cookies by default
COOKIES_ENABLED = True

# Retry settings
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
}

# Pipeline
ITEM_PIPELINES = {
    'pipelines.DuplicatesPipeline': 300,
    'pipelines.CLIPAnalysisPipeline': 350,
    'pipelines.RedisPipeline': 400,
}

# Redis connection
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0

# Splash settings (for JavaScript rendering)
SPLASH_URL = 'http://splash:8050'
SPLASH_SLOT_POLICY = 'scrapy_splash.SlotPolicy'

# Log settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Autothrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
