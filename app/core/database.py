"""
Database configuration and initialization
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
import asyncpg
from app.core.config import settings

# Database engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug
)

# Session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

def get_db_session():
    """Context manager for getting database session"""
    return async_session_maker()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.models.product import Product
        from app.models.analysis import Analysis
        from app.models.price_comparison import PriceComparison
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
