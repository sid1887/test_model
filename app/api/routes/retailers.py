"""
Retailers API Routes for Cumpair
Provides retailer information for navigation and filtering
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from app.core.monitoring import logger
from app.config.env import is_demo_mode

router = APIRouter(prefix="/api/retailers", tags=["retailers"])


class Retailer(BaseModel):
    """Retailer model"""
    id: str
    name: str
    display_name: str
    url: str
    logo_url: Optional[str] = None
    supported: bool = True
    scraping_enabled: bool = True
    countries: List[str]
    categories: List[str]
    description: Optional[str] = None


class RetailersResponse(BaseModel):
    """Response model for retailers list"""
    retailers: List[Retailer]
    total: int
    demo_mode: bool


# Seed retailer data
SEED_RETAILERS = [
    {
        "id": "amazon",
        "name": "amazon",
        "display_name": "Amazon",
        "url": "https://www.amazon.com",
        "logo_url": "/logos/amazon.svg",
        "supported": True,
        "scraping_enabled": True,
        "countries": ["USA", "India", "UK", "Germany", "Japan"],
        "categories": ["Electronics", "Books", "Clothing", "Home & Kitchen", "Toys"],
        "description": "World's largest online retailer"
    },
    {
        "id": "flipkart",
        "name": "flipkart",
        "display_name": "Flipkart",
        "url": "https://www.flipkart.com",
        "logo_url": "/logos/flipkart.svg",
        "supported": True,
        "scraping_enabled": True,
        "countries": ["India"],
        "categories": ["Electronics", "Clothing", "Home & Furniture", "Appliances"],
        "description": "India's leading e-commerce marketplace"
    },
    {
        "id": "croma",
        "name": "croma",
        "display_name": "Croma",
        "url": "https://www.croma.com",
        "logo_url": "/logos/croma.svg",
        "supported": True,
        "scraping_enabled": True,
        "countries": ["India"],
        "categories": ["Electronics", "Appliances", "Computers", "Mobile Phones"],
        "description": "India's electronics and appliances retail chain"
    },
    {
        "id": "walmart",
        "name": "walmart",
        "display_name": "Walmart",
        "url": "https://www.walmart.com",
        "logo_url": "/logos/walmart.svg",
        "supported": False,
        "scraping_enabled": False,
        "countries": ["USA", "Canada", "Mexico"],
        "categories": ["Groceries", "Electronics", "Clothing", "Home", "Toys"],
        "description": "American multinational retail corporation"
    },
    {
        "id": "ebay",
        "name": "ebay",
        "display_name": "eBay",
        "url": "https://www.ebay.com",
        "logo_url": "/logos/ebay.svg",
        "supported": False,
        "scraping_enabled": False,
        "countries": ["USA", "UK", "Germany", "Australia"],
        "categories": ["Electronics", "Collectibles", "Fashion", "Home & Garden"],
        "description": "Global online marketplace and auction platform"
    },
    {
        "id": "target",
        "name": "target",
        "display_name": "Target",
        "url": "https://www.target.com",
        "logo_url": "/logos/target.svg",
        "supported": False,
        "scraping_enabled": False,
        "countries": ["USA"],
        "categories": ["Clothing", "Home", "Electronics", "Toys", "Groceries"],
        "description": "American big box department store chain"
    },
    {
        "id": "bestbuy",
        "name": "bestbuy",
        "display_name": "Best Buy",
        "url": "https://www.bestbuy.com",
        "logo_url": "/logos/bestbuy.svg",
        "supported": False,
        "scraping_enabled": False,
        "countries": ["USA", "Canada"],
        "categories": ["Electronics", "Computers", "Appliances", "Gaming"],
        "description": "Consumer electronics retailer"
    }
]


@router.get("", response_model=RetailersResponse)
async def get_retailers(
    supported_only: bool = Query(False, description="Return only supported retailers"),
    country: Optional[str] = Query(None, description="Filter by country"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    Get list of all retailers
    
    - **supported_only**: Filter to show only supported retailers
    - **country**: Filter retailers available in specific country
    - **category**: Filter retailers selling specific category
    
    Returns a list of retailers with their details, support status,
    and scraping capabilities.
    """
    try:
        retailers = [Retailer(**r) for r in SEED_RETAILERS]
        
        # Apply filters
        if supported_only:
            retailers = [r for r in retailers if r.supported]
        
        if country:
            retailers = [r for r in retailers if country in r.countries]
        
        if category:
            retailers = [r for r in retailers if category in r.categories]
        
        logger.info(
            f"Retrieved {len(retailers)} retailers "
            f"(supported_only={supported_only}, country={country}, category={category})"
        )
        
        return RetailersResponse(
            retailers=retailers,
            total=len(retailers),
            demo_mode=is_demo_mode()
        )
        
    except Exception as e:
        logger.error(f"Failed to get retailers: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve retailers: {str(e)}"
        )


@router.get("/{retailer_id}", response_model=Retailer)
async def get_retailer(retailer_id: str):
    """
    Get details for a specific retailer
    
    - **retailer_id**: Unique retailer identifier
    """
    try:
        retailer_data = next(
            (r for r in SEED_RETAILERS if r["id"] == retailer_id),
            None
        )
        
        if not retailer_data:
            raise HTTPException(
                status_code=404,
                detail=f"Retailer '{retailer_id}' not found"
            )
        
        return Retailer(**retailer_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get retailer {retailer_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve retailer: {str(e)}"
        )
