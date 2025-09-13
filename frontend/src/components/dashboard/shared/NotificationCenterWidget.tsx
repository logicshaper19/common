/**
 * Notification Center Widget - Shared component for all dashboards
 * Shows recent notifications and alerts
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import LoadingSpinner from '../../ui/LoadingSpinner';
import { 
  BellIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  read: boolean;
  created_at: string;
  action_url?: string;
  action_text?: string;
}

interface NotificationCenterWidgetProps {
  className?: string;
  maxNotifications?: number;
}

export const NotificationCenterWidget: React.FC<NotificationCenterWidgetProps> = ({
  className = '',
  maxNotifications = 5
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to fetch from API, fallback to mock data
      try {
        const response = await fetch('/api/v1/notifications', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          const recentNotifications = data.slice(0, maxNotifications);
          setNotifications(recentNotifications);
          setUnreadCount(data.filter((n: Notification) => !n.read).length);
          return;
        }
      } catch (apiError) {
        console.log('API not available, using mock data');
      }

      // Fallback to mock data for development
      const mockNotifications: Notification[] = [
        {
          id: '1',
          title: 'Urgent: PO Confirmation Required',
          message: 'Purchase order PO-2024-001 expires in 2 hours',
          type: 'warning',
          priority: 'urgent',
          read: false,
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          action_url: '/purchase-orders/po-2024-001',
          action_text: 'Review Order'
        },
        {
          id: '2',
          title: 'Delivery Delay Alert',
          message: 'Shipment from Green Valley Farms is delayed by 3 days',
          type: 'warning',
          priority: 'high',
          read: false,
          created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '3',
          title: 'Supplier Onboarded',
          message: 'Mountain Coffee Co. has completed onboarding',
          type: 'success',
          priority: 'medium',
          read: false,
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '4',
          title: 'Transparency Score Updated',
          message: 'Your transparency score increased to 87%',
          type: 'info',
          priority: 'low',
          read: true,
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        }
      ];

      setNotifications(mockNotifications.slice(0, maxNotifications));
      setUnreadCount(mockNotifications.filter(n => !n.read).length);
    } catch (err) {
      console.error('Error loading notifications:', err);
      setError(err instanceof Error ? err.message : 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      const response = await fetch(`/api/v1/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });

      if (response.ok) {
        setNotifications(prev => 
          prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XMarkIcon className="h-5 w-5 text-red-500" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  const getPriorityBadgeColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'gray';
      default: return 'gray';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center">
            <BellIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Notifications</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="md" />
          </div>
        </CardBody>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardHeader>
          <div className="flex items-center">
            <BellIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Notifications</h3>
          </div>
        </CardHeader>
        <CardBody>
          <div className="text-center py-8">
            <p className="text-red-600 mb-2">Failed to load notifications</p>
            <Button onClick={loadNotifications} variant="outline" size="sm">
              Retry
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <BellIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium">Notifications</h3>
            {unreadCount > 0 && (
              <Badge color="red" size="sm" className="ml-2">
                {unreadCount}
              </Badge>
            )}
          </div>
          <Link to="/notifications">
            <Button size="sm" variant="outline">
              View All
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardBody>
        {notifications.length === 0 ? (
          <div className="text-center py-8">
            <BellIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Notifications</h4>
            <p className="text-gray-600">
              You're all caught up! New notifications will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifications.map((notification) => (
              <div 
                key={notification.id} 
                className={`p-3 rounded-lg border transition-colors ${
                  notification.read 
                    ? 'bg-gray-50 border-gray-200' 
                    : 'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-0.5">
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className={`text-sm font-medium ${
                        notification.read ? 'text-gray-700' : 'text-gray-900'
                      }`}>
                        {notification.title}
                      </h4>
                      <div className="flex items-center space-x-2">
                        {notification.priority !== 'low' && (
                          <Badge 
                            color={getPriorityBadgeColor(notification.priority)} 
                            size="xs"
                          >
                            {notification.priority}
                          </Badge>
                        )}
                        <span className="text-xs text-gray-500">
                          {formatTimeAgo(notification.created_at)}
                        </span>
                      </div>
                    </div>
                    <p className={`text-sm ${
                      notification.read ? 'text-gray-600' : 'text-gray-700'
                    }`}>
                      {notification.message}
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      {notification.action_url && notification.action_text && (
                        <Link 
                          to={notification.action_url}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          {notification.action_text} →
                        </Link>
                      )}
                      {!notification.read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="text-xs text-gray-500 hover:text-gray-700"
                        >
                          Mark as read
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default NotificationCenterWidget;
