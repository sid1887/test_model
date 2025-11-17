import json
import redis
import logging

logger = logging.getLogger(__name__)

class DuplicatesPipeline:
    """Remove duplicate products"""

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        # Create unique ID from title and site
        item_id = f"{item['site']}_{item['title']}"

        if item_id in self.ids_seen:
            raise DropItem(f"Duplicate item found: {item}")

        self.ids_seen.add(item_id)
        return item


class RedisPipeline:
    """Store products in Redis for caching"""

    def __init__(self, redis_host, redis_port, redis_db):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.redis_conn = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_host=crawler.settings.get('REDIS_HOST', 'localhost'),
            redis_port=crawler.settings.get('REDIS_PORT', 6379),
            redis_db=crawler.settings.get('REDIS_DB', 0)
        )

    def open_spider(self, spider):
        try:
            self.redis_conn = redis.StrictRedis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True
            )
            self.redis_conn.ping()
            logger.info('Redis connection established')
        except Exception as e:
            logger.error(f'Failed to connect to Redis: {e}')
            self.redis_conn = None

    def close_spider(self, spider):
        if self.redis_conn:
            self.redis_conn.close()

    def process_item(self, item, spider):
        if self.redis_conn:
            try:
                # Store product in Redis
                key = f"product:{item['site']}:{item['title']}"
                self.redis_conn.setex(
                    key,
                    3600,  # 1 hour expiry
                    json.dumps(dict(item))
                )

                # Add to search index
                search_key = f"search:{item['site']}:{item.get('query', 'unknown')}"
                self.redis_conn.rpush(search_key, json.dumps(dict(item)))
                self.redis_conn.expire(search_key, 3600)

            except Exception as e:
                logger.error(f'Error storing in Redis: {e}')

        return item


class DropItem(Exception):
    """Exception for dropping items"""
    pass
