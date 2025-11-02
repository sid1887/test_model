// React Query hooks for Price Alerts API with WebSocket
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, useCallback } from 'react';
import { alertsAPI } from '@/services/api';
import type {
  PriceAlert,
  CreateAlertRequest,
  UpdateAlertRequest,
  AlertHistoryEntry,
  AlertNotification,
  AlertPreferences,
  WebSocketMessage,
} from '@/services/api/alerts';
import { toast } from 'sonner';

/**
 * List all price alerts
 */
export const useAlerts = (active_only?: boolean) => {
  return useQuery<PriceAlert[]>({
    queryKey: ['alerts', 'list', active_only],
    queryFn: () => alertsAPI.listAlerts(active_only),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
};

/**
 * Get single alert
 */
export const useAlert = (alertId: number) => {
  return useQuery<PriceAlert>({
    queryKey: ['alerts', alertId],
    queryFn: () => alertsAPI.getAlert(alertId),
    enabled: !!alertId,
  });
};

/**
 * Create alert mutation
 */
export const useCreateAlert = () => {
  const queryClient = useQueryClient();

  return useMutation<PriceAlert, Error, CreateAlertRequest>({
    mutationFn: (request) => alertsAPI.createAlert(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Price alert created successfully!');
    },
    onError: (error) => {
      toast.error(`Failed to create alert: ${error.message}`);
    },
  });
};

/**
 * Update alert mutation
 */
export const useUpdateAlert = () => {
  const queryClient = useQueryClient();

  return useMutation<PriceAlert, Error, { alertId: number; request: UpdateAlertRequest }>({
    mutationFn: ({ alertId, request }) => alertsAPI.updateAlert(alertId, request),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.invalidateQueries({ queryKey: ['alerts', variables.alertId] });
      toast.success('Alert updated successfully!');
    },
    onError: (error) => {
      toast.error(`Failed to update alert: ${error.message}`);
    },
  });
};

/**
 * Delete alert mutation
 */
export const useDeleteAlert = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, number>({
    mutationFn: (alertId) => alertsAPI.deleteAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Alert deleted successfully!');
    },
    onError: (error) => {
      toast.error(`Failed to delete alert: ${error.message}`);
    },
  });
};

/**
 * Trigger alert manually
 */
export const useTriggerAlert = () => {
  return useMutation<{ message: string; fired: boolean }, Error, number>({
    mutationFn: (alertId) => alertsAPI.triggerAlert(alertId),
    onSuccess: (data) => {
      if (data.fired) {
        toast.success('Alert fired!');
      } else {
        toast.info('Alert conditions not met');
      }
    },
  });
};

/**
 * Pause alert
 */
export const usePauseAlert = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, number>({
    mutationFn: (alertId) => alertsAPI.pauseAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Alert paused');
    },
  });
};

/**
 * Resume alert
 */
export const useResumeAlert = () => {
  const queryClient = useQueryClient();

  return useMutation<{ message: string }, Error, number>({
    mutationFn: (alertId) => alertsAPI.resumeAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Alert resumed');
    },
  });
};

/**
 * Get alert history
 */
export const useAlertHistory = (alertId: number, limit?: number) => {
  return useQuery<AlertHistoryEntry[]>({
    queryKey: ['alerts', alertId, 'history', limit],
    queryFn: () => alertsAPI.getAlertHistory(alertId, limit),
    enabled: !!alertId,
  });
};

/**
 * Get alert notifications
 */
export const useAlertNotifications = (alertId: number, unread_only?: boolean) => {
  return useQuery<AlertNotification[]>({
    queryKey: ['alerts', alertId, 'notifications', unread_only],
    queryFn: () => alertsAPI.getAlertNotifications(alertId, unread_only),
    enabled: !!alertId,
  });
};

/**
 * Get/update alert preferences
 */
export const useAlertPreferences = () => {
  const queryClient = useQueryClient();

  const query = useQuery<AlertPreferences>({
    queryKey: ['alerts', 'preferences'],
    queryFn: () => alertsAPI.getAlertPreferences(),
  });

  const mutation = useMutation<AlertPreferences, Error, Partial<AlertPreferences>>({
    mutationFn: (preferences) => alertsAPI.updateAlertPreferences(preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'preferences'] });
      toast.success('Preferences updated!');
    },
  });

  return { ...query, update: mutation };
};

/**
 * WebSocket hook for real-time alert updates
 */
export const useAlertsWebSocket = () => {
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const queryClient = useQueryClient();

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      setMessages((prev) => [...prev, message]);

      // Handle different message types
      if (message.type === 'alert_fired') {
        toast.success(`🔔 Alert fired: ${message.data.product_name}`, {
          description: `New price: $${message.data.new_price}`,
          duration: 5000,
        });

        // Invalidate alerts to refresh data
        queryClient.invalidateQueries({ queryKey: ['alerts'] });
      } else if (message.type === 'price_update') {
        // Silent update, just refresh data
        queryClient.invalidateQueries({ queryKey: ['alerts'] });
      }
    },
    [queryClient]
  );

  useEffect(() => {
    const ws = alertsAPI.websocket;

    // Setup handlers
    const unsubMessage = ws.onMessage(handleMessage);
    const unsubOpen = ws.onOpen(() => setIsConnected(true));
    const unsubClose = ws.onClose(() => setIsConnected(false));
    const unsubError = ws.onError((error) => {
      console.error('WebSocket error:', error);
      toast.error('Lost connection to alerts service');
    });

    // Connect
    ws.connect();

    // Cleanup
    return () => {
      unsubMessage();
      unsubOpen();
      unsubClose();
      unsubError();
      ws.disconnect();
    };
  }, [handleMessage]);

  return {
    messages,
    isConnected,
    clearMessages: () => setMessages([]),
  };
};
