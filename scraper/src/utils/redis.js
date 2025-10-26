const redis = require('redis');
const logger = require('./logger');

class RedisClient {
  constructor() {
    this.client = null;
    this.isConnected = false;
    this.isEnabled = process.env.REDIS_ENABLED !== 'false';

    if (!this.isEnabled) {
      logger.info('Redis is disabled - running without caching');
    }
  }

  async connect() {
    if (!this.isEnabled) {
      logger.info('Redis is disabled, skipping connection');
      return null;
    }

    try {
      // Construct Redis URL (Redis v4+ format)
      const redisHost = process.env.REDIS_HOST || 'localhost';
      const redisPort = process.env.REDIS_PORT || 6379;
      const redisPassword = process.env.REDIS_PASSWORD;
      
      const redisUrl = redisPassword
        ? `redis://:${redisPassword}@${redisHost}:${redisPort}`
        : `redis://${redisHost}:${redisPort}`;
      
      this.client = redis.createClient({
        url: redisUrl,
        socket: {
          reconnectStrategy: (retries) => {
            if (retries > 2) {
              logger.warn('Redis max retry attempts reached - continuing without Redis');
              return false; // Stop retrying
            }
            return Math.min(retries * 100, 1000); // Exponential backoff
          },
          connectTimeout: 3000
        }
      });

      this.client.on('connect', () => {
        logger.info('Connected to Redis server');
        this.isConnected = true;
      });

      this.client.on('error', (err) => {
        if (err.code === 'ECONNREFUSED') {
          logger.warn('Redis not available - continuing without caching');
        } else {
          logger.error('Redis client error:', err);
        }
        this.isConnected = false;
      });

      this.client.on('end', () => {
        logger.info('Redis connection ended');
        this.isConnected = false;
      });

      await this.client.connect();
      return this.client;
    } catch (error) {
      logger.warn('Failed to connect to Redis - continuing without caching:', error.message);
      this.isConnected = false;
      return null;
    }
  }

  async disconnect() {
    if (this.client) {
      await this.client.quit();
      this.isConnected = false;
      logger.info('Disconnected from Redis server');
    }
  }
  async set(key, value, ttl = 3600) {
    try {
      if (!this.isConnected || !this.client) {
        logger.debug('Redis not available, skipping cache set');
        return;
      }
      const serializedValue = JSON.stringify(value);
      if (ttl) {
        await this.client.setEx(key, ttl, serializedValue);
      } else {
        await this.client.set(key, serializedValue);
      }
      logger.debug(`Set Redis key: ${key} with TTL: ${ttl}`);
    } catch (error) {
      logger.warn(`Failed to set Redis key ${key}:`, error.message);
      // Don't throw error, just warn
    }
  }

  async get(key) {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      const value = await this.client.get(key);
      if (value) {
        logger.debug(`Retrieved Redis key: ${key}`);
        return JSON.parse(value);
      }
      return null;
    } catch (error) {
      logger.error(`Failed to get Redis key ${key}:`, error);
      throw error;
    }
  }

  async del(key) {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      const result = await this.client.del(key);
      logger.debug(`Deleted Redis key: ${key}`);
      return result;
    } catch (error) {
      logger.error(`Failed to delete Redis key ${key}:`, error);
      throw error;
    }
  }

  async exists(key) {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      return await this.client.exists(key);
    } catch (error) {
      logger.error(`Failed to check Redis key existence ${key}:`, error);
      throw error;
    }
  }

  async getKeys(pattern = '*') {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      return await this.client.keys(pattern);
    } catch (error) {
      logger.error(`Failed to get Redis keys with pattern ${pattern}:`, error);
      throw error;
    }
  }

  async flushAll() {
    try {
      if (!this.isConnected) {
        await this.connect();
      }
      await this.client.flushAll();
      logger.info('Flushed all Redis data');
    } catch (error) {
      logger.error('Failed to flush Redis data:', error);
      throw error;
    }
  }

  getStatus() {
    return {
      isConnected: this.isConnected,
      host: process.env.REDIS_HOST || 'localhost',
      port: process.env.REDIS_PORT || 6379
    };
  }
}

module.exports = new RedisClient();
