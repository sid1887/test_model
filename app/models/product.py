"""
Product model for storing detected products
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, JSON, NUMERIC
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    """Product model for storing product information"""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    title = Column(Text, nullable=False)
    canonical_sku = Column(String(255), nullable=True)
    brand = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    main_image = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # JSONB for flexible metadata (use name parameter to avoid SQLAlchemy conflict)
    product_metadata = Column('metadata', JSON, nullable=True, default={})
    
    # Normalized price fields
    avg_price = Column(NUMERIC(12, 2), nullable=True)
    min_price = Column(NUMERIC(12, 2), nullable=True)
    max_price = Column(NUMERIC(12, 2), nullable=True)
    
    # Tracking
    views_count = Column(Integer, default=0)
    searches_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships - ONLY to tables that exist in database
    product_prices = relationship("ProductPrice", back_populates="product", cascade="all, delete-orphan")
    price_comparisons = relationship("PriceComparison", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="product", cascade="all, delete-orphan")
    price_alerts = relationship("PriceAlert", back_populates="product", cascade="all, delete-orphan")
    analytics_insights = relationship("AnalyticsInsight", back_populates="product", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="product", cascade="all, delete-orphan")
    sentiment_analyses = relationship("SentimentAnalysis", back_populates="product", cascade="all, delete-orphan")
    snapshots = relationship("ProductSnapshot", back_populates="product", cascade="all, delete-orphan")
    price_forecasts = relationship("PriceForecast", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}', brand='{self.brand}')>"
