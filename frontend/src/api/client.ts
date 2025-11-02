// Auto-generated API Client for Cumpair Backend
// Base URL configuration
import type {
  SearchResult,
  ImageSearchResult,
  CompleteProductContext,
  PriceComparison,
  ServiceHealth,
  Retailer,
  PredictionRequest,
  PredictionResult,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API Client
export class CumpairAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
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

  // Search API V2 - God Engine
  async unifiedSearch(params: {
    q: string;
    limit?: number;
    use_cache?: boolean;
    use_vector?: boolean;
    enrich?: boolean;
  }): Promise<SearchResult> {
    const queryParams = new URLSearchParams();
    queryParams.append('q', params.q);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.use_cache !== undefined) queryParams.append('use_cache', params.use_cache.toString());
    if (params.use_vector !== undefined) queryParams.append('use_vector', params.use_vector.toString());
    if (params.enrich !== undefined) queryParams.append('enrich', params.enrich.toString());

    return this.request<SearchResult>(`/api/v2/search?${queryParams.toString()}`);
  }

  // SSE Streaming Search
  streamingSearch(params: { q: string; limit?: number }) {
    const queryParams = new URLSearchParams();
    queryParams.append('q', params.q);
    if (params.limit) queryParams.append('limit', params.limit.toString());

    const url = `${this.baseURL}/api/v2/search/stream?${queryParams.toString()}`;
    return new EventSource(url);
  }

  // Image Search V2
  async imageSearch(file: File, params: { limit?: number; enrich?: boolean }): Promise<ImageSearchResult> {
    const formData = new FormData();
    formData.append('file', file);
    if (params.limit) formData.append('limit', params.limit.toString());
    if (params.enrich !== undefined) formData.append('enrich', params.enrich.toString());

    return fetch(`${this.baseURL}/api/v2/search/image`, {
      method: 'POST',
      body: formData,
    }).then(res => res.json() as Promise<ImageSearchResult>);
  }

  // Complete Product Context
  async getCompleteProductContext(productId: string): Promise<CompleteProductContext> {
    return this.request<CompleteProductContext>(`/api/v2/product/${productId}/complete`);
  }

  // Legacy Search
  async search(query: string): Promise<SearchResult> {
    const queryParams = new URLSearchParams({ query });
    return this.request<SearchResult>(`/api/search?${queryParams.toString()}`);
  }

  // Price Comparison
  async getPriceComparison(params: { product_id: string; days?: number }): Promise<PriceComparison> {
    const queryParams = new URLSearchParams();
    queryParams.append('product_id', params.product_id);
    if (params.days) queryParams.append('days', params.days.toString());

    return this.request<PriceComparison>(`/api/price-comparison?${queryParams.toString()}`);
  }

  // Create Price Alert
  async createPriceAlert(data: {
    product_id: string;
    target_price: number;
    email: string;
  }): Promise<{ id: string }> {
    return this.request<{ id: string }>('/api/price-alerts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Service Health
  async getServiceHealth(): Promise<ServiceHealth> {
    return this.request<ServiceHealth>('/health/services');
  }

  // Metrics
  async getMetrics() {
    const response = await fetch(`${this.baseURL}/metrics`);
    return response.text();
  }

  // Retailers
  async getRetailers(): Promise<Retailer[]> {
    return this.request<Retailer[]>('/api/retailers');
  }

  // Analysis endpoints
  async analyzeProduct(productId: string): Promise<unknown> {
    return this.request(`/api/analysis/${productId}`);
  }

  async runPrediction(data: PredictionRequest): Promise<PredictionResult> {
    return this.request<PredictionResult>('/api/analysis/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

// Export singleton instance
export const api = new CumpairAPI();
