// Smart Lists API Service - CRUD operations with SSE streaming comparison jobs
// /api/lists/*

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ==================== TYPES ====================

export interface SmartList {
  id: number;
  user_id?: number;
  name: string;
  description?: string;
  category?: string;
  items: ListItem[];
  total_items: number;
  estimated_total: number;
  created_at: string;
  updated_at: string;
  shared: boolean;
  tags?: string[];
}

export interface ListItem {
  id: number;
  list_id: number;
  product_id?: number;
  product_name: string;
  quantity: number;
  priority: 'low' | 'medium' | 'high';
  notes?: string;
  target_price?: number;
  current_best_price?: number;
  current_best_retailer?: string;
  position: number;
  completed: boolean;
  added_at: string;
}

export interface CreateListRequest {
  name: string;
  description?: string;
  category?: string;
  tags?: string[];
}

export interface UpdateListRequest {
  name?: string;
  description?: string;
  category?: string;
  tags?: string[];
  shared?: boolean;
}

export interface AddItemRequest {
  product_name: string;
  product_id?: number;
  quantity?: number;
  priority?: 'low' | 'medium' | 'high';
  notes?: string;
  target_price?: number;
}

export interface UpdateItemRequest {
  product_name?: string;
  quantity?: number;
  priority?: 'low' | 'medium' | 'high';
  notes?: string;
  target_price?: number;
  completed?: boolean;
}

export interface ReorderItemsRequest {
  item_positions: { item_id: number; position: number }[];
}

