"""
Elasticsearch Integration Service (Port 8015) - Phase 7
Full-text search for 100M+ documents with advanced features
"""

from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch
import logging
from typing import List, Optional, Dict
from core_infrastructure import ShardedServiceBase
import asyncio
import json

app = FastAPI(title="Elasticsearch Service", version="1.0")
logger = logging.getLogger('elasticsearch_service')

# Initialize service
es_service = ShardedServiceBase(service_name="ElasticsearchService")

# Elasticsearch connection
es_client = None


# ============================================================================
# ELASTICSEARCH SETUP & MANAGEMENT
# ============================================================================

async def initialize_elasticsearch():
    """Initialize Elasticsearch with optimal settings"""
    global es_client

    try:
        es_client = Elasticsearch(['http://elasticsearch:9200'], timeout=20)

        # Wait for connection
        await asyncio.sleep(1)

        # Create indices with optimized mappings
        indices = {
            'products': {
                'settings': {
                    'number_of_shards': 5,
                    'number_of_replicas': 2,
                    'index.codec': 'best_compression',
                    'analysis': {
                        'analyzer': {
                            'text_analyzer': {
                                'type': 'standard',
                                'stopwords': '_english_'
                            },
                            'synonym_analyzer': {
                                'type': 'standard',
                                'stopwords': '_english_',
                                'synonyms': [
                                    'phone,mobile,cellular',
                                    'laptop,notebook,computer',
                                    'shirt,tshirt,clothing'
                                ]
                            },
                            'fuzzy_analyzer': {
                                'type': 'standard',
                                'stopwords': '_english_'
                            }
                        },
                        'filter': {
                            'stop_filter': {
                                'type': 'stop',
                                'stopwords': '_english_'
                            }
                        }
                    }
                },
                'mappings': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'name': {
                            'type': 'text',
                            'analyzer': 'text_analyzer',
                            'fields': {
                                'keyword': {'type': 'keyword'},
                                'synonym': {'type': 'text', 'analyzer': 'synonym_analyzer'},
                                'ngram': {
                                    'type': 'text',
                                    'analyzer': 'ngram_analyzer'
                                }
                            }
                        },
                        'description': {
                            'type': 'text',
                            'analyzer': 'text_analyzer'
                        },
                        'category': {'type': 'keyword'},
                        'subcategory': {'type': 'keyword'},
                        'price': {'type': 'float'},
                        'rating': {'type': 'float'},
                        'reviews_count': {'type': 'integer'},
                        'stock': {'type': 'integer'},
                        'warehouse': {'type': 'keyword'},
                        'tags': {'type': 'keyword'},
                        'brand': {'type': 'keyword'},
                        'created_date': {'type': 'date'},
                        'updated_date': {'type': 'date'},
                        'popularity_score': {'type': 'float'},
                        'boosted': {'type': 'boolean'}
                    }
                }
            },
            'reviews': {
                'settings': {
                    'number_of_shards': 3,
                    'number_of_replicas': 1
                },
                'mappings': {
                    'properties': {
                        'id': {'type': 'keyword'},
                        'product_id': {'type': 'keyword'},
                        'user_id': {'type': 'keyword'},
                        'rating': {'type': 'integer'},
                        'title': {'type': 'text', 'analyzer': 'text_analyzer'},
                        'content': {'type': 'text', 'analyzer': 'text_analyzer'},
                        'verified': {'type': 'boolean'},
                        'helpful_count': {'type': 'integer'},
                        'created_date': {'type': 'date'}
                    }
                }
            }
        }

        for index_name, config in indices.items():
            try:
                if not es_client.indices.exists(index=index_name):
                    es_client.indices.create(index=index_name, body=config)
                    logger.info(f"✅ Created index: {index_name}")
            except Exception as e:
                logger.warning(f"Index creation error for {index_name}: {e}")

        logger.info("✅ Elasticsearch initialized")
        return True

    except Exception as e:
        logger.error(f"Elasticsearch initialization error: {e}")
        return False


# ============================================================================
# ELASTICSEARCH OPERATIONS
# ============================================================================

