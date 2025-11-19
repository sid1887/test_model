"""
Multi-Source Integration Service
Integrates news (NewsAPI), cryptocurrency (CoinGecko), and stock data (yfinance)
Fetches, normalizes, and stores real-time market data
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import aiohttp
import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Keys
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")  # Get from environment
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Database
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "database": os.getenv("DB_NAME", "cumpair"),
}

# ============================================================================
# MODELS
# ============================================================================

class NewsArticleIngest(BaseModel):
    title: str
    content: str
    source: str
    url: str
    category: str = "general"
    published_at: Optional[str] = None

class CryptoPriceUpdate(BaseModel):
    symbol: str
    name: str
    price: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None

class StockPriceUpdate(BaseModel):
    ticker: str
    company_name: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    trading_date: str

class FetchNewsRequest(BaseModel):
    query: str
    category: Optional[str] = None
    language: str = "en"
    sort_by: str = "publishedAt"  # 'relevancy', 'popularity', 'publishedAt'
    page_size: int = 50

class FetchCryptoRequest(BaseModel):
    symbols: Optional[List[str]] = None  # If None, fetch top 50
    vs_currency: str = "usd"

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Multi-Source Integration Service",
    description="Fetch and integrate news, crypto, and stock data from external APIs",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(**DB_CONFIG)
        logger.info("✅ Database pool created")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()

async def execute_query(query: str, *args):
    """Execute a database query"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    async with db_pool.acquire() as conn:
        return await conn.fetch(query, *args)

