"""
User Features & Auth Service
Google OAuth, JWT, Wishlist, Recommendations
Port: 8011
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import secrets
import hashlib
import json

from fastapi import FastAPI, HTTPException, Header, Query, Body
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
import asyncpg
from redis import asyncio as aioredis
import httpx
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="User Features & Auth Service",
    description="Google OAuth, JWT, Wishlist, Recommendations",
    version="1.0.0"
)

# Configuration
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "user": "admin",
    "password": "password",
    "database": "productdb"
}

REDIS_URL = "redis://redis:6379/3"
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY = 3600 * 24  # 24 hours

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "your-client-id.apps.googleusercontent.com")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "your-client-secret")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8011/auth/callback")

# ============================================================================
# DATA MODELS
# ============================================================================

class RecommendationType(str, Enum):
    """Recommendation types"""
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    TRENDING = "trending"
    PERSONALIZED = "personalized"

class User(BaseModel):
    """User model"""
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: str
    last_login: str

class AuthToken(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str
    user: User
    expires_in: int

class WishlistItem(BaseModel):
    """Wishlist item"""
    product_id: str
    title: str
    price: float
    image_url: str
    added_at: str

class ProductRecommendation(BaseModel):
    """Product recommendation"""
    product_id: str
    title: str
    price: float
    rating: float
    image_url: str
    reason: str
    score: float

class UserProfile(BaseModel):
    """User profile"""
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    wishlist_count: int
    recommendations_count: int
    searches_count: int
    created_at: str
    last_login: str

# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

async def get_db_pool():
    """Get database connection pool"""
    return await asyncpg.create_pool(**DB_CONFIG, min_size=5, max_size=20)

async def get_redis_client():
    """Get Redis client"""
    return await aioredis.from_url(REDIS_URL)

# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_jwt_token(user_id: str, email: str) -> str:
    """Create JWT token"""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRY),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_token_from_header(authorization: Optional[str]) -> str:
    """Extract token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    return parts[1]

# ============================================================================
# GOOGLE OAUTH ENDPOINTS
# ============================================================================

@app.get("/auth/google/login")
async def google_login():
    """Initiate Google OAuth login"""

    state = secrets.token_urlsafe(32)

    redis = await get_redis_client()
    await redis.setex(f"oauth_state:{state}", 600, "pending")
    await redis.close()

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"state={state}"
    )

    logger.info(f"🔐 Initiating Google OAuth login")

    return RedirectResponse(url=google_auth_url)

