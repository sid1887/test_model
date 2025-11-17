"""
Analytics Insights Database Model
Maps to: analytics_insights table (cached AI-generated insights)
"""

from sqlalchemy import Column, Text, DateTime, NUMERIC
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class AnalyticsInsight(Base):
    """
    Cached analytics and AI insights
    Stores trend analysis, forecasts, anomalies, sentiment analysis
    """
    __tablename__ = "analytics_insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    
    insight_type = Column(Text, nullable=False)  # 'trend', 'forecast', 'anomaly', 'sentiment'
    
    # Results stored as JSONB
    data = Column(JSONB, nullable=False)
    
    # Metadata
    model_name = Column(Text, nullable=True)
    confidence = Column(NUMERIC(5, 4), nullable=True)
    
    # Validity window
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="analytics_insights")
    
    def __repr__(self):
        return f"<AnalyticsInsight(id={self.id}, type={self.insight_type}, product_id={self.product_id})>"
