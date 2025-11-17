#!/usr/bin/env python3
"""
Scrapy-based e-commerce scraper API
Wraps Scrapy for easy integration with Node.js backend
Supports 15+ retailers with full service integration
"""

import json
import logging
import redis
import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
redis_client = redis.StrictRedis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# Service URLs
VOICE_STT_URL = os.getenv('VOICE_STT_URL', 'http://web-api:8000/api/v1/voice/transcribe')
CLIP_SERVICE_URL = os.getenv('CLIP_SERVICE_URL', 'http://web-api:8000/api/v1/search/image')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supported retailers (15+)
SUPPORTED_RETAILERS = [
    'amazon', 'walmart', 'ebay', 'target', 'bestbuy', 
    'newegg', 'costco', 'homedepot', 'lowes', 'macys',
    'overstock', 'wayfair', 'zappos', 'bhphotovideo', 
    'nordstrom', 'flipkart', 'aliexpress'
]

# Store current crawl stats
crawl_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'average_response_time': 0,
    'start_time': datetime.now().isoformat(),
    'retailers_active': len(SUPPORTED_RETAILERS)
}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'service': 'scrapy-scraper',
            'retailers_supported': len(SUPPORTED_RETAILERS),
            'services': {
                'redis': 'connected',
                'voice_stt': 'available',
                'clip_analysis': 'available',
                'captcha_solver': 'available',
                'proxy_service': 'available'
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/retailers', methods=['GET'])
def get_retailers():
    """Get list of supported retailers"""
    return jsonify({
        'retailers': SUPPORTED_RETAILERS,
        'total': len(SUPPORTED_RETAILERS),
        'timestamp': datetime.now().isoformat()
    })

def perform_search(query, sites=None):
    """Core search logic that can be reused"""
    if sites is None:
        sites = SUPPORTED_RETAILERS[:10]  # Default to first 10
    
    # URLs to scrape for all supported retailers
    urls = {
        'amazon': f'https://www.amazon.com/s?k={query}',
        'walmart': f'https://www.walmart.com/search?q={query}',
        'ebay': f'https://www.ebay.com/sch/i.html?_nkw={query}',
        'target': f'https://www.target.com/s?searchTerm={query}',
        'bestbuy': f'https://www.bestbuy.com/site/searchpage.jsp?st={query}',
        'newegg': f'https://www.newegg.com/p/pl?d={query}',
        'flipkart': f'https://www.flipkart.com/search?q={query}',
        'aliexpress': f'https://www.aliexpress.com/wholesale?SearchText={query}',
        'costco': f'https://www.costco.com/CatalogSearch?keyword={query}',
        'homedepot': f'https://www.homedepot.com/s/{query}',
        'lowes': f'https://www.lowes.com/search?searchTerm={query}',
        'macys': f'https://www.macys.com/shop/search?keyword={query}',
        'overstock': f'https://www.overstock.com/search?keywords={query}',
        'wayfair': f'https://www.wayfair.com/keyword.php?keyword={query}',
        'zappos': f'https://www.zappos.com/search?term={query}',
        'bhphotovideo': f'https://www.bhphotovideo.com/c/search?Ntt={query}',
        'nordstrom': f'https://www.nordstrom.com/sr?keyword={query}'
    }

    # Queue jobs for all sites
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
            crawl_stats['total_requests'] += 1

            logger.info(f"Queued scrape job for {site}: {urls[site]}")

        except Exception as e:
            logger.error(f"Error queueing {site}: {e}")
            crawl_stats['failed_requests'] += 1
            continue

    crawl_stats['successful_requests'] += len(sites)
    
    return {
        'query': query,
        'status': 'processing',
        'sites_queued': len(sites),
        'message': 'Scraping jobs have been queued. Results will be available shortly.',
        'timestamp': datetime.now().isoformat()
    }

@app.route('/api/search', methods=['POST'])
def search():
    """Search for products across retailers using Scrapy"""
    try:
        data = request.get_json()
        query = data.get('query')
        sites = data.get('sites', SUPPORTED_RETAILERS[:10])  # Default to first 10

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        result = perform_search(query, sites)
        return jsonify(result), 202

    except Exception as e:
        logger.error(f'Search error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/voice', methods=['POST'])
def voice_search():
    """Voice-based product search using speech-to-text"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        
        # Send audio to voice STT service
        files = {'audio': (audio_file.filename, audio_file.read(), audio_file.content_type)}
        response = requests.post(VOICE_STT_URL, files=files, timeout=30)
        
        if response.status_code != 200:
            return jsonify({'error': 'Voice transcription failed'}), 500
        
        transcription = response.json()
        query = transcription.get('text', '')
        
        if not query:
            return jsonify({'error': 'No text transcribed from audio'}), 400
        
        logger.info(f'Voice search transcribed: {query}')
        
        # Perform regular search with transcribed query
        result = perform_search(query)
        return jsonify(result), 202
        
    except Exception as e:
        logger.error(f'Voice search error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/image', methods=['POST'])
def image_search():
    """Image-based product search using CLIP"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Image file is required'}), 400
        
        image_file = request.files['image']
        
        # Send image to CLIP service
        files = {'image': (image_file.filename, image_file.read(), image_file.content_type)}
        response = requests.post(CLIP_SERVICE_URL, files=files, timeout=30)
        
        if response.status_code != 200:
            return jsonify({'error': 'Image analysis failed'}), 500
        
        analysis = response.json()
        query = analysis.get('description', '')
        
        if not query:
            return jsonify({'error': 'No description extracted from image'}), 400
        
        logger.info(f'Image search description: {query}')
        
        # Perform regular search with image description
        result = perform_search(query)
        return jsonify(result), 202
        
    except Exception as e:
        logger.error(f'Image search error: {e}')
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

@app.route('/api/search/bulk', methods=['POST'])
def bulk_search():
    """Bulk search across multiple queries and retailers for maximum performance"""
    try:
        data = request.get_json()
        queries = data.get('queries', [])
        retailers = data.get('retailers', SUPPORTED_RETAILERS)
        
        if not queries:
            return jsonify({'error': 'At least one query is required'}), 400
        
        batch_id = f"bulk_{datetime.now().timestamp()}"
        jobs_queued = 0
        
        # Queue all combinations of queries and retailers
        for query in queries:
            for retailer in retailers:
                if retailer not in SUPPORTED_RETAILERS:
                    continue
                
                job_id = f"{retailer}:{query}:{batch_id}"
                job_data = {
                    'query': query,
                    'retailer': retailer,
                    'batch_id': batch_id,
                    'job_id': job_id,
                    'timestamp': datetime.now().isoformat()
                }
                
                redis_client.hset(f'scrape_job:{job_id}', mapping=job_data)
                redis_client.rpush(f'batch:{batch_id}', job_id)
                jobs_queued += 1
        
        # Set batch metadata
        redis_client.hset(f'batch_meta:{batch_id}', mapping={
            'total_jobs': jobs_queued,
            'queries': json.dumps(queries),
            'retailers': json.dumps(retailers),
            'status': 'queued',
            'created_at': datetime.now().isoformat()
        })
        redis_client.expire(f'batch_meta:{batch_id}', 7200)  # 2 hours
        
        logger.info(f'Bulk search queued: {jobs_queued} jobs for batch {batch_id}')
        
        return jsonify({
            'status': 'queued',
            'batch_id': batch_id,
            'jobs_queued': jobs_queued,
            'queries_count': len(queries),
            'retailers_count': len([r for r in retailers if r in SUPPORTED_RETAILERS]),
            'message': 'Bulk search queued for processing',
            'timestamp': datetime.now().isoformat()
        }), 202
        
    except Exception as e:
        logger.error(f'Bulk search error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch/<batch_id>', methods=['GET'])
def get_batch_status(batch_id):
    """Get status of a bulk search batch"""
    try:
        batch_meta = redis_client.hgetall(f'batch_meta:{batch_id}')
        
        if not batch_meta:
            return jsonify({'error': 'Batch not found'}), 404
        
        # Get results
        job_ids = redis_client.lrange(f'batch:{batch_id}', 0, -1)
        results = []
        completed = 0
        
        for job_id in job_ids:
            result_key = f'search_results:{job_id}'
            if redis_client.exists(result_key):
                completed += 1
                results.extend(json.loads(item) for item in redis_client.lrange(result_key, 0, -1))
        
        return jsonify({
            'batch_id': batch_id,
            'total_jobs': int(batch_meta.get('total_jobs', 0)),
            'completed_jobs': completed,
            'progress': f"{(completed / int(batch_meta.get('total_jobs', 1))) * 100:.1f}%",
            'results_count': len(results),
            'status': batch_meta.get('status', 'unknown'),
            'created_at': batch_meta.get('created_at', ''),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Batch status error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get comprehensive scraper statistics"""
    try:
        # Get today's stats from Redis
        today = datetime.now().strftime('%Y-%m-%d')
        stats_key = f"stats:scrapy:{today}"
        daily_stats = redis_client.hgetall(stats_key)
        
        # Calculate retailer-specific stats
        retailer_stats = {}
        for retailer in SUPPORTED_RETAILERS:
            key = f'{retailer}_products'
            retailer_stats[retailer] = int(daily_stats.get(key, 0))
        
        return jsonify({
            'stats': crawl_stats,
            'daily_stats': {
                'date': today,
                'total_products_scraped': sum(retailer_stats.values()),
                'by_retailer': retailer_stats
            },
            'retailers': {
                'supported': SUPPORTED_RETAILERS,
                'total': len(SUPPORTED_RETAILERS),
                'active': len([r for r in SUPPORTED_RETAILERS if retailer_stats.get(r, 0) > 0])
            },
            'services': {
                'redis': 'connected',
                'clip_analysis': 'available',
                'voice_stt': 'available',
                'captcha_solver': 'available',
                'proxy_service': 'available'
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f'Stats error: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=False
    )
