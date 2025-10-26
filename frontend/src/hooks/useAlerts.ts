/**
 * Custom hook for managing price alerts
 * Provides CRUD operations and real-time updates
 */

import { useState, useEffect, useCallback } from 'react';
import { Alert, AlertCreateRequest, AlertUpdateRequest } from '../types/alerts';
import { API_BASE_URL } from '../config/env';

interface UseAlertsReturn {
  alerts: Alert[];
  loading: boolean;
  error: string | null;
  totalAlerts: number;
  createAlert: (data: AlertCreateRequest) => Promise<Alert>;
  updateAlert: (id: number, data: AlertUpdateRequest) => Promise<Alert>;
  deleteAlert: (id: number) => Promise<void>;
  pauseAlert: (id: number) => Promise<Alert>;
  resumeAlert: (id: number) => Promise<Alert>;
  triggerAlert: (id: number) => Promise<void>;
  refreshAlerts: () => Promise<void>;
  getAlertHistory: (id: number) => Promise<Record<string, unknown>>;
}

export const useAlerts = (statusFilter: string = 'all'): UseAlertsReturn => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalAlerts, setTotalAlerts] = useState(0);

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      params.append('page_size', '100');
      
      const response = await fetch(`${API_BASE_URL}/api/alerts?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch alerts: ${response.statusText}`);
      }
      
      const data = await response.json();
      setAlerts(data.alerts || []);
      setTotalAlerts(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const createAlert = async (data: AlertCreateRequest): Promise<Alert> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create alert');
      }
      
      const alert = await response.json();
      await fetchAlerts(); // Refresh list
      return alert;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create alert');
      throw err;
    }
  };

  const updateAlert = async (id: number, data: AlertUpdateRequest): Promise<Alert> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update alert');
      }
      
      const alert = await response.json();
      await fetchAlerts(); // Refresh list
      return alert;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update alert');
      throw err;
    }
  };

  const deleteAlert = async (id: number): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete alert');
      }
      
      await fetchAlerts(); // Refresh list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete alert');
      throw err;
    }
  };

  const pauseAlert = async (id: number): Promise<Alert> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${id}/pause`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to pause alert');
      }
      
      const alert = await response.json();
      await fetchAlerts(); // Refresh list
      return alert;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pause alert');
      throw err;
    }
  };

  const resumeAlert = async (id: number): Promise<Alert> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${id}/resume`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to resume alert');
      }
      
      const alert = await response.json();
      await fetchAlerts(); // Refresh list
      return alert;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume alert');
      throw err;
    }
  };

  const triggerAlert = async (id: number): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${id}/trigger-now`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to trigger alert');
      }
      
      // Don't refresh immediately, as it's just queued
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger alert');
      throw err;
    }
  };

  const getAlertHistory = async (id: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/alerts/${id}/history`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch alert history');
      }
      
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
      throw err;
    }
  };

  return {
    alerts,
    loading,
    error,
    totalAlerts,
    createAlert,
    updateAlert,
    deleteAlert,
    pauseAlert,
    resumeAlert,
    triggerAlert,
    refreshAlerts: fetchAlerts,
    getAlertHistory,
  };
};
