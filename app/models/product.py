"""
Product model for storing detected products
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    """Product model for storing product information"""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    
    # Image information
    image_path = Column(String(500), nullable=False)
    image_hash = Column(String(64), nullable=True, index=True)
    
    # Detected specifications
    specifications = Column(JSON, nullable=True)
    
    # Confidence scores
    detection_confidence = Column(DECIMAL(3, 2), nullable=True)
    specification_confidence = Column(DECIMAL(3, 2), nullable=True)
    
    # Status
    is_processed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
      # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
      # Relationships
    analyses = relationship("Analysis", back_populates="product")
    price_comparisons = relationship("PriceComparison", back_populates="product")
    price_history = relationship("PriceHistory", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', brand='{self.brand}')>"
