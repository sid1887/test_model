"""
Product Price model - Price snapshots per site
Matches db/init/02_schema.sql product_prices table
"""

from sqlalchemy import Column, BigInteger, Text, DateTime, Boolean, NUMERIC
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.core.database import Base


class ProductPrice(Base):
    """
    Price snapshots per site with JSONB for flexible offer data
    Maps to: product_prices table
    """
    
    __tablename__ = "product_prices"
    
    # Primary key
    id = Column(BigInteger, primary_key=True, index=True)
    
    # Foreign key to products
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Site information
    site_name = Column(Text, nullable=False)
    site_product_id = Column(Text, nullable=True)
    site_url = Column(Text, nullable=True)
    
    # Price data
    price = Column(NUMERIC(12, 2), nullable=False)
    original_price = Column(NUMERIC(12, 2), nullable=True)
    discount_percent = Column(NUMERIC(5, 2), nullable=True)
    currency = Column(Text, nullable=False, default='INR', server_default='INR')
    
    # Availability
    availability = Column(Text, nullable=True)
    in_stock = Column(Boolean, nullable=False, default=True, server_default='true')
    
    # Structured data from scrape
    scraped_data = Column(JSONB, nullable=True, default=dict, server_default='{}')
    
    # Timestamps
    scraped_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="product_prices")
    
    def __repr__(self):
        return f"<ProductPrice(id={self.id}, product_id={self.product_id}, price={self.price}, site={self.site_name})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "product_id": str(self.product_id),
            "site_name": self.site_name,
            "site_product_id": self.site_product_id,
            "site_url": self.site_url,
            "price": float(self.price) if self.price else None,
            "original_price": float(self.original_price) if self.original_price else None,
            "discount_percent": float(self.discount_percent) if self.discount_percent else None,
            "currency": self.currency,
            "availability": self.availability,
            "in_stock": self.in_stock,
            "scraped_data": self.scraped_data,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
