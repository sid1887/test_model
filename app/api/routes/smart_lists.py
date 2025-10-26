"""
Smart Lists API Endpoints
Provides list management, item tracking, and batch comparison
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.core.database import get_db
from app.models.smart_list import (
    SmartList, SmartListItem, ListCompareJob, ListTemplate,
    SmartListVisibility, CompareJobStatus
)


router = APIRouter(prefix="/api/lists", tags=["smart-lists"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class ListCreateRequest(BaseModel):
    """Request schema for creating smart list"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=10)
    default_retailers: Optional[List[int]] = Field(None, max_items=50)
    auto_monitor: bool = Field(default=False)
    auto_monitor_threshold: Optional[float] = Field(None, gt=0)
    visibility: SmartListVisibility = Field(default=SmartListVisibility.PRIVATE)


class ListUpdateRequest(BaseModel):
    """Request schema for updating smart list"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=10)
    default_retailers: Optional[List[int]] = Field(None, max_items=50)
    auto_monitor: Optional[bool] = None
    auto_monitor_threshold: Optional[float] = Field(None, gt=0)
    visibility: Optional[SmartListVisibility] = None


class ItemAddRequest(BaseModel):
    """Request schema for adding item to list"""
    product_id: int = Field(..., gt=0)
    desired_price: Optional[float] = Field(None, gt=0)
    priority: str = Field(default="normal")
    notes: Optional[str] = Field(None, max_length=500)
    quantity: int = Field(default=1, ge=1, le=999)
    
    @validator('priority')
    def validate_priority(cls, v):
        if v not in ['low', 'normal', 'high', 'urgent']:
            raise ValueError('Priority must be low, normal, high, or urgent')
        return v


class ItemUpdateRequest(BaseModel):
    """Request schema for updating list item"""
    desired_price: Optional[float] = Field(None, gt=0)
    priority: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    quantity: Optional[int] = Field(None, ge=1, le=999)
    position: Optional[int] = Field(None, ge=0)


class ListResponse(BaseModel):
    """Response schema for smart list"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    tags: Optional[List[str]]
    default_retailers: Optional[List[int]]
    
    auto_monitor: bool
    auto_monitor_threshold: Optional[float]
    visibility: str
    share_token: Optional[str]
    
    item_count: int
    total_value: Optional[float]
    last_compared_at: Optional[datetime]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ItemResponse(BaseModel):
    """Response schema for list item"""
    id: int
    list_id: int
    product_id: int
    
    desired_price: Optional[float]
    priority: str
    notes: Optional[str]
    position: int
    quantity: int
    
    added_price: Optional[float]
    current_price: Optional[float]
    best_retailer_id: Optional[int]
    is_available: bool
    alert_created: bool
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ListDetailResponse(BaseModel):
    """Response schema for list with items"""
    list: ListResponse
    items: List[ItemResponse]
    total_items: int
    
    # Aggregated stats
    total_value: float
    potential_savings: Optional[float]
    unavailable_items: int


class CompareJobRequest(BaseModel):
    """Request schema for starting comparison job"""
    retailers: Optional[List[int]] = Field(None, max_items=20, description="Override default retailers")
    force_rescrape: bool = Field(default=False, description="Force fresh scraping")


class CompareJobResponse(BaseModel):
    """Response schema for comparison job"""
    id: int
    list_id: int
    status: str
    
    total_items: int
    completed_items: int
    failed_items: int
    
    results: Optional[dict]
    total_savings: Optional[float]
    best_store_overall: Optional[str]
    
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplateResponse(BaseModel):
    """Response schema for list template"""
    id: int
    name: str
    category: str
    description: Optional[str]
    template_items: List[dict]
    usage_count: int
    is_public: bool
    is_featured: bool
    
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_user_id():
    """Mock function - replace with actual auth"""
    # TODO: Integrate with your authentication system
    return 1


def generate_share_token() -> str:
    """Generate unique share token for list"""
    import secrets
    return secrets.token_urlsafe(16)


def calculate_list_stats(db: Session, list_id: int) -> dict:
    """Calculate aggregated list statistics"""
    items = db.query(SmartListItem).filter(SmartListItem.list_id == list_id).all()
    
    total_value = sum((item.current_price or 0) * item.quantity for item in items)
    unavailable_items = sum(1 for item in items if not item.is_available)
    
    # Calculate potential savings (if desired price set)
    potential_savings = 0
    for item in items:
        if item.desired_price and item.current_price:
            savings = (item.current_price - item.desired_price) * item.quantity
            if savings > 0:
                potential_savings += savings
    
    return {
        "total_value": total_value,
        "potential_savings": potential_savings if potential_savings > 0 else None,
        "unavailable_items": unavailable_items
    }


# ============================================================================
# List CRUD Endpoints
# ============================================================================

