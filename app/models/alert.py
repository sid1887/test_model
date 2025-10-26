"""
Price Alerts Database Models
Tables: alerts, alert_events, notifications, user_preferences
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from app.core.database import Base


class AlertOperator(str, Enum):
    """Alert price comparison operators"""
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    EQUAL = "=="
    PERCENT_OFF = "percent_off"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    PAUSED = "paused"
    FIRED = "fired"
    EXPIRED = "expired"
    DELETED = "deleted"


class AlertFrequency(str, Enum):
    """Alert check frequency"""
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class PriceAlert(Base):
    """
    Price alerts for products
    Monitors product prices and triggers notifications
    """
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Reference to users table
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    # Alert configuration
    target_price = Column(Float, nullable=False)
    operator = Column(SQLEnum(AlertOperator), default=AlertOperator.LESS_THAN_EQUAL)
    target_percent_off = Column(Float, nullable=True)  # For percent-based alerts
    
    # Filters
    retailers = Column(JSON, nullable=True)  # List of retailer IDs to monitor, null = all
    
    # Notification settings
    channels = Column(JSON, nullable=False)  # List of NotificationChannel values
    frequency = Column(SQLEnum(AlertFrequency), default=AlertFrequency.IMMEDIATE)
    
    # Status & metadata
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE, index=True)
    priority = Column(String(20), default="normal")  # normal, urgent
    
    # Timing
    expires_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    last_fired_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    events = relationship("AlertEvent", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PriceAlert(id={self.id}, product_id={self.product_id}, target={self.target_price}, status={self.status})>"


class AlertEventType(str, Enum):
    """Alert event types"""
    CREATED = "created"
    CHECKED = "checked"
    PRICE_CHANGED = "price_changed"
    FIRED = "fired"
    PAUSED = "paused"
    RESUMED = "resumed"
    EXPIRED = "expired"
    DELETED = "deleted"
    ERROR = "error"


class AlertEvent(Base):
    """
    Alert event history
    Tracks all significant events for an alert
    """
    __tablename__ = "alert_events"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(SQLEnum(AlertEventType), nullable=False)
    event_payload = Column(JSON, nullable=True)  # Additional event data
    
    # Price data at time of event
    current_price = Column(Float, nullable=True)
    previous_price = Column(Float, nullable=True)
    retailer_id = Column(Integer, nullable=True)
    retailer_name = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relationships
    alert = relationship("PriceAlert", back_populates="events")
    notifications = relationship("Notification", back_populates="alert_event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AlertEvent(id={self.id}, alert_id={self.alert_id}, type={self.event_type})>"


class Notification(Base):
    """
    Notification delivery log
    Tracks notification attempts across all channels
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_event_id = Column(Integer, ForeignKey("alert_events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Delivery
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, index=True)
    
    # Recipient details
    recipient = Column(String(255), nullable=False)  # email address, phone number, etc.
    
    # Content
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)  # Full notification data
    
    # Tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    
    # Error handling
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # External IDs
    external_id = Column(String(255), nullable=True)  # Twilio SID, SendGrid ID, etc.
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    alert_event = relationship("AlertEvent", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, channel={self.channel}, status={self.status})>"


class UserPreferences(Base):
    """
    User notification preferences and settings
    """
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    
    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    
    # Notification preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    
    # Notification frequency limits (rate limiting)
    max_notifications_per_hour = Column(Integer, default=10)
    max_notifications_per_day = Column(Integer, default=50)
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)
    
    # Timezone
    timezone = Column(String(50), default="UTC")
    
    # Additional preferences
    preferences = Column(JSON, nullable=True)  # Flexible preferences storage
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, email={self.email})>"
