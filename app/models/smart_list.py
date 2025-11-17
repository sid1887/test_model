"""
Smart Lists Database Models
Maps to: smart_lists, smart_list_items tables in database
"""

from enum import Enum
from sqlalchemy import Column, BigInteger, Text, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
from app.core.database import Base


class SmartListVisibility(str, Enum):
    """List visibility"""
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


class CompareJobStatus(str, Enum):
    """Compare job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SmartList(Base):
    """
    Smart Lists - User shopping lists
    Actual table: smart_lists (with BigInteger ID, UUID user_id)
    """
    __tablename__ = "smart_lists"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    auto_update = Column(Boolean, default=True)
    settings = Column(JSONB, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("SmartListItem", back_populates="smart_list", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SmartList(id={self.id}, name={self.name}, user_id={self.user_id})>"


class SmartListItem(Base):
    """
    Items in a Smart List
    Actual table: smart_list_items (products in lists)
    """
    __tablename__ = "smart_list_items"
    
    id = Column(BigInteger, primary_key=True, index=True)
    list_id = Column(BigInteger, ForeignKey("smart_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    quantity = Column(Integer, default=1)
    priority = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    smart_list = relationship("SmartList", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<SmartListItem(id={self.id}, list_id={self.list_id}, product_id={self.product_id})>"


class ListCompareJob(Base):
    """
    Batch comparison jobs for Smart Lists (stub model - no table in DB yet)
    """
    __tablename__ = "list_compare_jobs"
    
    id = Column(BigInteger, primary_key=True, index=True)
    list_id = Column(BigInteger, ForeignKey("smart_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    status = Column(SQLEnum(CompareJobStatus), default=CompareJobStatus.PENDING, index=True)
    
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    results = Column(JSONB, nullable=True)
    total_savings = Column(JSONB, nullable=True)
    best_store_overall = Column(Text, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ListCompareJob(id={self.id}, list_id={self.list_id}, status={self.status})>"


class ListTemplate(Base):
    """
    Predefined list templates (stub model - no table in DB yet)
    """
    __tablename__ = "list_templates"
    
    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Text, nullable=True)
    icon = Column(Text, nullable=True)
    
    template_items = Column(JSONB, nullable=False)
    usage_count = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ListTemplate(id={self.id}, name={self.name})>"
