"""Add price alerts and smart lists tables

Revision ID: add_alerts_smartlists
Revises: add_analytics_tables
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON


# revision identifiers
revision = 'add_alerts_smartlists'
down_revision = 'add_analytics_tables'
branch_labels = None
depends_on = None


def upgrade():
    # ============================================================================
    # PRICE ALERTS TABLES
    # ============================================================================
    
    # Create price_alerts table
    op.create_table('price_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('target_price', sa.Float(), nullable=False),
        sa.Column('operator', sa.String(length=20), nullable=False),
        sa.Column('retailers', JSON(), nullable=True),
        sa.Column('channels', JSON(), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.Column('last_fired_at', sa.DateTime(), nullable=True),
        sa.Column('fire_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_price_alerts_user_id', 'price_alerts', ['user_id'], unique=False)
    op.create_index('ix_price_alerts_product_id', 'price_alerts', ['product_id'], unique=False)
    op.create_index('ix_price_alerts_status', 'price_alerts', ['status'], unique=False)
    
    # Create alert_events table
    op.create_table('alert_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('previous_price', sa.Float(), nullable=True),
        sa.Column('retailer_id', sa.Integer(), nullable=True),
        sa.Column('event_payload', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['alert_id'], ['price_alerts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_events_alert_id', 'alert_events', ['alert_id'], unique=False)
    op.create_index('ix_alert_events_created_at', 'alert_events', ['created_at'], unique=False)
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('recipient', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('external_id', sa.String(length=200), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['alert_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_event_id', 'notifications', ['event_id'], unique=False)
    op.create_index('ix_notifications_status', 'notifications', ['status'], unique=False)
    
    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('whatsapp', sa.String(length=20), nullable=True),
        sa.Column('push_token', sa.String(length=500), nullable=True),
        sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sms_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('whatsapp_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('max_notifications_per_hour', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_notifications_per_day', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default="'UTC'"),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'], unique=True)
    
    # ============================================================================
    # SMART LISTS TABLES
    # ============================================================================
    
    # Create smart_lists table
    op.create_table('smart_lists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', JSON(), nullable=True),
        sa.Column('default_retailers', JSON(), nullable=True),
        sa.Column('auto_monitor', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('auto_monitor_threshold', sa.Float(), nullable=True),
        sa.Column('visibility', sa.String(length=20), nullable=False, server_default="'private'"),
        sa.Column('share_token', sa.String(length=50), nullable=True),
        sa.Column('item_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_value', sa.Float(), nullable=True),
        sa.Column('last_compared_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_smart_lists_user_id', 'smart_lists', ['user_id'], unique=False)
    op.create_index('ix_smart_lists_share_token', 'smart_lists', ['share_token'], unique=True)
    
    # Create smart_list_items table
    op.create_table('smart_list_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('desired_price', sa.Float(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default="'normal'"),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('added_price', sa.Float(), nullable=True),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('best_retailer_id', sa.Integer(), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('alert_created', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['list_id'], ['smart_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_smart_list_items_list_id', 'smart_list_items', ['list_id'], unique=False)
    op.create_index('ix_smart_list_items_product_id', 'smart_list_items', ['product_id'], unique=False)
    
    # Create list_compare_jobs table
    op.create_table('list_compare_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('list_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default="'pending'"),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('retailers', JSON(), nullable=True),
        sa.Column('results', JSON(), nullable=True),
        sa.Column('total_savings', sa.Float(), nullable=True),
        sa.Column('best_store_overall', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['list_id'], ['smart_lists.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_list_compare_jobs_list_id', 'list_compare_jobs', ['list_id'], unique=False)
    op.create_index('ix_list_compare_jobs_user_id', 'list_compare_jobs', ['user_id'], unique=False)
    op.create_index('ix_list_compare_jobs_status', 'list_compare_jobs', ['status'], unique=False)
    
    # Create list_templates table
    op.create_table('list_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_items', JSON(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_list_templates_category', 'list_templates', ['category'], unique=False)
    op.create_index('ix_list_templates_is_featured', 'list_templates', ['is_featured'], unique=False)


def downgrade():
    # Drop smart lists tables
    op.drop_index('ix_list_templates_is_featured', table_name='list_templates')
    op.drop_index('ix_list_templates_category', table_name='list_templates')
    op.drop_table('list_templates')
    
    op.drop_index('ix_list_compare_jobs_status', table_name='list_compare_jobs')
    op.drop_index('ix_list_compare_jobs_user_id', table_name='list_compare_jobs')
    op.drop_index('ix_list_compare_jobs_list_id', table_name='list_compare_jobs')
    op.drop_table('list_compare_jobs')
    
    op.drop_index('ix_smart_list_items_product_id', table_name='smart_list_items')
    op.drop_index('ix_smart_list_items_list_id', table_name='smart_list_items')
    op.drop_table('smart_list_items')
    
    op.drop_index('ix_smart_lists_share_token', table_name='smart_lists')
    op.drop_index('ix_smart_lists_user_id', table_name='smart_lists')
    op.drop_table('smart_lists')
    
    # Drop price alerts tables
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
    
    op.drop_index('ix_notifications_status', table_name='notifications')
    op.drop_index('ix_notifications_event_id', table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index('ix_alert_events_created_at', table_name='alert_events')
    op.drop_index('ix_alert_events_alert_id', table_name='alert_events')
    op.drop_table('alert_events')
    
    op.drop_index('ix_price_alerts_status', table_name='price_alerts')
    op.drop_index('ix_price_alerts_product_id', table_name='price_alerts')
    op.drop_index('ix_price_alerts_user_id', table_name='price_alerts')
    op.drop_table('price_alerts')
