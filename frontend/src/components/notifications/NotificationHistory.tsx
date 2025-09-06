/**
 * Notification History Component
 * View and manage notification history with filtering and search
 */
import React, { useState, useEffect } from 'react';
import { 
  ClockIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ArchiveBoxIcon,
  TrashIcon,
  EyeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { notificationApi } from '../../lib/notificationApi';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Badge from '../ui/Badge';
import { 
  Notification,
  NotificationFilters,
  NotificationListResponse,
  NotificationType,
  NotificationPriority,
  NotificationStatus,
} from '../../types/notifications';
import { cn, formatDate, formatTimeAgo } from '../../lib/utils';

interface NotificationHistoryProps {
  className?: string;
}

const NotificationHistory: React.FC<NotificationHistoryProps> = ({
  className,
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<NotificationFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [selectedNotifications, setSelectedNotifications] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  const pageSize = 20;

  // Load notifications
  useEffect(() => {
    loadNotifications(1);
  }, [filters, searchQuery]);

  const loadNotifications = async (page: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const searchFilters = {
        ...filters,
        search_query: searchQuery || undefined,
      };

      const response = await notificationApi.getNotifications(searchFilters, page, pageSize);
      
      if (page === 1) {
        setNotifications(response.notifications);
      } else {
        setNotifications(prev => [...prev, ...response.notifications]);
      }
      
      setCurrentPage(page);
      setTotalCount(response.total_count);
      setHasNext(response.has_next);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      setError('Failed to load notification history');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof NotificationFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  // Load more notifications
  const loadMore = () => {
    if (hasNext && !isLoading) {
      loadNotifications(currentPage + 1);
    }
  };

  // Toggle notification selection
  const toggleNotificationSelection = (notificationId: string) => {
    setSelectedNotifications(prev => {
      const newSet = new Set(prev);
      if (newSet.has(notificationId)) {
        newSet.delete(notificationId);
      } else {
        newSet.add(notificationId);
      }
      return newSet;
    });
  };

  // Select all visible notifications
  const selectAllVisible = () => {
    const visibleIds = notifications.map(n => n.id);
    setSelectedNotifications(new Set(visibleIds));
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedNotifications(new Set());
  };

  // Bulk actions
  const handleBulkAction = async (action: 'archive' | 'delete') => {
    const notificationIds = Array.from(selectedNotifications);
    
    try {
      for (const id of notificationIds) {
        if (action === 'archive') {
          await notificationApi.archiveNotification(id);
        } else {
          await notificationApi.deleteNotification(id);
        }
      }
      
      // Remove from local state
      setNotifications(prev => prev.filter(n => !notificationIds.includes(n.id)));
      setSelectedNotifications(new Set());
    } catch (error) {
      console.error(`Failed to ${action} notifications:`, error);
      setError(`Failed to ${action} selected notifications`);
    }
  };

  // Get notification type icon
  const getNotificationIcon = (type: NotificationType) => {
    switch (type) {
      case 'po_created':
      case 'po_confirmed':
      case 'po_shipped':
      case 'po_delivered':
        return '📦';
      case 'transparency_updated':
        return '📊';
      case 'supplier_invited':
      case 'supplier_joined':
        return '🤝';
      case 'system_alert':
        return '⚠️';
      case 'user_mention':
        return '💬';
      case 'deadline_reminder':
        return '⏰';
      case 'quality_issue':
        return '🔍';
      case 'compliance_alert':
        return '🛡️';
      default:
        return '📢';
    }
  };

  // Get priority color
  const getPriorityColor = (priority: NotificationPriority) => {
    switch (priority) {
      case 'urgent': return 'text-error-600';
      case 'high': return 'text-warning-600';
      case 'normal': return 'text-primary-600';
      case 'low': return 'text-neutral-600';
      default: return 'text-neutral-600';
    }
  };

  // Get status badge variant
  const getStatusBadgeVariant = (status: NotificationStatus) => {
    switch (status) {
      case 'unread': return 'primary';
      case 'read': return 'neutral';
      case 'archived': return 'secondary';
      default: return 'neutral';
    }
  };

  return (
    <Card className={className}>
      <CardHeader 
        title="Notification History"
        subtitle={`${totalCount} total notifications`}
        action={
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              leftIcon={<FunnelIcon className="h-4 w-4" />}
            >
              Filters
            </Button>
            
            {selectedNotifications.size > 0 && (
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkAction('archive')}
                  leftIcon={<ArchiveBoxIcon className="h-4 w-4" />}
                >
                  Archive ({selectedNotifications.size})
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleBulkAction('delete')}
                  leftIcon={<TrashIcon className="h-4 w-4" />}
                  className="text-error-600 hover:text-error-700"
                >
                  Delete ({selectedNotifications.size})
                </Button>
              </div>
            )}
          </div>
        }
      />
      
      <CardBody>
        {/* Search and Filters */}
        <div className="mb-6 space-y-4">
          <Input
            placeholder="Search notifications..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            icon={MagnifyingGlassIcon}
          />
          
          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-neutral-50 rounded-lg">
              <Select
                value={filters.status?.[0] || 'all'}
                onChange={(e) => handleFilterChange('status', e.target.value === 'all' ? undefined : [e.target.value])}
              >
                <option value="all">All Status</option>
                <option value="unread">Unread</option>
                <option value="read">Read</option>
                <option value="archived">Archived</option>
              </Select>
              
              <Select
                value={filters.priorities?.[0] || 'all'}
                onChange={(e) => handleFilterChange('priorities', e.target.value === 'all' ? undefined : [e.target.value])}
              >
                <option value="all">All Priority</option>
                <option value="urgent">Urgent</option>
                <option value="high">High</option>
                <option value="normal">Normal</option>
                <option value="low">Low</option>
              </Select>
              
              <Select
                value={filters.types?.[0] || 'all'}
                onChange={(e) => handleFilterChange('types', e.target.value === 'all' ? undefined : [e.target.value])}
              >
                <option value="all">All Types</option>
                <option value="po_created">Purchase Orders</option>
                <option value="transparency_updated">Transparency</option>
                <option value="supplier_invited">Suppliers</option>
                <option value="system_alert">System Alerts</option>
              </Select>
              
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={selectAllVisible}
                  disabled={notifications.length === 0}
                >
                  Select All
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearSelection}
                  disabled={selectedNotifications.size === 0}
                >
                  Clear
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-error-50 border border-error-200 rounded-lg text-error-800 flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 mr-2" />
            {error}
          </div>
        )}

        {/* Notification List */}
        {isLoading && notifications.length === 0 ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-neutral-600">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-8">
            <ClockIcon className="h-12 w-12 text-neutral-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-neutral-900 mb-2">No notifications found</h3>
            <p className="text-neutral-600">
              {searchQuery || Object.keys(filters).length > 0
                ? 'Try adjusting your search or filter criteria.'
                : 'You have no notification history yet.'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={cn(
                  'flex items-start space-x-3 p-4 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors',
                  notification.status === 'unread' && 'bg-primary-50 border-primary-200',
                  selectedNotifications.has(notification.id) && 'bg-primary-100 border-primary-300'
                )}
              >
                {/* Selection checkbox */}
                <input
                  type="checkbox"
                  checked={selectedNotifications.has(notification.id)}
                  onChange={() => toggleNotificationSelection(notification.id)}
                  className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
                />

                {/* Notification icon */}
                <div className="text-xl">{getNotificationIcon(notification.notification_type)}</div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className={cn(
                        'text-sm font-medium truncate',
                        notification.status === 'unread' ? 'text-neutral-900' : 'text-neutral-700'
                      )}>
                        {notification.title}
                      </h4>
                      <p className="text-sm text-neutral-600 mt-1 line-clamp-2">
                        {notification.message}
                      </p>
                    </div>

                    {/* Priority indicator */}
                    <div className={cn('w-2 h-2 rounded-full ml-2 mt-1', getPriorityColor(notification.priority))} />
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center space-x-2">
                      <Badge variant={getStatusBadgeVariant(notification.status)} size="sm">
                        {notification.status}
                      </Badge>
                      <span className="text-xs text-neutral-500">
                        {formatDate(notification.created_at)}
                      </span>
                      {notification.read_at && (
                        <span className="text-xs text-neutral-500">
                          • Read {formatTimeAgo(notification.read_at)}
                        </span>
                      )}
                    </div>

                    {/* Delivery status */}
                    <div className="flex items-center space-x-1">
                      {notification.delivery_status.in_app === 'delivered' && (
                        <CheckCircleIcon className="h-4 w-4 text-success-600" title="Delivered in-app" />
                      )}
                      {notification.delivery_status.email === 'delivered' && (
                        <CheckCircleIcon className="h-4 w-4 text-primary-600" title="Delivered via email" />
                      )}
                    </div>
                  </div>

                  {/* Action button */}
                  {notification.action_url && notification.action_text && (
                    <div className="mt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.location.href = notification.action_url!}
                        leftIcon={<EyeIcon className="h-4 w-4" />}
                      >
                        {notification.action_text}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Load More */}
            {hasNext && (
              <div className="text-center pt-4">
                <Button
                  variant="outline"
                  onClick={loadMore}
                  disabled={isLoading}
                >
                  {isLoading ? 'Loading...' : 'Load More'}
                </Button>
              </div>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
};

export default NotificationHistory;
