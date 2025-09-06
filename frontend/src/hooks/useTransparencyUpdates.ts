/**
 * Hook for real-time transparency updates
 * Manages WebSocket connections and transparency data updates
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { TransparencyUpdate, TransparencyMetrics } from '../types/transparency';

interface UseTransparencyUpdatesOptions {
  companyId: string;
  enabled?: boolean;
  onUpdate?: (update: TransparencyUpdate) => void;
  reconnectInterval?: number;
}

interface TransparencyUpdatesState {
  isConnected: boolean;
  lastUpdate: TransparencyUpdate | null;
  connectionError: string | null;
  updateCount: number;
}

export function useTransparencyUpdates({
  companyId,
  enabled = true,
  onUpdate,
  reconnectInterval = 5000,
}: UseTransparencyUpdatesOptions) {
  const [state, setState] = useState<TransparencyUpdatesState>({
    isConnected: false,
    lastUpdate: null,
    connectionError: null,
    updateCount: 0,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // WebSocket URL for real-time transparency updates
  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.REACT_APP_WS_HOST || window.location.host;
    return `${protocol}//${host}/ws/transparency/${companyId}`;
  }, [companyId]);

  // Handle incoming messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const update: TransparencyUpdate = JSON.parse(event.data);
      
      setState(prev => ({
        ...prev,
        lastUpdate: update,
        updateCount: prev.updateCount + 1,
      }));

      if (onUpdate) {
        onUpdate(update);
      }
    } catch (error) {
      console.error('Failed to parse transparency update:', error);
    }
  }, [onUpdate]);

  // Handle connection open
  const handleOpen = useCallback(() => {
    setState(prev => ({
      ...prev,
      isConnected: true,
      connectionError: null,
    }));
    reconnectAttemptsRef.current = 0;
  }, []);

  // Handle connection close
  const handleClose = useCallback(() => {
    setState(prev => ({
      ...prev,
      isConnected: false,
    }));

    // Attempt to reconnect if enabled
    if (enabled && reconnectAttemptsRef.current < 5) {
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current += 1;
        connect();
      }, reconnectInterval * Math.pow(2, reconnectAttemptsRef.current));
    }
  }, [enabled, reconnectInterval]);

  // Handle connection error
  const handleError = useCallback((error: Event) => {
    setState(prev => ({
      ...prev,
      connectionError: 'WebSocket connection failed',
      isConnected: false,
    }));
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!enabled || !companyId) return;

    try {
      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close();
      }



      // Real WebSocket connection
      const ws = new WebSocket(getWebSocketUrl());
      
      ws.addEventListener('open', handleOpen);
      ws.addEventListener('message', handleMessage);
      ws.addEventListener('close', handleClose);
      ws.addEventListener('error', handleError);

      wsRef.current = ws;
    } catch (error) {
      setState(prev => ({
        ...prev,
        connectionError: 'Failed to create WebSocket connection',
        isConnected: false,
      }));
    }
  }, [enabled, companyId, getWebSocketUrl, handleOpen, handleMessage, handleClose, handleError, onUpdate]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
    }));
  }, []);

  // Send message to WebSocket
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && state.isConnected) {
      try {
        wsRef.current.send(JSON.stringify(message));
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
      }
    }
  }, [state.isConnected]);

  // Connect on mount and when dependencies change
  useEffect(() => {
    if (enabled && companyId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, companyId, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
  };
}

// Hook for transparency metrics with real-time updates
export function useTransparencyMetricsWithUpdates(
  companyId: string,
  initialMetrics?: TransparencyMetrics
) {
  const [metrics, setMetrics] = useState<TransparencyMetrics | null>(initialMetrics || null);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleUpdate = useCallback((update: TransparencyUpdate) => {
    if (update.type === 'score_change' && update.data) {
      setIsUpdating(true);
      
      // Update metrics with new data
      setMetrics(prev => {
        if (!prev) return null;
        
        return {
          ...prev,
          overall_score: update.data.new_score || prev.overall_score,
          last_updated: update.timestamp,
        };
      });

      // Reset updating state after animation
      setTimeout(() => setIsUpdating(false), 1000);
    }
  }, []);

  const updatesState = useTransparencyUpdates({
    companyId,
    onUpdate: handleUpdate,
  });

  return {
    metrics,
    setMetrics,
    isUpdating,
    ...updatesState,
  };
}

export default useTransparencyUpdates;
