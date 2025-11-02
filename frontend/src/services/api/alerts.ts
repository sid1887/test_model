// Price Alerts API Service - CRUD operations and WebSocket real-time updates
// /api/alerts/* and WebSocket /ws/alerts

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

// ==================== TYPES ====================

export interface PriceAlert {
  id: number;
  user_id?: number;
  product_id: number;
  product_name?: string;
  target_price: number;
  condition: 'below' | 'above' | 'equals' | 'change';
  percentage_change?: number;
  active: boolean;
  triggered: boolean;
  last_triggered?: string;
  created_at: string;
  updated_at: string;
  notification_method: 'email' | 'push' | 'sms' | 'all';
  retailers?: string[];
  frequency: 'instant' | 'hourly' | 'daily';
}

export interface CreateAlertRequest {
  product_id: number;
  target_price: number;
  condition: 'below' | 'above' | 'equals' | 'change';
  percentage_change?: number;
  notification_method?: 'email' | 'push' | 'sms' | 'all';
  retailers?: string[];
  frequency?: 'instant' | 'hourly' | 'daily';
}

export interface UpdateAlertRequest {
  target_price?: number;
  condition?: 'below' | 'above' | 'equals' | 'change';
  percentage_change?: number;
  active?: boolean;
  notification_method?: 'email' | 'push' | 'sms' | 'all';
  retailers?: string[];
  frequency?: 'instant' | 'hourly' | 'daily';
}

export interface AlertHistoryEntry {
  id: number;
  alert_id: number;
  triggered_at: string;
  price_at_trigger: number;
  retailer: string;
  notification_sent: boolean;
  notification_method: string;
}

export interface AlertNotification {
  id: number;
  alert_id: number;
  product_name: string;
  message: string;
  notification_type: 'price_drop' | 'price_increase' | 'target_reached' | 'back_in_stock';
  sent_at: string;
  read: boolean;
}

export interface AlertPreferences {
  email_enabled: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
  quiet_hours_start?: string; // "22:00"
  quiet_hours_end?: string; // "08:00"
  max_notifications_per_day?: number;
  notification_sound?: boolean;
}

