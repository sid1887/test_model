"""
Enhanced Data Pipeline & Scoring Service for Cumpair
Implements advanced feature normalization, value scoring, and outlier handling
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from enum import Enum
import asyncio
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class NormalizationMethod(Enum):
    """Normalization methods for feature scaling"""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    ROBUST = "robust"

class ScoringWeights(Enum):
    """Pre-defined scoring weight configurations"""
    BALANCED = {
        'price': 0.4,
        'rating': 0.3,
        'review_count': 0.2,
        'availability': 0.1
    }
    PRICE_FOCUSED = {
        'price': 0.6,
        'rating': 0.2,
        'review_count': 0.15,
        'availability': 0.05
    }
    QUALITY_FOCUSED = {
        'price': 0.2,
        'rating': 0.5,
        'review_count': 0.25,
        'availability': 0.05
    }

class DataPipelineService:
    """Enhanced data pipeline with advanced scoring and normalization"""
    
    def __init__(self):
        self.scalers = {}
        self.label_encoders = {}
        self.outlier_detectors = {}
        self.feature_stats = {}
        
    async def normalize_features(
        self, 
        data: List[Dict[str, Any]], 
        features: List[str],
        method: NormalizationMethod = NormalizationMethod.MIN_MAX
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Normalize features using specified method with outlier handling
        
        Args:
            data: List of product dictionaries
            features: Features to normalize
            method: Normalization method to use
            
        Returns:
            Tuple of (normalized_df, normalization_metadata)
        """
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Initialize metadata
            metadata = {
                'method': method.value,
                'features_processed': [],
                'outliers_detected': {},
                'feature_statistics': {}
            }
            
            normalized_df = df.copy()
            
            for feature in features:
                if feature not in df.columns:
                    logger.warning(f"Feature '{feature}' not found in data")
                    continue
                    
                # Extract numeric values
                feature_data = self._extract_numeric_values(df[feature])
                
                if len(feature_data) == 0:
                    logger.warning(f"No valid numeric data for feature '{feature}'")
                    continue
                
                # Handle outliers
                outlier_info = await self._detect_outliers(feature_data, feature)
                metadata['outliers_detected'][feature] = outlier_info
                
                # Apply robust preprocessing if outliers detected
                if outlier_info['outlier_count'] > 0:
                    feature_data = self._handle_outliers(feature_data, outlier_info)
                
                # Apply normalization
                normalized_values = await self._apply_normalization(
                    feature_data, feature, method
                )
                
                # Store feature statistics
                metadata['feature_statistics'][feature] = {
                    'original_min': float(np.min(feature_data)),
                    'original_max': float(np.max(feature_data)),
                    'original_mean': float(np.mean(feature_data)),
                    'original_std': float(np.std(feature_data)),
                    'normalized_min': float(np.min(normalized_values)),
                    'normalized_max': float(np.max(normalized_values)),
                    'normalized_mean': float(np.mean(normalized_values))
                }
                
                # Update DataFrame
                normalized_df[f'{feature}_normalized'] = normalized_values
                metadata['features_processed'].append(feature)
            
            return normalized_df, metadata
            
        except Exception as e:
            logger.error(f"Feature normalization failed: {e}")
            raise Exception(f"Feature normalization error: {e}")
    
    async def calculate_value_score(
        self,
        products: List[Dict[str, Any]],
        weights: Union[Dict[str, float], ScoringWeights] = ScoringWeights.BALANCED,
        custom_features: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate comprehensive value scores with weighted features
        
        Args:
            products: List of product dictionaries
            weights: Feature weights for scoring
            custom_features: Custom feature mappings
            
        Returns:
            Products with enhanced value scores
        """
        try:
            if isinstance(weights, ScoringWeights):
                weight_dict = weights.value
            else:
                weight_dict = weights
            
            # Default feature mappings
            feature_map = {
                'price': 'price',
                'rating': 'rating', 
                'review_count': 'review_count',
                'availability': 'in_stock'
            }
            
            if custom_features:
                feature_map.update(custom_features)
            
            # Extract and normalize features
            feature_data = []
            for product in products:
                features = {}
                for score_feature, data_field in feature_map.items():
                    value = product.get(data_field, 0)
                    if isinstance(value, bool):
                        features[score_feature] = 1.0 if value else 0.0
                    else:
                        features[score_feature] = self._safe_float(value)
                feature_data.append(features)
            
            # Normalize features
            feature_names = list(weight_dict.keys())
            normalized_df, norm_metadata = await self.normalize_features(
                feature_data, feature_names, NormalizationMethod.MIN_MAX
            )
            
            # Calculate weighted scores
            enhanced_products = []
            for i, product in enumerate(products):
                # Base value score calculation
                score_components = {}
                total_score = 0.0
                
                for feature, weight in weight_dict.items():
                    normalized_col = f'{feature}_normalized'
                    if normalized_col in normalized_df.columns:
                        feature_value = normalized_df.iloc[i][normalized_col]
                        
                        # Invert price scoring (lower price = higher score)
                        if feature == 'price':
                            feature_value = 1.0 - feature_value
                        
                        score_components[feature] = {
                            'value': float(feature_value),
                            'weight': weight,
                            'contribution': float(feature_value * weight)
                        }
                        total_score += feature_value * weight
                
                # Enhanced product with scoring details
                enhanced_product = product.copy()
                enhanced_product.update({
                    'value_score': round(total_score * 5.0, 2),  # Scale to 1-5
                    'value_score_raw': round(total_score, 4),
                    'score_components': score_components,
                    'scoring_metadata': {
                        'weights_used': weight_dict,
                        'normalization_method': norm_metadata['method'],
                        'features_processed': norm_metadata['features_processed']
                    }
                })
                
                enhanced_products.append(enhanced_product)
            
            # Sort by value score
            enhanced_products.sort(key=lambda x: x['value_score'], reverse=True)
            
            return enhanced_products
            
        except Exception as e:
            logger.error(f"Value score calculation failed: {e}")
            raise Exception(f"Value scoring error: {e}")
    
    async def engineer_categorical_features(
        self,
        data: List[Dict[str, Any]],
        categorical_features: List[str],
        encoding_method: str = "onehot"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Engineer categorical features with encoding
        
        Args:
            data: Product data
            categorical_features: List of categorical feature names
            encoding_method: "onehot" or "label"
            
        Returns:
            DataFrame with engineered features and metadata
        """
        try:
            df = pd.DataFrame(data)
            engineered_df = df.copy()
            metadata = {
                'encoding_method': encoding_method,
                'features_engineered': [],
                'encoding_mappings': {}
            }
            
            for feature in categorical_features:
                if feature not in df.columns:
                    continue
                
                # Clean and prepare categorical data
                feature_data = df[feature].fillna('unknown').astype(str)
                unique_values = feature_data.unique()
                
                if encoding_method == "onehot":
                    # One-hot encoding
                    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
                    encoded = encoder.fit_transform(feature_data.values.reshape(-1, 1))
                    
                    # Create column names
                    feature_names = [f"{feature}_{val}" for val in encoder.categories_[0]]
                    
                    # Add to DataFrame
                    for i, col_name in enumerate(feature_names):
                        engineered_df[col_name] = encoded[:, i]
                    
                    metadata['encoding_mappings'][feature] = {
                        'categories': encoder.categories_[0].tolist(),
                        'feature_names': feature_names
                    }
                    
                elif encoding_method == "label":
                    # Label encoding
                    encoder = LabelEncoder()
                    encoded = encoder.fit_transform(feature_data)
                    engineered_df[f"{feature}_encoded"] = encoded
                    
                    metadata['encoding_mappings'][feature] = {
                        'classes': encoder.classes_.tolist(),
                        'mapping': dict(zip(encoder.classes_, range(len(encoder.classes_))))
                    }
                
                metadata['features_engineered'].append(feature)
                self.label_encoders[feature] = encoder
            
            return engineered_df, metadata
            
        except Exception as e:
            logger.error(f"Categorical feature engineering failed: {e}")
            raise Exception(f"Feature engineering error: {e}")
    
    async def _detect_outliers(
        self, 
        data: np.ndarray, 
        feature_name: str,
        contamination: float = 0.1
    ) -> Dict[str, Any]:
        """Detect outliers using Isolation Forest"""
        try:
            if len(data) < 10:  # Not enough data for outlier detection
                return {
                    'outlier_count': 0,
                    'outlier_indices': [],
                    'method': 'insufficient_data'
                }
            
            # Reshape for sklearn
            data_reshaped = data.reshape(-1, 1)
            
            # Use Isolation Forest
            detector = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            outlier_labels = detector.fit_predict(data_reshaped)
            
            # Find outlier indices
            outlier_indices = np.where(outlier_labels == -1)[0].tolist()
            
            self.outlier_detectors[feature_name] = detector
            
            return {
                'outlier_count': len(outlier_indices),
                'outlier_indices': outlier_indices,
                'method': 'isolation_forest',
                'contamination': contamination
            }
            
        except Exception as e:
            logger.error(f"Outlier detection failed for {feature_name}: {e}")
            return {
                'outlier_count': 0,
                'outlier_indices': [],
                'method': 'error',
                'error': str(e)
            }
    
    def _handle_outliers(
        self, 
        data: np.ndarray, 
        outlier_info: Dict[str, Any],
        method: str = "clip"
    ) -> np.ndarray:
        """Handle outliers using specified method"""
        try:
            if outlier_info['outlier_count'] == 0:
                return data
            
            if method == "clip":
                # Clip outliers to 5th and 95th percentiles
                q5, q95 = np.percentile(data, [5, 95])
                return np.clip(data, q5, q95)
            
            elif method == "remove":
                # Remove outliers (not recommended for scoring)
                outlier_indices = outlier_info['outlier_indices']
                mask = np.ones(len(data), dtype=bool)
                mask[outlier_indices] = False
                return data[mask]
            
            else:
                return data
                
        except Exception as e:
            logger.error(f"Outlier handling failed: {e}")
            return data
    
    async def _apply_normalization(
        self,
        data: np.ndarray,
        feature_name: str,
        method: NormalizationMethod
    ) -> np.ndarray:
        """Apply specified normalization method"""
        try:
            data_reshaped = data.reshape(-1, 1)
            
            if method == NormalizationMethod.MIN_MAX:
                scaler = MinMaxScaler()
            elif method == NormalizationMethod.Z_SCORE:
                scaler = StandardScaler()
            elif method == NormalizationMethod.ROBUST:
                scaler = RobustScaler()
            else:
                raise ValueError(f"Unknown normalization method: {method}")
            
            normalized = scaler.fit_transform(data_reshaped).flatten()
            self.scalers[feature_name] = scaler
            return normalized
            
        except Exception as e:
            logger.error(f"Normalization failed for {feature_name}: {e}")
            raise
    
    def _extract_numeric_values(self, series: pd.Series) -> np.ndarray:
        """Extract numeric values from mixed data"""
        try:
            numeric_values = []
            for value in series:
                numeric_val = self._safe_float(value)
                if numeric_val is not None:
                    numeric_values.append(numeric_val)
            return np.array(numeric_values)
            
        except Exception as e:
            logger.error(f"Numeric extraction failed: {e}")
            return np.array([])
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        try:
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove common price/number formatting
                cleaned = value.replace('$', '').replace(',', '').replace('%', '').strip()
                if cleaned:
                    return float(cleaned)
            return None
        except (ValueError, TypeError):
            return None

    async def score_retailer_performance(
        self,
        retailer_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Score and compare retailer performance across multiple metrics
        
        Args:
            retailer_data: Dictionary with retailer names as keys and product lists as values
            
        Returns:
            Comprehensive retailer performance analysis
        """
        try:
            retailer_scores = {}
            retailer_stats = {}
            
            for retailer_name, products in retailer_data.items():
                if not products:
                    continue
                
                # Extract metrics
                prices = [self._safe_float(p.get('price', 0)) for p in products]
                ratings = [self._safe_float(p.get('rating', 0)) for p in products]
                response_times = [self._safe_float(p.get('scrape_time', 0)) for p in products]
                availability = [p.get('in_stock', True) for p in products]
                
                # Calculate statistics
                stats = {
                    'total_products': len(products),
                    'avg_price': np.mean(prices) if prices else 0,
                    'price_range': {
                        'min': float(np.min(prices)) if prices else 0,
                        'max': float(np.max(prices)) if prices else 0,
                        'std': float(np.std(prices)) if prices else 0
                    },
                    'avg_rating': np.mean(ratings) if ratings else 0,
                    'avg_response_time': np.mean(response_times) if response_times else 0,
                    'availability_rate': sum(availability) / len(availability) if availability else 0,
                    'price_competitiveness': 0.0,  # Will be calculated later
                    'data_quality_score': 0.0  # Will be calculated later
                }
                
                # Data quality assessment
                quality_metrics = {
                    'price_completeness': len([p for p in prices if p > 0]) / len(products),
                    'rating_completeness': len([r for r in ratings if r > 0]) / len(products),
                    'image_completeness': len([p for p in products if p.get('image')]) / len(products),
                    'description_completeness': len([p for p in products if p.get('title')]) / len(products)
                }
                
                stats['data_quality_score'] = np.mean(list(quality_metrics.values()))
                retailer_stats[retailer_name] = stats
            
            # Calculate competitive metrics
            all_prices = []
            for retailer_name, stats in retailer_stats.items():
                if stats['avg_price'] > 0:
                    all_prices.append(stats['avg_price'])
            
            market_avg_price = np.mean(all_prices) if all_prices else 0
            
            # Score retailers
            for retailer_name, stats in retailer_stats.items():
                score_components = {
                    'price_competitiveness': 0.0,
                    'data_quality': stats['data_quality_score'] * 100,
                    'availability': stats['availability_rate'] * 100,
                    'response_time': 0.0,
                    'catalog_size': min(stats['total_products'] / 100, 1.0) * 100
                }
                
                # Price competitiveness (lower is better)
                if market_avg_price > 0 and stats['avg_price'] > 0:
                    price_ratio = stats['avg_price'] / market_avg_price
                    score_components['price_competitiveness'] = max(0, (2.0 - price_ratio) * 50)
                
                # Response time score (lower is better)
                if stats['avg_response_time'] > 0:
                    score_components['response_time'] = max(0, 100 - (stats['avg_response_time'] * 10))
                
                # Calculate overall score
                weights = {
                    'price_competitiveness': 0.3,
                    'data_quality': 0.25,
                    'availability': 0.2,
                    'response_time': 0.15,
                    'catalog_size': 0.1
                }
                
                overall_score = sum(
                    score_components[metric] * weight 
                    for metric, weight in weights.items()
                )
                
                retailer_scores[retailer_name] = {
                    'overall_score': overall_score,
                    'components': score_components,
                    'statistics': stats,
                    'rank': 0  # Will be set after sorting
                }
            
            # Rank retailers
            sorted_retailers = sorted(
                retailer_scores.items(),
                key=lambda x: x[1]['overall_score'],
                reverse=True
            )
            
            for rank, (retailer_name, score_data) in enumerate(sorted_retailers, 1):
                retailer_scores[retailer_name]['rank'] = rank
            
            return {
                'retailer_scores': retailer_scores,
                'market_insights': {
                    'total_retailers': len(retailer_scores),
                    'market_avg_price': market_avg_price,
                    'best_performer': sorted_retailers[0][0] if sorted_retailers else None,
                    'most_competitive_price': min(
                        retailer_stats.items(),
                        key=lambda x: x[1]['avg_price']
                    )[0] if retailer_stats else None,
                    'highest_availability': max(
                        retailer_stats.items(),
                        key=lambda x: x[1]['availability_rate']
                    )[0] if retailer_stats else None
                },
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Retailer performance scoring failed: {e}")
            return {
                'retailer_scores': {},
                'market_insights': {},
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    async def detect_price_anomalies(
        self,
        product_data: List[Dict[str, Any]],
        sensitivity: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect price anomalies across retailers using statistical methods
        
        Args:
            product_data: List of product data from multiple retailers
            sensitivity: Z-score threshold for anomaly detection
            
        Returns:
            Anomaly detection results
        """
        try:
            prices = [self._safe_float(p.get('price', 0)) for p in product_data if p.get('price', 0) > 0]
            
            if len(prices) < 3:
                return {
                    'anomalies': [],
                    'statistics': {},
                    'message': 'Insufficient data for anomaly detection'
                }
            
            # Calculate statistical measures
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            median_price = np.median(prices)
            
            # Detect anomalies using Z-score
            anomalies = []
            for i, product in enumerate(product_data):
                price = self._safe_float(product.get('price', 0))
                if price > 0:
                    z_score = abs((price - mean_price) / std_price) if std_price > 0 else 0
                    
                    if z_score > sensitivity:
                        anomaly_type = 'high_outlier' if price > mean_price else 'low_outlier'
                        anomalies.append({
                            'product_index': i,
                            'retailer': product.get('site', 'unknown'),
                            'price': price,
                            'z_score': z_score,
                            'anomaly_type': anomaly_type,
                            'deviation_percentage': ((price - mean_price) / mean_price) * 100
                        })
            
            # Price distribution analysis
            quartiles = np.percentile(prices, [25, 50, 75])
            iqr = quartiles[2] - quartiles[0]
            
            return {
                'anomalies': anomalies,
                'statistics': {
                    'mean_price': mean_price,
                    'median_price': median_price,
                    'std_price': std_price,
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'quartiles': {
                        'q1': quartiles[0],
                        'q2': quartiles[1],
                        'q3': quartiles[2]
                    },
                    'iqr': iqr,
                    'coefficient_of_variation': (std_price / mean_price) * 100 if mean_price > 0 else 0
                },
                'anomaly_summary': {
                    'total_products': len(product_data),
                    'valid_prices': len(prices),
                    'anomaly_count': len(anomalies),
                    'anomaly_rate': (len(anomalies) / len(prices)) * 100 if prices else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Price anomaly detection failed: {e}")
            return {
                'anomalies': [],
                'statistics': {},
                'error': str(e)
            }

    async def generate_market_insights(
        self,
        multi_retailer_data: Dict[str, List[Dict[str, Any]]],
        product_category: str = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive market insights from multi-retailer data
        
        Args:
            multi_retailer_data: Data from multiple retailers
            product_category: Product category for context
            
        Returns:
            Market analysis and insights
        """
        try:
            insights = {
                'market_overview': {},
                'price_analysis': {},
                'competitive_landscape': {},
                'recommendations': [],
                'category': product_category,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
            # Aggregate all products
            all_products = []
            retailer_counts = {}
            
            for retailer, products in multi_retailer_data.items():
                retailer_counts[retailer] = len(products)
                for product in products:
                    product['retailer'] = retailer
                    all_products.append(product)
            
            if not all_products:
                insights['message'] = 'No product data available for analysis'
                return insights
            
            # Market overview
            insights['market_overview'] = {
                'total_products': len(all_products),
                'total_retailers': len(multi_retailer_data),
                'retailer_distribution': retailer_counts,
                'data_completeness': self._calculate_data_completeness(all_products)
            }
            
            # Price analysis
            prices = [self._safe_float(p.get('price', 0)) for p in all_products if p.get('price', 0) > 0]
            if prices:
                insights['price_analysis'] = {
                    'price_range': {
                        'min': min(prices),
                        'max': max(prices),
                        'spread': max(prices) - min(prices)
                    },
                    'price_distribution': {
                        'mean': np.mean(prices),
                        'median': np.median(prices),
                        'std': np.std(prices),
                        'quartiles': np.percentile(prices, [25, 50, 75]).tolist()
                    },
                    'price_segments': self._categorize_prices(prices)
                }
            
            # Competitive landscape
            retailer_performance = await self.score_retailer_performance(multi_retailer_data)
            insights['competitive_landscape'] = retailer_performance
            
            # Generate recommendations
            insights['recommendations'] = self._generate_market_recommendations(
                insights, all_products
            )
            
            return insights
            
        except Exception as e:
            logger.error(f"Market insights generation failed: {e}")
            return {
                'market_overview': {},
                'price_analysis': {},
                'competitive_landscape': {},
                'recommendations': [],
                'error': str(e),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

    def _calculate_data_completeness(self, products: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate data completeness metrics"""
        if not products:
            return {}
        
        fields = ['title', 'price', 'image', 'rating', 'availability']
        completeness = {}
        
        for field in fields:
            valid_count = len([p for p in products if p.get(field) not in [None, '', 0]])
            completeness[field] = (valid_count / len(products)) * 100
        
        completeness['overall'] = np.mean(list(completeness.values()))
        return completeness

    def _categorize_prices(self, prices: List[float]) -> Dict[str, int]:
        """Categorize prices into segments"""
        if not prices:
            return {}
        
        q1, q3 = np.percentile(prices, [25, 75])
        
        return {
            'budget': len([p for p in prices if p <= q1]),
            'mid_range': len([p for p in prices if q1 < p <= q3]),
            'premium': len([p for p in prices if p > q3])
        }

    def _generate_market_recommendations(
        self,
        insights: Dict[str, Any],
        products: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable market recommendations"""
        recommendations = []
        
        try:
            price_analysis = insights.get('price_analysis', {})
            competitive_landscape = insights.get('competitive_landscape', {})
            
            # Price-based recommendations
            if price_analysis:
                price_range = price_analysis.get('price_range', {})
                if price_range.get('spread', 0) > price_range.get('min', 0) * 0.5:
                    recommendations.append("Significant price variation detected - consider shopping around for better deals")
            
            # Retailer recommendations
            retailer_scores = competitive_landscape.get('retailer_scores', {})
            if retailer_scores:
                best_retailer = max(retailer_scores.items(), key=lambda x: x[1]['overall_score'])
                recommendations.append(f"Best overall retailer for this search: {best_retailer[0]}")
                
                # Price competitiveness
                price_competitive = max(
                    retailer_scores.items(),
                    key=lambda x: x[1]['components'].get('price_competitiveness', 0)
                )
                recommendations.append(f"Most competitive pricing: {price_competitive[0]}")
            
            # Data quality recommendations
            data_quality = insights.get('market_overview', {}).get('data_completeness', {})
            if data_quality.get('overall', 100) < 80:
                recommendations.append("Some retailers have incomplete product information - verify details before purchase")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return ["Unable to generate recommendations due to data processing error"]

# Create global instance
data_pipeline_service = DataPipelineService()
