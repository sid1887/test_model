"""
Simplified database configuration for Alembic migrations
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Use a simple connection string for migrations
DATABASE_URL = "postgresql+asyncpg://compair:compair123@localhost:5432/compair"

# Database engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """Base class for all database models"""
    metadata = MetaData()
