// Analytics API Service - Price trends, forecasts, sentiment analysis
// GET /api/analytics/*

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ==================== TYPES ====================

export interface AnalyticsOverview {
  total_products: number;
  total_comparisons: number;
  total_searches: number;
  avg_price_savings: number;
  active_alerts: number;
  smart_lists_count: number;
  trending_categories: { category: string; count: number }[];
  recent_activity: { type: string; timestamp: string; description: string }[];
}

export interface PriceTrendPoint {
  date: string;
  price: number;
  retailer: string;
  change_percent?: number;
}

export interface PriceTrendsResponse {
  product_id: number;
  product_name: string;
  trends: PriceTrendPoint[];
  trend_direction: 'up' | 'down' | 'stable';
  avg_price: number;
  min_price: number;
  max_price: number;
  price_volatility: number;
}

export interface PriceForecastPoint {
  date: string;
  predicted_price: number;
  confidence_lower: number;
  confidence_upper: number;
  confidence_level: number;
}

export interface PriceForecastResponse {
  product_id: number;
  product_name: string;
  current_price: number;
  forecasts: PriceForecastPoint[];
  model: string;
  accuracy_score: number;
  recommendation: 'buy_now' | 'wait' | 'monitor';
  reasoning: string;
}

export interface SentimentAnalysis {
  product_id: number;
  product_name: string;
  overall_sentiment: 'positive' | 'neutral' | 'negative';
  sentiment_score: number; // -1 to 1
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  total_reviews: number;
  key_positive_themes: string[];
  key_negative_themes: string[];
  sentiment_trend: 'improving' | 'declining' | 'stable';
  last_analyzed: string;
}

export interface RetailerPerformance {
  retailer: string;
  avg_price: number;
  avg_rating: number;
  avg_shipping_cost: number;
  availability_rate: number;
  response_time_ms: number;
  total_products: number;
  price_competitiveness: 'best' | 'competitive' | 'average' | 'expensive';
}

export interface PriceAnomaly {
  product_id: number;
  product_name: string;
  retailer: string;
  current_price: number;
  expected_price: number;
  deviation_percent: number;
  anomaly_type: 'spike' | 'drop' | 'unusual';
  detected_at: string;
  confidence: number;
}

export interface TrendingProduct {
  product_id: number;
  title: string;
  image_url?: string;
  category: string;
  current_price: number;
  trend_score: number;
  search_count: number;
  price_change_percent: number;
  sentiment: 'positive' | 'neutral' | 'negative';
}

// ==================== HELPER FUNCTIONS ====================

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || error.message || 'Request failed');
  }

  return response.json();
}

// ==================== API FUNCTIONS ====================

/**
 * Get analytics dashboard overview
 * GET /api/analytics/overview
 */
export const getAnalyticsOverview = async (): Promise<AnalyticsOverview> => {
  return fetchJSON<AnalyticsOverview>('/api/analytics/overview');
};

/**
 * Get price trends for a product
 * GET /api/analytics/product/{id}/trends
 */
export const getProductTrends = async (
  productId: number | string,
  days?: number
): Promise<PriceTrendsResponse> => {
  const params = days ? `?days=${days}` : '';
  return fetchJSON<PriceTrendsResponse>(`/api/analytics/product/${productId}/trends${params}`);
};

/**
 * Get price forecast for a product
 * GET /api/analytics/product/{id}/forecast
 */
export const getProductForecast = async (
  productId: number | string,
  days_ahead?: number
): Promise<PriceForecastResponse> => {
  const params = days_ahead ? `?days_ahead=${days_ahead}` : '';
  return fetchJSON<PriceForecastResponse>(
    `/api/analytics/product/${productId}/forecast${params}`
  );
};

/**
 * Generate new forecast for a product
 * POST /api/analytics/product/{id}/forecast/generate
 */
export const generateForecast = async (
  productId: number | string,
  days_ahead?: number
): Promise<PriceForecastResponse> => {
  return fetchJSON<PriceForecastResponse>(
    `/api/analytics/product/${productId}/forecast/generate`,
    {
      method: 'POST',
      body: JSON.stringify({ days_ahead }),
    }
  );
};

/**
 * Get sentiment analysis for a product
 * GET /api/analytics/sentiment/{id}
 */
export const getProductSentiment = async (
  productId: number | string
): Promise<SentimentAnalysis> => {
  return fetchJSON<SentimentAnalysis>(`/api/analytics/sentiment/${productId}`);
};

/**
 * Trigger sentiment analysis for a product
 * POST /api/analytics/sentiment/{id}/analyze
 */
export const analyzeSentiment = async (
  productId: number | string
): Promise<SentimentAnalysis> => {
  return fetchJSON<SentimentAnalysis>(`/api/analytics/sentiment/${productId}/analyze`, {
    method: 'POST',
  });
};

/**
 * Get retailer performance comparison
 * GET /api/analytics/retailers/comparison
 */
export const getRetailerComparison = async (
  category?: string
): Promise<RetailerPerformance[]> => {
  const params = category ? `?category=${category}` : '';
  return fetchJSON<RetailerPerformance[]>(`/api/analytics/retailers/comparison${params}`);
};

/**
 * Get price anomalies
 * GET /api/analytics/anomalies
 */
export const getPriceAnomalies = async (
  min_confidence?: number,
  limit?: number
): Promise<PriceAnomaly[]> => {
  const params = new URLSearchParams();
  if (min_confidence !== undefined) params.append('min_confidence', min_confidence.toString());
  if (limit !== undefined) params.append('limit', limit.toString());

  const query = params.toString();
  return fetchJSON<PriceAnomaly[]>(`/api/analytics/anomalies${query ? `?${query}` : ''}`);
};

/**
 * Get trending products
 * GET /api/analytics/products/trending
 */
export const getTrendingProducts = async (
  category?: string,
  limit?: number
): Promise<TrendingProduct[]> => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (limit !== undefined) params.append('limit', limit.toString());

  const query = params.toString();
  return fetchJSON<TrendingProduct[]>(`/api/analytics/products/trending${query ? `?${query}` : ''}`);
};

/**
 * Get category insights
 * GET /api/analytics/categories/insights
 */
export const getCategoryInsights = async (): Promise<{
  categories: {
    name: string;
    avg_price: number;
    product_count: number;
    price_trend: 'up' | 'down' | 'stable';
    best_retailer: string;
  }[];
}> => {
  return fetchJSON(`/api/analytics/categories/insights`);
};

/**
 * Get market trends
 * GET /api/analytics/market/trends
 */
export const getMarketTrends = async (
  days?: number
): Promise<{
  overall_trend: 'up' | 'down' | 'stable';
  avg_price_change: number;
  categories_up: number;
  categories_down: number;
  top_gainers: TrendingProduct[];
  top_losers: TrendingProduct[];
}> => {
  const params = days ? `?days=${days}` : '';
  return fetchJSON(`/api/analytics/market/trends${params}`);
};

// ==================== EXPORT ====================

export const analyticsAPI = {
  getAnalyticsOverview,
  getProductTrends,
  getProductForecast,
  generateForecast,
  getProductSentiment,
  analyzeSentiment,
  getRetailerComparison,
  getPriceAnomalies,
  getTrendingProducts,
  getCategoryInsights,
  getMarketTrends,
};

export default analyticsAPI;
