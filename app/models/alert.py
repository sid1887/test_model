"""
Price Alerts Database Models
Provides compatibility models and enums expected by the API routes.
Maps to: price_alerts, alert_history (and light-weight notification/preferences models)
"""

from enum import Enum
from sqlalchemy import Column, BigInteger, Text, Boolean, DateTime, NUMERIC, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLEnum
from app.core.database import Base


class AlertOperator(str, Enum):
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    EQUAL = "=="
    PERCENT_OFF = "percent_off"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    FIRED = "fired"
    EXPIRED = "expired"
    DELETED = "deleted"


class AlertFrequency(str, Enum):
    IMMEDIATE = "immediate"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    WEBHOOK = "webhook"


class AlertEventType(str, Enum):
    CREATED = "created"
    CHECKED = "checked"
    PRICE_CHANGED = "price_changed"
    FIRED = "fired"
    PAUSED = "paused"
    RESUMED = "resumed"
    EXPIRED = "expired"
    DELETED = "deleted"
    ERROR = "error"


class PriceAlert(Base):
    """ORM for `price_alerts` with compatibility fields used by API routes."""
    __tablename__ = "price_alerts"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    # Legacy/condition fields (kept for internal logic)
    condition_type = Column(Text, nullable=True)  # 'below', 'percent_drop', 'back_in_stock'
    threshold = Column(NUMERIC(12, 2), nullable=True)
    threshold_percent = Column(NUMERIC(5, 2), nullable=True)

    # Compatibility fields expected by API routes
    target_price = Column(NUMERIC(12, 2), nullable=True)
    operator = Column(SQLEnum(AlertOperator), nullable=True)
    target_percent_off = Column(NUMERIC(5, 2), nullable=True)

    # Filters & notification config
    retailers = Column(JSONB, nullable=True)
    channels = Column(JSONB, name="notification_channels", default=list)
    frequency = Column(SQLEnum(AlertFrequency), nullable=True)

    # Status & meta
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE, index=True)
    priority = Column(Text, default="normal")
    notes = Column(Text, nullable=True)

    # Tracking
    times_triggered = Column(BigInteger, default=0)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="price_alerts")
    events = relationship("AlertEvent", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PriceAlert(id={self.id}, product_id={self.product_id}, status={self.status})>"


class AlertEvent(Base):
    """ORM for `alert_history` table. Exposed as AlertEvent for compatibility with routes."""
    __tablename__ = "alert_history"

    id = Column(BigInteger, primary_key=True, index=True)
    alert_id = Column(BigInteger, ForeignKey("price_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_price_id = Column(BigInteger, ForeignKey("product_prices.id"), nullable=True)

    event_type = Column(SQLEnum(AlertEventType), nullable=False)
    event_payload = Column(JSONB, nullable=True)

    # Price snapshot
    current_price = Column(NUMERIC(12, 2), nullable=True)
    previous_price = Column(NUMERIC(12, 2), nullable=True)
    retailer_id = Column(BigInteger, nullable=True)
    retailer_name = Column(Text, nullable=True)

    # Map DB column `triggered_at` to attribute `created_at` used by API
    created_at = Column('triggered_at', DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    alert = relationship("PriceAlert", back_populates="events")
    product_price = relationship("ProductPrice")

    def __repr__(self):
        return f"<AlertEvent(id={self.id}, alert_id={self.alert_id}, type={self.event_type})>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, index=True)
    alert_event_id = Column(BigInteger, ForeignKey("alert_history.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    recipient = Column(Text, nullable=False)
    subject = Column(Text, nullable=True)
    message = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship back to event
    alert_event = relationship("AlertEvent")

    def __repr__(self):
        return f"<Notification(id={self.id}, channel={self.channel}, status={self.status})>"


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    email = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    whatsapp = Column(Text, nullable=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    whatsapp_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    max_notifications_per_hour = Column(BigInteger, default=10)
    max_notifications_per_day = Column(BigInteger, default=50)
    quiet_hours_start = Column(Text, nullable=True)
    quiet_hours_end = Column(Text, nullable=True)
    timezone = Column(Text, default="UTC")
    preferences = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id})>"
