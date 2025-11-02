"""
Price comparison worker tasks
"""
from app.core.database import SessionLocal


async def compare_prices(list_id: int):
    """Background task for price comparison"""
    db = SessionLocal()
    try:
        # Price comparison logic
        return {"list_id": list_id, "status": "completed"}
    finally:
        db.close()
