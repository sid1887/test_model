"""
ML Recommendation Engine (Port 8014) - Phase 7
Collaborative filtering, content-based recommendations, demand forecasting
"""

from fastapi import FastAPI, HTTPException
import logging
from typing import List, Optional, Dict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import asyncio
from core_infrastructure import ShardedServiceBase
from datetime import datetime, timedelta
import json

app = FastAPI(title="ML Recommendation Engine", version="1.0")
logger = logging.getLogger('ml_engine')

# Initialize service
ml_service = ShardedServiceBase(service_name="MLEngine")


# ============================================================================
# COLLABORATIVE FILTERING
# ============================================================================

class CollaborativeFilter:
    """User-user and item-item collaborative filtering"""

    def __init__(self, ml_service: ShardedServiceBase):
        self.ml_service = ml_service
        self.user_item_matrix = None
        self.user_similarity = None
        self.item_similarity = None
        self.last_updated = None

    async def build_matrices(self, days: int = 30):
        """Build user-item interaction matrix from purchase history"""
        try:
            # Get user-product interactions
            query = """
                SELECT u.id as user_id, p.id as product_id,
                       COUNT(*) as interactions,
                       AVG(CASE WHEN pr.rating > 0 THEN pr.rating ELSE NULL END) as avg_rating
                FROM users u
                JOIN purchase_history ph ON u.id = ph.user_id
                JOIN products p ON ph.product_id = p.id
                LEFT JOIN product_reviews pr ON u.id = pr.user_id AND p.id = pr.product_id
                WHERE ph.purchase_date > NOW() - INTERVAL '%d days'
                GROUP BY u.id, p.id
            """ % days

            interactions = await self.ml_service.aggregation(query, ())

            if not interactions:
                logger.warning("No interactions found for matrix building")
                return

            # Build sparse matrix
            users = sorted(set(r['user_id'] for r in interactions))
            products = sorted(set(r['product_id'] for r in interactions))

            user_idx = {uid: i for i, uid in enumerate(users)}
            product_idx = {pid: i for i, pid in enumerate(products)}

            # Create matrix (interactions * rating)
            matrix = np.zeros((len(users), len(products)))
            for row in interactions:
                u_idx = user_idx[row['user_id']]
                p_idx = product_idx[row['product_id']]
                weight = row['interactions'] * (row['avg_rating'] if row['avg_rating'] else 1.0)
                matrix[u_idx, p_idx] = weight

            # Compute similarities
            self.user_item_matrix = matrix
            self.user_similarity = cosine_similarity(matrix)
            self.item_similarity = cosine_similarity(matrix.T)
            self.last_updated = datetime.utcnow()

            logger.info(f"✅ Collaborative filter matrices built: "
                       f"{len(users)} users x {len(products)} products")

        except Exception as e:
            logger.error(f"Matrix building error: {e}")

    async def get_user_based_recommendations(self, user_id: str, n: int = 10) -> List[Dict]:
        """Get recommendations based on similar users"""
        try:
            if self.user_similarity is None:
                return []

            # Find similar users
            query = """
                SELECT id FROM users
                WHERE id != $1 AND active = true
                LIMIT 1000
            """

            similar_users = await self.ml_service.query(user_id, query, (user_id,))

            if not similar_users:
                return []

            # Get their purchases
            rec_query = """
                SELECT DISTINCT p.id, p.name, p.category, p.price, p.rating
                FROM products p
                JOIN purchase_history ph ON p.id = ph.product_id
                WHERE ph.user_id = ANY($1::text[])
                AND p.id NOT IN (
                    SELECT product_id FROM purchase_history WHERE user_id = $2
                )
                ORDER BY p.rating DESC, p.views DESC
                LIMIT $3
            """

            similar_user_ids = [u['id'] for u in similar_users]
            recommendations = await self.ml_service.aggregation(
                rec_query,
                (similar_user_ids, user_id, n)
            )

            return recommendations

        except Exception as e:
            logger.error(f"User-based recommendation error: {e}")
            return []

    async def get_item_based_recommendations(self, product_id: str, n: int = 10) -> List[Dict]:
        """Get recommendations based on similar items"""
        try:
            # Find similar products using cached embeddings
            query = """
                SELECT p.id, p.name, p.category, p.price, p.rating,
                       1 - (e.embedding <-> (
                           SELECT embedding FROM product_embeddings
                           WHERE product_id = $1
                       )) as similarity
                FROM products p
                JOIN product_embeddings e ON p.id = e.product_id
                WHERE p.id != $1
                ORDER BY similarity DESC
                LIMIT $2
            """

            recommendations = await ml_service.aggregation(query, (product_id, n))
            return recommendations

        except Exception as e:
            logger.error(f"Item-based recommendation error: {e}")
            return []