export interface WebSocketMessage {
  type: 'alert_fired' | 'price_update' | 'alert_status' | 'connection' | 'error';
  data: {
    alert_id?: number;
    product_id?: number;
    product_name?: string;
    old_price?: number;
    new_price?: number;
    retailer?: string;
    timestamp?: string;
    message?: string;
    [key: string]: unknown;
  };
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
 * List all alerts for current user
 * GET /api/alerts
 */
export const listAlerts = async (active_only?: boolean): Promise<PriceAlert[]> => {
  const params = active_only !== undefined ? `?active_only=${active_only}` : '';
  return fetchJSON<PriceAlert[]>(`/api/alerts${params}`);
};

/**
 * Create new price alert
 * POST /api/alerts
 */
export const createAlert = async (request: CreateAlertRequest): Promise<PriceAlert> => {
  return fetchJSON<PriceAlert>('/api/alerts', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * Get alert details
 * GET /api/alerts/{id}
 */
export const getAlert = async (alertId: number): Promise<PriceAlert> => {
  return fetchJSON<PriceAlert>(`/api/alerts/${alertId}`);
};

/**
 * Update alert
 * PUT /api/alerts/{id}
 */
export const updateAlert = async (
  alertId: number,
  request: UpdateAlertRequest
): Promise<PriceAlert> => {
  return fetchJSON<PriceAlert>(`/api/alerts/${alertId}`, {
    method: 'PUT',
    body: JSON.stringify(request),
  });
};

/**
 * Delete alert
 * DELETE /api/alerts/{id}
 */
export const deleteAlert = async (alertId: number): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/alerts/${alertId}`, {
    method: 'DELETE',
  });
};

/**
 * Manually trigger alert (test)
 * POST /api/alerts/{id}/trigger-now
 */
export const triggerAlert = async (alertId: number): Promise<{ message: string; fired: boolean }> => {
  return fetchJSON<{ message: string; fired: boolean }>(`/api/alerts/${alertId}/trigger-now`, {
    method: 'POST',
  });
};

/**
 * Pause alert
 * POST /api/alerts/{id}/pause
 */
export const pauseAlert = async (alertId: number): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/alerts/${alertId}/pause`, {
    method: 'POST',
  });
};

/**
 * Resume alert
 * POST /api/alerts/{id}/resume
 */
export const resumeAlert = async (alertId: number): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/alerts/${alertId}/resume`, {
    method: 'POST',
  });
};

/**
 * Get alert history
 * GET /api/alerts/{id}/history
 */
export const getAlertHistory = async (
  alertId: number,
  limit?: number
): Promise<AlertHistoryEntry[]> => {
  const params = limit ? `?limit=${limit}` : '';
  return fetchJSON<AlertHistoryEntry[]>(`/api/alerts/${alertId}/history${params}`);
};

/**
 * Get alert notifications
 * GET /api/alerts/{id}/notifications
 */
export const getAlertNotifications = async (
  alertId: number,
  unread_only?: boolean
): Promise<AlertNotification[]> => {
  const params = unread_only ? `?unread_only=${unread_only}` : '';
  return fetchJSON<AlertNotification[]>(`/api/alerts/${alertId}/notifications${params}`);
};

/**
 * Mark notification as read
 * POST /api/alerts/notifications/{id}/read
 */
export const markNotificationRead = async (
  notificationId: number
): Promise<{ message: string }> => {
  return fetchJSON<{ message: string }>(`/api/alerts/notifications/${notificationId}/read`, {
    method: 'POST',
  });
};

/**
 * Get user alert preferences
 * GET /api/alerts/preferences
 */
export const getAlertPreferences = async (): Promise<AlertPreferences> => {
  return fetchJSON<AlertPreferences>('/api/alerts/preferences');
};

/**
 * Update user alert preferences
 * PUT /api/alerts/preferences
 */
export const updateAlertPreferences = async (
  preferences: Partial<AlertPreferences>
): Promise<AlertPreferences> => {
  return fetchJSON<AlertPreferences>('/api/alerts/preferences', {
    method: 'PUT',
    body: JSON.stringify(preferences),
  });
};

// ==================== WEBSOCKET CONNECTION ====================

export class AlertsWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private messageHandlers: ((message: WebSocketMessage) => void)[] = [];
  private errorHandlers: ((error: Event) => void)[] = [];
  private closeHandlers: (() => void)[] = [];
  private openHandlers: (() => void)[] = [];

  /**
   * Connect to WebSocket for real-time alert updates
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    const url = `${WS_BASE_URL}/ws/alerts`;
    console.log('Connecting to WebSocket:', url);

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      this.openHandlers.forEach((handler) => handler());
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('📨 WebSocket message:', message);
        this.messageHandlers.forEach((handler) => handler(message));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.ws.onerror = (error: Event) => {
      console.error('❌ WebSocket error:', error);
      this.errorHandlers.forEach((handler) => handler(error));
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.closeHandlers.forEach((handler) => handler());
      this.attemptReconnect();
    };
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached. Giving up.');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Add message handler
   */
  onMessage(handler: (message: WebSocketMessage) => void): () => void {
    this.messageHandlers.push(handler);
    // Return unsubscribe function
    return () => {
      const index = this.messageHandlers.indexOf(handler);
      if (index > -1) {
        this.messageHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Add error handler
   */
  onError(handler: (error: Event) => void): () => void {
    this.errorHandlers.push(handler);
    return () => {
      const index = this.errorHandlers.indexOf(handler);
      if (index > -1) {
        this.errorHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Add close handler
   */
  onClose(handler: () => void): () => void {
    this.closeHandlers.push(handler);
    return () => {
      const index = this.closeHandlers.indexOf(handler);
      if (index > -1) {
        this.closeHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Add open handler
   */
  onOpen(handler: () => void): () => void {
    this.openHandlers.push(handler);
    return () => {
      const index = this.openHandlers.indexOf(handler);
      if (index > -1) {
        this.openHandlers.splice(index, 1);
      }
    };
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Create singleton instance
export const alertsWebSocket = new AlertsWebSocket();

// ==================== EXPORT ====================

export const alertsAPI = {
  listAlerts,
  createAlert,
  getAlert,
  updateAlert,
  deleteAlert,
  triggerAlert,
  pauseAlert,
  resumeAlert,
  getAlertHistory,
  getAlertNotifications,
  markNotificationRead,
  getAlertPreferences,
  updateAlertPreferences,
  websocket: alertsWebSocket,
};

export default alertsAPI;
