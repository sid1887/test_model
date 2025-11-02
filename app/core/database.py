"""
Database configuration and initialization
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy import MetaData, create_engine
import asyncpg
from app.core.config import settings

# Async database engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.debug
)

# Sync database engine (for workers and background tasks)
sync_engine = create_engine(
    settings.database_url.replace("postgresql://", "postgresql://"),
    echo=settings.debug
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync session factory (for workers)
SessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
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
