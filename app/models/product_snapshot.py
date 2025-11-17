"""
Product snapshot model for storing point-in-time product data snapshots
Maps to product_snapshots table in database
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ProductSnapshot(Base):
    """Historical product snapshots - uses product_snapshots table"""
    __tablename__ = "product_snapshots"
    
    id = Column(BigInteger, primary_key=True, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Snapshot data
    snapshot_data = Column(JSONB, nullable=False)
    
    # Metadata
    snapshot_type = Column(String(50), nullable=True)  # 'automated', 'manual', 'scheduled'
    reason = Column(Text, nullable=True)
    
    # Timestamps
    snapshot_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="snapshots")
    
    def __repr__(self):
        return f"<ProductSnapshot(id={self.id}, product_id={self.product_id}, type={self.snapshot_type})>"