@router.post("", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(
    request: ListCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create new smart list
    
    - Organizes products for batch comparison
    - Supports auto-monitoring with price alerts
    - Can be shared with others
    """
    user_id = get_current_user_id()
    
    smart_list = SmartList(
        user_id=user_id,
        name=request.name,
        description=request.description,
        tags=request.tags,
        default_retailers=request.default_retailers,
        auto_monitor=request.auto_monitor,
        auto_monitor_threshold=request.auto_monitor_threshold,
        visibility=request.visibility,
        share_token=generate_share_token() if request.visibility != SmartListVisibility.PRIVATE else None
    )
    
    db.add(smart_list)
    db.commit()
    db.refresh(smart_list)
    
    return smart_list


@router.get("", response_model=List[ListResponse])
async def list_user_lists(
    visibility: Optional[SmartListVisibility] = Query(None),
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List user's smart lists
    
    - Filter by visibility or tag
    - Returns list metadata with stats
    """
    user_id = get_current_user_id()
    
    query = db.query(SmartList).filter(SmartList.user_id == user_id)
    
    if visibility:
        query = query.filter(SmartList.visibility == visibility)
    
    if tag:
        # Filter lists containing the tag
        query = query.filter(SmartList.tags.contains([tag]))
    
    lists = query.order_by(SmartList.created_at.desc()).all()
    
    return lists


@router.get("/{list_id}", response_model=ListDetailResponse)
async def get_list_detail(
    list_id: int,
    db: Session = Depends(get_db)
):
    """
    Get list with all items
    
    - Returns full list detail
    - Includes items with current prices
    - Shows aggregated stats
    """
    user_id = get_current_user_id()
    
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Get items
    items = db.query(SmartListItem) \
              .filter(SmartListItem.list_id == list_id) \
              .order_by(SmartListItem.position) \
              .all()
    
    # Calculate stats
    stats = calculate_list_stats(db, list_id)
    
    return {
        "list": smart_list,
        "items": items,
        "total_items": len(items),
        **stats
    }


@router.put("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: int,
    request: ListUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update list configuration
    
    - Modify name, tags, retailers, etc.
    """
    user_id = get_current_user_id()
    
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(smart_list, field, value)
    
    # Generate share token if visibility changed to shared/public
    if request.visibility in [SmartListVisibility.SHARED, SmartListVisibility.PUBLIC]:
        if not smart_list.share_token:
            smart_list.share_token = generate_share_token()
    
    db.commit()
    db.refresh(smart_list)
    
    return smart_list


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete smart list
    
    - Removes list and all items
    - Cascade deletes comparison jobs
    """
    user_id = get_current_user_id()
    
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    db.delete(smart_list)
    db.commit()
    
    return None


# ============================================================================
# Item Management Endpoints
# ============================================================================

@router.post("/{list_id}/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    list_id: int,
    request: ItemAddRequest,
    db: Session = Depends(get_db)
):
    """
    Add item to list
    
    - Links product to list
    - Optionally sets desired price for alerts
    - Auto-creates alert if list has auto_monitor enabled
    """
    user_id = get_current_user_id()
    
    # Verify list ownership
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Check if product already in list
    existing = db.query(SmartListItem).filter(
        and_(
            SmartListItem.list_id == list_id,
            SmartListItem.product_id == request.product_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already in list"
        )
    
    # Get next position
    max_position = db.query(SmartListItem.position) \
                     .filter(SmartListItem.list_id == list_id) \
                     .order_by(SmartListItem.position.desc()) \
                     .first()
    next_position = (max_position[0] + 1) if max_position else 0
    
    # Create item
    item = SmartListItem(
        list_id=list_id,
        product_id=request.product_id,
        desired_price=request.desired_price,
        priority=request.priority,
        notes=request.notes,
        quantity=request.quantity,
        position=next_position
    )
    
    db.add(item)
    
    # Update list item count
    smart_list.item_count += 1
    
    db.commit()
    db.refresh(item)
    
    # TODO: Auto-create alert if auto_monitor enabled
    # if smart_list.auto_monitor and request.desired_price:
    #     from app.models.alert import PriceAlert
    #     # Create alert logic here
    
    return item


@router.put("/{list_id}/items/{item_id}", response_model=ItemResponse)
async def update_item(
    list_id: int,
    item_id: int,
    request: ItemUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update list item
    
    - Modify desired price, priority, notes, position
    """
    user_id = get_current_user_id()
    
    # Verify list ownership
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Get item
    item = db.query(SmartListItem).filter(
        and_(
            SmartListItem.id == item_id,
            SmartListItem.list_id == list_id
        )
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)
    
    db.commit()
    db.refresh(item)
    
    return item


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    list_id: int,
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove item from list
    """
    user_id = get_current_user_id()
    
    # Verify list ownership
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Get item
    item = db.query(SmartListItem).filter(
        and_(
            SmartListItem.id == item_id,
            SmartListItem.list_id == list_id
        )
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    db.delete(item)
    
    # Update list item count
    smart_list.item_count = max(0, smart_list.item_count - 1)
    
    db.commit()
    
    return None


@router.post("/{list_id}/items/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_items(
    list_id: int,
    item_ids: List[int] = Body(..., description="Item IDs in desired order"),
    db: Session = Depends(get_db)
):
    """
    Reorder list items
    
    - Updates position of all items
    - Pass item IDs in desired order
    """
    user_id = get_current_user_id()
    
    # Verify list ownership
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Update positions
    for position, item_id in enumerate(item_ids):
        item = db.query(SmartListItem).filter(
            and_(
                SmartListItem.id == item_id,
                SmartListItem.list_id == list_id
            )
        ).first()
        
        if item:
            item.position = position
    
    db.commit()
    
    return None


# ============================================================================
# Comparison Endpoints
# ============================================================================

@router.post("/{list_id}/compare", response_model=CompareJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_comparison(
    list_id: int,
    request: CompareJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start batch comparison job
    
    - Compares all items across retailers
    - Runs asynchronously in background
    - Returns job ID for status tracking
    """
    user_id = get_current_user_id()
    
    # Verify list ownership
    smart_list = db.query(SmartList).filter(
        and_(
            SmartList.id == list_id,
            SmartList.user_id == user_id
        )
    ).first()
    
    if not smart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="List not found"
        )
    
    # Get item count
    item_count = db.query(SmartListItem).filter(SmartListItem.list_id == list_id).count()
    
    if item_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare empty list"
        )
    
    # Create job
    job = ListCompareJob(
        list_id=list_id,
        user_id=user_id,
        status=CompareJobStatus.PENDING,
        total_items=item_count,
        retailers=request.retailers or smart_list.default_retailers
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # TODO: Start Celery task
    # from app.workers.compare_worker import run_comparison
    # background_tasks.add_task(run_comparison, job.id)
    
    return job


@router.get("/compare-jobs/{job_id}", response_model=CompareJobResponse)
async def get_comparison_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comparison job status
    
    - Shows progress and results
    - Updates in real-time via SSE (use /compare-jobs/{id}/stream)
    """
    user_id = get_current_user_id()
    
    job = db.query(ListCompareJob).filter(
        and_(
            ListCompareJob.id == job_id,
            ListCompareJob.user_id == user_id
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison job not found"
        )
    
    return job


@router.get("/compare-jobs/{job_id}/stream")
async def stream_comparison_progress(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Stream comparison progress via SSE
    
    - Real-time updates as items are compared
    - Use EventSource API on frontend
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    
    user_id = get_current_user_id()
    
    # Verify job ownership
    job = db.query(ListCompareJob).filter(
        and_(
            ListCompareJob.id == job_id,
            ListCompareJob.user_id == user_id
        )
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison job not found"
        )
    
    async def event_generator():
        """Generate SSE events for job progress"""
        while True:
            # Refresh job status
            db.refresh(job)
            
            # Send progress update
            progress = {
                "job_id": job.id,
                "status": job.status,
                "completed_items": job.completed_items,
                "total_items": job.total_items,
                "progress_percent": (job.completed_items / job.total_items * 100) if job.total_items > 0 else 0
            }
            
            yield f"data: {progress}\n\n"
            
            # Stop if job completed
            if job.status in [CompareJobStatus.COMPLETED, CompareJobStatus.FAILED, CompareJobStatus.CANCELLED]:
                break
            
            await asyncio.sleep(1)  # Poll every second
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============================================================================
# Template Endpoints
# ============================================================================

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    List available list templates
    
    - Predefined lists for common shopping scenarios
    - Filter by category
    """
    query = db.query(ListTemplate).filter(ListTemplate.is_public == True)
    
    if category:
        query = query.filter(ListTemplate.category == category)
    
    if featured_only:
        query = query.filter(ListTemplate.is_featured == True)
    
    templates = query.order_by(ListTemplate.usage_count.desc()).all()
    
    return templates


@router.post("/templates/{template_id}/apply", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def apply_template(
    template_id: int,
    list_name: Optional[str] = Query(None, description="Custom list name"),
    db: Session = Depends(get_db)
):
    """
    Create list from template
    
    - Instantiates template with all items
    - Useful for quick setup
    """
    user_id = get_current_user_id()
    
    template = db.query(ListTemplate).filter(
        and_(
            ListTemplate.id == template_id,
            ListTemplate.is_public == True
        )
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Create list from template
    smart_list = SmartList(
        user_id=user_id,
        name=list_name or f"{template.name} - {datetime.utcnow().strftime('%Y-%m-%d')}",
        description=template.description,
        tags=[template.category],
        item_count=len(template.template_items)
    )
    
    db.add(smart_list)
    db.commit()
    db.refresh(smart_list)
    
    # Add template items
    for idx, template_item in enumerate(template.template_items):
        item = SmartListItem(
            list_id=smart_list.id,
            product_id=template_item.get("product_id"),
            desired_price=template_item.get("desired_price"),
            priority=template_item.get("priority", "normal"),
            notes=template_item.get("notes"),
            quantity=template_item.get("quantity", 1),
            position=idx
        )
        db.add(item)
    
    # Increment template usage
    template.usage_count += 1
    
    db.commit()
    db.refresh(smart_list)
    
    return smart_list
