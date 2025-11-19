import React, { useEffect, useState, useRef } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { api } from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Zap, AlertCircle, TrendingUp } from 'lucide-react';

interface RealTimeUpdatesProps {
  userId?: string;
  enabled?: boolean;
}

interface Update {
  id: string;
  type: 'price' | 'inventory' | 'alert' | 'recommendation';
  title: string;
  message: string;
  timestamp: number;
  data?: Record<string, unknown>;
}

export function RealTimeUpdates({ userId, enabled = true }: RealTimeUpdatesProps) {
  const [updates, setUpdates] = useState<Update[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled || !userId) return;

    try {
      // Connect to WebSocket
      ws.current = api.connectRealtime(userId);

      ws.current.onopen = () => {
        setIsConnected(true);
        console.log('✅ Connected to real-time service');

        // Subscribe to channels
        if (ws.current) {
          ws.current.send(JSON.stringify({
            type: 'subscribe',
            channel: 'live_prices',
          }));
          ws.current.send(JSON.stringify({
            type: 'subscribe',
            channel: 'price_alerts',
          }));
          ws.current.send(JSON.stringify({
            type: 'subscribe',
            channel: 'inventory_updates',
          }));
        }
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'update') {
            const eventData = message.event;
            const update: Update = {
              id: `${Date.now()}-${Math.random()}`,
              type: eventData.type || 'price',
              title: getUpdateTitle(eventData.type),
              message: getUpdateMessage(eventData),
              timestamp: Date.now(),
              data: eventData.data,
            };

            setUpdates((prev) => [update, ...prev.slice(0, 9)]);
          } else if (message.type === 'pong') {
            // Ping-pong for keep-alive
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      ws.current.onclose = () => {
        console.log('❌ Disconnected from real-time service');
        setIsConnected(false);
      };

      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);

      return () => {
        clearInterval(pingInterval);
        if (ws.current) {
          ws.current.close();
        }
      };
    } catch (error) {
      console.error('Failed to connect to real-time service:', error);
    }
  }, [userId, enabled]);

  const getUpdateTitle = (type: string): string => {
    switch (type) {
      case 'price_update':
        return 'Price Update';
      case 'inventory_update':
        return 'Inventory Change';
      case 'price_alert':
        return 'Price Alert';
      default:
        return 'Update';
    }
  };

  const getUpdateMessage = (event: Record<string, unknown>): string => {
    const type = event.type as string;
    switch (type) {
      case 'price_update':
        return `${event.product_name} is now $${event.new_price}`;
      case 'inventory_update':
        return `${event.product_name} inventory: ${event.quantity} units`;
      case 'price_alert':
        return `${event.product_name} reached your target price of $${event.price}`;
      default:
        return 'New update available';
    }
  };

  const getUpdateIcon = (type: string) => {
    switch (type) {
      case 'price':
        return <TrendingUp className="w-4 h-4" />;
      case 'alert':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Zap className="w-4 h-4" />;
    }
  };

  const getUpdateColor = (type: string): string => {
    switch (type) {
      case 'price':
        return 'bg-blue-100 text-blue-800';
      case 'inventory':
        return 'bg-green-100 text-green-800';
      case 'alert':
        return 'bg-orange-100 text-orange-800';
      case 'recommendation':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!userId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Real-Time Updates</CardTitle>
          <CardDescription>Sign in to get live updates</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Real-Time Updates</CardTitle>
            <CardDescription>Live price and inventory changes</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs font-semibold">{isConnected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {!isConnected && (
          <Alert className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>Connecting to real-time service...</AlertDescription>
          </Alert>
        )}

        <div className="space-y-2 max-h-80 overflow-y-auto">
          {updates.length > 0 ? (
            updates.map((update) => (
              <div
                key={update.id}
                className={`flex gap-3 p-3 rounded-lg border-l-4 ${getUpdateColor(update.type)} bg-white`}
              >
                <div className="flex-shrink-0 pt-0.5">{getUpdateIcon(update.type)}</div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm">{update.title}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{update.message}</p>
                </div>
                <span className="text-xs text-gray-500 flex-shrink-0">
                  {Math.round((Date.now() - update.timestamp) / 1000)}s ago
                </span>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              {isConnected ? (
                <>
                  <Zap className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Waiting for updates...</p>
                </>
              ) : (
                <>
                  <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Connection pending...</p>
                </>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
