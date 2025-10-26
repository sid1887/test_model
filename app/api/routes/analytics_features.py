"""
Analytics & Forecasting API Endpoints
Provides price trends, forecasting, and retailer analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.analytics import (
    PriceForecast, SentimentAnalysis, ForecastValidation, SentimentTrend
)


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class PriceDataPoint(BaseModel):
    """Single price data point for charts"""
    timestamp: datetime
    price: float
    retailer_id: Optional[int]
    retailer_name: Optional[str]


class TrendAnalysis(BaseModel):
    """Price trend analysis"""
    direction: str  # increasing, decreasing, stable
    strength_percent: float
    period_days: int
    start_price: float
    end_price: float
    change_percent: float


class ForecastPrediction(BaseModel):
    """Single forecast prediction"""
    date: datetime
    predicted_price: float
    lower_bound: float
    upper_bound: float
    confidence: float


class ProductForecastResponse(BaseModel):
    """Response schema for product forecast"""
    product_id: int
    current_price: float
    forecast_horizon_days: int
    model_type: str
    confidence_interval: float
    
    predictions: List[ForecastPrediction]
    trend_analysis: TrendAnalysis
    
    best_buy_date: Optional[datetime]
    best_buy_price: Optional[float]
    recommendation: Optional[str]
    
    # Accuracy metrics
    mae: Optional[float]
    rmse: Optional[float]
    
    generated_at: datetime


class PriceTrendResponse(BaseModel):
    """Response schema for price trends"""
    product_id: int
    period_days: int
    data_points: List[PriceDataPoint]
    
    current_price: float
    avg_price: float
    min_price: float
    max_price: float
    price_volatility: float
    
    trend: TrendAnalysis


class RetailerComparisonItem(BaseModel):
    """Retailer comparison data"""
    retailer_id: int
    retailer_name: str
    avg_price: float
    product_count: int
    availability_rate: float
    avg_response_time_ms: Optional[float]
    competitiveness_score: float


class RetailerComparisonResponse(BaseModel):
    """Response schema for retailer comparison"""
    retailers: List[RetailerComparisonItem]
    best_overall: Optional[int]  # retailer_id
    best_price: Optional[int]
    best_availability: Optional[int]


class SentimentScore(BaseModel):
    """Sentiment analysis scores"""
    score: float  # -1 to 1
    label: str  # positive, negative, neutral
    confidence: float


class SentimentResponse(BaseModel):
    """Response schema for sentiment analysis"""
    product_id: int
    total_reviews: int
    processed_reviews: int
    
    overall_sentiment: SentimentScore
    positive_keywords: List[str]
    negative_keywords: List[str]
    
    sentiment_trend: Optional[str]  # improving, declining, stable
    
    analyzed_at: datetime


class AnalyticsOverviewResponse(BaseModel):
    """Dashboard overview statistics"""
    total_products: int
    total_retailers: int
    total_price_points: int
    
    active_alerts: int
    alerts_fired_today: int
    
    smart_lists: int
    comparisons_today: int
    
    forecasts_available: int
    avg_forecast_accuracy: Optional[float]
    
    top_trending_products: List[Dict[str, Any]]
    recent_price_drops: List[Dict[str, Any]]


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_user_id():
    """Mock function - replace with actual auth"""
    return 1


def calculate_trend_analysis(price_history: List[tuple]) -> TrendAnalysis:
    """Calculate trend from price history [(timestamp, price)]"""
    if len(price_history) < 2:
        return TrendAnalysis(
            direction="stable",
            strength_percent=0.0,
            period_days=0,
            start_price=price_history[0][1] if price_history else 0,
            end_price=price_history[0][1] if price_history else 0,
            change_percent=0.0
        )
    
    start_price = price_history[0][1]
    end_price = price_history[-1][1]
    change_percent = ((end_price - start_price) / start_price * 100) if start_price > 0 else 0
    
    period_days = (price_history[-1][0] - price_history[0][0]).days
    
    # Determine direction
    if abs(change_percent) < 5:
        direction = "stable"
    elif change_percent > 0:
        direction = "increasing"
    else:
        direction = "decreasing"
    
    return TrendAnalysis(
        direction=direction,
        strength_percent=abs(change_percent),
        period_days=period_days,
        start_price=start_price,
        end_price=end_price,
        change_percent=change_percent
    )


# ============================================================================
# Analytics Endpoints
# ============================================================================

@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    db: Session = Depends(get_db)
):
    """
    Get analytics dashboard overview
    
    - Summary statistics across all features
    - Trending products and recent price drops
    - Alert and comparison activity
    """
    user_id = get_current_user_id()
    
    # TODO: Replace with actual queries when models are imported
    # For now, return mock data structure
    
    from app.models.alert import PriceAlert, AlertStatus, AlertEvent, AlertEventType
    from app.models.smart_list import SmartList, ListCompareJob, CompareJobStatus
    
    # Count statistics
    # total_products = db.query(func.count(Product.id)).scalar() or 0
    # total_retailers = db.query(func.count(Retailer.id)).scalar() or 0
    total_products = 0
    total_retailers = 0
    total_price_points = 0
    
    # Alert statistics
    active_alerts = db.query(func.count(PriceAlert.id)) \
        .filter(PriceAlert.user_id == user_id) \
        .filter(PriceAlert.status == AlertStatus.ACTIVE) \
        .scalar() or 0
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    alerts_fired_today = db.query(func.count(AlertEvent.id)) \
        .join(PriceAlert) \
        .filter(PriceAlert.user_id == user_id) \
        .filter(AlertEvent.event_type == AlertEventType.FIRED) \
        .filter(AlertEvent.created_at >= today) \
        .scalar() or 0
    
    # Smart list statistics
    smart_lists = db.query(func.count(SmartList.id)) \
        .filter(SmartList.user_id == user_id) \
        .scalar() or 0
    
    comparisons_today = db.query(func.count(ListCompareJob.id)) \
        .filter(ListCompareJob.user_id == user_id) \
        .filter(ListCompareJob.created_at >= today) \
        .scalar() or 0
    
    # Forecast statistics
    forecasts_available = db.query(func.count(PriceForecast.id)) \
        .filter(PriceForecast.is_active == True) \
        .scalar() or 0
    
    # Calculate average forecast accuracy from validations
    avg_accuracy = db.query(func.avg(ForecastValidation.accuracy_band_10pct)) \
        .scalar() or None
    
    return {
        "total_products": total_products,
        "total_retailers": total_retailers,
        "total_price_points": total_price_points,
        "active_alerts": active_alerts,
        "alerts_fired_today": alerts_fired_today,
        "smart_lists": smart_lists,
        "comparisons_today": comparisons_today,
        "forecasts_available": forecasts_available,
        "avg_forecast_accuracy": avg_accuracy,
        "top_trending_products": [],  # TODO: Implement trending logic
        "recent_price_drops": []  # TODO: Implement price drop detection
    }


@router.get("/product/{product_id}/trends", response_model=PriceTrendResponse)
async def get_product_price_trends(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Historical period in days"),
    retailer_id: Optional[int] = Query(None, description="Filter by retailer"),
    db: Session = Depends(get_db)
):
    """
    Get product price trends over time
    
    - Historical price data points
    - Statistical analysis (avg, min, max, volatility)
    - Trend direction and strength
    """
    # TODO: Query actual price history from database
    # For now, create structure
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Mock data - replace with actual query
    data_points = []
    
    # Calculate statistics
    if data_points:
        prices = [dp.price for dp in data_points]
        current_price = prices[-1]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Calculate volatility (standard deviation)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        volatility = variance ** 0.5
        
        # Calculate trend
        price_history = [(dp.timestamp, dp.price) for dp in data_points]
        trend = calculate_trend_analysis(price_history)
    else:
        current_price = 0
        avg_price = 0
        min_price = 0
        max_price = 0
        volatility = 0
        trend = TrendAnalysis(
            direction="stable",
            strength_percent=0,
            period_days=days,
            start_price=0,
            end_price=0,
            change_percent=0
        )
    
    return {
        "product_id": product_id,
        "period_days": days,
        "data_points": data_points,
        "current_price": current_price,
        "avg_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "price_volatility": volatility,
        "trend": trend
    }


@router.get("/product/{product_id}/forecast", response_model=ProductForecastResponse)
async def get_product_forecast(
    product_id: int,
    horizon_days: int = Query(30, ge=7, le=90, description="Forecast horizon"),
    db: Session = Depends(get_db)
):
    """
    Get price forecast for product
    
    - Prophet/ARIMA predictions
    - Confidence intervals
    - Best buy date recommendation
    - Accuracy metrics
    """
    # Get latest forecast
    forecast = db.query(PriceForecast) \
        .filter(PriceForecast.product_id == product_id) \
        .filter(PriceForecast.is_active == True) \
        .filter(PriceForecast.forecast_horizon_days >= horizon_days) \
        .order_by(desc(PriceForecast.created_at)) \
        .first()
    
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No forecast available for this product"
        )
    
    # Parse forecast predictions from JSON
    predictions_data = forecast.predictions
    predictions = []
    
    if isinstance(predictions_data, list):
        for pred in predictions_data[:horizon_days]:
            predictions.append(ForecastPrediction(
                date=pred.get("date"),
                predicted_price=pred.get("yhat", 0),
                lower_bound=pred.get("yhat_lower", 0),
                upper_bound=pred.get("yhat_upper", 0),
                confidence=forecast.confidence_interval
            ))
    
    # Calculate trend from predictions
    if predictions:
        price_history = [(p.date, p.predicted_price) for p in predictions]
        trend_analysis = calculate_trend_analysis(price_history)
    else:
        trend_analysis = TrendAnalysis(
            direction="stable",
            strength_percent=0,
            period_days=horizon_days,
            start_price=forecast.current_price or 0,
            end_price=forecast.predicted_30day_price or 0,
            change_percent=0
        )
    
    # Get validation metrics if available
    validation = db.query(ForecastValidation) \
        .filter(ForecastValidation.forecast_id == forecast.id) \
        .order_by(desc(ForecastValidation.created_at)) \
        .first()
    
    return {
        "product_id": product_id,
        "current_price": forecast.current_price or 0,
        "forecast_horizon_days": horizon_days,
        "model_type": forecast.model_version,
        "confidence_interval": forecast.confidence_interval,
        "predictions": predictions,
        "trend_analysis": trend_analysis,
        "best_buy_date": forecast.best_buy_date,
        "best_buy_price": forecast.best_buy_price,
        "recommendation": forecast.recommendation,
        "mae": validation.mae if validation else None,
        "rmse": validation.rmse if validation else None,
        "generated_at": forecast.created_at
    }


@router.get("/retailers/comparison", response_model=RetailerComparisonResponse)
async def get_retailer_comparison(
    category: Optional[str] = Query(None, description="Filter by product category"),
    db: Session = Depends(get_db)
):
    """
    Compare retailer performance
    
    - Average prices across retailers
    - Availability rates
    - Response time metrics
    - Competitiveness scoring
    """
    # TODO: Implement actual retailer comparison logic
    # This requires joining products, prices, and retailer metrics
    
    retailers = []
    
    return {
        "retailers": retailers,
        "best_overall": None,
        "best_price": None,
        "best_availability": None
    }


@router.get("/sentiment/{product_id}", response_model=SentimentResponse)
async def get_product_sentiment(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get product sentiment analysis
    
    - Overall sentiment score from reviews
    - Positive/negative keywords
    - Sentiment trends over time
    """
    # Get latest sentiment analysis
    sentiment = db.query(SentimentAnalysis) \
        .filter(SentimentAnalysis.product_id == product_id) \
        .filter(SentimentAnalysis.is_active == True) \
        .order_by(desc(SentimentAnalysis.created_at)) \
        .first()
    
    if not sentiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sentiment analysis available for this product"
        )
    
    # Get sentiment trend
    recent_trends = db.query(SentimentTrend) \
        .filter(SentimentTrend.product_id == product_id) \
        .order_by(desc(SentimentTrend.period_end)) \
        .limit(2) \
        .all()
    
    sentiment_trend = None
    if len(recent_trends) >= 2:
        sentiment_trend = recent_trends[0].trend_direction
    
    return {
        "product_id": product_id,
        "total_reviews": sentiment.total_reviews,
        "processed_reviews": sentiment.processed_reviews,
        "overall_sentiment": {
            "score": sentiment.sentiment_score,
            "label": sentiment.sentiment_label,
            "confidence": sentiment.confidence
        },
        "positive_keywords": sentiment.positive_keywords or [],
        "negative_keywords": sentiment.negative_keywords or [],
        "sentiment_trend": sentiment_trend,
        "analyzed_at": sentiment.created_at
    }


