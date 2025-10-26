/**
 * Alert Detail Modal Component
 * Shows alert history and details
 */

import React, { useEffect, useState, useCallback } from 'react';
import { X, Clock, TrendingDown, Bell } from 'lucide-react';
import { Alert, AlertEvent } from '../../types/alerts';
import { useAlerts } from '../../hooks/useAlerts';
import { formatDistanceToNow } from 'date-fns';

interface AlertDetailModalProps {
  alert: Alert;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: (id: number, data: Record<string, unknown>) => Promise<Alert>;
}

export const AlertDetailModal: React.FC<AlertDetailModalProps> = ({
  alert,
  isOpen,
  onClose,
}) => {
  const [history, setHistory] = useState<{ events: AlertEvent[]; total_events: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const { getAlertHistory } = useAlerts();

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getAlertHistory(alert.id);
      setHistory(data as { events: AlertEvent[]; total_events: number });
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  }, [alert.id, getAlertHistory]);

  useEffect(() => {
    if (isOpen && alert) {
      loadHistory();
    }
  }, [isOpen, alert, loadHistory]);

  if (!isOpen) return null;

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'created':
        return <Bell className="h-4 w-4 text-green-600" />;
      case 'checked':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'price_changed':
        return <TrendingDown className="h-4 w-4 text-orange-600" />;
      case 'fired':
        return <Bell className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-30" onClick={onClose}></div>
        
        <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full p-6 max-h-[80vh] overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6 sticky top-0 bg-white pb-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">Alert Details</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          
          {/* Alert Info */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Product ID</p>
                <p className="font-medium text-gray-900">#{alert.product_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Target Price</p>
                <p className="font-medium text-gray-900">${alert.target_price.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <p className="font-medium text-gray-900 capitalize">{alert.status}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Fire Count</p>
                <p className="font-medium text-gray-900">{alert.fire_count}</p>
              </div>
            </div>
          </div>
          
          {/* History Timeline */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Event History</h3>
            
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : history && history.events.length > 0 ? (
              <div className="space-y-4">
                {history.events.map((event, index) => (
                  <div key={event.id} className="flex gap-4">
                    <div className="flex flex-col items-center">
                      <div className="p-2 bg-gray-100 rounded-full">
                        {getEventIcon(event.event_type)}
                      </div>
                      {index < history.events.length - 1 && (
                        <div className="flex-1 w-0.5 bg-gray-200 min-h-[40px]"></div>
                      )}
                    </div>
                    
                    <div className="flex-1 pb-6">
                      <p className="font-medium text-gray-900 capitalize">
                        {event.event_type.replace('_', ' ')}
                      </p>
                      <p className="text-sm text-gray-600">
                        {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
                      </p>
                      {event.current_price && (
                        <p className="text-sm text-gray-700 mt-1">
                          Price: ${event.current_price.toFixed(2)}
                          {event.previous_price && (
                            <span className="text-gray-500">
                              {' '}(was ${event.previous_price.toFixed(2)})
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-600 py-8">No events yet</p>
            )}
          </div>
          
          {/* Close Button */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={onClose}
              className="w-full px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
