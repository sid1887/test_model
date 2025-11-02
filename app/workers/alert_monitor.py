"""
Alert monitoring worker tasks
"""
from app.core.database import SessionLocal
from app.models.alert import PriceAlert


async def monitor_alerts():
    """Background task to monitor and trigger alerts"""
    db = SessionLocal()
    try:
        alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).all()
        # Alert monitoring logic here
        return {"monitored": len(alerts)}
    finally:
        db.close()
