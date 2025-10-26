"""
Celery worker configuration for background task processing
Handles image analysis, web scraping, price alerts, and notifications
"""

from celery import Celery
from celery.utils.log import get_task_logger
import asyncio
import os
from typing import Dict, Any, List
from datetime import datetime

from app.core.config import settings
from app.core.monitoring import ACTIVE_TASKS
from app.core.metrics import track_celery_task, get_metrics_manager
import time

# Configure Celery
celery_app = Celery(
    "cumpair",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.worker']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_compression='gzip',  # Compress task data
    result_compression='gzip',  # Compress results
    task_routes={
        'analyze_image': {'queue': 'image_processing'},
        'scrape_prices': {'queue': 'web_scraping'},
        'full_product_analysis': {'queue': 'image_processing'},
    },
    task_annotations={
        '*': {'rate_limit': '10/s'},
        'scrape_prices': {'rate_limit': '5/s'},  # Lower rate for scraping
    },
    worker_hijack_root_logger=False,  # Don't hijack logging
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
)

logger = get_task_logger(__name__)

@celery_app.task(bind=True, name='analyze_image')
def analyze_image_task(self, image_path: str, product_id: int) -> Dict[str, Any]:
    """
    Background task for image analysis
    
    Args:
        image_path: Path to the uploaded image
        product_id: Database ID of the product record
        
    Returns:
        Analysis results
    """
    ACTIVE_TASKS.inc()
    
    try:
        logger.info(f"Starting image analysis for product {product_id}")
        
        # Import here to avoid circular imports
        from app.services.image_analysis import image_analysis_service
        
        # Perform analysis
        result = image_analysis_service.analyze_image(image_path)
        
        # Update database with results
        asyncio.run(update_analysis_results(product_id, result))
        
        logger.info(f"Image analysis completed for product {product_id}")
        return result
        
    except Exception as e:
        logger.error(f"Image analysis failed for product {product_id}: {e}")
        # Update database with error
        asyncio.run(update_analysis_error(product_id, str(e)))
        raise
    finally:
        ACTIVE_TASKS.dec()

@celery_app.task(bind=True, name='scrape_prices')
def scrape_prices_task(self, product_id: int, search_queries: list) -> Dict[str, Any]:
    """
    Background task for price scraping
    
    Args:
        product_id: Database ID of the product
        search_queries: List of search queries to use
        
    Returns:
        Scraping results
    """
    ACTIVE_TASKS.inc()
    
    try:
        logger.info(f"Starting price scraping for product {product_id}")
        
        # Import here to avoid circular imports
        from app.services.price_comparison import price_comparison_service
        
        # Perform scraping
        result = asyncio.run(
            price_comparison_service.compare_prices(product_id, search_queries)
        )
        
        logger.info(f"Price scraping completed for product {product_id}")
        return result
        
    except Exception as e:
        logger.error(f"Price scraping failed for product {product_id}: {e}")
        raise
    finally:
        ACTIVE_TASKS.dec()

@celery_app.task(bind=True, name='full_product_analysis')
def full_product_analysis_task(self, image_path: str, product_id: int) -> Dict[str, Any]:
    """
    Complete product analysis pipeline: image analysis + price comparison
    
    Args:
        image_path: Path to the uploaded image
        product_id: Database ID of the product
        
    Returns:
        Complete analysis results
    """
    ACTIVE_TASKS.inc()
    
    try:
        logger.info(f"Starting full analysis for product {product_id}")
        
        # Step 1: Image Analysis
        analysis_result = analyze_image_task.apply_async(
            args=[image_path, product_id]
        ).get()
        
        # Step 2: Generate search queries from analysis
        search_queries = generate_search_queries(analysis_result)
        
        # Step 3: Price Comparison
        price_result = scrape_prices_task.apply_async(
            args=[product_id, search_queries]
        ).get()
        
        # Combine results
        complete_result = {
            'analysis': analysis_result,
            'price_comparison': price_result,
            'status': 'completed'
        }
        
        logger.info(f"Full analysis completed for product {product_id}")
        return complete_result
        
    except Exception as e:
        logger.error(f"Full analysis failed for product {product_id}: {e}")
        raise
    finally:
        ACTIVE_TASKS.dec()

async def update_analysis_results(product_id: int, results: Dict):
    """Update database with analysis results"""
    try:
        from app.core.database import async_session_maker
        from app.models.product import Product
        from app.models.analysis import Analysis
        from sqlalchemy import select
        
        async with async_session_maker() as session:
            # Update product
            stmt = select(Product).where(Product.id == product_id)
            result = await session.execute(stmt)
            product = result.scalar_one_or_none()
            
            if product:
                # Update product specifications
                if 'specification_extraction' in results:
                    product.specifications = results['specification_extraction'].get('specifications', {})
                
                # Update confidence scores
                if 'object_detection' in results:
                    detections = results['object_detection'].get('detections', [])
                    if detections:
                        product.detection_confidence = detections[0].get('confidence', 0)
                
                product.is_processed = True
                
                # Create analysis record
                analysis = Analysis(
                    product_id=product_id,
                    analysis_type='complete',
                    raw_results=results,
                    confidence_score=results.get('confidence', 0),
                    processing_time=results.get('total_processing_time', 0),
                    status='completed'
                )
                
                session.add(analysis)
                await session.commit()
                
    except Exception as e:
        logger.error(f"Failed to update analysis results: {e}")

