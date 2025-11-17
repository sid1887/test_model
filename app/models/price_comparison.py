"""
Price comparison models for storing price comparison and historical data
Maps to price_comparisons and price_history tables in database
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, NUMERIC, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class PriceComparison(Base):
    """Price comparison model - maps to price_comparisons table"""
    
    __tablename__ = "price_comparisons"
    
    id = Column(BigInteger, primary_key=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Comparison metadata
    comparison_date = Column(DateTime(timezone=True), server_default=func.now())
    num_retailers = Column(Integer, nullable=True)
    
    # Price statistics
    lowest_price = Column(NUMERIC(12, 2), nullable=True)
    highest_price = Column(NUMERIC(12, 2), nullable=True)
    avg_price = Column(NUMERIC(12, 2), nullable=True)
    median_price = Column(NUMERIC(12, 2), nullable=True)
    
    # Availability
    in_stock_count = Column(Integer, nullable=True)
    out_of_stock_count = Column(Integer, nullable=True)
    
    # Detailed comparison data
    comparison_data = Column(JSONB, default=dict)
    
    # Results
    best_deal_retailer = Column(Text, nullable=True)
    best_deal_url = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="price_comparisons")
    
    def __repr__(self):
        return f"<PriceComparison(id={self.id}, product_id={self.product_id}, avg_price={self.avg_price})>"


class PriceHistory(Base):
    """Price history model - maps to price_history table"""
    
    __tablename__ = "price_history"
    
    id = Column(BigInteger, primary_key=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Site information
    site_name = Column(Text, nullable=False)
    site_product_id = Column(Text, nullable=True)
    
    # Historical price data
    price = Column(NUMERIC(12, 2), nullable=False)
    original_price = Column(NUMERIC(12, 2), nullable=True)
    discount_percent = Column(NUMERIC(5, 2), nullable=True)
    currency = Column(String(3), default="INR")
    
    # Availability
    in_stock = Column(Boolean, default=True)
    
    # Source
    scraped_from = Column(JSONB, default=dict)
    
    # Timestamps
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="price_history")
    
    def __repr__(self):
        return f"<PriceHistory(id={self.id}, product_id={self.product_id}, price={self.price})>"
