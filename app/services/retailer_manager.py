"""
Enhanced Retailer Management System for Cumpair
Manages 15+ retailers with scalable configuration and expansion capabilities
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.monitoring import logger, performance_timer
from app.services.scraping import scraping_engine
from app.services.data_pipeline import data_pipeline_service, NormalizationMethod, ScoringWeights

class RetailerCategory(Enum):
    """Retailer categories for better organization"""
    GENERAL = "general"
    ELECTRONICS = "electronics"
    FASHION = "fashion"
    HOME_IMPROVEMENT = "home_improvement"
    WHOLESALE = "wholesale"
    SPECIALTY = "specialty"

class RetailerPriority(Enum):
    """Priority levels for retailer scraping"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class RetailerConfig:
    """Configuration for a single retailer"""
    name: str
    domain: str
    category: RetailerCategory
    priority: RetailerPriority
    selectors: Dict[str, List[str]]
    rate_limit: float
    search_url_template: str
    base_url: str
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    timeout: int = 30
    max_retries: int = 3
    anti_bot_measures: bool = True
    requires_js: bool = True
    currency: str = "USD"
    country_code: str = "US"
    status: str = "active"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['category'] = self.category.value
        result['priority'] = self.priority.value
        return result

class RetailerManager:
    """Enhanced retailer management system supporting 15+ retailers"""
    
    def __init__(self):
        self.retailers = {}
        self.performance_stats = {}
        self.last_updated = None
        self._initialize_retailers()
        
    def _initialize_retailers(self):
        """Initialize all 15+ supported retailers"""
        
        # TIER 1: Major US Retailers (High Priority)
        self.retailers.update({
            'amazon': RetailerConfig(
                name="Amazon",
                domain="amazon.com",
                category=RetailerCategory.GENERAL,
                priority=RetailerPriority.HIGH,
                selectors={
                    'product_container': ['[data-component-type="s-search-result"]', '.s-result-item'],
                    'title': ['h2 a span', '.a-link-normal .a-text-normal', '[data-cy="title-recipe-title"]'],
                    'price': ['.a-price .a-offscreen', '.a-price-whole', '.a-price-fraction'],
                    'rating': ['.a-icon-alt', '.cr-widget-FocalReviews', '.a-link-normal .a-icon-alt'],
                    'availability': ['#availability span', '.a-color-success', '.a-color-state'],
                    'image': ['.imgTagWrapper img', '#landingImage', '.s-image'],
                    'link': ['h2 a', '.a-link-normal']
                },
                rate_limit=2.0,
                search_url_template="https://www.amazon.com/s?k={query}&ref=sr_pg_{page}",
                base_url="https://www.amazon.com"
            ),
            
            'walmart': RetailerConfig(
                name="Walmart",
                domain="walmart.com",
                category=RetailerCategory.GENERAL,
                priority=RetailerPriority.HIGH,
                selectors={
                    'product_container': ['[data-automation-id="product-title"]', '[data-item-id]'],
                    'title': ['[data-automation-id="product-title"]', 'h1', '.f4'],
                    'price': ['[data-automation-id="product-price"]', '[itemprop="price"]', '.price-current'],
                    'rating': ['.average-rating', '.star-rating', '.stars-reviews-count'],
                    'availability': ['[data-automation-id="fulfillment-summary"]', '.availability'],
                    'image': ['.prod-hero-image img', '.slider-list img', 'img'],
                    'link': ['a']
                },
                rate_limit=2.5,
                search_url_template="https://www.walmart.com/search?q={query}&page={page}",
                base_url="https://www.walmart.com"
            ),
            
            'target': RetailerConfig(
                name="Target",
                domain="target.com",
                category=RetailerCategory.GENERAL,
                priority=RetailerPriority.HIGH,
                selectors={
                    'product_container': ['[data-test="product-card"]', '.ProductCard'],
                    'title': ['[data-test="product-title"]', '.ProductCard__title', 'h3'],
                    'price': ['[data-test="product-price"]', '.Price', '.price'],
                    'rating': ['[data-test="ratings"]', '.Ratings', '.rating'],
                    'availability': ['[data-test="fulfillment-summary"]', '.fulfillment'],
                    'image': ['[data-test="product-image"]', '.ProductCard__image img'],
                    'link': ['a']
                },
                rate_limit=2.0,
                search_url_template="https://www.target.com/s?searchTerm={query}&page={page}",
                base_url="https://www.target.com"
            ),
            
            'bestbuy': RetailerConfig(
                name="Best Buy",
                domain="bestbuy.com",
                category=RetailerCategory.ELECTRONICS,
                priority=RetailerPriority.HIGH,
                selectors={
                    'product_container': ['.sku-item', '.product-item'],
                    'title': ['.sku-title h1', '.v-fw-regular', '.sku-title'],
                    'price': ['.priceView-hero-price span', '.priceView-customer-price span', '.sr-only'],
                    'rating': ['.ugc-ratings-reviews', '.c-ratings-reviews-v2', '.sr-only'],
                    'availability': ['.fulfillment-fulfillment-summary', '.availability'],
                    'image': ['.primary-image', '.media-wrapper img'],
                    'link': ['a']
                },
                rate_limit=2.0,
                search_url_template="https://www.bestbuy.com/site/searchpage.jsp?st={query}&page={page}",
                base_url="https://www.bestbuy.com"
            ),
            
            'ebay': RetailerConfig(
                name="eBay",
                domain="ebay.com",
                category=RetailerCategory.GENERAL,
                priority=RetailerPriority.HIGH,
                selectors={
                    'product_container': ['.s-item', '.srp-item'],
                    'title': ['.s-item__title', '.it-ttl', '#x-title-label-lbl'],
                    'price': ['.s-item__price', '.u-flL.condText', '.u-flL.u-bold'],
                    'rating': ['.ebay-review-star-rating', '.reviews', '.x-star-rating'],
                    'availability': ['.u-flL.vi-acc-del-range', '.availability'],
                    'image': ['.s-item__image img', '.ux-image-carousel-item img'],
                    'link': ['.s-item__link', 'a']
                },
                rate_limit=1.5,
                search_url_template="https://www.ebay.com/sch/i.html?_nkw={query}&_pgn={page}",
                base_url="https://www.ebay.com"
            )
        })
        
        # TIER 2: Major Specialized Retailers (Medium Priority)
        self.retailers.update({
            'costco': RetailerConfig(
                name="Costco",
                domain="costco.com",
                category=RetailerCategory.WHOLESALE,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['.product-tile', '.product'],
                    'title': ['.description', '.product-title', 'h1'],
                    'price': ['.price', '.product-price'],
                    'rating': ['.ratings', '.stars'],
                    'availability': ['.availability', '.stock'],
                    'image': ['img.product-image', '.product-img'],
                    'link': ['a']
                },
                rate_limit=3.0,
                search_url_template="https://www.costco.com/CatalogSearch?keyword={query}&pageSize=24&currentPage={page}",
                base_url="https://www.costco.com"
            ),
            
            'homedepot': RetailerConfig(
                name="Home Depot",
                domain="homedepot.com",
                category=RetailerCategory.HOME_IMPROVEMENT,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['.plp-pod', '.product-pod'],
                    'title': ['.product-title', '.pod-plp__title'],
                    'price': ['.price', '.price-format__main-price'],
                    'rating': ['.stars', '.average-rating'],
                    'availability': ['.fulfillment-method', '.availability'],
                    'image': ['.product-image', '.product-pod__image img'],
                    'link': ['a']
                },
                rate_limit=2.5,
                search_url_template="https://www.homedepot.com/s/{query}?page={page}",
                base_url="https://www.homedepot.com"
            ),
            
            'lowes': RetailerConfig(
                name="Lowe's",
                domain="lowes.com",
                category=RetailerCategory.HOME_IMPROVEMENT,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['.plp-tile', '.product-tile'],
                    'title': ['.product-title', '.art-pd-title'],
                    'price': ['.price', '.price-current'],
                    'rating': ['.rating', '.stars'],
                    'availability': ['.fulfillment', '.availability'],
                    'image': ['.product-image img', '.art-pd-image img'],
                    'link': ['a']
                },
                rate_limit=2.5,
                search_url_template="https://www.lowes.com/search?searchTerm={query}&page={page}",
                base_url="https://www.lowes.com"
            ),
            
            'newegg': RetailerConfig(
                name="Newegg",
                domain="newegg.com",
                category=RetailerCategory.ELECTRONICS,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['.item-cell', '.item-container'],
                    'title': ['.item-title', '.item-brand'],
                    'price': ['.price-current', '.price-current-num'],
                    'rating': ['.item-rating', '.rating'],
                    'availability': ['.item-stock', '.availability'],
                    'image': ['.item-img img', '.product-image'],
                    'link': ['.item-title a', 'a']
                },
                rate_limit=2.0,
                search_url_template="https://www.newegg.com/p/pl?d={query}&page={page}",
                base_url="https://www.newegg.com"
            ),
            
            'macys': RetailerConfig(
                name="Macy's",
                domain="macys.com",
                category=RetailerCategory.FASHION,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['.productThumbnail', '.product-thumbnail'],
                    'title': ['.product-title', '.productDescription'],
                    'price': ['.price', '.product-price'],
                    'rating': ['.rating', '.ratings'],
                    'availability': ['.availability', '.stock'],
                    'image': ['.product-image img', '.productThumbnailImage'],
                    'link': ['a']
                },
                rate_limit=2.5,
                search_url_template="https://www.macys.com/shop/search?keyword={query}&page={page}",
                base_url="https://www.macys.com"
            )
        })
        
        # TIER 3: Specialized Online Retailers (Medium-Low Priority)
        self.retailers.update({
            'overstock': RetailerConfig(
                name="Overstock",
                domain="overstock.com",
                category=RetailerCategory.HOME_IMPROVEMENT,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['.product-item', '.product'],
                    'title': ['.product-title', '.product-name'],
                    'price': ['.price', '.product-price'],
                    'rating': ['.rating', '.stars'],
                    'availability': ['.availability', '.stock'],
                    'image': ['.product-image img'],
                    'link': ['a']
                },
                rate_limit=3.0,
                search_url_template="https://www.overstock.com/search?keywords={query}&page={page}",
                base_url="https://www.overstock.com"
            ),
            
            'wayfair': RetailerConfig(
                name="Wayfair",
                domain="wayfair.com",
                category=RetailerCategory.HOME_IMPROVEMENT,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['[data-testid="ProductCard"]', '.ProductCard'],
                    'title': ['[data-testid="ProductName"]', '.ProductCard__name'],
                    'price': ['[data-testid="PrimaryPrice"]', '.ProductCard__price'],
                    'rating': ['[data-testid="StarsContainer"]', '.Stars'],
                    'availability': ['.fulfillment', '.availability'],
                    'image': ['[data-testid="ProductCardImage"]', '.ProductCard__image img'],
                    'link': ['a']
                },
                rate_limit=2.5,
                search_url_template="https://www.wayfair.com/keyword.php?keyword={query}&page={page}",
                base_url="https://www.wayfair.com"
            ),
            
            'zappos': RetailerConfig(
                name="Zappos",
                domain="zappos.com",
                category=RetailerCategory.FASHION,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['[data-testid="product-grid-item"]', '.product'],
                    'title': ['[data-testid="product-name"]', '.product-name'],
                    'price': ['[data-testid="product-price"]', '.product-price'],
                    'rating': ['[data-testid="product-rating"]', '.rating'],
                    'availability': ['.availability', '.stock'],
                    'image': ['[data-testid="product-image"]', '.product-image img'],
                    'link': ['a']
                },
                rate_limit=2.0,
                search_url_template="https://www.zappos.com/search?term={query}&page={page}",
                base_url="https://www.zappos.com"
            ),
            
            'bhphotovideo': RetailerConfig(
                name="B&H Photo",
                domain="bhphotovideo.com",
                category=RetailerCategory.ELECTRONICS,
                priority=RetailerPriority.MEDIUM,
                selectors={
                    'product_container': ['[data-selenium="itemInner"]', '.js-item-container'],
                    'title': ['[data-selenium="itemTitle"]', '.item-title'],
                    'price': ['[data-selenium="itemPrice"]', '.price'],
                    'rating': ['[data-selenium="itemRating"]', '.rating'],
                    'availability': ['[data-selenium="itemAvailability"]', '.availability'],
                    'image': ['[data-selenium="itemImage"]', '.item-image img'],
                    'link': ['a']
                },
                rate_limit=2.0,
                search_url_template="https://www.bhphotovideo.com/c/search?Ntt={query}&page={page}",
                base_url="https://www.bhphotovideo.com"
            ),
            
            'nordstrom': RetailerConfig(
                name="Nordstrom",
                domain="nordstrom.com",
                category=RetailerCategory.FASHION,
                priority=RetailerPriority.LOW,
                selectors={
                    'product_container': ['[data-testid="product-module"]', '.product-module'],
                    'title': ['[data-testid="product-title"]', '.product-title'],
                    'price': ['[data-testid="product-price"]', '.product-price'],
                    'rating': ['[data-testid="product-rating"]', '.rating'],
                    'availability': ['.availability', '.stock'],
                    'image': ['[data-testid="product-image"]', '.product-image img'],
                    'link': ['a']
                },
                rate_limit=3.0,
                search_url_template="https://www.nordstrom.com/sr?keyword={query}&page={page}",
                base_url="https://www.nordstrom.com"
            )
        })
        
        self.last_updated = datetime.utcnow()
        logger.info(f"✅ Initialized {len(self.retailers)} retailers across all categories")
    
    @performance_timer
    async def get_active_retailers(self, 
                                  category: Optional[RetailerCategory] = None,
                                  priority: Optional[RetailerPriority] = None) -> List[RetailerConfig]:
        """Get active retailers, optionally filtered by category and priority"""
        retailers = []
        
        for retailer_config in self.retailers.values():
            if retailer_config.status != "active":
                continue
                
            if category and retailer_config.category != category:
                continue
                
            if priority and retailer_config.priority != priority:
                continue
                
            retailers.append(retailer_config)
        
        # Sort by priority (high first)
        retailers.sort(key=lambda x: x.priority.value)
        return retailers
    
    @performance_timer
    async def get_retailer_config(self, retailer_key: str) -> Optional[RetailerConfig]:
        """Get configuration for a specific retailer"""
        return self.retailers.get(retailer_key)
    
    @performance_timer
    async def generate_search_urls(self, 
                                  retailer_key: str, 
                                  query: str, 
                                  pages: int = 2) -> List[str]:
        """Generate search URLs for a retailer"""
        config = await self.get_retailer_config(retailer_key)
        if not config:
            return []
        
        urls = []
        clean_query = re.sub(r'[^\w\s-]', '', query).strip()
        encoded_query = clean_query.replace(' ', '+')
        
        for page in range(1, pages + 1):
            try:
                url = config.search_url_template.format(
                    query=encoded_query,
                    page=page
                )
                urls.append(url)
            except Exception as e:
                logger.error(f"URL generation failed for {retailer_key}: {e}")
                
        return urls
    
    @performance_timer
    async def get_retailer_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all retailers"""
        stats = {
            'total_retailers': len(self.retailers),
            'active_retailers': len([r for r in self.retailers.values() if r.status == "active"]),
            'by_category': {},
            'by_priority': {},
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
        
        # Category breakdown
        for category in RetailerCategory:
            count = len([r for r in self.retailers.values() 
                        if r.category == category and r.status == "active"])
            stats['by_category'][category.value] = count
        
        # Priority breakdown
        for priority in RetailerPriority:
            count = len([r for r in self.retailers.values() 
                        if r.priority == priority and r.status == "active"])
            stats['by_priority'][priority.value] = count
        
        return stats
    
    @performance_timer
    async def add_retailer(self, retailer_key: str, config: RetailerConfig) -> bool:
        """Add a new retailer configuration"""
        try:
            self.retailers[retailer_key] = config
            self.last_updated = datetime.utcnow()
            logger.info(f"✅ Added new retailer: {config.name} ({retailer_key})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add retailer {retailer_key}: {e}")
            return False
    
    @performance_timer
    async def update_retailer_status(self, retailer_key: str, status: str) -> bool:
        """Update retailer status (active/inactive/maintenance)"""
        if retailer_key not in self.retailers:
            return False
        
        self.retailers[retailer_key].status = status
        self.last_updated = datetime.utcnow()
        logger.info(f"📝 Updated {retailer_key} status to: {status}")
        return True
    
    @performance_timer
    async def get_retailer_list_for_frontend(self) -> List[Dict[str, Any]]:
        """Get simplified retailer list for frontend consumption"""
        return [
            {
                'key': key,
                'name': config.name,
                'domain': config.domain,
                'category': config.category.value,
                'priority': config.priority.value,
                'status': config.status
            }
            for key, config in self.retailers.items()
            if config.status == "active"
        ]
    
    @performance_timer
    async def export_retailer_configs(self) -> Dict[str, Any]:
        """Export all retailer configurations for backup/migration"""
        return {
            'retailers': {key: config.to_dict() for key, config in self.retailers.items()},
            'metadata': {
                'total_count': len(self.retailers),
                'export_timestamp': datetime.utcnow().isoformat(),
                'version': "2.0"
            }
        }

# Global instance
retailer_manager = RetailerManager()