async def update_analysis_error(product_id: int, error_message: str):
    """Update database with analysis error"""
    try:
        from app.core.database import async_session_maker
        from app.models.analysis import Analysis
        
        async with async_session_maker() as session:
            analysis = Analysis(
                product_id=product_id,
                analysis_type='complete',
                status='failed',
                error_message=error_message
            )
            
            session.add(analysis)
            await session.commit()
            
    except Exception as e:
        logger.error(f"Failed to update analysis error: {e}")

def generate_search_queries(analysis_result: Dict) -> list:
    """Generate search queries based on analysis results"""
    queries = []
    
    # Extract product information
    detections = analysis_result.get('object_detection', {}).get('detections', [])
    specs = analysis_result.get('specification_extraction', {}).get('specifications', {})
    
    # Base query from detected objects
    if detections:
        for detection in detections[:3]:  # Top 3 detections
            class_name = detection.get('class_name', '')
            if class_name:
                queries.append(class_name)
    
    # Enhanced queries with specifications
    if specs.get('detected_text'):
        for text in specs['detected_text'][:2]:
            queries.append(text)
    
    # Fallback generic queries
    if not queries:
        queries = ['product', 'item', 'electronics']
    
    return queries[:5]  # Limit to 5 queries

# Health check task
@celery_app.task(name='health_check')
def health_check():
    """Simple health check task"""
    import time
    return {"status": "healthy", "timestamp": time.time()}


# ============================================================================
# PRICE ALERT MONITORING TASKS
# ============================================================================

@celery_app.task(bind=True, name='alert_monitor_task')
def alert_monitor_task(self):
    """
    Periodic task to check all active price alerts
    Runs every 15 minutes to monitor price changes
    """
    start_time = time.time()
    try:
        logger.info("Starting alert monitor task")
        
        # Import here to avoid circular imports
        from app.api.routes.alerts import check_and_trigger_alerts
        
        result = asyncio.run(check_and_trigger_alerts())
        
        duration = time.time() - start_time
        track_celery_task('alert_monitor', 'success', duration)
        
        logger.info(f"Alert monitor task completed: {result}")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        track_celery_task('alert_monitor', 'failed', duration)
        logger.error(f"Alert monitor task failed: {e}")
        raise


@celery_app.task(bind=True, name='notification_sender_task')
def notification_sender_task(self, notification_id: int):
    """
    Send notification via configured channel
    
    Args:
        notification_id: Database ID of the notification to send
    """
    start_time = time.time()
    try:
        logger.info(f"Sending notification {notification_id}")
        
        from app.services.notifications import notification_service
        
        result = asyncio.run(notification_service.send_notification(notification_id))
        
        duration = time.time() - start_time
        track_celery_task('notification_sender', 'success', duration)
        
        logger.info(f"Notification {notification_id} sent successfully")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        track_celery_task('notification_sender', 'failed', duration)
        logger.error(f"Failed to send notification {notification_id}: {e}")
        raise


# ============================================================================
# SMART LIST TASKS
# ============================================================================

@celery_app.task(bind=True, name='compare_prices_task')
def compare_prices_task(self, list_id: int):
    """
    Compare prices for all items in a smart list
    
    Args:
        list_id: Database ID of the smart list
    """
    start_time = time.time()
    try:
        logger.info(f"Comparing prices for list {list_id}")
        
        from app.api.routes.smart_lists import compare_list_prices
        
        result = asyncio.run(compare_list_prices(list_id))
        
        duration = time.time() - start_time
        track_celery_task('compare_prices', 'success', duration)
        
        logger.info(f"Price comparison completed for list {list_id}")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        track_celery_task('compare_prices', 'failed', duration)
        logger.error(f"Price comparison failed for list {list_id}: {e}")
        raise


# ============================================================================
# ANALYTICS TASKS
# ============================================================================

@celery_app.task(bind=True, name='generate_forecast_task')
def generate_forecast_task(self, product_id: int):
    """
    Generate price forecast for a product
    
    Args:
        product_id: Database ID of the product
    """
    start_time = time.time()
    try:
        logger.info(f"Generating forecast for product {product_id}")
        
        from app.api.routes.analytics import generate_price_forecast
        
        result = asyncio.run(generate_price_forecast(product_id))
        
        duration = time.time() - start_time
        track_celery_task('generate_forecast', 'success', duration)
        
        logger.info(f"Forecast generated for product {product_id}")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        track_celery_task('generate_forecast', 'failed', duration)
        logger.error(f"Forecast generation failed for product {product_id}: {e}")
        raise


@celery_app.task(bind=True, name='analyze_sentiment_task')
def analyze_sentiment_task(self, product_id: int):
    """
    Analyze sentiment from product reviews
    
    Args:
        product_id: Database ID of the product
    """
    start_time = time.time()
    try:
        logger.info(f"Analyzing sentiment for product {product_id}")
        
        from app.api.routes.analytics import analyze_product_sentiment
        
        result = asyncio.run(analyze_product_sentiment(product_id))
        
        duration = time.time() - start_time
        track_celery_task('analyze_sentiment', 'success', duration)
        
        logger.info(f"Sentiment analysis completed for product {product_id}")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        track_celery_task('analyze_sentiment', 'failed', duration)
        logger.error(f"Sentiment analysis failed for product {product_id}: {e}")
        raise


if __name__ == '__main__':
    celery_app.start()
