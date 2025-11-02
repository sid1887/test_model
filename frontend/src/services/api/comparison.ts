// Price Comparison API Service - Real-time multi-retailer price comparison
// POST /api/comparison/*

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ==================== TYPES ====================

export interface PriceComparisonResult {
  id: number;
  product_id: number;
  retailer: string;
  price: number;
  currency: string;
  url: string;
  availability: 'in_stock' | 'out_of_stock' | 'limited' | 'pre_order';
  last_updated: string;
  shipping_cost?: number;
  rating?: number;
  reviews_count?: number;
}

export interface PriceComparisonResponse {
  product_id: number;
  product_name: string;
  comparisons: PriceComparisonResult[];
  statistics: {
    min_price: number;
    max_price: number;
    avg_price: number;
    median_price: number;
    range: number;
    savings_potential: number;
    best_deal: PriceComparisonResult;
  };
  last_updated: string;
}

export interface PriceHistoryEntry {
  date: string;
  price: number;
  retailer: string;
}

export interface RealTimeSearchRequest {
  query: string;
  retailers?: string[];
  max_results_per_site?: number;
}

export interface RealTimeSearchResponse {
  query: string;
  results: SearchResult[];
  grouped_by_retailer: Record<string, SearchResult[]>;
  best_deals: SearchResult[];
  search_time: number;
}

export interface SearchResult {
  title: string;
  price: number;
  currency: string;
  image_url?: string;
  product_url: string;
  retailer: string;
  availability: string;
  rating?: number;
  reviews_count?: number;
}

export interface SmartSearchRequest {
  query?: string;
  product_id?: number;
  use_clip?: boolean;
  retailers?: string[];
}

export interface RetailerInfo {
  key: string;
  name: string;
  url: string;
  logo_url?: string;
  category: 'general' | 'electronics' | 'fashion' | 'home_improvement' | 'wholesale' | 'specialty';
  priority: 'high' | 'medium' | 'low';
  active: boolean;
  avg_price_level: 'budget' | 'mid-range' | 'premium';
  response_time_ms: number;
  success_rate: number;
}

export interface RetailerFilterRequest {
  category?: string;
  priority?: string;
  active_only?: boolean;
  min_success_rate?: number;
}

export interface ImageSearchByImageRequest {
  file: File;
  retailers?: string[];
}

