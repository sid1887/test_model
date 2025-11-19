// Enhanced API Client for Cumpair Backend
// Connects to unified API gateway (Port 8000) which routes to all Phase 7 services
import type {
  SearchResult,
  PriceComparison,
  ServiceHealth,
  Retailer,
  PredictionRequest,
  PredictionResult,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// API Client
export class CumpairAPI {
  private baseURL: string;
  private wsBaseURL: string;

  constructor(baseURL: string = API_BASE_URL, wsBaseURL: string = WS_BASE_URL) {
    this.baseURL = baseURL;
    this.wsBaseURL = wsBaseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // ========================================================================
  // SEARCH API (Service 8010)
  // ========================================================================

  async search(q: string, limit = 20, offset = 0): Promise<SearchResult> {
    const params = new URLSearchParams({ q, limit: limit.toString(), offset: offset.toString() });
    return this.request<SearchResult>(`/api/search?${params}`);
  }

  async semanticSearch(q: string, limit = 10): Promise<SearchResult> {
    const params = new URLSearchParams({ q, limit: limit.toString() });
    return this.request<SearchResult>(`/api/search/semantic?${params}`);
  }

  async autocomplete(q: string, limit = 10): Promise<Record<string, unknown>> {
    const params = new URLSearchParams({ q, limit: limit.toString() });
    return this.request(`/api/search/autocomplete?${params}`);
  }

  async facetedSearch(q: string, category?: string, minPrice?: number, maxPrice?: number, limit = 20): Promise<SearchResult> {
    const params = new URLSearchParams({ q, limit: limit.toString() });
    if (category) params.append('category', category);
    if (minPrice !== undefined) params.append('min_price', minPrice.toString());
    if (maxPrice !== undefined) params.append('max_price', maxPrice.toString());
    return this.request<SearchResult>(`/api/search/faceted?${params}`);
  }

  async trendingSearch(limit = 10): Promise<Record<string, unknown>> {
    return this.request(`/api/search/trending?limit=${limit}`);
  }

  // ========================================================================
  // ELASTICSEARCH API (Service 8015)
  // ========================================================================

  async elasticsearchSearch(q: string, limit = 10): Promise<SearchResult> {
    const params = new URLSearchParams({ q, limit: limit.toString() });
    return this.request<SearchResult>(`/api/search/elasticsearch?${params}`);
  }

  async fuzzySearch(q: string, limit = 10): Promise<SearchResult> {
    const params = new URLSearchParams({ q, limit: limit.toString() });
    return this.request<SearchResult>(`/api/search/fuzzy?${params}`);
  }

  async elasticsearchAutocomplete(q: string, limit = 10): Promise<Record<string, unknown>> {
    const params = new URLSearchParams({ q, limit: limit.toString() });
    return this.request(`/api/search/autocomplete-es?${params}`);
  }

  // ========================================================================
  // RECOMMENDATIONS API (Service 8014)
  // ========================================================================

  async getRecommendations(userId: string, limit = 10): Promise<Record<string, unknown>> {
    return this.request(`/api/recommendations/for-you/${userId}?limit=${limit}`);
  }

  async getSimilarProducts(productId: string, limit = 10): Promise<Record<string, unknown>> {
    return this.request(`/api/recommendations/similar/${productId}?limit=${limit}`);
  }

  async getTrendingProducts(limit = 10): Promise<Record<string, unknown>> {
    return this.request(`/api/recommendations/trending?limit=${limit}`);
  }

  async forecastDemand(productId: string): Promise<Record<string, unknown>> {
    return this.request(`/api/forecast/demand/${productId}`);
  }

  // ========================================================================
  // REAL-TIME API (Service 8013)
  // ========================================================================

  async getRealtimeStats(): Promise<Record<string, unknown>> {
    return this.request('/api/realtime/stats');
  }

  async sendNotification(userId: string, message: string): Promise<Record<string, unknown>> {
    return this.request('/api/realtime/notify', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, message }),
    });
  }

  // ========================================================================
  // EVENTS API (Service 8016)
  // ========================================================================

  async publishEvent(eventType: string, data: Record<string, unknown>, userId?: string): Promise<Record<string, unknown>> {
    return this.request('/api/events/publish', {
      method: 'POST',
      body: JSON.stringify({ event_type: eventType, data, user_id: userId }),
    });
  }

  async getEventStream(streamKey: string, limit = 100): Promise<Record<string, unknown>> {
    return this.request(`/api/events/stream/${streamKey}?limit=${limit}`);
  }

  async getUserEvents(userId: string, limit = 100): Promise<Record<string, unknown>> {
    return this.request(`/api/events/user/${userId}?limit=${limit}`);
  }

  async getDeadLetterQueue(): Promise<Record<string, unknown>> {
    return this.request('/api/events/dlq');
  }

  async retryEvent(eventId: string): Promise<Record<string, unknown>> {
    return this.request(`/api/events/retry/${eventId}`, { method: 'POST' });
  }

  // ========================================================================
  // PRICE ALERTS API (Combined: Events + Real-time)
  // ========================================================================

  async createPriceAlert(productId: string, targetPrice: number, userId: string): Promise<Record<string, unknown>> {
    return this.request('/api/alerts/price', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, target_price: targetPrice, user_id: userId }),
    });
  }

  async getUserAlerts(userId: string): Promise<Record<string, unknown>> {
    return this.request(`/api/alerts/user/${userId}`);
  }

  // ========================================================================
  // LEGACY COMPATIBILITY
  // ========================================================================

  async unifiedSearch(params: {
    q: string;
    limit?: number;
    use_cache?: boolean;
    use_vector?: boolean;
    enrich?: boolean;
  }): Promise<SearchResult> {
    return this.search(params.q, params.limit, 0);
  }

  async getPriceComparison(params: { product_id: string; days?: number }): Promise<PriceComparison> {
    return this.request<PriceComparison>(`/api/price-comparison?product_id=${params.product_id}`);
  }

  async getServiceHealth(): Promise<ServiceHealth> {
    return this.request<ServiceHealth>('/health');
  }

  async getMetrics() {
    const response = await fetch(`${this.baseURL}/metrics`);
    return response.text();
  }

  async getRetailers(): Promise<Retailer[]> {
    return this.request<Retailer[]>('/api/retailers');
  }

  async analyzeProduct(productId: string): Promise<unknown> {
    return this.request(`/api/analysis/${productId}`);
  }

  async runPrediction(data: PredictionRequest): Promise<PredictionResult> {
    return this.request<PredictionResult>('/api/analysis/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ========================================================================
  // WEBSOCKET
  // ========================================================================

  connectRealtime(userId: string): WebSocket {
    const wsUrl = `${this.wsBaseURL}/ws/realtime/${userId}`;
    return new WebSocket(wsUrl);
  }
}

// Export singleton instance
export const api = new CumpairAPI();
