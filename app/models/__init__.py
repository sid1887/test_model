# Models Package - All ORM models matching database schema
from .product import Product
from .product_price import ProductPrice
from .embedding import Embedding
from .raw_scrape import RawScrape
from .alert import PriceAlert, AlertEvent, Notification, UserPreferences
from .retailer import Retailer
from .smart_list import SmartList, SmartListItem, ListCompareJob, ListTemplate
from .analytics_insight import AnalyticsInsight
from .analysis import Analysis
from .analytics import PriceForecast, SentimentAnalysis, ForecastValidation, SentimentTrend
from .price_comparison import PriceComparison, PriceHistory
from .product_snapshot import ProductSnapshot
from .user import User

# Alias for backward compatibility
AlertHistory = AlertEvent

__all__ = [
    "Product",
    "ProductPrice",
    "Embedding",
    "RawScrape",
    "PriceAlert",
    "AlertEvent",
    "AlertHistory",
    "Notification",
    "UserPreferences",
    "Retailer",
    "SmartList",
    "SmartListItem",
    "ListCompareJob",
    "ListTemplate",
    "AnalyticsInsight",
    "Analysis",
    "PriceForecast",
    "SentimentAnalysis",
    "ForecastValidation",
    "SentimentTrend",
    "PriceComparison",
    "PriceHistory",
    "ProductSnapshot",
    "User",
]
