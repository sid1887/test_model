"""
Pricing Analytics & Sentiment Analysis Service for Cumpair
Implements Prophet forecasting and advanced sentiment analysis
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Any, Optional, Tuple
import logging
import asyncio
from datetime import datetime, timedelta
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.price_comparison import PriceComparison
from app.models.product import Product

logger = logging.getLogger(__name__)

class SentimentModel:
    """Sentiment analysis model configurations"""
    VADER = "vader"
    TEXTBLOB = "textblob"
    HUGGINGFACE = "huggingface"
    ENSEMBLE = "ensemble"

class ForecastMetrics:
    """Forecast validation metrics"""
    def __init__(self):
        self.mae = 0.0  # Mean Absolute Error
        self.mape = 0.0  # Mean Absolute Percentage Error
        self.rmse = 0.0  # Root Mean Square Error
        self.accuracy_band = 0.0  # Percentage within 10% of actual

class PricingAnalyticsService:
    """Advanced pricing analytics with Prophet forecasting"""
    
    def __init__(self):
        self.prophet_models = {}
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.hf_sentiment_pipeline = None
        self._init_hf_models()
    
    def _init_hf_models(self):
        """Initialize HuggingFace sentiment models"""
        try:
            # Load pre-trained sentiment model for product reviews
            self.hf_sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                tokenizer="nlptown/bert-base-multilingual-uncased-sentiment",
                return_all_scores=True
            )
            logger.info("HuggingFace sentiment model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load HuggingFace model: {e}")
            self.hf_sentiment_pipeline = None
    
    async def generate_price_forecast(
        self,
        product_id: int,
        db: AsyncSession,
        forecast_days: int = 30,
        confidence_interval: float = 0.8
    ) -> Dict[str, Any]:
        """
        Generate price forecasts using Prophet
        
        Args:
            product_id: Product ID for forecasting
            db: Database session
            forecast_days: Number of days to forecast
            confidence_interval: Confidence interval for predictions
            
        Returns:
            Forecast data with validation metrics
        """
        try:
            # Fetch historical price data
            price_history = await self._get_price_history(product_id, db)
            
            if len(price_history) < 10:
                raise ValueError(f"Insufficient price history data: {len(price_history)} points")
            
            # Prepare data for Prophet
            prophet_df = self._prepare_prophet_data(price_history)
            
            # Create and fit Prophet model
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=confidence_interval,
                changepoint_prior_scale=0.1,  # Control flexibility
                seasonality_prior_scale=10.0
            )
            
            # Add custom regressors if available
            self._add_custom_regressors(model, prophet_df)
            
            # Fit model
            model.fit(prophet_df)
            
            # Generate future dataframe
            future = model.make_future_dataframe(periods=forecast_days)
            
            # Make predictions
            forecast = model.predict(future)
            
            # Calculate validation metrics
            validation_metrics = await self._validate_forecast(
                model, prophet_df, forecast_days=7  # Use last 7 days for validation
            )
            
            # Prepare response
            forecast_data = {
                'product_id': product_id,
                'forecast_date': datetime.now().isoformat(),
                'forecast_horizon_days': forecast_days,
                'confidence_interval': confidence_interval,
                'historical_data_points': len(price_history),
                'predictions': self._format_predictions(forecast, len(price_history)),
                'validation_metrics': validation_metrics,
                'trend_analysis': self._analyze_price_trend(forecast),
                'price_insights': await self._generate_price_insights(forecast, price_history)
            }
            
            # Store model for future use
            self.prophet_models[product_id] = model
            
            return forecast_data
            
        except Exception as e:
            logger.error(f"Price forecasting failed for product {product_id}: {e}")
            raise Exception(f"Price forecast error: {e}")
    
    async def analyze_review_sentiment(
        self,
        reviews: List[str],
        model: SentimentModel = SentimentModel.ENSEMBLE,
        include_topics: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of product reviews using multiple models
        
        Args:
            reviews: List of review texts
            model: Sentiment model to use
            include_topics: Whether to include topic analysis
            
        Returns:
            Comprehensive sentiment analysis results
        """
        try:
            if not reviews:
                return {
                    'sentiment_score': 0.0,
                    'sentiment_label': 'neutral',
                    'confidence': 0.0,
                    'total_reviews': 0,
                    'model_used': model
                }
            
            # Clean reviews
            cleaned_reviews = [self._clean_review_text(review) for review in reviews]
            cleaned_reviews = [r for r in cleaned_reviews if len(r.strip()) > 10]
            
            if not cleaned_reviews:
                raise ValueError("No valid reviews after cleaning")
            
            sentiment_results = {}
            
            if model == SentimentModel.VADER or model == SentimentModel.ENSEMBLE:
                sentiment_results['vader'] = await self._analyze_vader_sentiment(cleaned_reviews)
            
            if model == SentimentModel.TEXTBLOB or model == SentimentModel.ENSEMBLE:
                sentiment_results['textblob'] = await self._analyze_textblob_sentiment(cleaned_reviews)
            
            if model == SentimentModel.HUGGINGFACE or model == SentimentModel.ENSEMBLE:
                if self.hf_sentiment_pipeline:
                    sentiment_results['huggingface'] = await self._analyze_hf_sentiment(cleaned_reviews)
            
            # Ensemble or single model result
            if model == SentimentModel.ENSEMBLE:
                final_sentiment = self._ensemble_sentiment(sentiment_results)
            else:
                final_sentiment = sentiment_results.get(model.lower(), {})
            
            # Add topic analysis if requested
            if include_topics:
                final_sentiment['topics'] = await self._extract_review_topics(cleaned_reviews)
            
            # Add review statistics
            final_sentiment.update({
                'total_reviews': len(reviews),
                'processed_reviews': len(cleaned_reviews),
                'model_used': model,
                'analysis_date': datetime.now().isoformat()
            })
            
            return final_sentiment
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            raise Exception(f"Sentiment analysis error: {e}")
    
    async def validate_forecast_accuracy(
        self,
        product_id: int,
        db: AsyncSession,
        validation_days: int = 30
    ) -> Dict[str, Any]:
        """
        Validate forecast accuracy using historical data
        
        Args:
            product_id: Product ID
            db: Database session
            validation_days: Days to use for validation
            
        Returns:
            Validation metrics and accuracy assessment
        """
        try:
            # Get historical data
            price_history = await self._get_price_history(product_id, db, days=validation_days + 30)
            
            if len(price_history) < validation_days + 10:
                raise ValueError("Insufficient data for validation")
            
            # Split data (use first part for training, last part for validation)
            split_point = len(price_history) - validation_days
            train_data = price_history[:split_point]
            validation_data = price_history[split_point:]
            
            # Train model on historical data
            prophet_df = self._prepare_prophet_data(train_data)
            model = Prophet()
            model.fit(prophet_df)
            
            # Generate predictions for validation period
            future = model.make_future_dataframe(periods=validation_days)
            forecast = model.predict(future)
            
            # Get prediction values for validation period
            predictions = forecast['yhat'].tail(validation_days).values
            actual_values = [p['price'] for p in validation_data]
            
            # Calculate metrics
            metrics = self._calculate_forecast_metrics(predictions, actual_values)
            
            return {
                'product_id': product_id,
                'validation_period_days': validation_days,
                'data_points_used': len(train_data),
                'validation_points': len(validation_data),
                'metrics': metrics,
                'accuracy_assessment': self._assess_forecast_accuracy(metrics),
                'validation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Forecast validation failed: {e}")
            raise Exception(f"Forecast validation error: {e}")
    
    async def _get_price_history(
        self, 
        product_id: int, 
        db: AsyncSession,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """Fetch price history from database"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            stmt = select(PriceComparison).where(
                and_(
                    PriceComparison.product_id == product_id,
                    PriceComparison.price_updated_at >= cutoff_date,
                    PriceComparison.price.isnot(None)
                )
            ).order_by(PriceComparison.price_updated_at)
            
            result = await db.execute(stmt)
            price_records = result.scalars().all()
            
            # Convert to price history format
            price_history = []
            for record in price_records:
                price_history.append({
                    'date': record.price_updated_at,
                    'price': float(record.price),
                    'source': record.source_name,
                    'currency': record.currency or 'USD'
                })
            
            return price_history
            
        except Exception as e:
            logger.error(f"Failed to fetch price history: {e}")
            return []
    
    def _prepare_prophet_data(self, price_history: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare data for Prophet model"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(price_history)
            
            # Aggregate by date (in case multiple prices per day)
            df['ds'] = pd.to_datetime(df['date']).dt.date
            df_agg = df.groupby('ds').agg({
                'price': 'mean'  # Use average price if multiple sources
            }).reset_index()
            
            # Rename columns for Prophet
            df_agg['ds'] = pd.to_datetime(df_agg['ds'])
            df_agg.rename(columns={'price': 'y'}, inplace=True)
            
            return df_agg
            
        except Exception as e:
            logger.error(f"Prophet data preparation failed: {e}")
            raise
    
    def _add_custom_regressors(self, model: Prophet, df: pd.DataFrame):
        """Add custom regressors to Prophet model"""
        try:
            # Add day of week effect
            df['day_of_week'] = df['ds'].dt.dayofweek
            model.add_regressor('day_of_week')
            
            # Add month effect  
            df['month'] = df['ds'].dt.month
            model.add_regressor('month')
            
        except Exception as e:
            logger.warning(f"Failed to add custom regressors: {e}")
    
    async def _validate_forecast(
        self,
        model: Prophet,
        df: pd.DataFrame,
        forecast_days: int = 7
    ) -> Dict[str, float]:
        """Validate forecast using cross-validation"""
        try:
            if len(df) < forecast_days + 5:
                return {'error': 'insufficient_data'}
            
            # Use last few days for validation
            train_df = df.iloc[:-forecast_days]
            validation_df = df.iloc[-forecast_days:]
            
            # Make predictions
            future = model.make_future_dataframe(periods=forecast_days, freq='D')
            forecast = model.predict(future)
            
            # Get predictions for validation period
            predictions = forecast['yhat'].tail(forecast_days).values
            actual_values = validation_df['y'].values
            
            # Calculate metrics
            return self._calculate_forecast_metrics(predictions, actual_values)
            
        except Exception as e:
            logger.error(f"Forecast validation failed: {e}")
            return {'error': str(e)}
    
    def _calculate_forecast_metrics(
        self, 
        predictions: np.ndarray, 
        actual_values: np.ndarray
    ) -> Dict[str, float]:
        """Calculate forecast accuracy metrics"""
        try:
            if len(predictions) != len(actual_values):
                raise ValueError("Prediction and actual arrays must have same length")
            
            # Remove any NaN values
            mask = ~(np.isnan(predictions) | np.isnan(actual_values))
            pred_clean = predictions[mask]
            actual_clean = actual_values[mask]
            
            if len(pred_clean) == 0:
                return {'error': 'no_valid_data'}
            
            # Calculate metrics
            mae = np.mean(np.abs(pred_clean - actual_clean))
            mape = np.mean(np.abs((actual_clean - pred_clean) / actual_clean)) * 100
            rmse = np.sqrt(np.mean((pred_clean - actual_clean) ** 2))
            
            # Accuracy within 10% band
            within_10_percent = np.sum(np.abs((actual_clean - pred_clean) / actual_clean) <= 0.1)
            accuracy_band = (within_10_percent / len(actual_clean)) * 100
            
            return {
                'mae': round(float(mae), 2),
                'mape': round(float(mape), 2),
                'rmse': round(float(rmse), 2),
                'accuracy_band_10pct': round(float(accuracy_band), 2),
                'data_points': len(actual_clean)
            }
            
        except Exception as e:
            logger.error(f"Metrics calculation failed: {e}")
            return {'error': str(e)}
    
    def _format_predictions(self, forecast: pd.DataFrame, historical_points: int) -> List[Dict[str, Any]]:
        """Format predictions for API response"""
        try:
            predictions = []
            
            for i, row in forecast.iterrows():
                prediction = {
                    'date': row['ds'].isoformat(),
                    'predicted_price': round(float(row['yhat']), 2),
                    'lower_bound': round(float(row['yhat_lower']), 2),
                    'upper_bound': round(float(row['yhat_upper']), 2),
                    'is_historical': i < historical_points
                }
                predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Prediction formatting failed: {e}")
            return []
    
    def _analyze_price_trend(self, forecast: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price trends from forecast"""
        try:
            # Get trend component
            trend = forecast['trend'].values
            
            # Calculate trend direction
            recent_trend = trend[-7:]  # Last 7 days
            older_trend = trend[-14:-7]  # Previous 7 days
            
            recent_avg = np.mean(recent_trend)
            older_avg = np.mean(older_trend)
            
            trend_direction = "stable"
            trend_strength = abs(recent_avg - older_avg) / older_avg * 100
            
            if recent_avg > older_avg * 1.02:
                trend_direction = "increasing"
            elif recent_avg < older_avg * 0.98:
                trend_direction = "decreasing"
            
            return {
                'direction': trend_direction,
                'strength_percent': round(float(trend_strength), 2),
                'recent_average': round(float(recent_avg), 2),
                'previous_average': round(float(older_avg), 2)
            }
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return {'error': str(e)}
    
    async def _generate_price_insights(
        self,
        forecast: pd.DataFrame,
        price_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate actionable price insights"""
        try:
            current_price = price_history[-1]['price'] if price_history else 0
            predicted_prices = forecast['yhat'].tail(30).values  # Next 30 days
            
            # Price change analysis
            price_change = predicted_prices[-1] - current_price
            price_change_percent = (price_change / current_price) * 100 if current_price > 0 else 0
            
            # Volatility analysis
            volatility = np.std(predicted_prices)
            
            # Best time to buy
            min_price_idx = np.argmin(predicted_prices)
            best_buy_date = forecast['ds'].tail(30).iloc[min_price_idx]
            
            insights = {
                'current_price': round(float(current_price), 2),
                'predicted_30day_price': round(float(predicted_prices[-1]), 2),
                'price_change_amount': round(float(price_change), 2),
                'price_change_percent': round(float(price_change_percent), 2),
                'volatility': round(float(volatility), 2),
                'best_buy_date': best_buy_date.isoformat(),
                'best_buy_price': round(float(predicted_prices[min_price_idx]), 2),
                'recommendation': self._generate_price_recommendation(price_change_percent, volatility)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Price insights generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_price_recommendation(self, price_change_percent: float, volatility: float) -> str:
        """Generate price recommendation based on forecast"""
        if price_change_percent > 5:
            return "Consider buying soon - price expected to increase"
        elif price_change_percent < -5:
            return "Wait for better pricing - price expected to decrease"
        elif volatility > 20:
            return "Monitor closely - high price volatility expected"
        else:
            return "Stable pricing expected - buy when convenient"
    
    async def _analyze_vader_sentiment(self, reviews: List[str]) -> Dict[str, Any]:
        """Analyze sentiment using VADER"""
        try:
            scores = []
            for review in reviews:
                score = self.sentiment_analyzer.polarity_scores(review)
                scores.append(score)
            
            # Aggregate scores
            avg_scores = {
                'positive': np.mean([s['pos'] for s in scores]),
                'negative': np.mean([s['neg'] for s in scores]),
                'neutral': np.mean([s['neu'] for s in scores]),
                'compound': np.mean([s['compound'] for s in scores])
            }
            
            # Determine overall sentiment
            compound = avg_scores['compound']
            if compound >= 0.05:
                sentiment_label = 'positive'
            elif compound <= -0.05:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': round(float(compound), 3),
                'sentiment_label': sentiment_label,
                'confidence': round(abs(float(compound)), 3),
                'detailed_scores': avg_scores,
                'model': 'vader'
            }
            
        except Exception as e:
            logger.error(f"VADER sentiment analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_textblob_sentiment(self, reviews: List[str]) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob"""
        try:
            polarities = []
            subjectivities = []
            
            for review in reviews:
                blob = TextBlob(review)
                polarities.append(blob.sentiment.polarity)
                subjectivities.append(blob.sentiment.subjectivity)
            
            avg_polarity = np.mean(polarities)
            avg_subjectivity = np.mean(subjectivities)
            
            # Determine sentiment label
            if avg_polarity > 0.1:
                sentiment_label = 'positive'
            elif avg_polarity < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': round(float(avg_polarity), 3),
                'sentiment_label': sentiment_label,
                'confidence': round(abs(float(avg_polarity)), 3),
                'subjectivity': round(float(avg_subjectivity), 3),
                'model': 'textblob'
            }
            
        except Exception as e:
            logger.error(f"TextBlob sentiment analysis failed: {e}")
            return {'error': str(e)}
    
    async def _analyze_hf_sentiment(self, reviews: List[str]) -> Dict[str, Any]:
        """Analyze sentiment using HuggingFace model"""
        try:
            if not self.hf_sentiment_pipeline:
                return {'error': 'HuggingFace model not available'}
            
            # Process reviews in batches
            batch_size = 10
            all_results = []
            
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                batch_results = self.hf_sentiment_pipeline(batch)
                all_results.extend(batch_results)
            
            # Aggregate results
            positive_scores = []
            negative_scores = []
            
            for result in all_results:
                # HF model returns list of scores for each label
                for score_dict in result:
                    if 'POSITIVE' in score_dict['label'].upper():
                        positive_scores.append(score_dict['score'])
                    elif 'NEGATIVE' in score_dict['label'].upper():
                        negative_scores.append(score_dict['score'])
            
            avg_positive = np.mean(positive_scores) if positive_scores else 0
            avg_negative = np.mean(negative_scores) if negative_scores else 0
            
            # Calculate compound score
            compound_score = avg_positive - avg_negative
            
            if compound_score > 0.1:
                sentiment_label = 'positive'
            elif compound_score < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': round(float(compound_score), 3),
                'sentiment_label': sentiment_label,
                'confidence': round(max(abs(float(compound_score)), abs(avg_positive), abs(avg_negative)), 3),
                'positive_probability': round(float(avg_positive), 3),
                'negative_probability': round(float(avg_negative), 3),
                'model': 'huggingface'
            }
            
        except Exception as e:
            logger.error(f"HuggingFace sentiment analysis failed: {e}")
            return {'error': str(e)}
    
    def _ensemble_sentiment(self, sentiment_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple sentiment analysis results"""
        try:
            valid_results = {k: v for k, v in sentiment_results.items() if 'error' not in v}
            
            if not valid_results:
                return {'error': 'No valid sentiment results'}
            
            # Average sentiment scores
            scores = [result['sentiment_score'] for result in valid_results.values()]
            confidences = [result['confidence'] for result in valid_results.values()]
            
            avg_score = np.mean(scores)
            avg_confidence = np.mean(confidences)
            
            # Determine final label
            if avg_score > 0.1:
                sentiment_label = 'positive'
            elif avg_score < -0.1:
                sentiment_label = 'negative'
            else:
                sentiment_label = 'neutral'
            
            return {
                'sentiment_score': round(float(avg_score), 3),
                'sentiment_label': sentiment_label,
                'confidence': round(float(avg_confidence), 3),
                'models_used': list(valid_results.keys()),
                'individual_results': valid_results,
                'model': 'ensemble'
            }
            
        except Exception as e:
            logger.error(f"Ensemble sentiment analysis failed: {e}")
            return {'error': str(e)}
    
    async def _extract_review_topics(self, reviews: List[str]) -> Dict[str, Any]:
        """Extract topics from reviews using keyword analysis"""
        try:
            # Common product review topics
            topic_keywords = {
                'quality': ['quality', 'build', 'material', 'construction', 'sturdy', 'flimsy'],
                'value': ['price', 'value', 'worth', 'expensive', 'cheap', 'cost'],
                'usability': ['easy', 'difficult', 'user', 'interface', 'setup', 'install'],
                'design': ['design', 'look', 'appearance', 'style', 'color', 'beautiful'],
                'performance': ['fast', 'slow', 'performance', 'speed', 'efficient', 'lag'],
                'customer_service': ['service', 'support', 'help', 'response', 'staff'],
                'shipping': ['shipping', 'delivery', 'arrived', 'package', 'fast delivery']
            }
            
            topic_scores = {}
            
            # Combine all reviews
            all_text = ' '.join(reviews).lower()
            
            for topic, keywords in topic_keywords.items():
                mentions = sum(all_text.count(keyword) for keyword in keywords)
                topic_scores[topic] = mentions
            
            # Normalize scores
            total_mentions = sum(topic_scores.values())
            if total_mentions > 0:
                topic_percentages = {
                    topic: round((count / total_mentions) * 100, 1)
                    for topic, count in topic_scores.items()
                }
            else:
                topic_percentages = {topic: 0.0 for topic in topic_keywords.keys()}
            
            # Find top topics
            sorted_topics = sorted(topic_percentages.items(), key=lambda x: x[1], reverse=True)
            top_topics = sorted_topics[:3]
            
            return {
                'topic_distribution': topic_percentages,
                'top_topics': [{'topic': topic, 'percentage': pct} for topic, pct in top_topics],
                'total_keyword_mentions': total_mentions
            }
            
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return {'error': str(e)}
    
    def _clean_review_text(self, review: str) -> str:
        """Clean and preprocess review text"""
        try:
            if not isinstance(review, str):
                return ""
            
            # Remove HTML tags
            review = re.sub(r'<[^>]+>', '', review)
            
            # Remove excessive whitespace
            review = re.sub(r'\s+', ' ', review).strip()
            
            # Remove very short reviews
            if len(review) < 10:
                return ""
            
            return review
            
        except Exception as e:
            logger.error(f"Review cleaning failed: {e}")
            return ""
    
    def _assess_forecast_accuracy(self, metrics: Dict[str, float]) -> str:
        """Assess forecast accuracy based on metrics"""
        try:
            if 'error' in metrics:
                return 'unknown'
            
            mape = metrics.get('mape', 100)
            accuracy_band = metrics.get('accuracy_band_10pct', 0)
            
            if mape < 5 and accuracy_band > 80:
                return 'excellent'
            elif mape < 10 and accuracy_band > 60:
                return 'good'
            elif mape < 20 and accuracy_band > 40:
                return 'fair'
            else:
                return 'poor'
                
        except Exception as e:
            logger.error(f"Accuracy assessment failed: {e}")
            return 'unknown'

# Create global instance
pricing_analytics_service = PricingAnalyticsService()
