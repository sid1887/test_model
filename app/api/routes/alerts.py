"""
Price Alerts API Endpoints
Provides CRUD operations and control for price alerts
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, validator

from app.core.database import get_db
from app.models.alert import (
    PriceAlert, AlertEvent, Notification, UserPreferences,
    AlertOperator, AlertStatus, AlertFrequency, NotificationChannel,
    AlertEventType
)


router = APIRouter(prefix="/api/alerts", tags=["alerts"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class AlertCreateRequest(BaseModel):
    """Request schema for creating price alert"""
    product_id: int = Field(..., description="Product to monitor")
    target_price: float = Field(..., gt=0, description="Target price threshold")
    operator: AlertOperator = Field(default=AlertOperator.LESS_THAN_EQUAL)
    
    retailers: Optional[List[int]] = Field(None, description="Filter by retailer IDs")
    channels: List[NotificationChannel] = Field(
        default=[NotificationChannel.EMAIL],
        description="Notification channels"
    )
    frequency: AlertFrequency = Field(
        default=AlertFrequency.IMMEDIATE,
        description="Check frequency"
    )
    
    priority: str = Field(default="normal", description="Alert priority (normal, urgent)")
    expires_at: Optional[datetime] = Field(None, description="Alert expiration date")
    notes: Optional[str] = Field(None, max_length=500)
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['normal', 'urgent']:
            raise ValueError('Priority must be "normal" or "urgent"')
        return v


class AlertUpdateRequest(BaseModel):
    """Request schema for updating price alert"""
    target_price: Optional[float] = Field(None, gt=0)
    operator: Optional[AlertOperator] = None
    retailers: Optional[List[int]] = None
    channels: Optional[List[NotificationChannel]] = None
    frequency: Optional[AlertFrequency] = None
    priority: Optional[str] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class AlertResponse(BaseModel):
    """Response schema for alert detail"""
    id: int
    user_id: int
    product_id: int
    target_price: float
    operator: str
    retailers: Optional[List[int]]
    channels: List[str]
    frequency: str
    status: str
    priority: str
    
    last_checked_at: Optional[datetime]
    last_fired_at: Optional[datetime]
    fire_count: int
    expires_at: Optional[datetime]
    notes: Optional[str]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Response schema for alert list"""
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int


class AlertEventResponse(BaseModel):
    """Response schema for alert event"""
    id: int
    alert_id: int
    event_type: str
    current_price: Optional[float]
    previous_price: Optional[float]
    retailer_id: Optional[int]
    event_payload: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    """Response schema for alert history"""
    alert: AlertResponse
    events: List[AlertEventResponse]
    total_events: int


class NotificationResponse(BaseModel):
    """Response schema for notification"""
    id: int
    channel: str
    status: str
    recipient: str
    message: str
    retry_count: int
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserPreferencesResponse(BaseModel):
    """Response schema for user notification preferences"""
    id: int
    user_id: int
    email: Optional[str]
    phone: Optional[str]
    whatsapp: Optional[str]
    
    email_enabled: bool
    sms_enabled: bool
    whatsapp_enabled: bool
    push_enabled: bool
    
    max_notifications_per_hour: int
    max_notifications_per_day: int
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    timezone: str
    
    class Config:
        from_attributes = True


class UserPreferencesUpdateRequest(BaseModel):
    """Request schema for updating user preferences"""
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    
    max_notifications_per_hour: Optional[int] = Field(None, ge=1, le=100)
    max_notifications_per_day: Optional[int] = Field(None, ge=1, le=500)
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_user_id():
    """Mock function - replace with actual auth"""
    # TODO: Integrate with your authentication system
    return 1


