"""
Retailer Database Model
Maps to: retailers table (stores retailer/site configuration)
"""

from sqlalchemy import Column, Integer, Text, Boolean, DateTime, NUMERIC
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class Retailer(Base):
    """
    Retailer/site configuration
    Stores scraper config, status, and performance metrics per site
    """
    __tablename__ = "retailers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False, unique=True)
    domain = Column(Text, nullable=False)
    
    # Scraper configuration
    scraper_config = Column(JSONB, default=dict)  # selectors, rate limits, auth config
    
    # Status
    active = Column(Boolean, default=True, index=True)
    last_scrape_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    success_rate = Column(NUMERIC(5, 2), nullable=True)
    avg_response_time = Column(NUMERIC(8, 2), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Retailer(id={self.id}, name={self.name}, active={self.active})>"
