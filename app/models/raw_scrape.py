"""
Raw Scrapes Database Model
Maps to: raw_scrapes table (stores raw scraper output as JSONB)
"""

from sqlalchemy import Column, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class RawScrape(Base):
    """
    Raw scraper output storage
    Stores every scrape as JSONB for maximum flexibility
    """
    __tablename__ = "raw_scrapes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), index=True)
    product_identifier = Column(Text, nullable=True)
    site_name = Column(Text, nullable=False, index=True)
    url = Column(Text, nullable=False)
    
    # Raw scraped data as JSONB
    raw_data = Column(JSONB, nullable=False)
    headers = Column(JSONB, nullable=True)
    
    # Processing status
    processed = Column(Boolean, default=False, index=True)
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<RawScrape(id={self.id}, site={self.site_name}, processed={self.processed})>"
