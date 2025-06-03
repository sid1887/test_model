"""
Price comparison model for storing scraped price data
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from alembic_database import Base

class PriceComparison(Base):
    """Price comparison model for storing price data from different sources"""
    
    __tablename__ = "price_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Source information
    source_name = Column(String(100), nullable=False)  # Amazon, eBay, etc.
    source_url = Column(String(1000), nullable=False)
    
    # Product information from source
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # Price information
    price = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(3), default="USD")
    original_price = Column(DECIMAL(10, 2), nullable=True)  # If on sale
    discount_percentage = Column(DECIMAL(5, 2), nullable=True)
    
    # Availability
    in_stock = Column(Boolean, nullable=True)
    stock_quantity = Column(Integer, nullable=True)
    
    # Ratings and reviews
    rating = Column(DECIMAL(3, 2), nullable=True)
    review_count = Column(Integer, nullable=True)
    
    # Seller information
    seller_name = Column(String(200), nullable=True)
    seller_rating = Column(DECIMAL(3, 2), nullable=True)
    
    # Shipping information
    shipping_cost = Column(DECIMAL(8, 2), nullable=True)
    shipping_time = Column(String(100), nullable=True)
      # Additional data
    additional_data = Column(JSON, nullable=True)
    
    # Scraping information
    scraping_method = Column(String(50), nullable=True)  # api, html, browser
    proxy_used = Column(String(100), nullable=True)
    scraping_duration = Column(DECIMAL(8, 4), nullable=True)
    
    # Status
    is_valid = Column(Boolean, default=True)
    confidence_score = Column(DECIMAL(3, 2), nullable=True)
    
    # Timestamps
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    price_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="price_comparisons")
    
    def __repr__(self):
        return f"<PriceComparison(id={self.id}, source='{self.source_name}', price={self.price})>"