class ElasticsearchManager:
    """Manage Elasticsearch operations"""

    def __init__(self, es_client):
        self.es = es_client

    async def index_product(self, product_id: str, product_data: Dict):
        """Index a product in Elasticsearch"""
        try:
            self.es.index(
                index='products',
                id=product_id,
                body=product_data
            )
            return True
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            return False

    async def bulk_index_products(self, products: List[Dict]):
        """Bulk index products"""
        try:
            from elasticsearch.helpers import bulk

            actions = [
                {
                    '_index': 'products',
                    '_id': p['id'],
                    '_source': p
                }
                for p in products
            ]

            success, errors = bulk(self.es, actions, chunk_size=1000)
            logger.info(f"Bulk indexed {success} documents")

            if errors:
                logger.warning(f"Bulk index errors: {errors[:5]}")

            return success

        except Exception as e:
            logger.error(f"Bulk indexing error: {e}")
            return 0

    async def search(self, query_text: str, limit: int = 20, offset: int = 0) -> Dict:
        """Full-text search with ranking"""
        try:
            search_query = {
                'query': {
                    'multi_match': {
                        'query': query_text,
                        'fields': [
                            'name^3',  # 3x boost
                            'name.synonym^2',
                            'description',
                            'tags^2',
                            'brand'
                        ],
                        'type': 'best_fields',
                        'operator': 'or'
                    }
                },
                'size': limit,
                'from': offset,
                'sort': [
                    {'_score': {'order': 'desc'}},
                    {'popularity_score': {'order': 'desc'}},
                    {'rating': {'order': 'desc'}}
                ]
            }

            results = self.es.search(index='products', body=search_query)

            hits = results['hits']['hits']
            return {
                'total': results['hits']['total']['value'],
                'results': [
                    {
                        'id': hit['_id'],
                        'score': hit['_score'],
                        **hit['_source']
                    }
                    for hit in hits
                ]
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'total': 0, 'results': []}

    async def fuzzy_search(self, query_text: str, limit: int = 20) -> Dict:
        """Fuzzy search for typo tolerance"""
        try:
            search_query = {
                'query': {
                    'multi_match': {
                        'query': query_text,
                        'fields': ['name', 'description', 'brand'],
                        'fuzziness': 'AUTO',
                        'prefix_length': 1
                    }
                },
                'size': limit
            }

            results = self.es.search(index='products', body=search_query)

            hits = results['hits']['hits']
            return {
                'total': results['hits']['total']['value'],
                'results': [
                    {'id': hit['_id'], 'score': hit['_score'], **hit['_source']}
                    for hit in hits
                ]
            }

        except Exception as e:
            logger.error(f"Fuzzy search error: {e}")
            return {'total': 0, 'results': []}

    async def faceted_search(self, query_text: str, filters: Dict) -> Dict:
        """Faceted search with aggregations"""
        try:
            # Build filter
            must_clauses = [
                {'multi_match': {'query': query_text, 'fields': ['name', 'description']}}
            ]

            if filters.get('category'):
                must_clauses.append({'term': {'category': filters['category']}})

            if filters.get('brand'):
                must_clauses.append({'term': {'brand': filters['brand']}})

            if filters.get('price_min') and filters.get('price_max'):
                must_clauses.append({
                    'range': {
                        'price': {
                            'gte': filters['price_min'],
                            'lte': filters['price_max']
                        }
                    }
                })

            if filters.get('rating_min'):
                must_clauses.append({'range': {'rating': {'gte': filters['rating_min']}}})

            search_query = {
                'query': {'bool': {'must': must_clauses}},
                'aggs': {
                    'categories': {'terms': {'field': 'category', 'size': 50}},
                    'brands': {'terms': {'field': 'brand', 'size': 50}},
                    'price_range': {
                        'range': {
                            'field': 'price',
                            'ranges': [
                                {'to': 50},
                                {'from': 50, 'to': 100},
                                {'from': 100, 'to': 500},
                                {'from': 500}
                            ]
                        }
                    },
                    'avg_rating': {'avg': {'field': 'rating'}}
                },
                'size': 20
            }

            results = self.es.search(index='products', body=search_query)

            facets = results.get('aggregations', {})
            hits = results['hits']['hits']

            return {
                'results': [{'id': h['_id'], **h['_source']} for h in hits],
                'facets': {
                    'categories': [{'name': f['key'], 'count': f['doc_count']}
                                 for f in facets.get('categories', {}).get('buckets', [])],
                    'brands': [{'name': f['key'], 'count': f['doc_count']}
                             for f in facets.get('brands', {}).get('buckets', [])],
                    'price_ranges': facets.get('price_range', {}).get('buckets', [])}
            }

        except Exception as e:
            logger.error(f"Faceted search error: {e}")
            return {'results': [], 'facets': {}}

    async def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        """Autocomplete suggestions"""
        try:
            search_query = {
                'query': {
                    'match_phrase_prefix': {
                        'name': {
                            'query': prefix,
                            'boost': 2
                        }
                    }
                },
                'size': limit,
                '_source': ['name']
            }

            results = self.es.search(index='products', body=search_query)

            suggestions = [hit['_source']['name'] for hit in results['hits']['hits']]
            return list(set(suggestions))  # Deduplicate

        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return []

    async def search_reviews(self, product_id: str, query_text: Optional[str] = None) -> List[Dict]:
        """Search reviews for a product"""
        try:
            must_clauses = [{'term': {'product_id': product_id}}]

            if query_text:
                must_clauses.append({
                    'multi_match': {
                        'query': query_text,
                        'fields': ['title', 'content']
                    }
                })

            search_query = {
                'query': {'bool': {'must': must_clauses}},
                'sort': [{'helpful_count': {'order': 'desc'}}, {'created_date': {'order': 'desc'}}],
                'size': 20
            }

            results = self.es.search(index='reviews', body=search_query)

            return [
                {'id': hit['_id'], **hit['_source']}
                for hit in results['hits']['hits']
            ]

        except Exception as e:
            logger.error(f"Review search error: {e}")
            return []

    async def get_stats(self) -> Dict:
        """Get Elasticsearch cluster stats"""
        try:
            stats = self.es.indices.stats(index='products')

            return {
                'products_count': stats['_all']['total']['docs']['count'],
                'products_size': stats['_all']['total']['store']['size_in_bytes'],
                'indices': list(stats['indices'].keys())
            }

        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}


