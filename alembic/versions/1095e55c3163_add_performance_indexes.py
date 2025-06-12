"""add_performance_indexes

Revision ID: 1095e55c3163
Revises: efff0d7ab253
Create Date: 2025-06-11 16:28:10.791161

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1095e55c3163'
down_revision: Union[str, None] = 'efff0d7ab253'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for search and foreign key operations."""
    # ### Performance indexes for Products table ###
    
    # Full-text search indexes for product name and category (PostgreSQL GIN)
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_name_gin ON products USING gin(to_tsvector('english', name))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_brand_gin ON products USING gin(to_tsvector('english', coalesce(brand, '')))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_category_gin ON products USING gin(to_tsvector('english', coalesce(category, '')))")
    
    # Regular indexes for filtering and sorting
    op.create_index('idx_products_category', 'products', ['category'])
    op.create_index('idx_products_brand', 'products', ['brand'])
    op.create_index('idx_products_is_processed', 'products', ['is_processed'])
    op.create_index('idx_products_is_active', 'products', ['is_active'])
    op.create_index('idx_products_created_at', 'products', ['created_at'])
    
    # Composite index for common queries
    op.create_index('idx_products_active_processed', 'products', ['is_active', 'is_processed'])
    
    ### Performance indexes for Analyses table ###
    
    # Foreign key index (critical for joins)
    op.create_index('idx_analyses_product_id', 'analyses', ['product_id'])
    
    # Analysis type and status filtering
    op.create_index('idx_analyses_type', 'analyses', ['analysis_type'])
    op.create_index('idx_analyses_status', 'analyses', ['status'])
    op.create_index('idx_analyses_created_at', 'analyses', ['created_at'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_analyses_product_type', 'analyses', ['product_id', 'analysis_type'])
    op.create_index('idx_analyses_product_status', 'analyses', ['product_id', 'status'])
    op.create_index('idx_analyses_type_status', 'analyses', ['analysis_type', 'status'])
    
    ### Performance indexes for Price Comparisons table ###
    
    # Foreign key index (critical for joins)
    op.create_index('idx_price_comparisons_product_id', 'price_comparisons', ['product_id'])
    
    # Source and filtering indexes
    op.create_index('idx_price_comparisons_source', 'price_comparisons', ['source_name'])
    op.create_index('idx_price_comparisons_is_valid', 'price_comparisons', ['is_valid'])
    op.create_index('idx_price_comparisons_in_stock', 'price_comparisons', ['in_stock'])
    op.create_index('idx_price_comparisons_scraped_at', 'price_comparisons', ['scraped_at'])
    
    # Price sorting and filtering (critical for price comparison queries)
    op.create_index('idx_price_comparisons_price', 'price_comparisons', ['price'])
    op.create_index('idx_price_comparisons_rating', 'price_comparisons', ['rating'])
    
    # Composite indexes for optimized price comparison queries
    op.create_index('idx_price_comparisons_product_valid', 'price_comparisons', ['product_id', 'is_valid'])
    op.create_index('idx_price_comparisons_product_price', 'price_comparisons', ['product_id', 'price'])
    op.create_index('idx_price_comparisons_source_valid', 'price_comparisons', ['source_name', 'is_valid'])
    op.create_index('idx_price_comparisons_valid_price_asc', 'price_comparisons', ['is_valid', 'price'])
    
    # Full-text search index for product titles in price comparisons
    op.execute("CREATE INDEX IF NOT EXISTS idx_price_comparisons_title_gin ON price_comparisons USING gin(to_tsvector('english', coalesce(title, '')))")


def downgrade() -> None:
    """Remove performance indexes."""
    # ### Drop indexes in reverse order ###
    
    # Price Comparisons indexes
    op.execute("DROP INDEX IF EXISTS idx_price_comparisons_title_gin")
    op.drop_index('idx_price_comparisons_valid_price_asc', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_source_valid', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_product_price', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_product_valid', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_rating', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_price', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_scraped_at', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_in_stock', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_is_valid', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_source', table_name='price_comparisons')
    op.drop_index('idx_price_comparisons_product_id', table_name='price_comparisons')
    
    # Analyses indexes
    op.drop_index('idx_analyses_type_status', table_name='analyses')
    op.drop_index('idx_analyses_product_status', table_name='analyses')
    op.drop_index('idx_analyses_product_type', table_name='analyses')
    op.drop_index('idx_analyses_created_at', table_name='analyses')
    op.drop_index('idx_analyses_status', table_name='analyses')
    op.drop_index('idx_analyses_type', table_name='analyses')
    op.drop_index('idx_analyses_product_id', table_name='analyses')
    
    # Products indexes
    op.drop_index('idx_products_active_processed', table_name='products')
    op.drop_index('idx_products_created_at', table_name='products')
    op.drop_index('idx_products_is_active', table_name='products')
    op.drop_index('idx_products_is_processed', table_name='products')
    op.drop_index('idx_products_brand', table_name='products')
    op.drop_index('idx_products_category', table_name='products')
    op.execute("DROP INDEX IF EXISTS idx_products_category_gin")
    op.execute("DROP INDEX IF EXISTS idx_products_brand_gin")
    op.execute("DROP INDEX IF EXISTS idx_products_name_gin")