@app.get("/auth/callback")
async def google_callback(code: str = Query(...), state: str = Query(...)):
    """
    Google OAuth callback

    Exchanges authorization code for tokens
    """
    try:
        # Verify state
        redis = await get_redis_client()
        state_exists = await redis.exists(f"oauth_state:{state}")
        await redis.delete(f"oauth_state:{state}")
        await redis.close()

        if not state_exists:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )

            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code")

            tokens = token_response.json()

            # Get user info
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v1/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )

            user_info = user_info_response.json()

        # Create or update user in database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            user_id = hashlib.md5(user_info['email'].encode()).hexdigest()

            user = await conn.fetchrow("""
                SELECT * FROM users WHERE id = $1
            """, user_id)

            if user:
                # Update last login
                await conn.execute("""
                    UPDATE users SET last_login = NOW()
                    WHERE id = $1
                """, user_id)
            else:
                # Create new user
                await conn.execute("""
                    INSERT INTO users (id, email, name, avatar_url, created_at, last_login)
                    VALUES ($1, $2, $3, $4, NOW(), NOW())
                """, user_id, user_info['email'], user_info.get('name', ''), user_info.get('picture', ''))

        await pool.close()

        # Create JWT token
        jwt_token = create_jwt_token(user_id, user_info['email'])

        logger.info(f"✅ User authenticated: {user_info['email']}")

        # Redirect to frontend with token
        return RedirectResponse(url=f"http://localhost:3000/auth/success?token={jwt_token}")

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
async def login(email: str = Body(...), password: str = Body(...)):
    """
    Email/password login (optional)

    For demo purposes
    """
    try:
        # In production, implement proper password hashing
        pool = await get_db_pool()

        async with pool.acquire() as conn:
            user = await conn.fetchrow("""
                SELECT * FROM users WHERE email = $1
            """, email)

        await pool.close()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create JWT
        jwt_token = create_jwt_token(user['id'], user['email'])

        logger.info(f"✅ Login successful: {email}")

        return AuthToken(
            access_token=jwt_token,
            token_type="bearer",
            user=User(
                id=user['id'],
                email=user['email'],
                name=user['name'],
                avatar_url=user['avatar_url'],
                created_at=user['created_at'].isoformat(),
                last_login=user['last_login'].isoformat()
            ),
            expires_in=JWT_EXPIRY
        )

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/verify")
async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token"""
    try:
        token = get_token_from_header(authorization)
        payload = verify_jwt_token(token)

        logger.info(f"✅ Token verified for user: {payload['sub']}")

        return {"valid": True, "user_id": payload['sub'], "email": payload['email']}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

# ============================================================================
# WISHLIST ENDPOINTS
# ============================================================================

@app.post("/wishlist/add")
async def add_to_wishlist(product_id: str = Body(...), authorization: Optional[str] = Header(None)):
    """Add product to wishlist"""
    try:
        token = get_token_from_header(authorization)
        payload = verify_jwt_token(token)
        user_id = payload['sub']

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            # Get product details
            product = await conn.fetchrow("""
                SELECT id, title, price, image_url FROM products WHERE id = $1
            """, product_id)

            if not product:
                await pool.close()
                raise HTTPException(status_code=404, detail="Product not found")

            # Add to wishlist
            await conn.execute("""
                INSERT INTO wishlist (user_id, product_id, added_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id, product_id) DO NOTHING
            """, user_id, product_id)

        await pool.close()

        logger.info(f"❤️ Product added to wishlist: {user_id}")

        return {"status": "added", "product_id": product_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add to wishlist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/wishlist/remove")
async def remove_from_wishlist(product_id: str = Query(...), authorization: Optional[str] = Header(None)):
    """Remove product from wishlist"""
    try:
        token = get_token_from_header(authorization)
        payload = verify_jwt_token(token)
        user_id = payload['sub']

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM wishlist
                WHERE user_id = $1 AND product_id = $2
            """, user_id, product_id)

        await pool.close()

        logger.info(f"🗑️ Product removed from wishlist: {user_id}")

        return {"status": "removed", "product_id": product_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove from wishlist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wishlist")
async def get_wishlist(authorization: Optional[str] = Header(None)):
    """Get user's wishlist"""
    try:
        token = get_token_from_header(authorization)
        payload = verify_jwt_token(token)
        user_id = payload['sub']

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            items = await conn.fetch("""
                SELECT p.id, p.title, p.price, p.image_url, w.added_at
                FROM wishlist w
                JOIN products p ON w.product_id = p.id
                WHERE w.user_id = $1
                ORDER BY w.added_at DESC
            """, user_id)

        await pool.close()

        wishlist = [
            WishlistItem(
                product_id=str(item['id']),
                title=item['title'],
                price=float(item['price']),
                image_url=item['image_url'] or "",
                added_at=item['added_at'].isoformat()
            )
            for item in items
        ]

        logger.info(f"📋 Retrieved wishlist for {user_id}: {len(wishlist)} items")

        return {"items": wishlist, "count": len(wishlist)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get wishlist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RECOMMENDATIONS ENDPOINTS
# ============================================================================

@app.get("/recommendations")
async def get_recommendations(
    recommendation_type: RecommendationType = RecommendationType.PERSONALIZED,
    limit: int = 20,
    authorization: Optional[str] = Header(None)
):
    """
    Get personalized product recommendations

    Types:
    - collaborative: Based on user similarity
    - content_based: Based on browsing history
    - trending: Popular products
    - personalized: Hybrid approach
    """
    try:
        token = get_token_from_header(authorization)
        payload = verify_jwt_token(token)
        user_id = payload['sub']

        pool = await get_db_pool()

        recommendations = []

        async with pool.acquire() as conn:
            if recommendation_type == RecommendationType.COLLABORATIVE:
                # Find similar users and recommend their liked products
                rows = await conn.fetch(f"""
                    SELECT DISTINCT p.id, p.title, p.price, p.rating, p.image_url,
                           'Similar users liked this' as reason,
                           COUNT(*) as score
                    FROM users u
                    JOIN purchases up ON u.id = up.user_id
                    JOIN products p ON up.product_id = p.id
                    WHERE u.id != $1
                    AND up.user_id IN (
                        SELECT user_id FROM (
                            SELECT u2.id FROM users u2
                            WHERE u2.created_at > NOW() - INTERVAL '1 year'
                            LIMIT 100
                        ) AS similar_users
                    )
                    AND p.id NOT IN (
                        SELECT product_id FROM purchases WHERE user_id = $1
                    )
                    GROUP BY p.id, p.title, p.price, p.rating, p.image_url
                    ORDER BY score DESC
                    LIMIT $2
                """, user_id, limit)

            elif recommendation_type == RecommendationType.CONTENT_BASED:
                # Recommend products similar to ones user viewed
                rows = await conn.fetch(f"""
                    SELECT p.id, p.title, p.price, p.rating, p.image_url,
                           'Similar to your interests' as reason,
                           0.9 as score
                    FROM products p
                    WHERE p.category IN (
                        SELECT DISTINCT category
                        FROM products
                        WHERE id IN (
                            SELECT product_id FROM user_searches
                            WHERE user_id = $1
                        )
                    )
                    AND p.id NOT IN (
                        SELECT product_id FROM purchases WHERE user_id = $1
                    )
                    ORDER BY p.rating DESC
                    LIMIT $2
                """, user_id, limit)

            elif recommendation_type == RecommendationType.TRENDING:
                # Get trending products
                rows = await conn.fetch(f"""
                    SELECT id, title, price, rating, image_url,
                           'Trending now' as reason,
                           reviews_count::float as score
                    FROM products
                    ORDER BY reviews_count DESC, rating DESC
                    LIMIT $1
                """, limit)

            else:  # PERSONALIZED (hybrid)
                # Combine all approaches
                rows = await conn.fetch(f"""
                    SELECT id, title, price, rating, image_url,
                           'Recommended for you' as reason,
                           (rating * 0.5 + (reviews_count::float / 1000) * 0.5) as score
                    FROM products
                    WHERE id NOT IN (
                        SELECT product_id FROM purchases WHERE user_id = $1
                    )
                    AND id NOT IN (
                        SELECT product_id FROM wishlist WHERE user_id = $1
                    )
                    ORDER BY score DESC, rating DESC
                    LIMIT $2
                """, user_id, limit)

        await pool.close()

        recommendations = [
            ProductRecommendation(
                product_id=str(row['id']),
                title=row['title'],
                price=float(row['price']),
                rating=float(row['rating'] or 0),
                image_url=row['image_url'] or "",
                reason=row['reason'],
                score=float(row['score'])
            )
            for row in rows
        ]

        logger.info(f"🎁 Generated {len(recommendations)} recommendations for {user_id}")

        return {"recommendations": recommendations, "type": recommendation_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@app.get("/profile")
async def get_profile(authorization: Optional[str] = Header(None)):
    """Get user profile"""
    try:
        token = get_token_from_header(authorization)
        payload = verify_jwt_token(token)
        user_id = payload['sub']

        pool = await get_db_pool()

        async with pool.acquire() as conn:
            user = await conn.fetchrow("""
                SELECT * FROM users WHERE id = $1
            """, user_id)

            wishlist_count = await conn.fetchval("""
                SELECT COUNT(*) FROM wishlist WHERE user_id = $1
            """, user_id)

            search_count = await conn.fetchval("""
                SELECT COUNT(*) FROM user_searches WHERE user_id = $1
            """, user_id)

        await pool.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        profile = UserProfile(
            id=user['id'],
            email=user['email'],
            name=user['name'],
            avatar_url=user['avatar_url'],
            wishlist_count=wishlist_count or 0,
            recommendations_count=20,
            searches_count=search_count or 0,
            created_at=user['created_at'].isoformat(),
            last_login=user['last_login'].isoformat()
        )

        logger.info(f"👤 Retrieved profile for {user_id}")

        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Service health check"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        await pool.close()

        redis = await get_redis_client()
        await redis.ping()
        await redis.close()

        return {
            "status": "healthy",
            "service": "user-auth",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/")
async def root():
    """Service info"""
    return {
        "service": "User Features & Auth",
        "version": "1.0.0",
        "port": 8011,
        "endpoints": {
            "google_login": "GET /auth/google/login",
            "callback": "GET /auth/callback",
            "login": "POST /auth/login",
            "verify": "GET /auth/verify",
            "profile": "GET /profile",
            "wishlist": "GET /wishlist",
            "wishlist_add": "POST /wishlist/add",
            "wishlist_remove": "DELETE /wishlist/remove",
            "recommendations": "GET /recommendations"
        }
    }

if __name__ == "__main__":
    import uvicorn

    print(f"\n{'='*60}")
    print(f"👤 User Features & Auth Service Starting")
    print(f"   Port: 8011")
    print(f"   Google OAuth, JWT, Wishlist, Recommendations")
    print(f"{'='*60}\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8011,
        log_level="info"
    )
