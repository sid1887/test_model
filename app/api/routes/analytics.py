"""
API endpoints for enhanced data pipelines and pricing analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import asyncio
import logging

from app.core.database import get_db
from app.models.product import Product
from app.models.price_comparison import PriceComparison
from app.models.analytics import PriceForecast, SentimentAnalysis, ForecastValidation
from app.services.data_pipeline import data_pipeline_service, NormalizationMethod, ScoringWeights
from app.services.pricing_analytics import pricing_analytics_service, SentimentModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Data Pipelines & Analytics"])

# Pydantic models for requests/responses
class ValueScoringRequest(BaseModel):
    product_ids: Optional[List[int]] = None
    weights: Optional[Dict[str, float]] = None
    weight_preset: Optional[str] = Field(None, description="balanced, price_focused, quality_focused")
    normalization_method: Optional[str] = Field("min_max", description="min_max, z_score, robust")

class ValueScoringResponse(BaseModel):
    products: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time_ms: float

class PriceForecastRequest(BaseModel):
    product_id: int
    forecast_days: Optional[int] = Field(30, ge=7, le=90)
    confidence_interval: Optional[float] = Field(0.8, ge=0.5, le=0.99)

class PriceForecastResponse(BaseModel):
    forecast_data: Dict[str, Any]
    validation_metrics: Dict[str, Any]
    processing_time_ms: float

class SentimentAnalysisRequest(BaseModel):
    product_id: int
    model: Optional[str] = Field("ensemble", description="vader, textblob, huggingface, ensemble")
    include_topics: Optional[bool] = True
    review_sources: Optional[List[str]] = None

class SentimentAnalysisResponse(BaseModel):
    sentiment_data: Dict[str, Any]
    processing_time_ms: float

class FeatureEngineeringRequest(BaseModel):
    product_ids: Optional[List[int]] = None
    categorical_features: List[str] = Field(default=["brand", "category", "source_name"])
    encoding_method: Optional[str] = Field("onehot", description="onehot, label")

@router.post("/value-scoring", response_model=ValueScoringResponse)
async def calculate_value_scores(
    request: ValueScoringRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate enhanced value scores for products using advanced data pipelines
    """
    start_time = datetime.now()
    
    try:
        # Fetch product data with price comparisons
        query = select(Product).options(
            selectinload(Product.price_comparisons)
        )
        
        if request.product_ids:
            query = query.where(Product.id.in_(request.product_ids))
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found")
        
        # Convert to dictionaries with price data
        product_data = []
        for product in products:
            # Get latest price comparison data
            latest_prices = sorted(
                product.price_comparisons, 
                key=lambda x: x.price_updated_at or datetime.min, 
                reverse=True
            )
            
            if latest_prices:
                price_data = latest_prices[0]
                product_dict = {
                    'id': product.id,
                    'name': product.name,
                    'brand': product.brand,
                    'category': product.category,
                    'price': float(price_data.price) if price_data.price else 0,
                    'rating': float(price_data.rating) if price_data.rating else 0,
                    'review_count': price_data.review_count or 0,
                    'in_stock': price_data.in_stock or False,
                    'source_name': price_data.source_name,
                    'specifications': product.specifications or {}
                }
                product_data.append(product_dict)
        
        if not product_data:
            raise HTTPException(status_code=404, detail="No products with price data found")
        
        # Determine weights
        weights = request.weights
        if request.weight_preset:
            if request.weight_preset == "balanced":
                weights = ScoringWeights.BALANCED.value
            elif request.weight_preset == "price_focused":
                weights = ScoringWeights.PRICE_FOCUSED.value
            elif request.weight_preset == "quality_focused":
                weights = ScoringWeights.QUALITY_FOCUSED.value
        
        if not weights:
            weights = ScoringWeights.BALANCED.value
        
        # Calculate value scores
        enhanced_products = await data_pipeline_service.calculate_value_score(
            product_data, weights
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ValueScoringResponse(
            products=enhanced_products,
            metadata={
                'total_products': len(enhanced_products),
                'weights_used': weights,
                'normalization_method': request.normalization_method,
                'timestamp': datetime.now().isoformat()
            },
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Value scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Value scoring error: {str(e)}")

@router.post("/price-forecast", response_model=PriceForecastResponse)
async def generate_price_forecast(
    request: PriceForecastRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate price forecasts using Prophet model
    """
    start_time = datetime.now()
    
    try:
        # Verify product exists
        product_query = select(Product).where(Product.id == request.product_id)
        result = await db.execute(product_query)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Generate forecast
        forecast_data = await pricing_analytics_service.generate_price_forecast(
            product_id=request.product_id,
            db=db,
            forecast_days=request.forecast_days,
            confidence_interval=request.confidence_interval
        )
        
        # Store forecast in database (background task)
        background_tasks.add_task(
            store_price_forecast,
            forecast_data,
            db
        )
        
        # Generate validation metrics
        validation_metrics = await pricing_analytics_service.validate_forecast_accuracy(
            product_id=request.product_id,
            db=db,
            validation_days=min(request.forecast_days, 14)
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return PriceForecastResponse(
            forecast_data=forecast_data,
            validation_metrics=validation_metrics,
            processing_time_ms=round(processing_time, 2)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Price forecasting failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")

@router.post("/sentiment-analysis", response_model=SentimentAnalysisResponse)
async def analyze_product_sentiment(
    request: SentimentAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze product sentiment from reviews using NLP models
    """
    start_time = datetime.now()
    
    try:
        # Verify product exists and fetch reviews
        product_query = select(Product).options(
            selectinload(Product.price_comparisons)
        ).where(Product.id == request.product_id)
        
        result = await db.execute(product_query)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Extract review texts from price comparisons and additional data
        reviews = []
        for price_comp in product.price_comparisons:
            if price_comp.additional_data:
                review_text = price_comp.additional_data.get('review_text')
                if review_text:
                    reviews.append(review_text)
        
        # Mock some sample reviews if none found (for demo purposes)
        if not reviews:
            reviews = [
                "Great product, excellent quality and fast delivery!",
                "Good value for money, but could be improved.",
                "Amazing design and very user-friendly interface.",
                "Poor quality materials, disappointed with purchase.",
                "Outstanding performance, highly recommended!"
            ]
        
        # Determine sentiment model
        model = SentimentModel.ENSEMBLE
        if request.model == "vader":
            model = SentimentModel.VADER
        elif request.model == "textblob":
            model = SentimentModel.TEXTBLOB
        elif request.model == "huggingface":
            model = SentimentModel.HUGGINGFACE
        
        # Analyze sentiment
        sentiment_data = await pricing_analytics_service.analyze_review_sentiment(
            reviews=reviews,
            model=model,
            include_topics=request.include_topics
        )
        
        # Store sentiment analysis (background task)
        background_tasks.add_task(
            store_sentiment_analysis,
            request.product_id,
            sentiment_data,
            db
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SentimentAnalysisResponse(
            sentiment_data=sentiment_data,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis error: {str(e)}")

@router.post("/feature-engineering")
async def engineer_categorical_features(
    request: FeatureEngineeringRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Engineer categorical features for products
    """
    try:
        # Fetch product data
        query = select(Product).options(
            selectinload(Product.price_comparisons)
        )
        
        if request.product_ids:
            query = query.where(Product.id.in_(request.product_ids))
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        if not products:
            raise HTTPException(status_code=404, detail="No products found")
        
        # Prepare data for feature engineering
        product_data = []
        for product in products:
            data = {
                'id': product.id,
                'brand': product.brand or 'unknown',
                'category': product.category or 'general'
            }
            
            # Add price comparison data
            if product.price_comparisons:
                latest_price = product.price_comparisons[0]
                data['source_name'] = latest_price.source_name
            
            product_data.append(data)
        
        # Engineer features
        engineered_df, metadata = await data_pipeline_service.engineer_categorical_features(
            product_data,
            request.categorical_features,
            request.encoding_method
        )
        
        return {
            'engineered_features': engineered_df.to_dict('records'),
            'metadata': metadata,
            'total_products': len(product_data)
        }
        
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Feature engineering error: {str(e)}")

@router.get("/forecast-validation/{product_id}")
async def get_forecast_validation(
    product_id: int,
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """
    Get forecast validation metrics for a product
    """
    try:
        validation_data = await pricing_analytics_service.validate_forecast_accuracy(
            product_id=product_id,
            db=db,
            validation_days=days
        )
        
        return validation_data
        
    except Exception as e:
        logger.error(f"Forecast validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

@router.get("/products/{product_id}/analytics-summary")
async def get_product_analytics_summary(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive analytics summary for a product
    """
    try:
        # Fetch product with all analytics data
        query = select(Product).options(
            selectinload(Product.price_forecasts),
            selectinload(Product.sentiment_analyses),
            selectinload(Product.price_comparisons)
        ).where(Product.id == product_id)
        
        result = await db.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get latest forecast
        latest_forecast = None
        if product.price_forecasts:
            latest_forecast = max(product.price_forecasts, key=lambda x: x.created_at)
        
        # Get latest sentiment analysis
        latest_sentiment = None
        if product.sentiment_analyses:
            latest_sentiment = max(product.sentiment_analyses, key=lambda x: x.created_at)
        
        # Calculate basic price statistics
        price_stats = {}
        if product.price_comparisons:
            prices = [float(pc.price) for pc in product.price_comparisons if pc.price]
            if prices:
                price_stats = {
                    'current_price': prices[-1] if prices else 0,
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'avg_price': sum(prices) / len(prices),
                    'price_sources': len(set(pc.source_name for pc in product.price_comparisons))
                }
        
        return {
            'product_id': product_id,
            'product_name': product.name,
            'brand': product.brand,
            'category': product.category,
            'price_statistics': price_stats,
            'latest_forecast': {
                'has_forecast': latest_forecast is not None,
                'forecast_date': latest_forecast.forecast_date.isoformat() if latest_forecast else None,
                'accuracy_assessment': latest_forecast.accuracy_assessment if latest_forecast else None,
                'trend_direction': latest_forecast.trend_direction if latest_forecast else None,
                'recommendation': latest_forecast.recommendation if latest_forecast else None
            },
            'latest_sentiment': {
                'has_sentiment': latest_sentiment is not None,
                'analysis_date': latest_sentiment.analysis_date.isoformat() if latest_sentiment else None,
                'sentiment_score': latest_sentiment.sentiment_score if latest_sentiment else None,
                'sentiment_label': latest_sentiment.sentiment_label if latest_sentiment else None,
                'confidence': latest_sentiment.confidence if latest_sentiment else None,
                'total_reviews': latest_sentiment.total_reviews if latest_sentiment else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Analytics summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics summary error: {str(e)}")

# Background task functions
async def store_price_forecast(forecast_data: Dict[str, Any], db: AsyncSession):
    """Store price forecast in database"""
    try:
        # Create new forecast record
        forecast = PriceForecast(
            product_id=forecast_data['product_id'],
            forecast_horizon_days=forecast_data['forecast_horizon_days'],
            confidence_interval=forecast_data['confidence_interval'],
            historical_data_points=forecast_data['historical_data_points'],
            predictions=forecast_data['predictions'],
            validation_metrics=forecast_data.get('validation_metrics', {}),
            accuracy_assessment=forecast_data.get('validation_metrics', {}).get('accuracy_assessment'),
            trend_direction=forecast_data.get('trend_analysis', {}).get('direction'),
            trend_strength_percent=forecast_data.get('trend_analysis', {}).get('strength_percent'),
            current_price=forecast_data.get('price_insights', {}).get('current_price'),
            predicted_30day_price=forecast_data.get('price_insights', {}).get('predicted_30day_price'),
            price_change_percent=forecast_data.get('price_insights', {}).get('price_change_percent'),
            recommendation=forecast_data.get('price_insights', {}).get('recommendation')
        )
        
        db.add(forecast)
        await db.commit()
        logger.info(f"Stored price forecast for product {forecast_data['product_id']}")
        
    except Exception as e:
        logger.error(f"Failed to store price forecast: {e}")
        await db.rollback()

async def store_sentiment_analysis(product_id: int, sentiment_data: Dict[str, Any], db: AsyncSession):
    """Store sentiment analysis in database"""
    try:
        # Create new sentiment analysis record
        sentiment = SentimentAnalysis(
            product_id=product_id,
            model_used=sentiment_data.get('model', 'unknown'),
            total_reviews=sentiment_data.get('total_reviews', 0),
            processed_reviews=sentiment_data.get('processed_reviews', 0),
            sentiment_score=sentiment_data.get('sentiment_score', 0.0),
            sentiment_label=sentiment_data.get('sentiment_label', 'neutral'),
            confidence=sentiment_data.get('confidence', 0.0),
            detailed_scores=sentiment_data.get('detailed_scores'),
            topic_distribution=sentiment_data.get('topics', {}).get('topic_distribution'),
            top_topics=sentiment_data.get('topics', {}).get('top_topics'),
            individual_results=sentiment_data.get('individual_results'),
            subjectivity_score=sentiment_data.get('subjectivity')
        )
        
        db.add(sentiment)
        await db.commit()
        logger.info(f"Stored sentiment analysis for product {product_id}")
        
    except Exception as e:
        logger.error(f"Failed to store sentiment analysis: {e}")
        await db.rollback()
