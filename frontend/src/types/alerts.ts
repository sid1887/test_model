/**
 * TypeScript type definitions for Price Alerts, Smart Lists, and Analytics
 */

// ============================================================================
// PRICE ALERTS TYPES
// ============================================================================

export type AlertOperator = '<=' | '<' | '>' | '>=' | '==' | 'percent_off';
export type AlertStatus = 'active' | 'paused' | 'fired' | 'expired' | 'deleted';
export type AlertFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly';
export type NotificationChannel = 'email' | 'sms' | 'whatsapp' | 'push' | 'webhook';
export type AlertEventType = 'created' | 'checked' | 'price_changed' | 'fired' | 'paused' | 'resumed' | 'expired' | 'deleted' | 'error';
export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'failed' | 'bounced';

export interface Alert {
  id: number;
  user_id: number;
  product_id: number;
  target_price: number;
  operator: AlertOperator;
  retailers?: number[];
  channels: NotificationChannel[];
  frequency: AlertFrequency;
  status: AlertStatus;
  priority: 'normal' | 'urgent';
  last_checked_at?: string;
  last_fired_at?: string;
  fire_count: number;
  expires_at?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface AlertEvent {
  id: number;
  alert_id: number;
  event_type: AlertEventType;
  current_price?: number;
  previous_price?: number;
  retailer_id?: number;
  event_payload?: Record<string, unknown>;
  created_at: string;
}

export interface Notification {
  id: number;
  channel: NotificationChannel;
  status: NotificationStatus;
  recipient: string;
  message: string;
  retry_count: number;
  sent_at?: string;
  delivered_at?: string;
  opened_at?: string;
}

export interface UserPreferences {
  id: number;
  user_id: number;
  email?: string;
  phone?: string;
  whatsapp?: string;
  email_enabled: boolean;
  sms_enabled: boolean;
  whatsapp_enabled: boolean;
  push_enabled: boolean;
  max_notifications_per_hour: number;
  max_notifications_per_day: number;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
  timezone: string;
}

export interface AlertCreateRequest {
  product_id: number;
  target_price: number;
  operator?: AlertOperator;
  retailers?: number[];
  channels?: NotificationChannel[];
  frequency?: AlertFrequency;
  priority?: 'normal' | 'urgent';
  expires_at?: string;
  notes?: string;
}

export interface AlertUpdateRequest {
  target_price?: number;
  operator?: AlertOperator;
  retailers?: number[];
  channels?: NotificationChannel[];
  frequency?: AlertFrequency;
  priority?: 'normal' | 'urgent';
  expires_at?: string;
  notes?: string;
}

// ============================================================================
// SMART LISTS TYPES
// ============================================================================

export type SmartListVisibility = 'private' | 'shared' | 'public';
export type CompareJobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface SmartList {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  tags?: string[];
  default_retailers?: number[];
  auto_monitor: boolean;
  auto_monitor_threshold?: number;
  visibility: SmartListVisibility;
  is_public?: boolean;
  share_token?: string;
  item_count: number;
  total_value?: number;
  last_compared_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface SmartListItem {
  id: number;
  list_id: number;
  product_id: number;
  desired_price?: number;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  notes?: string;
  position: number;
  quantity: number;
  added_price?: number;
  current_price?: number;
  best_retailer_id?: number;
  is_available: boolean;
  alert_created: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ListCompareJob {
  id: number;
  list_id: number;
  status: CompareJobStatus;
  total_items: number;
  completed_items: number;
  failed_items: number;
  results?: Record<string, unknown>;
  total_savings?: number;
  best_store_overall?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface ListTemplate {
  id: number;
  name: string;
  category: string;
  description?: string;
  template_items: Record<string, unknown>[];
  usage_count: number;
  is_public: boolean;
  is_featured: boolean;
  created_at: string;
}

export interface ListCreateRequest {
  name: string;
  description?: string;
  tags?: string[];
  default_retailers?: number[];
  auto_monitor?: boolean;
  auto_monitor_threshold?: number;
  visibility?: SmartListVisibility;
}

export interface ItemAddRequest {
  product_id: number;
  desired_price?: number;
  priority?: string;
  notes?: string;
  quantity?: number;
}

// ============================================================================
// ANALYTICS TYPES
// ============================================================================

export interface PriceDataPoint {
  timestamp: string;
  price: number;
  retailer_id?: number;
  retailer_name?: string;
}

export interface TrendAnalysis {
  direction: 'increasing' | 'decreasing' | 'stable';
  strength_percent: number;
  period_days: number;
  start_price: number;
  end_price: number;
  change_percent: number;
}

export interface ForecastPrediction {
  date: string;
  predicted_price: number;
  lower_bound: number;
  upper_bound: number;
  confidence: number;
}

export interface ProductForecast {
  product_id: number;
  current_price: number;
  forecast_horizon_days: number;
  model_type: string;
  confidence_interval: number;
  predictions: ForecastPrediction[];
  trend_analysis: TrendAnalysis;
  best_buy_date?: string;
  best_buy_price?: number;
  recommendation?: string;
  mae?: number;
  rmse?: number;
  generated_at: string;
}

export interface PriceTrend {
  product_id: number;
  period_days: number;
  data_points: PriceDataPoint[];
  current_price: number;
  avg_price: number;
  min_price: number;
  max_price: number;
  price_volatility: number;
  trend: TrendAnalysis;
}

export interface SentimentScore {
  score: number;
  label: 'positive' | 'negative' | 'neutral';
  confidence: number;
}

export interface SentimentAnalysis {
  product_id: number;
  total_reviews: number;
  processed_reviews: number;
  overall_sentiment: SentimentScore;
  positive_keywords: string[];
  negative_keywords: string[];
  sentiment_trend?: string;
  analyzed_at: string;
  positive_count?: number;
  negative_count?: number;
  neutral_count?: number;
  key_topics?: string[];
  sample_reviews?: Array<{ text: string; sentiment: 'positive' | 'negative' | 'neutral'; confidence: number }>;
}

export interface AnalyticsOverview {
  total_products: number;
  total_retailers: number;
  total_price_points: number;
  active_alerts: number;
  alerts_fired_today: number;
  smart_lists: number;
  comparisons_today: number;
  forecasts_available: number;
  avg_forecast_accuracy?: number;
  avg_price_change?: number;
  total_savings?: number;
  forecasts_generated?: number;
  top_trending_products: Record<string, unknown>[];
  recent_price_drops: Record<string, unknown>[];
}

export interface RetailerComparison {
  retailer_id: number;
  retailer_name: string;
  avg_price: number;
  product_count: number;
  availability_rate: number;
  avg_response_time_ms?: number;
  competitiveness_score: number;
}

// ============================================================================
// COMMON/SHARED TYPES
// ============================================================================

export interface Product {
  id: number;
  name: string;
  category?: string;
  image_url?: string;
  current_price?: number;
  description?: string;
}

export interface Retailer {
  id: number;
  name: string;
  logo_url?: string;
  website?: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface WebSocketMessage {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}
