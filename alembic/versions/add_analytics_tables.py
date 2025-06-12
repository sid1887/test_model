"""Add analytics tables for forecasting and sentiment analysis

Revision ID: add_analytics_tables
Revises: 
Create Date: 2025-06-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON


# revision identifiers
revision = 'add_analytics_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create price_forecasts table
    op.create_table('price_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('forecast_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('forecast_horizon_days', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('confidence_interval', sa.Float(), nullable=True),
        sa.Column('historical_data_points', sa.Integer(), nullable=False),
        sa.Column('training_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('predictions', JSON(), nullable=False),
        sa.Column('validation_metrics', JSON(), nullable=True),
        sa.Column('accuracy_assessment', sa.String(length=20), nullable=True),
        sa.Column('trend_direction', sa.String(length=20), nullable=True),
        sa.Column('trend_strength_percent', sa.Float(), nullable=True),
        sa.Column('current_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('predicted_30day_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('price_change_percent', sa.Float(), nullable=True),
        sa.Column('best_buy_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('best_buy_price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_price_forecasts_id'), 'price_forecasts', ['id'], unique=False)

    # Create sentiment_analyses table
    op.create_table('sentiment_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('model_used', sa.String(length=50), nullable=False),
        sa.Column('total_reviews', sa.Integer(), nullable=False),
        sa.Column('processed_reviews', sa.Integer(), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('sentiment_label', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('detailed_scores', JSON(), nullable=True),
        sa.Column('topic_distribution', JSON(), nullable=True),
        sa.Column('top_topics', JSON(), nullable=True),
        sa.Column('individual_results', JSON(), nullable=True),
        sa.Column('positive_keywords', JSON(), nullable=True),
        sa.Column('negative_keywords', JSON(), nullable=True),
        sa.Column('subjectivity_score', sa.Float(), nullable=True),
        sa.Column('review_quality_score', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentiment_analyses_id'), 'sentiment_analyses', ['id'], unique=False)

    # Create forecast_validations table
    op.create_table('forecast_validations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('forecast_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('validation_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('validation_period_days', sa.Integer(), nullable=False),
        sa.Column('actual_data_points', sa.Integer(), nullable=False),
        sa.Column('mae', sa.Float(), nullable=True),
        sa.Column('mape', sa.Float(), nullable=True),
        sa.Column('rmse', sa.Float(), nullable=True),
        sa.Column('accuracy_band_10pct', sa.Float(), nullable=True),
        sa.Column('predictions_vs_actual', JSON(), nullable=True),
        sa.Column('accuracy_grade', sa.String(length=20), nullable=True),
        sa.Column('model_performance', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['forecast_id'], ['price_forecasts.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forecast_validations_id'), 'forecast_validations', ['id'], unique=False)

    # Create sentiment_trends table
    op.create_table('sentiment_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(length=20), nullable=True),
        sa.Column('avg_sentiment_score', sa.Float(), nullable=False),
        sa.Column('sentiment_change', sa.Float(), nullable=True),
        sa.Column('sentiment_volatility', sa.Float(), nullable=True),
        sa.Column('total_reviews', sa.Integer(), nullable=False),
        sa.Column('positive_reviews', sa.Integer(), nullable=False),
        sa.Column('negative_reviews', sa.Integer(), nullable=False),
        sa.Column('neutral_reviews', sa.Integer(), nullable=False),
        sa.Column('trend_direction', sa.String(length=20), nullable=True),
        sa.Column('trend_strength', sa.Float(), nullable=True),
        sa.Column('trending_topics', JSON(), nullable=True),
        sa.Column('topic_changes', JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sentiment_trends_id'), 'sentiment_trends', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_sentiment_trends_id'), table_name='sentiment_trends')
    op.drop_table('sentiment_trends')
    op.drop_index(op.f('ix_forecast_validations_id'), table_name='forecast_validations')
    op.drop_table('forecast_validations')
    op.drop_index(op.f('ix_sentiment_analyses_id'), table_name='sentiment_analyses')
    op.drop_table('sentiment_analyses')
    op.drop_index(op.f('ix_price_forecasts_id'), table_name='price_forecasts')
    op.drop_table('price_forecasts')
