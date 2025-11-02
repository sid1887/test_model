"""
Price forecast worker tasks
"""
from app.core.database import SessionLocal


async def generate_forecast(product_id: int):
    """Background task for price forecasting"""
    db = SessionLocal()
    try:
        # Forecasting logic
        return {"product_id": product_id, "status": "completed"}
    finally:
        db.close()
