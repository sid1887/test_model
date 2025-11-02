// TypeScript Types for Cumpair API

export interface Product {
  id: string;
  name: string;
  current_price: number;
  original_price?: number;
  retailer: string;
  image_url?: string;
  product_url?: string;
  category?: string;
  in_stock: boolean;
  rating?: number;
  reviews_count?: number;
  created_at: string;
  updated_at: string;
}

export interface ProductSnapshot {
  id: string;
  product_id: string;
  price: number;
  in_stock: boolean;
  created_at: string;
}

export interface SearchResult {
  results: Product[];
  total: number;
  metadata: {
    cache_hit?: boolean;
    latency_ms?: number;
    enriched?: boolean;
    vector_search_used?: boolean;
    query_analysis?: {
      sentiment?: {
        label: string;
        score: number;
      };
      category?: {
        labels: string[];
        scores: number[];
      };
      entities?: Array<{
        entity: string;
        word: string;
        score: number;
      }>;
    };
    realtime_context?: RealTimeContext;
  };
}

export interface Sentiment {
  label: string;
  score: number;
}

export interface CategoryPrediction {
  labels: string[];
  scores: number[];
}

export interface Entity {
  entity: string;
  word: string;
  score: number;
}

export interface RealTimeContext {
  stocks?: Record<string, StockData>;
  crypto?: Record<string, CryptoData>;
  news?: NewsItem[];
  tickets?: TicketEvent[];
}

export interface StockData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  timestamp: string;
}

export interface CryptoData {
  id: string;
  symbol: string;
  name: string;
  current_price: number;
  market_cap: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
}

export interface NewsItem {
  title: string;
  description: string;
  source: string;
  url: string;
  published_at: string;
  image_url?: string;
}

export interface TicketEvent {
  id: string;
  name: string;
  venue: string;
  date: string;
  min_price: number;
  max_price: number;
}

export interface StreamPhase {
  phase: 'ghost' | 'real' | 'enriched' | 'realtime' | 'complete';
  results?: Product[];
  message?: string;
  timestamp: string;
}

export interface ImageSearchResult {
  query: string;
  results: Product[];
  image_analysis: {
    clip_similarity?: number;
    detected_objects?: string[];
    barcode?: string;
    ocr_text?: string;
    classification?: {
      label: string;
      score: number;
    };
  };
}

export interface CompleteProductContext {
  product: Product;
  ai_analysis?: {
    sentiment?: Sentiment;
    entities?: Entity[];
    summary?: string;
    category?: CategoryPrediction;
  };
  realtime_context?: RealTimeContext;
  similar_products?: Product[];
  price_history?: ProductSnapshot[];
}

export interface PriceComparison {
  product: Product;
  price_history: ProductSnapshot[];
  statistics: {
    min_price: number;
    max_price: number;
    avg_price: number;
    current_price: number;
  };
  retailers: Array<{
    retailer: string;
    price: number;
    url: string;
  }>;
}

export interface PriceAlert {
  id: string;
  product_id: string;
  target_price: number;
  email: string;
  active: boolean;
  created_at: string;
}

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms: number;
  services: Record<string, {
    healthy: boolean;
    latency_ms: number;
    error?: string;
  }>;
}

export interface Retailer {
  id: string;
  name: string;
  domain: string;
  logo_url?: string;
  active: boolean;
}

export interface PredictionRequest {
  product_id: string;
  days: number;
}

export interface PredictionResult {
  product_id: string;
  predictions: Array<{
    date: string;
    predicted_price: number;
    confidence: number;
  }>;
  trend: 'increasing' | 'decreasing' | 'stable';
  confidence_score: number;
}
