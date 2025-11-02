// Search V2 API Service - God Engine with streaming, image, voice search
// Uses native fetch API to avoid axios dependency issues

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ==================== TYPES ====================

export interface SearchOptions {
  top_k?: number;
  cache_level?: 'l1' | 'l2' | 'both';
  enrich?: boolean;
  use_faiss?: boolean;
}

export interface UnifiedSearchResponse {
  query: string;
  results: SearchResult[];
  cache_info: {
    level: string;
    hit: boolean;
  };
  enriched: boolean;
  total_results: number;
}

export interface SearchResult {
  id: string;
  title: string;
  description?: string;
  price?: number;
  image_url?: string;
  retailer?: string;
  similarity_score?: number;
  in_stock?: boolean;
  url?: string;
  category?: string;
}

export interface ImageSearchRequest {
  file: File;
  sites?: string[];
  top_k?: number;
}

export interface ImageSearchResponse {
  image_id: string;
  analysis: {
    clip_results?: {
      product_id: string;
      similarity: number;
      title: string;
    }[];
    barcode?: string;
    ocr_text?: string;
  };
  search_results: SearchResult[];
}

export interface VoiceSearchRequest {
  audio: Blob;
}

export interface VoiceSearchResponse {
  transcription: string;
  confidence: number;
  entities?: string[];
  search_results: SearchResult[];
}

export interface CompleteProductContext {
  product: {
    id: number | string;
    title: string;
    description?: string;
    price?: number;
    image_url?: string;
  };
  price_history: {
    date: string;
    price: number;
    retailer: string;
  }[];
  similar_products: SearchResult[];
  analytics: {
    avg_price: number;
    price_trend: 'up' | 'down' | 'stable';
    best_deal: SearchResult;
  };
  real_time_data?: {
    stock_available: boolean;
    last_updated: string;
  };
  news?: {
    title: string;
    url: string;
    date: string;
  }[];
  ai_insights?: string;
}

export interface StreamingPhase {
  phase: 'ghost' | 'real' | 'enriched' | 'realtime' | 'complete';
  results?: SearchResult[];
  analysis?: Record<string, unknown>;
  message?: string;
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
 * Unified search with multi-tier cache and FAISS
 * GET /api/v2/search
 */
export const unifiedSearch = async (
  query: string,
  options?: SearchOptions
): Promise<UnifiedSearchResponse> => {
  const params = new URLSearchParams({
    q: query,
    ...(options?.top_k && { top_k: options.top_k.toString() }),
    ...(options?.cache_level && { cache_level: options.cache_level }),
    ...(options?.enrich !== undefined && { enrich: options.enrich.toString() }),
    ...(options?.use_faiss !== undefined && { use_faiss: options.use_faiss.toString() }),
  });

  return fetchJSON<UnifiedSearchResponse>(`/api/v2/search?${params}`);
};

/**
 * Streaming search with SSE (Server-Sent Events)
 * GET /api/v2/search/stream
 * 
 * Returns EventSource for real-time updates
 * 
 * Phases:
 * 1. ghost - Ghost/skeleton results
 * 2. real - Real cached results
 * 3. enriched - AI-enriched results
 * 4. realtime - Live scraper results
 * 5. complete - Search complete
 */
export const streamingSearch = (
  query: string,
  onMessage: (phase: StreamingPhase) => void,
  onError?: (error: Event) => void,
  onComplete?: () => void
): EventSource => {
  const url = `${API_BASE_URL}/api/v2/search/stream?q=${encodeURIComponent(query)}`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event: MessageEvent) => {
    try {
      const data: StreamingPhase = JSON.parse(event.data);
      onMessage(data);

      if (data.phase === 'complete' && onComplete) {
        onComplete();
        eventSource.close();
      }
    } catch (error) {
      console.error('Error parsing SSE message:', error);
    }
  };

  eventSource.onerror = (error: Event) => {
    console.error('SSE connection error:', error);
    if (onError) {
      onError(error);
    }
    eventSource.close();
  };

  return eventSource;
};

/**
 * Image search with CLIP AI
 * POST /api/v2/search/image
 */
export const imageSearch = async (
  file: File,
  sites?: string[],
  top_k: number = 10
): Promise<ImageSearchResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (sites && sites.length > 0) {
    formData.append('sites', sites.join(','));
  }
  formData.append('top_k', top_k.toString());

  const response = await fetch(`${API_BASE_URL}/api/v2/search/image`, {
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
 * Voice search with Whisper STT
 * POST /api/v2/search/voice
 */
export const voiceSearch = async (
  audioBlob: Blob
): Promise<VoiceSearchResponse> => {
  const formData = new FormData();
  formData.append('file', audioBlob, 'audio.webm');

  const response = await fetch(`${API_BASE_URL}/api/v2/search/voice`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Voice search failed');
  }

  return response.json();
};

/**
 * Get complete product context (price history, similar, analytics, etc.)
 * GET /api/v2/product/{id}/complete
 */
export const getCompleteProductContext = async (
  productId: string | number
): Promise<CompleteProductContext> => {
  return fetchJSON<CompleteProductContext>(`/api/v2/product/${productId}/complete`);
};

// ==================== EXPORT ====================

export const searchV2API = {
  unifiedSearch,
  streamingSearch,
  imageSearch,
  voiceSearch,
  getCompleteProductContext,
};

export default searchV2API;
