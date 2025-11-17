"""
Database models for analytics data
Properly maps to all forecast_validations, sentiment_trends, and analytics_insights tables
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Float, Integer, NUMERIC
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PriceForecast(Base):
    """Model for storing price forecast data - uses analytics_insights table"""
    
    __tablename__ = "analytics_insights"
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    
    # Insight type (for price forecasts)
    insight_type = Column(Text, nullable=False, default="price_forecast")
    
    # Forecast data stored as JSONB
    data = Column(JSONB, nullable=False, default=dict)
    
    # Model and confidence
    model_name = Column(Text, nullable=True)
    confidence = Column(NUMERIC(5, 4), nullable=True)
    
    # Validity window
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="price_forecasts")
    
    def __repr__(self):
        return f"<PriceForecast(id={self.id}, product_id={self.product_id})>"


class SentimentAnalysis(Base):
    """Model for storing sentiment analysis results - uses analytics_insights table"""
    
    __tablename__ = "analytics_insights"
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True)
    
    # Insight type (for sentiment)
    insight_type = Column(Text, nullable=False, default="sentiment_analysis")
    
    # Analysis data stored as JSONB
    data = Column(JSONB, nullable=False, default=dict)
    
    # Model and confidence
    model_name = Column(Text, nullable=True)
    confidence = Column(NUMERIC(5, 4), nullable=True)
    
    # Validity window
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="sentiment_analyses")
    
    def __repr__(self):
        return f"<SentimentAnalysis(id={self.id}, product_id={self.product_id})>"


class ForecastValidation(Base):
    """Model for tracking forecast accuracy over time - uses forecast_validations table"""
    
    __tablename__ = "forecast_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_id = Column(Integer, nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Validation metadata
    validation_date = Column(DateTime(timezone=True), server_default=func.now())
    validation_period_days = Column(Integer, nullable=True)
    actual_data_points = Column(Integer, nullable=True)
    
    # Accuracy metrics
    mae = Column(NUMERIC(12, 4), nullable=True)  # Mean Absolute Error
    mape = Column(NUMERIC(8, 4), nullable=True)  # Mean Absolute Percentage Error
    rmse = Column(NUMERIC(12, 4), nullable=True)  # Root Mean Square Error
    accuracy_band_10pct = Column(NUMERIC(5, 2), nullable=True)  # % within 10% of actual
    
    # Prediction vs actual data
    predictions_vs_actual = Column(JSONB, nullable=True)
    
    # Performance assessment
    accuracy_grade = Column(String(20), nullable=True)  # A, B, C, D, F
    model_performance = Column(String(20), nullable=True)  # excellent, good, fair, poor
    
    # Status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product")
    
    def __repr__(self):
        return f"<ForecastValidation(id={self.id}, forecast_id={self.forecast_id})>"


class SentimentTrend(Base):
    """Model for tracking sentiment trends over time - uses sentiment_trends table"""
    
    __tablename__ = "sentiment_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    period_type = Column(String(20), default="weekly")  # daily, weekly, monthly
    
    # Sentiment metrics
    avg_sentiment_score = Column(NUMERIC(5, 4), nullable=False)
    sentiment_change = Column(NUMERIC(5, 4), nullable=True)  # Change from previous period
    sentiment_volatility = Column(NUMERIC(5, 4), nullable=True)  # Standard deviation
    
    # Review volume
    total_reviews = Column(Integer, nullable=False)
    positive_reviews = Column(Integer, nullable=False)
    negative_reviews = Column(Integer, nullable=False)
    neutral_reviews = Column(Integer, nullable=False)
    
    # Trend indicators
    trend_direction = Column(String(20), nullable=True)  # improving, declining, stable
    trend_strength = Column(NUMERIC(5, 4), nullable=True)  # 0 to 1 scale
    
    # Topic trends
    trending_topics = Column(JSONB, nullable=True)
    topic_changes = Column(JSONB, nullable=True)
    
    # Status
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product")
    
    def __repr__(self):
        return f"<SentimentTrend(id={self.id}, product_id={self.product_id})>"
