"""
User API Routes for Cumpair
Handles user preferences, location, and personalization
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from app.core.monitoring import logger
from app.config.env import is_demo_mode, get_service_name

router = APIRouter(prefix="/api/user", tags=["user"])

# In-memory storage for demo purposes (replace with database in production)
_user_data_storage: Dict[str, Any] = {}
_location_storage_path = Path("/tmp/user_locations.json")


class UserLocation(BaseModel):
    """User location model"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    accuracy: Optional[float] = Field(None, description="Location accuracy in meters")
    city: Optional[str] = Field(None, description="City name")
    country: Optional[str] = Field(None, description="Country name")
    postal_code: Optional[str] = Field(None, description="Postal code")
    consent_given: bool = Field(True, description="User consent for location tracking")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class UserLocationResponse(BaseModel):
    """Response model for location updates"""
    success: bool
    message: str
    location: UserLocation


class UserPreferences(BaseModel):
    """User preferences model"""
    theme: Optional[str] = Field(None, description="UI theme preference (light/dark/system)")
    currency: Optional[str] = Field(None, description="Preferred currency")
    language: Optional[str] = Field(None, description="Preferred language")
    notifications_enabled: bool = Field(True, description="Enable notifications")


def _load_locations() -> Dict[str, UserLocation]:
    """Load locations from persistent storage"""
    if _location_storage_path.exists():
        try:
            with open(_location_storage_path, 'r') as f:
                data = json.load(f)
                return {k: UserLocation(**v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to load locations: {e}")
    return {}


def _save_locations(locations: Dict[str, UserLocation]):
    """Save locations to persistent storage"""
    try:
        _location_storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_location_storage_path, 'w') as f:
            data = {k: v.dict() for k, v in locations.items()}
            json.dump(data, f, default=str, indent=2)
    except Exception as e:
        logger.error(f"Failed to save locations: {e}")


@router.post("/location", response_model=UserLocationResponse)
async def update_user_location(
    location: UserLocation = Body(...),
    user_id: Optional[str] = "anonymous"
):
    """
    Update user's location for personalized results
    
    - **latitude**: Latitude coordinate (-90 to 90)
    - **longitude**: Longitude coordinate (-180 to 180)
    - **accuracy**: Optional accuracy in meters
    - **city**: Optional city name
    - **country**: Optional country name
    - **postal_code**: Optional postal code
    - **consent_given**: User consent for location tracking (required)
    
    The location is stored for personalization of search results,
    local deals, and store availability.
    """
    try:
        if not location.consent_given:
            raise HTTPException(
                status_code=400,
                detail="Location consent is required"
            )
        
        # Load existing locations
        locations = _load_locations()
        
        # Store location
        locations[user_id] = location
        _user_data_storage[user_id] = {
            "location": location.dict(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save to persistent storage
        _save_locations(locations)
        
        logger.info(
            f"Updated location for user {user_id}: "
            f"lat={location.latitude}, lon={location.longitude}, "
            f"city={location.city}, country={location.country}"
        )
        
        return UserLocationResponse(
            success=True,
            message="Location updated successfully",
            location=location
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user location: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update location: {str(e)}"
        )


@router.get("/location")
async def get_user_location(user_id: Optional[str] = "anonymous"):
    """
    Get user's stored location
    
    Returns the most recently stored location for the user.
    Returns 404 if no location has been stored yet.
    """
    try:
        locations = _load_locations()
        
        if user_id not in locations:
            raise HTTPException(
                status_code=404,
                detail="No location found for this user"
            )
        
        return {
            "success": True,
            "location": locations[user_id].dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user location: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve location: {str(e)}"
        )


@router.post("/preferences")
async def update_user_preferences(
    preferences: UserPreferences = Body(...),
    user_id: Optional[str] = "anonymous"
):
    """
    Update user preferences
    
    - **theme**: UI theme preference (light/dark/system)
    - **currency**: Preferred currency
    - **language**: Preferred language
    - **notifications_enabled**: Enable/disable notifications
    """
    try:
        if user_id not in _user_data_storage:
            _user_data_storage[user_id] = {}
        
        _user_data_storage[user_id]["preferences"] = preferences.dict()
        _user_data_storage[user_id]["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated preferences for user {user_id}")
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": preferences.dict()
        }
        
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.get("/preferences")
async def get_user_preferences(user_id: Optional[str] = "anonymous"):
    """Get user preferences"""
    try:
        if user_id not in _user_data_storage or "preferences" not in _user_data_storage[user_id]:
            # Return defaults
            return {
                "success": True,
                "preferences": UserPreferences().dict()
            }
        
        return {
            "success": True,
            "preferences": _user_data_storage[user_id]["preferences"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve preferences: {str(e)}"
        )
