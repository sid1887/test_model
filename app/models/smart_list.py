"""
Smart Lists Database Models
Tables: smart_lists, smart_list_items, list_compare_jobs
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
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
    Smart Lists - Curated product collections
    Users can create lists and run batch comparisons
    """
    __tablename__ = "smart_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # List metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags for organization
    
    # List configuration
    default_retailers = Column(JSON, nullable=True)  # Preferred retailers for this list
    default_notification_channel = Column(String(50), nullable=True)
    
    # Auto-monitoring
    auto_monitor = Column(Boolean, default=False)  # Auto-create alerts for items
    auto_monitor_threshold = Column(Float, nullable=True)  # Auto-alert when price < this
    
    # Sharing
    visibility = Column(SQLEnum(SmartListVisibility), default=SmartListVisibility.PRIVATE)
    share_token = Column(String(100), unique=True, nullable=True)  # For shared access
    
    # Stats
    item_count = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)  # Sum of best prices
    last_compared_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    items = relationship("SmartListItem", back_populates="smart_list", cascade="all, delete-orphan")
    compare_jobs = relationship("ListCompareJob", back_populates="smart_list", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SmartList(id={self.id}, name={self.name}, items={self.item_count})>"


class SmartListItem(Base):
    """
    Items in a Smart List
    Links products to lists with metadata
    """
    __tablename__ = "smart_list_items"
    
    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("smart_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Item-specific settings
    desired_price = Column(Float, nullable=True)  # Target price for this item
    priority = Column(Integer, default=0)  # User-defined priority (higher = more important)
    notes = Column(Text, nullable=True)  # User notes
    
    # Item metadata
    position = Column(Integer, default=0)  # Order in list
    quantity = Column(Integer, default=1)  # How many needed
    
    # Price tracking
    added_price = Column(Float, nullable=True)  # Price when added
    current_price = Column(Float, nullable=True)  # Last known best price
    best_retailer_id = Column(Integer, nullable=True)  # Retailer with best price
    last_checked_at = Column(DateTime, nullable=True)
    
    # Flags
    is_available = Column(Boolean, default=True)
    alert_created = Column(Boolean, default=False)  # Has alert been auto-created
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    smart_list = relationship("SmartList", back_populates="items")
    
    def __repr__(self):
        return f"<SmartListItem(id={self.id}, list_id={self.list_id}, product_id={self.product_id})>"


class ListCompareJob(Base):
    """
    Batch comparison jobs for Smart Lists
    Tracks progress of parallel product comparisons
    """
    __tablename__ = "list_compare_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("smart_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Job status
    status = Column(SQLEnum(CompareJobStatus), default=CompareJobStatus.PENDING, index=True)
    
    # Progress tracking
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    # Results
    results = Column(JSON, nullable=True)  # Comparison results
    total_savings = Column(Float, default=0.0)  # Total potential savings
    best_store_overall = Column(String(100), nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    smart_list = relationship("SmartList", back_populates="compare_jobs")
    
    def __repr__(self):
        return f"<ListCompareJob(id={self.id}, list_id={self.list_id}, status={self.status})>"


class ListTemplate(Base):
    """
    Predefined list templates (e.g., "Weekly Groceries", "Back to School")
    Users can create lists from templates
    """
    __tablename__ = "list_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # groceries, electronics, etc.
    icon = Column(String(50), nullable=True)  # Icon identifier
    
    # Template items
    template_items = Column(JSON, nullable=False)  # List of product queries/categories
    
    # Usage stats
    usage_count = Column(Integer, default=0)
    
    # Visibility
    is_public = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ListTemplate(id={self.id}, name={self.name})>"
