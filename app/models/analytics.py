"""
Database models for price forecasts and sentiment analysis
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class PriceForecast(Base):
    """Model for storing price forecast data"""
    
    __tablename__ = "price_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Forecast metadata
    forecast_date = Column(DateTime(timezone=True), server_default=func.now())
    forecast_horizon_days = Column(Integer, nullable=False)
    model_version = Column(String(50), default="prophet_v1")
    confidence_interval = Column(Float, default=0.8)
    
    # Historical data info
    historical_data_points = Column(Integer, nullable=False)
    training_start_date = Column(DateTime(timezone=True), nullable=True)
    training_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Predictions (JSON array of prediction objects)
    predictions = Column(JSON, nullable=False)
    
    # Validation metrics
    validation_metrics = Column(JSON, nullable=True)
    accuracy_assessment = Column(String(20), nullable=True)  # excellent, good, fair, poor
    
    # Trend analysis
    trend_direction = Column(String(20), nullable=True)  # increasing, decreasing, stable
    trend_strength_percent = Column(Float, nullable=True)
    
    # Price insights
    current_price = Column(DECIMAL(10, 2), nullable=True)
    predicted_30day_price = Column(DECIMAL(10, 2), nullable=True)
    price_change_percent = Column(Float, nullable=True)
    best_buy_date = Column(DateTime(timezone=True), nullable=True)
    best_buy_price = Column(DECIMAL(10, 2), nullable=True)
    recommendation = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="price_forecasts")

class SentimentAnalysis(Base):
    """Model for storing sentiment analysis results"""
    
    __tablename__ = "sentiment_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Analysis metadata
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())
    model_used = Column(String(50), nullable=False)  # vader, textblob, huggingface, ensemble
    total_reviews = Column(Integer, nullable=False)
    processed_reviews = Column(Integer, nullable=False)
    
    # Sentiment scores
    sentiment_score = Column(Float, nullable=False)  # -1 to 1 scale
    sentiment_label = Column(String(20), nullable=False)  # positive, negative, neutral
    confidence = Column(Float, nullable=False)  # 0 to 1 scale
    
    # Detailed scores (JSON for model-specific data)
    detailed_scores = Column(JSON, nullable=True)
    
    # Topic analysis
    topic_distribution = Column(JSON, nullable=True)
    top_topics = Column(JSON, nullable=True)
    
    # Individual model results (for ensemble)
    individual_results = Column(JSON, nullable=True)
    
    # Review text analysis
    positive_keywords = Column(JSON, nullable=True)
    negative_keywords = Column(JSON, nullable=True)
    
    # Quality metrics
    subjectivity_score = Column(Float, nullable=True)  # 0 to 1 scale
    review_quality_score = Column(Float, nullable=True)  # Average review length, complexity
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="sentiment_analyses")

class ForecastValidation(Base):
    """Model for tracking forecast accuracy over time"""
    
    __tablename__ = "forecast_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, ForeignKey("price_forecasts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Validation metadata
    validation_date = Column(DateTime(timezone=True), server_default=func.now())
    validation_period_days = Column(Integer, nullable=False)
    actual_data_points = Column(Integer, nullable=False)
    
    # Accuracy metrics
    mae = Column(Float, nullable=True)  # Mean Absolute Error
    mape = Column(Float, nullable=True)  # Mean Absolute Percentage Error
    rmse = Column(Float, nullable=True)  # Root Mean Square Error
    accuracy_band_10pct = Column(Float, nullable=True)  # % within 10% of actual
    
    # Prediction vs actual data
    predictions_vs_actual = Column(JSON, nullable=True)
    
    # Performance assessment
    accuracy_grade = Column(String(20), nullable=True)  # A, B, C, D, F
    model_performance = Column(String(20), nullable=True)  # excellent, good, fair, poor
    
    # Status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    forecast = relationship("PriceForecast")
    product = relationship("Product")

class SentimentTrend(Base):
    """Model for tracking sentiment trends over time"""
    
    __tablename__ = "sentiment_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), default="weekly")  # daily, weekly, monthly
    
    # Sentiment metrics
    avg_sentiment_score = Column(Float, nullable=False)
    sentiment_change = Column(Float, nullable=True)  # Change from previous period
    sentiment_volatility = Column(Float, nullable=True)  # Standard deviation
    
    # Review volume
    total_reviews = Column(Integer, nullable=False)
    positive_reviews = Column(Integer, nullable=False)
    negative_reviews = Column(Integer, nullable=False)
    neutral_reviews = Column(Integer, nullable=False)
    
    # Trend indicators
    trend_direction = Column(String(20), nullable=True)  # improving, declining, stable
    trend_strength = Column(Float, nullable=True)  # 0 to 1 scale
    
    # Topic trends
    trending_topics = Column(JSON, nullable=True)
    topic_changes = Column(JSON, nullable=True)
    
    # Status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product")

# Update the Product model to include relationships (add these to existing Product model)
"""
Add these relationships to the existing Product model in app/models/products.py:

# Forecasting and sentiment relationships
price_forecasts = relationship("PriceForecast", back_populates="product")
sentiment_analyses = relationship("SentimentAnalysis", back_populates="product")
"""