@router.post("/product/{product_id}/forecast/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_forecast(
    product_id: int,
    horizon_days: int = Query(30, ge=7, le=90),
    model_type: str = Query("prophet", regex="^(prophet|arima|linear)$"),
    db: Session = Depends(get_db)
):
    """
    Generate new forecast for product
    
    - Triggers background Celery task
    - Uses Prophet or ARIMA model
    - Returns job ID for tracking
    """
    # TODO: Trigger Celery task
    # from app.workers.forecast_worker import generate_product_forecast
    # task = generate_product_forecast.apply_async(
    #     args=[product_id, horizon_days, model_type]
    # )
    
    return {
        "message": "Forecast generation started",
        "product_id": product_id,
        "task_id": "mock-task-id",
        "status": "queued"
    }


@router.post("/sentiment/{product_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_sentiment(
    product_id: int,
    force_reanalyze: bool = Query(False, description="Force re-analysis"),
    db: Session = Depends(get_db)
):
    """
    Analyze product sentiment from reviews
    
    - Triggers background Celery task
    - Uses HuggingFace sentiment models
    - Returns job ID for tracking
    """
    # Check if recent analysis exists
    if not force_reanalyze:
        recent = db.query(SentimentAnalysis) \
            .filter(SentimentAnalysis.product_id == product_id) \
            .filter(SentimentAnalysis.created_at >= datetime.utcnow() - timedelta(days=7)) \
            .first()
        
        if recent:
            return {
                "message": "Recent analysis exists",
                "product_id": product_id,
                "analysis_id": recent.id,
                "analyzed_at": recent.created_at
            }
    
    # TODO: Trigger Celery task
    # from app.workers.sentiment_worker import analyze_product_sentiment
    # task = analyze_product_sentiment.apply_async(args=[product_id])
    
    return {
        "message": "Sentiment analysis started",
        "product_id": product_id,
        "task_id": "mock-task-id",
        "status": "queued"
    }


@router.get("/anomalies", response_model=List[Dict[str, Any]])
async def get_price_anomalies(
    days: int = Query(7, ge=1, le=30),
    severity_threshold: float = Query(0.5, ge=0, le=1),
    db: Session = Depends(get_db)
):
    """
    Get detected price anomalies
    
    - Unusual price spikes or drops
    - Statistical outliers
    - Pattern breaks
    """
    # TODO: Implement anomaly detection
    # from app.models.analytics import PriceAnomaly
    
    return []


@router.get("/products/trending", response_model=List[Dict[str, Any]])
async def get_trending_products(
    period: str = Query("week", regex="^(day|week|month)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get trending products
    
    - Based on price changes, searches, alerts
    - Sorted by trending score
    """
    # TODO: Implement trending logic based on user activity
    
    return []
