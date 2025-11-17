#!/usr/bin/env python3
"""
Scrapy-based e-commerce scraper API
Wraps Scrapy for easy integration with Node.js backend
"""

import json
import logging
import redis
import scrapy
from flask import Flask, request, jsonify
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.ecommerce import EcommerceSpider
import os
from datetime import datetime

app = Flask(__name__)
redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store current crawl stats
crawl_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'average_response_time': 0,
    'start_time': datetime.now().isoformat()
}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'service': 'scrapy-scraper',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/search', methods=['POST'])
def search():
    """Search for products across retailers using Scrapy"""
    try:
        data = request.get_json()
        query = data.get('query')
        sites = data.get('sites', [
            'amazon', 'walmart', 'ebay', 'target', 'bestbuy', 'newegg'
        ])

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # URLs to scrape
        urls = {
            'amazon': f'https://www.amazon.com/s?k={query}',
            'walmart': f'https://www.walmart.com/search?q={query}',
            'ebay': f'https://www.ebay.com/sch/i.html?_nkw={query}',
            'target': f'https://www.target.com/s?searchTerm={query}',
            'bestbuy': f'https://www.bestbuy.com/site/searchpage.jsp?st={query}',
            'newegg': f'https://www.newegg.com/p/pl?d={query}',
            'flipkart': f'https://www.flipkart.com/search?q={query}',
            'aliexpress': f'https://www.aliexpress.com/wholesale?SearchText={query}'
        }

        # Collect all products
        products = []
        for site in sites:
            if site not in urls:
                continue

            try:
                # Store job in Redis for processing
                job_id = f"{site}:{query}:{datetime.now().timestamp()}"
                job_data = {
                    'url': urls[site],
                    'site': site,
                    'query': query,
                    'job_id': job_id
                }

                redis_client.hset(f'scrape_job:{job_id}', mapping=job_data)

                logger.info(f"Queued scrape job for {site}: {urls[site]}")

            except Exception as e:
                logger.error(f"Error queueing {site}: {e}")
                continue

        return jsonify({
            'query': query,
            'status': 'processing',
            'sites_queued': len(sites),
            'message': 'Scraping jobs have been queued. Results will be available shortly.',
            'timestamp': datetime.now().isoformat()
        }), 202

    except Exception as e:
        logger.error(f'Search error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/parallel', methods=['POST'])
def search_parallel():
    """Parallel search using Scrapy's built-in concurrency"""
    try:
        data = request.get_json()
        query = data.get('query')

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Use Redis-backed queue for parallel processing
        search_queue_key = f'search_queue:{query}'
        results_key = f'search_results:{query}'

        # Clear old results
        redis_client.delete(results_key)

        # Queue search job
        redis_client.rpush(search_queue_key, json.dumps({'query': query}))

        # For now, return success - in production, this would be async
        return jsonify({
            'status': 'queued',
            'query': query,
            'message': 'Search queued for processing',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f'Parallel search error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get scraper statistics"""
    return jsonify({
        'stats': crawl_stats,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=False
    )