export interface ComparisonJob {
  job_id: string;
  list_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number; // 0-100
  items_processed: number;
  total_items: number;
  results?: ComparisonResult[];
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface ComparisonResult {
  item_id: number;
  product_name: string;
  quantity: number;
  best_deal: {
    retailer: string;
    price: number;
    url: string;
    availability: string;
  };
  alternatives: {
    retailer: string;
    price: number;
    url: string;
    availability: string;
  }[];
  total_cost: number;
  savings_vs_avg: number;
}

export interface ListTemplate {
  id: number;
  name: string;
  description: string;
  category: string;
  items: { product_name: string; quantity: number }[];
  usage_count: number;
}

export interface ComparisonJobUpdate {
  type: 'progress' | 'item_complete' | 'complete' | 'error';
  job_id: string;
  progress?: number;
  item?: ComparisonResult;
  message?: string;
  error?: string;
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
 * List all smart lists for current user
 * GET /api/lists
 */
export const listSmartLists = async (category?: string): Promise<SmartList[]> => {
  const params = category ? `?category=${category}` : '';
  return fetchJSON<SmartList[]>(`/api/lists${params}`);
};

/**
 * Create new smart list
 * POST /api/lists
 */
export const createSmartList = async (request: CreateListRequest): Promise<SmartList> => {
  return fetchJSON<SmartList>('/api/lists', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * Get smart list details
 * GET /api/lists/{id}
 */
export const getSmartList = async (listId: number): Promise<SmartList> => {
  return fetchJSON<SmartList>(`/api/lists/${listId}`);
};

/**
 * Update smart list
 * PUT /api/lists/{id}
 */
export const updateSmartList = async (
  listId: number,
  request: UpdateListRequest
): Promise<SmartList> => {
  return fetchJSON<SmartList>(`/api/lists/${listId}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
};

/**
 * Delete smart list
 * DELETE /api/lists/{id}
 */
export const deleteSmartList = async (listId: number): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/lists/${listId}`, {
    method: 'DELETE',
  });
};

/**
 * Add item to list
 * POST /api/lists/{id}/items
 */
export const addListItem = async (listId: number, request: AddItemRequest): Promise<ListItem> => {
  return fetchJSON<ListItem>(`/api/lists/${listId}/items`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * Update list item
 * PUT /api/lists/{id}/items/{item_id}
 */
export const updateListItem = async (
  listId: number,
  itemId: number,
  request: UpdateItemRequest
): Promise<ListItem> => {
  return fetchJSON<ListItem>(`/api/lists/${listId}/items/${itemId}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
};

/**
 * Delete list item
 * DELETE /api/lists/{id}/items/{item_id}
 */
export const deleteListItem = async (
  listId: number,
  itemId: number
): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/lists/${listId}/items/${itemId}`, {
    method: 'DELETE',
  });
};

/**
 * Reorder list items
 * POST /api/lists/{id}/items/reorder
 */
export const reorderListItems = async (
  listId: number,
  request: ReorderItemsRequest
): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/lists/${listId}/items/reorder`, {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * Start comparison job for list
 * POST /api/lists/{id}/compare
 */
export const startComparisonJob = async (
  listId: number,
  retailers?: string[]
): Promise<{ job_id: string; message: string }> => {
  return fetchJSON<{ job_id: string; message: string }>(`/api/lists/${listId}/compare`, {
    method: 'POST',
    body: JSON.stringify({ retailers }),
  });
};

/**
 * Get comparison job status
 * GET /api/lists/compare-jobs/{job_id}
 */
export const getComparisonJobStatus = async (jobId: string): Promise<ComparisonJob> => {
  return fetchJSON<ComparisonJob>(`/api/lists/compare-jobs/${jobId}`);
};

/**
 * Stream comparison job updates with SSE
 * GET /api/lists/compare-jobs/{job_id}/stream
 * 
 * Returns EventSource for real-time updates
 */
export const streamComparisonJob = (
  jobId: string,
  onUpdate: (update: ComparisonJobUpdate) => void,
  onError?: (error: Event) => void,
  onComplete?: (job: ComparisonJob) => void
): EventSource => {
  const url = `${API_BASE_URL}/api/lists/compare-jobs/${jobId}/stream`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event: MessageEvent) => {
    try {
      const update: ComparisonJobUpdate = JSON.parse(event.data);
      onUpdate(update);

      if (update.type === 'complete' && onComplete) {
        // Fetch full job results
        getComparisonJobStatus(jobId).then((job) => {
          onComplete(job);
          eventSource.close();
        });
      } else if (update.type === 'error') {
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
 * Get list templates
 * GET /api/lists/templates
 */
export const getListTemplates = async (category?: string): Promise<ListTemplate[]> => {
  const params = category ? `?category=${category}` : '';
  return fetchJSON<ListTemplate[]>(`/api/lists/templates${params}`);
};

/**
 * Apply template to create new list
 * POST /api/lists/templates/{id}/apply
 */
export const applyTemplate = async (
  templateId: number,
  list_name?: string
): Promise<SmartList> => {
  return fetchJSON<SmartList>(`/api/lists/templates/${templateId}/apply`, {
    method: 'POST',
    body: JSON.stringify({ list_name }),
  });
};

/**
 * Duplicate existing list
 * POST /api/lists/{id}/duplicate
 */
export const duplicateList = async (listId: number, new_name?: string): Promise<SmartList> => {
  return fetchJSON<SmartList>(`/api/lists/${listId}/duplicate`, {
    method: 'POST',
    body: JSON.stringify({ new_name }),
  });
};

/**
 * Export list to CSV
 * GET /api/lists/{id}/export
 */
export const exportList = async (listId: number, format: 'csv' | 'json' = 'csv'): Promise<Blob> => {
  const response = await fetch(`${API_BASE_URL}/api/lists/${listId}/export?format=${format}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Export failed');
  }

  return response.blob();
};

/**
 * Share list (get share link)
 * POST /api/lists/{id}/share
 */
export const shareList = async (
  listId: number
): Promise<{ share_token: string; share_url: string }> => {
  return fetchJSON<{ share_token: string; share_url: string }>(`/api/lists/${listId}/share`, {
    method: 'POST',
  });
};

/**
 * Get shared list
 * GET /api/lists/shared/{share_token}
 */
export const getSharedList = async (shareToken: string): Promise<SmartList> => {
  return fetchJSON<SmartList>(`/api/lists/shared/${shareToken}`);
};

// ==================== EXPORT ====================

export const smartListsAPI = {
  listSmartLists,
  createSmartList,
  getSmartList,
  updateSmartList,
  deleteSmartList,
  addListItem,
  updateListItem,
  deleteListItem,
  reorderListItems,
  startComparisonJob,
  getComparisonJobStatus,
  streamComparisonJob,
  getListTemplates,
  applyTemplate,
  duplicateList,
  exportList,
  shareList,
  getSharedList,
};

export default smartListsAPI;
