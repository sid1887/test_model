"""
Embedding model - Vector storage for AI/CLIP
Matches db/init/02_schema.sql embeddings table
"""

from sqlalchemy import Column, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from pgvector.sqlalchemy import Vector
import uuid

from app.core.database import Base


class Embedding(Base):
    """
    Vector embeddings for semantic/image search using pgvector
    Maps to: embeddings table
    """
    
    __tablename__ = "embeddings"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to products
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Model info
    model_name = Column(Text, nullable=False)
    model_version = Column(Text, nullable=True)
    
    # Vector (CLIP ViT-B/32 uses 512 dimensions)
    vec = Column(Vector(512), nullable=True)
    
    # Metadata
    meta = Column(JSONB, nullable=True, default=dict, server_default='{}')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="embeddings")
    
    def __repr__(self):
        return f"<Embedding(id={self.id}, product_id={self.product_id}, model={self.model_name})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "meta": self.meta,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
