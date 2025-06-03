"""
Analysis model for storing image analysis results
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from alembic_database import Base

class Analysis(Base):
    """Analysis model for storing analysis results"""
    
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Analysis type
    analysis_type = Column(String(50), nullable=False)  # 'object_detection', 'spec_extraction', etc.
    
    # Results
    raw_results = Column(JSON, nullable=True)
    processed_results = Column(JSON, nullable=True)
    
    # Confidence and metadata
    confidence_score = Column(DECIMAL(3, 2), nullable=True)
    processing_time = Column(DECIMAL(8, 4), nullable=True)  # seconds
    model_version = Column(String(50), nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis(id={self.id}, type='{self.analysis_type}', status='{self.status}')>"
