/**
 * Custom hook for WebSocket connections
 * Handles connection lifecycle and message handling
 */

import { useEffect, useState, useRef } from 'react';
import { WS_BASE_URL } from '../config/env';

interface UseWebSocketReturn {
  lastMessage: MessageEvent | null;
  sendMessage: (data: unknown) => void;
  isConnected: boolean;
}

export const useWebSocket = (path: string): UseWebSocketReturn => {
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const connect = () => {
      try {
        const wsUrl = `${WS_BASE_URL}${path}`;
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
          console.log(`WebSocket connected: ${path}`);
          setIsConnected(true);
        };

        ws.current.onmessage = (event) => {
          setLastMessage(event);
        };

        ws.current.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.current.onclose = () => {
          console.log(`WebSocket disconnected: ${path}`);
          setIsConnected(false);
          
          // Attempt to reconnect after 5 seconds
          reconnectTimeout.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 5000);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
      }
    };

    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [path]);

  const sendMessage = (data: unknown) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return {
    lastMessage,
    sendMessage,
    isConnected,
  };
};