es_manager = None


# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

@app.on_event('startup')
async def startup():
    """Initialize Elasticsearch service"""
    global es_manager

    shard_config = {
        0: {'primary_host': 'postgres-primary-0', 'port': 5432, 'replica_hosts': []},
        1: {'primary_host': 'postgres-primary-1', 'port': 5432, 'replica_hosts': []},
        2: {'primary_host': 'postgres-primary-2', 'port': 5432, 'replica_hosts': []},
        3: {'primary_host': 'postgres-primary-3', 'port': 5432, 'replica_hosts': []},
    }

    await es_service.initialize(shard_config)

    # Initialize Elasticsearch
    initialized = await initialize_elasticsearch()
    if initialized and es_client:
        es_manager = ElasticsearchManager(es_client)
        logger.info("✅ Elasticsearch Service started")
    else:
        logger.error("❌ Failed to initialize Elasticsearch")


@app.on_event('shutdown')
async def shutdown():
    """Cleanup"""
    await es_service.shutdown()
    if es_client:
        es_client.close()


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@app.get('/search')
async def search(q: str, limit: int = 20, offset: int = 0):
    """Full-text search"""
    if not es_manager:
        raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        results = await es_manager.search(q, limit, offset)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/search/fuzzy')
async def fuzzy_search(q: str, limit: int = 20):
    """Fuzzy search with typo tolerance"""
    if not es_manager:
        raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        results = await es_manager.fuzzy_search(q, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/search/faceted')
async def faceted_search(
    q: str,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    rating_min: Optional[float] = None
):
    """Faceted search with filters and aggregations"""
    if not es_manager:
        raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        filters = {
            'category': category,
            'brand': brand,
            'price_min': price_min,
            'price_max': price_max,
            'rating_min': rating_min
        }

        results = await es_manager.faceted_search(q, filters)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/autocomplete')
async def autocomplete(q: str, limit: int = 10):
    """Autocomplete suggestions"""
    if not es_manager:
        raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        suggestions = await es_manager.autocomplete(q, limit)
        return {'suggestions': suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/reviews/{product_id}')
async def search_reviews(product_id: str, q: Optional[str] = None):
    """Search reviews for product"""
    if not es_manager:
        raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        reviews = await es_manager.search_reviews(product_id, q)
        return {'product_id': product_id, 'reviews': reviews, 'count': len(reviews)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/index/product')
async def index_product(product_id: str, data: dict):
    """Index a product"""
    if not es_manager:
        raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        success = await es_manager.index_product(product_id, data)
        return {'status': 'indexed' if success else 'failed'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/index/bulk')
async def bulk_index(products: List[Dict]):
    """Bulk index products"""
    if not es_manager:
        raise HTTPException(status_code=503, detail="Elasticsearch not available")

    try:
        count = await es_manager.bulk_index_products(products)
        return {'indexed': count, 'total': len(products)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/stats')
async def get_stats():
    """Get Elasticsearch service statistics"""
    if not es_manager:
        return {'status': 'unavailable'}

    try:
        es_stats = await es_manager.get_stats()
        return {
            'service': 'elasticsearch',
            'es_stats': es_stats,
            'service_metrics': es_service.get_metrics()
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8015)
