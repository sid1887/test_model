"""
Real-Time Data Feeds
Stocks, Crypto, Event Tickets, News - all integrated per product
"""

from typing import Dict, List, Optional, Any
import aiohttp
import asyncio
from datetime import datetime, timedelta
from app.core.cache import cache_manager, CacheLevel
from app.core.metrics import metrics
import logging

logger = logging.getLogger(__name__)


class StockDataFeed:
    """Stock market data integration (NSE/BSE/Alpha Vantage)"""
    
    def __init__(self):
        self.alpha_vantage_key = "YOUR_ALPHA_VANTAGE_KEY"  # TODO: Add to settings
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price"""
        cache_key = f"stock:{symbol}"
        cached = await cache_manager.get("stocks", cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get("Global Quote", {})
                    
                    result = {
                        "symbol": symbol,
                        "price": float(quote.get("05. price", 0)),
                        "change": float(quote.get("09. change", 0)),
                        "change_percent": quote.get("10. change percent", "0%"),
                        "volume": int(quote.get("06. volume", 0)),
                        "last_updated": datetime.utcnow().isoformat()
                    }
                    
                    await cache_manager.set("stocks", cache_key, result, ttl=60)
                    metrics.feed_updates_total.labels(feed_type="stock", source="alpha_vantage").inc()
                    
                    return result
        except Exception as e:
            logger.error(f"Stock price fetch failed for {symbol}: {e}")
        
        return None
    
    async def get_related_stocks(self, product_name: str) -> List[Dict[str, Any]]:
        """Get related stock symbols for a product"""
        # Map product to stock symbols (simplified)
        stock_map = {
            "apple": ["AAPL"],
            "microsoft": ["MSFT"],
            "samsung": ["005930.KS"],
            "google": ["GOOGL"],
            "amazon": ["AMZN"],
            "tesla": ["TSLA"]
        }
        
        stocks = []
        for keyword, symbols in stock_map.items():
            if keyword.lower() in product_name.lower():
                for symbol in symbols:
                    stock_data = await self.get_stock_price(symbol)
                    if stock_data:
                        stocks.append(stock_data)
        
        return stocks


class CryptoDataFeed:
    """Cryptocurrency price feed (CoinGecko/Binance)"""
    
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_crypto_price(self, coin_id: str = "bitcoin") -> Optional[Dict[str, Any]]:
        """Get current crypto price"""
        cache_key = f"crypto:{coin_id}"
        cached = await cache_manager.get("crypto", cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"{self.coingecko_base}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd,inr",
                "include_24hr_change": "true",
                "include_market_cap": "true"
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    coin_data = data.get(coin_id, {})
                    
                    result = {
                        "coin_id": coin_id,
                        "price_usd": coin_data.get("usd", 0),
                        "price_inr": coin_data.get("inr", 0),
                        "change_24h": coin_data.get("usd_24h_change", 0),
                        "market_cap": coin_data.get("usd_market_cap", 0),
                        "last_updated": datetime.utcnow().isoformat()
                    }
                    
                    await cache_manager.set("crypto", cache_key, result, ttl=60)
                    metrics.feed_updates_total.labels(feed_type="crypto", source="coingecko").inc()
                    
                    return result
        except Exception as e:
            logger.error(f"Crypto price fetch failed for {coin_id}: {e}")
        
        return None
    
    async def get_top_cryptos(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top cryptocurrencies by market cap"""
        cache_key = f"top_cryptos:{limit}"
        cached = await cache_manager.get("crypto", cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"{self.coingecko_base}/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = [
                        {
                            "id": coin["id"],
                            "name": coin["name"],
                            "symbol": coin["symbol"],
                            "price_usd": coin["current_price"],
                            "change_24h": coin["price_change_percentage_24h"],
                            "market_cap": coin["market_cap"],
                            "rank": coin["market_cap_rank"]
                        }
                        for coin in data
                    ]
                    
                    await cache_manager.set("crypto", cache_key, results, ttl=300)
                    return results
        except Exception as e:
            logger.error(f"Top cryptos fetch failed: {e}")
        
        return []


class NewsDataFeed:
    """News aggregation (NewsAPI)"""
    
    def __init__(self):
        self.newsapi_key = "YOUR_NEWSAPI_KEY"  # TODO: Add to settings
        self.newsapi_base = "https://newsapi.org/v2"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_product_news(
        self,
        product_name: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get news related to product"""
        cache_key = f"news:{product_name}:{limit}"
        cached = await cache_manager.get("news", cache_key)
        if cached:
            return cached
        
        try:
            session = await self.get_session()
            url = f"{self.newsapi_base}/everything"
            params = {
                "q": product_name,
                "sortBy": "publishedAt",
                "pageSize": limit,
                "apiKey": self.newsapi_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get("articles", [])
                    
                    results = [
                        {
                            "title": article["title"],
                            "description": article["description"],
                            "url": article["url"],
                            "source": article["source"]["name"],
                            "published_at": article["publishedAt"],
                            "image_url": article.get("urlToImage")
                        }
                        for article in articles
                    ]
                    
                    await cache_manager.set("news", cache_key, results, ttl=1800)
                    metrics.feed_updates_total.labels(feed_type="news", source="newsapi").inc()
                    
                    return results
        except Exception as e:
            logger.error(f"News fetch failed for {product_name}: {e}")
        
        return []


class TicketDataFeed:
    """Event ticket data (BookMyShow, Paytm Insider)"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search_events(
        self,
        query: str,
        city: str = "mumbai",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for events/tickets"""
        # Placeholder - would integrate with actual ticket APIs
        return []


class RealTimeFeedAggregator:
    """Aggregate all real-time feeds for a product"""
    
    def __init__(self):
        self.stock_feed = StockDataFeed()
        self.crypto_feed = CryptoDataFeed()
        self.news_feed = NewsDataFeed()
        self.ticket_feed = TicketDataFeed()
    
    async def get_product_context(
        self,
        product_name: str,
        product_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all real-time context for a product
        Returns stocks, crypto, news, tickets in parallel
        """
        tasks = {
            "stocks": self.stock_feed.get_related_stocks(product_name),
            "crypto": self.crypto_feed.get_top_cryptos(5) if "crypto" in product_name.lower() else None,
            "news": self.news_feed.get_product_news(product_name, limit=5),
            "events": self.ticket_feed.search_events(product_name, limit=5)
        }
        
        # Run all in parallel
        results = await asyncio.gather(
            *[task for task in tasks.values() if task],
            return_exceptions=True
        )
        
        context = {}
        for key, result in zip(tasks.keys(), results):
            if not isinstance(result, Exception):
                context[key] = result
            else:
                context[key] = []
        
        return context
    
    async def close(self):
        """Close all sessions"""
        await asyncio.gather(
            self.stock_feed.session.close() if self.stock_feed.session else None,
            self.crypto_feed.session.close() if self.crypto_feed.session else None,
            self.news_feed.session.close() if self.news_feed.session else None,
            self.ticket_feed.session.close() if self.ticket_feed.session else None,
            return_exceptions=True
        )


# Global aggregator instance
realtime_feeds = RealTimeFeedAggregator()