async def execute_insert(query: str, *args):
    """Execute insert and return result"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Database not connected")

    async with db_pool.acquire() as conn:
        return await conn.fetch(query, *args)

# ============================================================================
# PHASE 4.1: NEWS INTEGRATION (NewsAPI)
# ============================================================================

@app.post("/api/news/fetch")
async def fetch_news(request: FetchNewsRequest, background_tasks: BackgroundTasks):
    """
    Fetch news articles from NewsAPI and store in database
    """
    try:
        if not NEWSAPI_KEY:
            raise HTTPException(status_code=500, detail="NewsAPI key not configured")

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": request.query,
            "language": request.language,
            "sortBy": request.sort_by,
            "pageSize": request.page_size,
            "apiKey": NEWSAPI_KEY
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="NewsAPI error")

                data = await response.json()
                articles = data.get("articles", [])

        # Store articles in database (background task)
        background_tasks.add_task(store_news_batch, articles, request.category)

        logger.info(f"✅ Fetched {len(articles)} news articles for '{request.query}'")

        return {
            "status": "success",
            "articles_fetched": len(articles),
            "articles": articles[:5]  # Return first 5 for preview
        }

    except Exception as e:
        logger.error(f"❌ News fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def store_news_batch(articles: List[Dict], category: Optional[str] = None):
    """Store news articles in database"""
    if not db_pool:
        logger.error("Database not available")
        return

    try:
        for article in articles:
            query = """
                INSERT INTO news_articles
                (title, content, source, url, category, published_at, ingested_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (url) DO NOTHING
            """

            try:
                await execute_insert(
                    query,
                    article.get("title", "")[:500],
                    article.get("description", ""),
                    article.get("source", {}).get("name", "Unknown"),
                    article.get("url", ""),
                    category or "general",
                    article.get("publishedAt")
                )
            except Exception as e:
                logger.warning(f"Failed to store article: {e}")

        logger.info(f"✅ Stored {len(articles)} news articles")
    except Exception as e:
        logger.error(f"❌ Store news batch error: {e}")

@app.get("/api/news/trending")
async def get_trending_news(days: int = 7, limit: int = 20):
    """Get trending news articles"""
    try:
        query = """
            SELECT id, title, content, source, url, category, published_at, ingested_at
            FROM news_articles
            WHERE published_at > NOW() - INTERVAL '1 day' * $1
            ORDER BY published_at DESC
            LIMIT $2
        """

        articles = await execute_query(query, days, limit)

        return {
            "trending_count": len(articles),
            "articles": articles
        }
    except Exception as e:
        logger.error(f"❌ Trending news error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/search")
async def search_news(q: str, limit: int = 20):
    """Full-text search for news articles"""
    try:
        query = """
            SELECT id, title, content, source, url, category, published_at
            FROM news_articles
            WHERE to_tsvector('english', title || ' ' || COALESCE(content, '')) @@
                  plainto_tsquery('english', $1)
            ORDER BY published_at DESC
            LIMIT $2
        """

        articles = await execute_query(query, q, limit)

        return {
            "query": q,
            "results": len(articles),
            "articles": articles
        }
    except Exception as e:
        logger.error(f"❌ News search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 4.2: CRYPTOCURRENCY DATA (CoinGecko API)
# ============================================================================

@app.post("/api/crypto/fetch")
async def fetch_crypto(request: FetchCryptoRequest, background_tasks: BackgroundTasks):
    """
    Fetch cryptocurrency data from CoinGecko
    CoinGecko API is free and doesn't require auth
    """
    try:
        # Get top cryptocurrencies if not specified
        if not request.symbols:
            symbols = ["bitcoin", "ethereum", "cardano", "solana", "ripple",
                      "polkadot", "dogecoin", "avalanche-2", "chainlink", "litecoin"]
        else:
            symbols = request.symbols

        url = f"{COINGECKO_API}/simple/price"
        params = {
            "ids": ",".join(symbols),
            "vs_currencies": request.vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
            "include_last_updated_at": "true"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="CoinGecko API error")

                data = await response.json()

        # Store in database (background)
        background_tasks.add_task(store_crypto_batch, data, request.vs_currency)

        logger.info(f"✅ Fetched {len(data)} crypto prices")

        return {
            "status": "success",
            "crypto_count": len(data),
            "prices": data
        }

    except Exception as e:
        logger.error(f"❌ Crypto fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def store_crypto_batch(prices_data: Dict, currency: str = "usd"):
    """Store cryptocurrency prices in database"""
    if not db_pool:
        return

    try:
        # Map CoinGecko IDs to symbols
        id_to_symbol = {
            "bitcoin": "BTC", "ethereum": "ETH", "cardano": "ADA",
            "solana": "SOL", "ripple": "XRP", "polkadot": "DOT",
            "dogecoin": "DOGE", "avalanche-2": "AVAX", "chainlink": "LINK",
            "litecoin": "LTC"
        }

        for crypto_id, prices in prices_data.items():
            symbol = id_to_symbol.get(crypto_id, crypto_id.upper())

            query = """
                INSERT INTO crypto_prices
                (symbol, price, market_cap, volume_24h, change_24h, source, recorded_at)
                VALUES ($1, $2, $3, $4, $5, 'coingecko', NOW())
            """

            try:
                market_cap_key = f"market_cap_{currency}"
                volume_key = f"{currency}_24h_vol"
                change_key = f"{currency}_24h_change"

                await execute_insert(
                    query,
                    symbol,
                    prices.get(currency, 0),
                    prices.get(market_cap_key),
                    prices.get(volume_key),
                    prices.get(change_key)
                )
            except Exception as e:
                logger.warning(f"Failed to store {symbol}: {e}")

        logger.info(f"✅ Stored {len(prices_data)} crypto prices")
    except Exception as e:
        logger.error(f"❌ Store crypto batch error: {e}")

@app.get("/api/crypto/prices/{symbol}")
async def get_crypto_price(symbol: str, hours: int = 24):
    """Get cryptocurrency price history"""
    try:
        query = """
            SELECT symbol, price, market_cap, volume_24h, change_24h, recorded_at
            FROM crypto_prices
            WHERE symbol = $1
            AND recorded_at > NOW() - INTERVAL '1 hour' * $2
            ORDER BY recorded_at DESC
            LIMIT 100
        """

        prices = await execute_query(query, symbol.upper(), hours)

        if not prices:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        # Calculate current and previous
        current = prices[0]
        previous = prices[-1] if len(prices) > 1 else current

        return {
            "symbol": symbol.upper(),
            "current_price": current['price'],
            "market_cap": current['market_cap'],
            "volume_24h": current['volume_24h'],
            "change_24h": current['change_24h'],
            "price_history": prices
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Crypto price error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crypto/top")
async def get_top_crypto(limit: int = 20):
    """Get top cryptocurrencies by market cap"""
    try:
        query = """
            SELECT DISTINCT ON (symbol) symbol, price, market_cap, volume_24h, change_24h
            FROM crypto_prices
            WHERE recorded_at > NOW() - INTERVAL '1 hour'
            AND market_cap IS NOT NULL
            ORDER BY symbol, market_cap DESC NULLS LAST
            LIMIT $1
        """

        cryptos = await execute_query(query, limit)

        return {
            "top_count": len(cryptos),
            "cryptos": cryptos
        }
    except Exception as e:
        logger.error(f"❌ Top crypto error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PHASE 4.3: STOCK DATA (yfinance via FastAPI wrapper)
# ============================================================================

@app.post("/api/stocks/fetch")
async def fetch_stock(ticker: str, background_tasks: BackgroundTasks):
    """
    Fetch stock data using yfinance
    """
    try:
        try:
            import yfinance as yf
        except ImportError:
            raise HTTPException(status_code=500, detail="yfinance not installed")

        # Fetch stock data
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period="1d")

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

        latest = hist.iloc[-1]

        stock_data = {
            "ticker": ticker.upper(),
            "company_name": stock.info.get("longName", ticker),
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "close": float(latest["Close"]),
            "volume": int(latest["Volume"]),
            "trading_date": hist.index[-1].strftime("%Y-%m-%d")
        }

        # Store in database
        background_tasks.add_task(store_stock_price, stock_data)

        logger.info(f"✅ Fetched stock: {ticker}")

        return {
            "status": "success",
            "stock": stock_data
        }

    except Exception as e:
        logger.error(f"❌ Stock fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def store_stock_price(stock_data: Dict):
    """Store stock price in database"""
    if not db_pool:
        return

    try:
        query = """
            INSERT INTO stock_prices
            (ticker, company_name, open, high, low, close, volume,
             trading_date, source, recorded_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'yfinance', NOW())
            ON CONFLICT (ticker, trading_date) DO NOTHING
        """

        await execute_insert(
            query,
            stock_data['ticker'],
            stock_data['company_name'],
            stock_data['open'],
            stock_data['high'],
            stock_data['low'],
            stock_data['close'],
            stock_data['volume'],
            stock_data['trading_date']
        )

        logger.info(f"✅ Stored stock: {stock_data['ticker']}")
    except Exception as e:
        logger.error(f"❌ Store stock error: {e}")

@app.get("/api/stocks/{ticker}")
async def get_stock_price(ticker: str, days: int = 30):
    """Get stock price history"""
    try:
        query = """
            SELECT ticker, company_name, open, high, low, close, volume, trading_date
            FROM stock_prices
            WHERE ticker = $1
            AND trading_date > NOW()::date - $2
            ORDER BY trading_date DESC
            LIMIT 100
        """

        prices = await execute_query(query, ticker.upper(), days)

        if not prices:
            raise HTTPException(status_code=404, detail=f"No data for {ticker}")

        return {
            "ticker": ticker.upper(),
            "price_history": prices
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Stock price error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "healthy" if db_pool else "unhealthy"
    news_status = "configured" if NEWSAPI_KEY else "not_configured"

    return {
        "status": "healthy",
        "database": db_status,
        "newsapi": news_status,
        "coingecko": "available",
        "yfinance": "available"
    }

# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_message():
    logger.info("""
    ╔════════════════════════════════════════════════╗
    ║  MULTI-SOURCE INTEGRATION SERVICE STARTED      ║
    ║  News (NewsAPI), Crypto (CoinGecko),           ║
    ║  Stocks (yfinance)                             ║
    ╚════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008, workers=4)