# ============================================================================
# CONTENT-BASED RECOMMENDATIONS
# ============================================================================

class ContentBasedRecommender:
    """Recommend based on product features and user preferences"""

    def __init__(self, ml_service: ShardedServiceBase):
        self.ml_service = ml_service

    async def get_recommendations(self, user_id: str, n: int = 10) -> List[Dict]:
        """Get recommendations based on user's browsing/purchase history"""
        try:
            # Get user's preference profile
            query = """
                SELECT category, COUNT(*) as count, AVG(price) as avg_price
                FROM (
                    SELECT p.category, p.price
                    FROM products p
                    JOIN user_views uv ON p.id = uv.product_id
                    WHERE uv.user_id = $1
                    AND uv.viewed_at > NOW() - INTERVAL '90 days'
                    UNION ALL
                    SELECT p.category, p.price
                    FROM products p
                    JOIN purchase_history ph ON p.id = ph.product_id
                    WHERE ph.user_id = $1
                ) as user_activities
                GROUP BY category
                ORDER BY count DESC
            """

            preferences = await self.ml_service.query(user_id, query, (user_id,))

            if not preferences:
                # Fallback to trending products
                trend_query = """
                    SELECT id, name, category, price, rating, views
                    FROM products
                    WHERE views > 1000 AND rating >= 4.0
                    ORDER BY views DESC
                    LIMIT $1
                """
                return await ml_service.aggregation(trend_query, (n,))

            # Get products matching preferences
            top_categories = [p['category'] for p in preferences[:3]]
            price_range = (
                min(p['avg_price'] for p in preferences) * 0.8,
                max(p['avg_price'] for p in preferences) * 1.2
            )

            rec_query = """
                SELECT id, name, category, price, rating, views
                FROM products
                WHERE category = ANY($1::text[])
                AND price BETWEEN $2 AND $3
                AND id NOT IN (
                    SELECT product_id FROM purchase_history WHERE user_id = $4
                )
                ORDER BY rating DESC, views DESC
                LIMIT $5
            """

            recommendations = await ml_service.aggregation(
                rec_query,
                (top_categories, price_range[0], price_range[1], user_id, n)
            )

            return recommendations

        except Exception as e:
            logger.error(f"Content-based recommendation error: {e}")
            return []


# ============================================================================
# DEMAND FORECASTING
# ============================================================================

class DemandForecaster:
    """Time series forecasting for demand prediction"""

    def __init__(self, ml_service: ShardedServiceBase):
        self.ml_service = ml_service

    async def forecast_demand(self, product_id: str, days_ahead: int = 7) -> List[Dict]:
        """Forecast demand for product over next N days"""
        try:
            # Get historical sales data
            query = """
                SELECT DATE(purchase_date) as date, COUNT(*) as units_sold
                FROM purchase_history
                WHERE product_id = $1
                AND purchase_date > NOW() - INTERVAL '90 days'
                GROUP BY DATE(purchase_date)
                ORDER BY date
            """

            historical_data = await self.ml_service.query(
                product_id, query, (product_id,)
            )

            if not historical_data or len(historical_data) < 7:
                logger.warning(f"Insufficient data for forecasting: {product_id}")
                return []

            # Simple moving average + trend
            sales = np.array([h['units_sold'] for h in historical_data])

            # Calculate 7-day moving average
            window = 7
            moving_avg = np.convolve(sales, np.ones(window)/window, mode='valid')

            # Calculate trend (simple linear regression)
            x = np.arange(len(moving_avg))
            z = np.polyfit(x, moving_avg, 1)
            trend = z[0]

            # Forecast
            last_avg = moving_avg[-1]
            forecasts = []

            for i in range(days_ahead):
                # Linear trend + seasonality
                forecast_value = int(last_avg + trend * i)
                forecast_value = max(0, forecast_value)  # No negative sales

                forecasts.append({
                    'date': (datetime.utcnow() + timedelta(days=i+1)).date().isoformat(),
                    'forecasted_units': forecast_value,
                    'confidence': 0.85 - (i * 0.05)  # Decreasing confidence
                })

            logger.info(f"✅ Forecast generated for {product_id}: "
                       f"avg={last_avg:.0f}, trend={trend:.2f}")

            return forecasts

        except Exception as e:
            logger.error(f"Demand forecasting error: {e}")
            return []

    async def get_inventory_recommendations(self) -> Dict:
        """Recommend inventory levels based on forecasts"""
        try:
            # Get all products with forecasts
            query = """
                SELECT DISTINCT product_id FROM purchase_history
                WHERE purchase_date > NOW() - INTERVAL '90 days'
                ORDER BY RANDOM()
                LIMIT 1000
            """

            products = await self.ml_service.aggregation(query, ())

            recommendations = {}
            for p in (products or []):
                forecasts = await self.forecast_demand(p['product_id'], days_ahead=7)
                if forecasts:
                    avg_forecast = np.mean([f['forecasted_units'] for f in forecasts])
                    recommendations[p['product_id']] = {
                        'recommended_stock': int(avg_forecast * 1.2),  # 20% buffer
                        'forecasted_demand': int(avg_forecast),
                        'forecasts': forecasts
                    }

            return recommendations

        except Exception as e:
            logger.error(f"Inventory recommendation error: {e}")
            return {}


# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

collab_filter = CollaborativeFilter(ml_service)
content_recommender = ContentBasedRecommender(ml_service)
demand_forecaster = DemandForecaster(ml_service)


@app.on_event('startup')
async def startup():
    """Initialize ML service"""
    shard_config = {
        0: {'primary_host': 'postgres-primary-0', 'port': 5432, 'replica_hosts': []},
        1: {'primary_host': 'postgres-primary-1', 'port': 5432, 'replica_hosts': []},
        2: {'primary_host': 'postgres-primary-2', 'port': 5432, 'replica_hosts': []},
        3: {'primary_host': 'postgres-primary-3', 'port': 5432, 'replica_hosts': []},
    }

    await ml_service.initialize(shard_config)

    # Build collaborative filtering matrices periodically
    asyncio.create_task(update_collab_matrices())

    logger.info("✅ ML Recommendation Engine started")


@app.on_event('shutdown')
async def shutdown():
    """Cleanup"""
    await ml_service.shutdown()


async def update_collab_matrices():
    """Background task: Update collaboration matrices every 24 hours"""
    while True:
        try:
            await asyncio.sleep(86400)  # 24 hours
            await collab_filter.build_matrices()
        except Exception as e:
            logger.error(f"Matrix update error: {e}")


# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@app.get('/recommendations/for-you/{user_id}')
async def get_for_you_recommendations(user_id: str, count: int = 10):
    """Get personalized recommendations"""
    try:
        # Combine collaborative + content-based
        collab_recs = await collab_filter.get_user_based_recommendations(user_id, count//2)
        content_recs = await content_recommender.get_recommendations(user_id, count//2)

        # Merge and deduplicate
        all_recs = collab_recs + content_recs
        seen_ids = set()
        merged = []
        for rec in all_recs:
            if rec['id'] not in seen_ids:
                merged.append(rec)
                seen_ids.add(rec['id'])

        return {
            'recommendations': merged[:count],
            'algorithm': 'hybrid_collab_content',
            'count': len(merged[:count])
        }

    except Exception as e:
        logger.error(f"For-you recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/recommendations/similar/{product_id}')
async def get_similar_products(product_id: str, count: int = 10):
    """Get similar products (item-based collaborative filtering)"""
    try:
        recommendations = await collab_filter.get_item_based_recommendations(
            product_id, count
        )

        return {
            'product_id': product_id,
            'similar_products': recommendations,
            'algorithm': 'item_based_collab',
            'count': len(recommendations)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/recommendations/trending')
async def get_trending_recommendations(category: Optional[str] = None, count: int = 20):
    """Get trending products (content-based)"""
    try:
        category_filter = f"AND category = '{category}'" if category else ""

        query = f"""
            SELECT id, name, category, price, rating, views,
                   views + (SELECT COUNT(*) FROM purchase_history
                           WHERE product_id = products.id
                           AND purchase_date > NOW() - INTERVAL '7 days') as trend_score
            FROM products
            WHERE views > 100 {category_filter}
            ORDER BY trend_score DESC
            LIMIT $1
        """

        results = await ml_service.aggregation(query, (count,))

        return {
            'category': category or 'all',
            'trending': results,
            'count': len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/forecast/demand/{product_id}')
async def get_demand_forecast(product_id: str, days_ahead: int = 7):
    """Get demand forecast for product"""
    try:
        forecasts = await demand_forecaster.forecast_demand(product_id, days_ahead)

        return {
            'product_id': product_id,
            'forecasts': forecasts,
            'days_ahead': days_ahead
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/inventory/recommendations')
async def get_inventory_recommendations():
    """Get inventory recommendations for all products"""
    try:
        recommendations = await demand_forecaster.get_inventory_recommendations()

        return {
            'products': len(recommendations),
            'recommendations': recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/update-matrices')
async def trigger_matrix_update():
    """Manually trigger collaborative filter matrix update"""
    try:
        await collab_filter.build_matrices()
        return {'status': 'matrices_updated'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/stats')
async def get_ml_stats():
    """Get ML engine statistics"""
    return {
        'service': 'ml_engine',
        'matrices_updated': collab_filter.last_updated.isoformat() if collab_filter.last_updated else None,
        'service_metrics': ml_service.get_metrics()
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8014)