export interface BarcodeSearchRequest {
  barcode: string;
  retailers?: string[];
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
 * Get price comparisons for a product
 * GET /api/comparison/compare/{product_id}
 */
export const getPriceComparison = async (
  productId: number | string
): Promise<PriceComparisonResponse> => {
  return fetchJSON<PriceComparisonResponse>(`/api/comparison/compare/${productId}`);
};

/**
 * Trigger fresh price scraping for a product
 * POST /api/comparison/compare/{product_id}/refresh
 */
export const refreshPriceComparison = async (
  productId: number | string
): Promise<{ message: string; job_id: string }> => {
  return fetchJSON<{ message: string; job_id: string }>(
    `/api/comparison/compare/${productId}/refresh`,
    { method: 'POST' }
  );
};

/**
 * Get price history for a product
 * GET /api/comparison/compare/{product_id}/history
 */
export const getPriceHistory = async (
  productId: number | string,
  days?: number
): Promise<PriceHistoryEntry[]> => {
  const params = days ? `?days=${days}` : '';
  return fetchJSON<PriceHistoryEntry[]>(`/api/comparison/compare/${productId}/history${params}`);
};

/**
 * Real-time multi-retailer search via Node.js scraper
 * POST /api/comparison/real-time-search
 */
export const realTimeSearch = async (
  request: RealTimeSearchRequest
): Promise<RealTimeSearchResponse> => {
  return fetchJSON<RealTimeSearchResponse>('/api/comparison/real-time-search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * Smart search - CLIP similarity + scraper combined
 * POST /api/comparison/smart-search
 */
export const smartSearch = async (
  request: SmartSearchRequest
): Promise<RealTimeSearchResponse> => {
  return fetchJSON<RealTimeSearchResponse>('/api/comparison/smart-search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * Get all supported retailers
 * GET /api/comparison/retailers
 */
export const getRetailers = async (
  filters?: RetailerFilterRequest
): Promise<RetailerInfo[]> => {
  const params = new URLSearchParams();
  if (filters?.category) params.append('category', filters.category);
  if (filters?.priority) params.append('priority', filters.priority);
  if (filters?.active_only !== undefined)
    params.append('active_only', filters.active_only.toString());
  if (filters?.min_success_rate !== undefined)
    params.append('min_success_rate', filters.min_success_rate.toString());

  const query = params.toString();
  return fetchJSON<RetailerInfo[]>(`/api/comparison/retailers${query ? `?${query}` : ''}`);
};

/**
 * Enhanced search with retailer filtering
 * POST /api/comparison/enhanced-search
 */
export const enhancedSearch = async (
  query: string,
  filters?: RetailerFilterRequest
): Promise<RealTimeSearchResponse> => {
  return fetchJSON<RealTimeSearchResponse>('/api/comparison/enhanced-search', {
    method: 'POST',
    body: JSON.stringify({ query, ...filters }),
  });
};

/**
 * Get retailer configuration
 * GET /api/comparison/retailers/{retailer_key}/config
 */
export const getRetailerConfig = async (retailerKey: string): Promise<RetailerInfo> => {
  return fetchJSON<RetailerInfo>(`/api/comparison/retailers/${retailerKey}/config`);
};

/**
 * Update retailer status (enable/disable)
 * POST /api/comparison/retailers/{retailer_key}/status
 */
export const updateRetailerStatus = async (
  retailerKey: string,
  active: boolean
): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/comparison/retailers/${retailerKey}/status`, {
    method: 'POST',
    body: JSON.stringify({ active }),
  });
};

/**
 * Search by image - Upload image → AI detection → scraper
 * POST /api/comparison/search-by-image
 */
export const searchByImage = async (
  file: File,
  retailers?: string[]
): Promise<RealTimeSearchResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (retailers && retailers.length > 0) {
    formData.append('retailers', JSON.stringify(retailers));
  }

  const response = await fetch(`${API_BASE_URL}/api/comparison/search-by-image`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Image search failed');
  }

  return response.json();
};

/**
 * Search by barcode
 * POST /api/comparison/search-by-barcode
 */
export const searchByBarcode = async (
  barcode: string,
  retailers?: string[]
): Promise<RealTimeSearchResponse> => {
  return fetchJSON<RealTimeSearchResponse>('/api/comparison/search-by-barcode', {
    method: 'POST',
    body: JSON.stringify({ barcode, retailers }),
  });
};

/**
 * Get comparison statistics
 * GET /api/comparison/stats
 */
export const getComparisonStats = async (): Promise<{
  total_comparisons: number;
  total_products: number;
  total_retailers: number;
  avg_price_difference: number;
  total_savings: number;
}> => {
  return fetchJSON(`/api/comparison/stats`);
};

/**
 * Get available price sources
 * GET /api/comparison/sources
 */
export const getPriceSources = async (): Promise<
  { name: string; url: string; active: boolean }[]
> => {
  return fetchJSON(`/api/comparison/sources`);
};

/**
 * Delete price comparison data for a product
 * DELETE /api/comparison/compare/{product_id}
 */
export const deletePriceComparison = async (
  productId: number | string
): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/comparison/compare/${productId}`, {
    method: 'DELETE',
  });
};

// ==================== EXPORT ====================

export const comparisonAPI = {
  getPriceComparison,
  refreshPriceComparison,
  getPriceHistory,
  realTimeSearch,
  smartSearch,
  getRetailers,
  enhancedSearch,
  getRetailerConfig,
  updateRetailerStatus,
  searchByImage,
  searchByBarcode,
  getComparisonStats,
  getPriceSources,
  deletePriceComparison,
};

export default comparisonAPI;