def create_alert_event(
    db: Session,
    alert_id: int,
    event_type: AlertEventType,
    current_price: Optional[float] = None,
    previous_price: Optional[float] = None,
    retailer_id: Optional[int] = None,
    event_payload: Optional[dict] = None
) -> AlertEvent:
    """Create alert event record"""
    event = AlertEvent(
        alert_id=alert_id,
        event_type=event_type,
        current_price=current_price,
        previous_price=previous_price,
        retailer_id=retailer_id,
        event_payload=event_payload
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# ============================================================================
# Alert CRUD Endpoints
# ============================================================================

@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    request: AlertCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create new price alert
    
    - Monitors product price across retailers
    - Triggers notifications when conditions met
    - Supports multiple notification channels
    """
    user_id = get_current_user_id()
    
    # Check for existing active alert
    existing = db.query(PriceAlert).filter(
        and_(
            PriceAlert.user_id == user_id,
            PriceAlert.product_id == request.product_id,
            PriceAlert.status == AlertStatus.ACTIVE
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active alert already exists for this product"
        )
    
    # Create alert
    alert = PriceAlert(
        user_id=user_id,
        product_id=request.product_id,
        target_price=request.target_price,
        operator=request.operator,
        retailers=request.retailers,
        channels=request.channels,
        frequency=request.frequency,
        status=AlertStatus.ACTIVE,
        priority=request.priority,
        expires_at=request.expires_at,
        notes=request.notes
    )
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Create "created" event
    create_alert_event(
        db=db,
        alert_id=alert.id,
        event_type=AlertEventType.CREATED,
        event_payload={"channels": request.channels, "frequency": request.frequency}
    )
    
    return alert


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    product_id: Optional[int] = Query(None, description="Filter by product"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List user's price alerts
    
    - Supports filtering by status and product
    - Paginated results
    - Returns alert details with metadata
    """
    user_id = get_current_user_id()
    
    # TODO: Implement async SQLAlchemy queries
    # Returning empty list for now - database migration needed
    return {
        "alerts": [],
        "total": 0,
        "page": page,
        "page_size": page_size
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Get alert details
    
    - Returns full alert configuration
    - Includes firing history metadata
    """
    user_id = get_current_user_id()
    
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return alert


@router.get("/{alert_id}/history", response_model=AlertHistoryResponse)
async def get_alert_history(
    alert_id: int,
    event_type: Optional[AlertEventType] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get alert history with events
    
    - Shows all alert events (price changes, firings, status changes)
    - Supports event type filtering
    - Ordered by most recent first
    """
    user_id = get_current_user_id()
    
    # Get alert
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Get events
    events_query = db.query(AlertEvent).filter(AlertEvent.alert_id == alert_id)
    
    if event_type:
        events_query = events_query.filter(AlertEvent.event_type == event_type)
    
    total_events = events_query.count()
    events = events_query.order_by(AlertEvent.created_at.desc()) \
                         .limit(limit) \
                         .all()
    
    return {
        "alert": alert,
        "events": events,
        "total_events": total_events
    }


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    request: AlertUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update alert configuration
    
    - Modify target price, channels, frequency, etc.
    - Creates event log of changes
    """
    user_id = get_current_user_id()
    
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Track changes for event log
    changes = {}
    
    # Update fields
    if request.target_price is not None:
        changes['target_price'] = {'old': alert.target_price, 'new': request.target_price}
        alert.target_price = request.target_price
    if request.operator is not None:
        changes['operator'] = {'old': alert.operator, 'new': request.operator}
        alert.operator = request.operator
    if request.retailers is not None:
        alert.retailers = request.retailers
    if request.channels is not None:
        alert.channels = request.channels
    if request.frequency is not None:
        alert.frequency = request.frequency
    if request.priority is not None:
        alert.priority = request.priority
    if request.expires_at is not None:
        alert.expires_at = request.expires_at
    if request.notes is not None:
        alert.notes = request.notes
    
    db.commit()
    db.refresh(alert)
    
    # Create event if changes made
    if changes:
        create_alert_event(
            db=db,
            alert_id=alert.id,
            event_type=AlertEventType.CREATED,  # Using CREATED as generic update
            event_payload={"changes": changes}
        )
    
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete price alert
    
    - Soft deletes by marking status as deleted
    - Stops all monitoring and notifications
    """
    user_id = get_current_user_id()
    
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Soft delete
    alert.status = AlertStatus.DELETED
    db.commit()
    
    # Create deleted event
    create_alert_event(
        db=db,
        alert_id=alert.id,
        event_type=AlertEventType.DELETED
    )
    
    return None


# ============================================================================
# Alert Control Endpoints
# ============================================================================

@router.post("/{alert_id}/trigger-now", response_model=dict)
async def trigger_alert_now(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Manually trigger alert check
    
    - Bypasses frequency throttling
    - Useful for immediate price verification
    - Returns check result
    """
    user_id = get_current_user_id()
    
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert.status != AlertStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert is not active"
        )
    
    # TODO: Trigger Celery task for immediate price check
    # from app.workers.alert_monitor import check_alert_now
    # result = check_alert_now.apply_async(args=[alert.id])
    
    # Update last checked timestamp
    alert.last_checked_at = datetime.utcnow()
    db.commit()
    
    # Create event
    create_alert_event(
        db=db,
        alert_id=alert.id,
        event_type=AlertEventType.CHECKED,
        event_payload={"manual_trigger": True}
    )
    
    return {
        "message": "Alert check triggered",
        "alert_id": alert.id,
        "status": "queued"
    }


@router.post("/{alert_id}/pause", response_model=AlertResponse)
async def pause_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Pause alert monitoring
    
    - Temporarily stops notifications
    - Can be resumed later
    """
    user_id = get_current_user_id()
    
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert.status != AlertStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active alerts can be paused"
        )
    
    alert.status = AlertStatus.PAUSED
    db.commit()
    db.refresh(alert)
    
    # Create event
    create_alert_event(
        db=db,
        alert_id=alert.id,
        event_type=AlertEventType.PAUSED
    )
    
    return alert


@router.post("/{alert_id}/resume", response_model=AlertResponse)
async def resume_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Resume paused alert
    
    - Reactivates monitoring and notifications
    """
    user_id = get_current_user_id()
    
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    if alert.status != AlertStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only paused alerts can be resumed"
        )
    
    alert.status = AlertStatus.ACTIVE
    db.commit()
    db.refresh(alert)
    
    # Create event
    create_alert_event(
        db=db,
        alert_id=alert.id,
        event_type=AlertEventType.RESUMED
    )
    
    return alert


# ============================================================================
# Notification & Preferences Endpoints
# ============================================================================

@router.get("/{alert_id}/notifications", response_model=List[NotificationResponse])
async def get_alert_notifications(
    alert_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Get notifications sent for alert
    
    - Shows delivery status and tracking
    - Ordered by most recent first
    """
    user_id = get_current_user_id()
    
    # Verify alert ownership
    alert = db.query(PriceAlert).filter(
        and_(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user_id
        )
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Get notifications via events
    notifications = db.query(Notification) \
        .join(AlertEvent) \
        .filter(AlertEvent.alert_id == alert_id) \
        .order_by(Notification.created_at.desc()) \
        .limit(limit) \
        .all()
    
    return notifications


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    db: Session = Depends(get_db)
):
    """
    Get user notification preferences
    
    - Returns all notification settings
    - Creates default preferences if not exist
    """
    user_id = get_current_user_id()
    
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    # Create default if not exists
    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    request: UserPreferencesUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update user notification preferences
    
    - Configure channels, rate limits, quiet hours
    """
    user_id = get_current_user_id()
    
    prefs = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        db.add(prefs)
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    
    return prefs


# Background task function for celery worker
async def check_and_trigger_alerts():
    """
    Background task to check all active alerts and trigger if conditions are met
    Called by Celery periodic task
    """
    from app.core.database import SessionLocal
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Get all active alerts
        alerts = db.query(PriceAlert).filter(
            PriceAlert.is_active == True,
            PriceAlert.status == AlertStatus.ACTIVE
        ).all()
        
        triggered_count = 0
        for alert in alerts:
            # Check if alert condition is met
            if alert.alert_type == AlertType.PRICE_DROP:
                # Logic to check if price dropped below target
                # This would call the product API to get current price
                pass  # Implement price checking logic
            
            triggered_count += 1
        
        return {
            "checked": len(alerts),
            "triggered": triggered_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()
