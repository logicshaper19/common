/**
 * Real-Time Updates Component - WebSocket integration for live dashboard updates
 * Provides real-time notifications and data updates across all dashboards
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { 
  WifiIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface RealTimeUpdate {
  id: string;
  type: 'po_update' | 'supplier_update' | 'transparency_update' | 'system_update';
  title: string;
  message: string;
  timestamp: string;
  data?: any;
  priority: 'low' | 'medium' | 'high' | 'urgent';
}

interface RealTimeUpdatesProps {
  onUpdate?: (update: RealTimeUpdate) => void;
  onConnectionChange?: (connected: boolean) => void;
  className?: string;
}

export const RealTimeUpdates: React.FC<RealTimeUpdatesProps> = ({
  onUpdate,
  onConnectionChange,
  className = ''
}) => {
  const [connected, setConnected] = useState(false);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<RealTimeUpdate | null>(null);
  const [updateCount, setUpdateCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      // Get authentication token
      const token = localStorage.getItem('auth_token');
      
      // Build WebSocket URL with token as query parameter
      const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
      const wsProtocol = apiBaseUrl.startsWith('https') ? 'wss' : 'ws';
      const wsHost = apiBaseUrl.replace(/^https?:\/\//, '');

      // Always use the development URL for now to avoid issues
      const baseUrl = `${wsProtocol}://${wsHost}/ws/dashboard`;
      const wsUrl = token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl;

      console.log('WebSocket connecting to:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setConnectionAttempts(0);
        onConnectionChange?.(true);
      };

      ws.onmessage = (event) => {
        try {
          const update: RealTimeUpdate = JSON.parse(event.data);
          setLastUpdate(update);
          setUpdateCount(prev => prev + 1);
          onUpdate?.(update);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnected(false);
        onConnectionChange?.(false);
        wsRef.current = null;

        // Attempt to reconnect unless it was a clean close
        if (event.code !== 1000 && connectionAttempts < 5) {
          const delay = Math.min(1000 * Math.pow(2, connectionAttempts), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            setConnectionAttempts(prev => prev + 1);
            connect();
          }, delay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnected(false);
      onConnectionChange?.(false);
    }
  }, [connectionAttempts, onUpdate, onConnectionChange]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }
    
    setConnected(false);
    onConnectionChange?.(false);
  }, [onConnectionChange]);

  const forceReconnect = useCallback(() => {
    disconnect();
    setConnectionAttempts(0);
    setTimeout(connect, 1000);
  }, [connect, disconnect]);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const getConnectionIcon = () => {
    if (connected) {
      return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
    } else if (connectionAttempts > 0) {
      return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />;
    } else {
      return <XMarkIcon className="h-4 w-4 text-red-500" />;
    }
  };

  const getConnectionStatus = () => {
    if (connected) {
      return 'Connected';
    } else if (connectionAttempts > 0) {
      return `Reconnecting... (${connectionAttempts}/5)`;
    } else {
      return 'Disconnected';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* Connection Status */}
      <div className="flex items-center space-x-2">
        <WifiIcon className="h-4 w-4 text-gray-400" />
        {getConnectionIcon()}
        <span className="text-sm text-gray-600">{getConnectionStatus()}</span>
      </div>

      {/* Update Counter */}
      {updateCount > 0 && (
        <Badge color="blue" size="sm">
          {updateCount} updates
        </Badge>
      )}

      {/* Last Update */}
      {lastUpdate && (
        <div className="text-xs text-gray-500">
          Last: {formatTimeAgo(lastUpdate.timestamp)}
        </div>
      )}

      {/* Reconnect Button */}
      {!connected && connectionAttempts === 0 && (
        <Button size="xs" variant="outline" onClick={forceReconnect}>
          Reconnect
        </Button>
      )}
    </div>
  );
};

/**
 * Real-Time Update Toast - Shows live updates as they come in
 */
interface RealTimeToastProps {
  update: RealTimeUpdate;
  onDismiss: () => void;
  autoHide?: boolean;
  hideDelay?: number;
}

export const RealTimeToast: React.FC<RealTimeToastProps> = ({
  update,
  onDismiss,
  autoHide = true,
  hideDelay = 5000
}) => {
  useEffect(() => {
    if (autoHide) {
      const timer = setTimeout(onDismiss, hideDelay);
      return () => clearTimeout(timer);
    }
  }, [autoHide, hideDelay, onDismiss]);

  const getToastColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'high':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'medium':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  return (
    <div className={`fixed top-4 right-4 max-w-sm p-4 rounded-lg border shadow-lg z-50 ${getToastColor(update.priority)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium">{update.title}</h4>
          <p className="text-sm mt-1">{update.message}</p>
          <p className="text-xs mt-2 opacity-75">
            {formatTimeAgo(update.timestamp)}
          </p>
        </div>
        <Button
          size="xs"
          variant="ghost"
          onClick={onDismiss}
          className="ml-2"
        >
          <XMarkIcon className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};

/**
 * Real-Time Updates Provider - Context provider for real-time updates
 */
interface RealTimeContextType {
  connected: boolean;
  updateCount: number;
  lastUpdate: RealTimeUpdate | null;
  subscribe: (callback: (update: RealTimeUpdate) => void) => () => void;
}

const RealTimeContext = React.createContext<RealTimeContextType | null>(null);

interface RealTimeProviderProps {
  children: React.ReactNode;
}

export const RealTimeProvider: React.FC<RealTimeProviderProps> = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [updateCount, setUpdateCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<RealTimeUpdate | null>(null);
  const subscribersRef = useRef<Set<(update: RealTimeUpdate) => void>>(new Set());

  const handleUpdate = useCallback((update: RealTimeUpdate) => {
    setLastUpdate(update);
    setUpdateCount(prev => prev + 1);
    
    // Notify all subscribers
    subscribersRef.current.forEach(callback => {
      try {
        callback(update);
      } catch (error) {
        console.error('Error in real-time update subscriber:', error);
      }
    });
  }, []);

  const subscribe = useCallback((callback: (update: RealTimeUpdate) => void) => {
    subscribersRef.current.add(callback);
    
    return () => {
      subscribersRef.current.delete(callback);
    };
  }, []);

  const contextValue: RealTimeContextType = {
    connected,
    updateCount,
    lastUpdate,
    subscribe
  };

  return (
    <RealTimeContext.Provider value={contextValue}>
      <RealTimeUpdates
        onUpdate={handleUpdate}
        onConnectionChange={setConnected}
      />
      {children}
    </RealTimeContext.Provider>
  );
};

export const useRealTimeUpdates = () => {
  const context = React.useContext(RealTimeContext);
  if (!context) {
    throw new Error('useRealTimeUpdates must be used within a RealTimeProvider');
  }
  return context;
};

const formatTimeAgo = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  return `${Math.floor(diffInSeconds / 86400)}d ago`;
};

export default RealTimeUpdates;
