/**
 * Notification Center Component
 * In-app notification center with real-time updates
 */
import React, { useState, useEffect, useRef } from 'react';
import { 
  BellIcon,
  XMarkIcon,
  CheckIcon,
  ArchiveBoxIcon,
  TrashIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  EllipsisVerticalIcon,
} from '@heroicons/react/24/outline';
import { BellIcon as BellSolidIcon } from '@heroicons/react/24/solid';
import { useNotifications } from '../../contexts/NotificationContext';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Badge from '../ui/Badge';
import { Menu } from '@headlessui/react';
import { 
  Notification, 
  NotificationFilters, 
  NotificationType, 
  NotificationPriority, 
  NotificationStatus 
} from '../../types/notifications';
import { cn, formatDate, formatTimeAgo } from '../../lib/utils';

interface NotificationCenterProps {
  isOpen: boolean;
  onClose: () => void;
  className?: string;
}

const NotificationCenter: React.FC<NotificationCenterProps> = ({
  isOpen,
  onClose,
  className,
}) => {
  const {
    notifications,
    summary,
    isLoading,
    isConnected,
    loadNotifications,
    markAsRead,
    markAsUnread,
    archiveNotification,
    deleteNotification,
    markAllAsRead,
  } = useNotifications();

  const [filters, setFilters] = useState<NotificationFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNotifications, setSelectedNotifications] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  const panelRef = useRef<HTMLDivElement>(null);

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  // Load notifications when filters change
  useEffect(() => {
    if (isOpen) {
      const searchFilters = {
        ...filters,
        search_query: searchQuery || undefined,
      };
      loadNotifications(searchFilters);
    }
  }, [isOpen, filters, searchQuery, loadNotifications]);

  // Handle filter changes
  const handleFilterChange = (key: keyof NotificationFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // Handle notification selection
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

  // Handle bulk actions
  const handleBulkAction = async (action: 'read' | 'unread' | 'archive' | 'delete') => {
    const notificationIds = Array.from(selectedNotifications);
    
    for (const id of notificationIds) {
      switch (action) {
        case 'read':
          await markAsRead(id);
          break;
        case 'unread':
          await markAsUnread(id);
          break;
        case 'archive':
          await archiveNotification(id);
          break;
        case 'delete':
          await deleteNotification(id);
          break;
      }
    }
    
    setSelectedNotifications(new Set());
  };

  // Get notification icon
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-25" onClick={onClose} />
      
      {/* Panel */}
      <div className="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-xl">
        <div ref={panelRef} className="flex h-full flex-col">
          {/* Header */}
          <div className="border-b border-neutral-200 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BellSolidIcon className="h-6 w-6 text-primary-600" />
                <h2 className="text-lg font-semibold text-neutral-900">Notifications</h2>
                {summary && (
                  <Badge variant="primary" size="sm">
                    {summary.unread_count}
                  </Badge>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                {/* Connection status */}
                <div className={cn(
                  'h-2 w-2 rounded-full',
                  isConnected ? 'bg-success-500' : 'bg-error-500'
                )} />
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  leftIcon={<XMarkIcon className="h-4 w-4" />}
                  aria-label="Close notifications"
                />
              </div>
            </div>

            {/* Quick actions */}
            <div className="mt-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowFilters(!showFilters)}
                  leftIcon={<FunnelIcon className="h-4 w-4" />}
                >
                  Filters
                </Button>
                
                {summary && summary.unread_count > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={markAllAsRead}
                  >
                    Mark All Read
                  </Button>
                )}
              </div>

              {selectedNotifications.size > 0 && (
                <Menu as="div" className="relative">
                  <Menu.Button as={Button} variant="outline" size="sm" leftIcon={<EllipsisVerticalIcon className="h-4 w-4" />}>
                    Actions ({selectedNotifications.size})
                  </Menu.Button>
                  
                  <Menu.Items className="absolute right-0 mt-2 w-48 bg-white border border-neutral-200 rounded-lg shadow-lg z-10">
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={() => handleBulkAction('read')}
                          className={cn(
                            'flex items-center w-full px-3 py-2 text-sm',
                            active ? 'bg-neutral-100' : ''
                          )}
                        >
                          <CheckIcon className="h-4 w-4 mr-2" />
                          Mark as Read
                        </button>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={() => handleBulkAction('archive')}
                          className={cn(
                            'flex items-center w-full px-3 py-2 text-sm',
                            active ? 'bg-neutral-100' : ''
                          )}
                        >
                          <ArchiveBoxIcon className="h-4 w-4 mr-2" />
                          Archive
                        </button>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={() => handleBulkAction('delete')}
                          className={cn(
                            'flex items-center w-full px-3 py-2 text-sm text-error-600',
                            active ? 'bg-neutral-100' : ''
                          )}
                        >
                          <TrashIcon className="h-4 w-4 mr-2" />
                          Delete
                        </button>
                      )}
                    </Menu.Item>
                  </Menu.Items>
                </Menu>
              )}
            </div>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="border-b border-neutral-200 p-4 space-y-3">
              <Input
                placeholder="Search notifications..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
                size="sm"
              />
              
              <div className="grid grid-cols-2 gap-2">
                <Select
                  value={filters.status?.[0] || 'all'}
                  onChange={(e) => handleFilterChange('status', e.target.value === 'all' ? undefined : [e.target.value])}
                  size="sm"
                  options={[
                    { label: 'All Status', value: 'all' },
                    { label: 'Unread', value: 'unread' },
                    { label: 'Read', value: 'read' },
                    { label: 'Archived', value: 'archived' }
                  ]}
                />
                
                <Select
                  value={filters.priorities?.[0] || 'all'}
                  onChange={(e) => handleFilterChange('priorities', e.target.value === 'all' ? undefined : [e.target.value])}
                  size="sm"
                  options={[
                    { label: 'All Priority', value: 'all' },
                    { label: 'Urgent', value: 'urgent' },
                    { label: 'High', value: 'high' },
                    { label: 'Normal', value: 'normal' },
                    { label: 'Low', value: 'low' }
                  ]}
                />
              </div>
            </div>
          )}

          {/* Notification list */}
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : (notifications || []).length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-neutral-500">
                <BellIcon className="h-12 w-12 mb-2" />
                <p className="text-sm">No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-neutral-200">
                {(notifications || []).map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    isSelected={selectedNotifications.has(notification.id)}
                    onSelect={() => toggleNotificationSelection(notification.id)}
                    onMarkAsRead={() => markAsRead(notification.id)}
                    onMarkAsUnread={() => markAsUnread(notification.id)}
                    onArchive={() => archiveNotification(notification.id)}
                    onDelete={() => deleteNotification(notification.id)}
                    getIcon={getNotificationIcon}
                    getPriorityColor={getPriorityColor}
                    getStatusBadgeVariant={getStatusBadgeVariant}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Individual notification item component
interface NotificationItemProps {
  notification: Notification;
  isSelected: boolean;
  onSelect: () => void;
  onMarkAsRead: () => void;
  onMarkAsUnread: () => void;
  onArchive: () => void;
  onDelete: () => void;
  getIcon: (type: NotificationType) => string;
  getPriorityColor: (priority: NotificationPriority) => string;
  getStatusBadgeVariant: (status: NotificationStatus) => any;
}

const NotificationItem: React.FC<NotificationItemProps> = ({
  notification,
  isSelected,
  onSelect,
  onMarkAsRead,
  onMarkAsUnread,
  onArchive,
  onDelete,
  getIcon,
  getPriorityColor,
  getStatusBadgeVariant,
}) => {
  const isUnread = notification.status === 'unread';

  return (
    <div className={cn(
      'p-4 hover:bg-neutral-50 transition-colors',
      isUnread && 'bg-primary-50 border-l-4 border-primary-500',
      isSelected && 'bg-primary-100'
    )}>
      <div className="flex items-start space-x-3">
        {/* Selection checkbox */}
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onSelect}
          className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-neutral-300 rounded"
        />

        {/* Notification icon */}
        <div className="text-xl">{getIcon(notification.notification_type)}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className={cn(
                'text-sm font-medium truncate',
                isUnread ? 'text-neutral-900' : 'text-neutral-700'
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
                {formatTimeAgo(notification.created_at)}
              </span>
            </div>

            {/* Actions */}
            <Menu as="div" className="relative">
              <Menu.Button className="p-1 rounded hover:bg-neutral-200">
                <EllipsisVerticalIcon className="h-4 w-4 text-neutral-500" />
              </Menu.Button>
              
              <Menu.Items className="absolute right-0 mt-1 w-32 bg-white border border-neutral-200 rounded-lg shadow-lg z-10">
                {isUnread ? (
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onMarkAsRead}
                        className={cn(
                          'flex items-center w-full px-3 py-2 text-sm',
                          active ? 'bg-neutral-100' : ''
                        )}
                      >
                        <CheckIcon className="h-4 w-4 mr-2" />
                        Mark Read
                      </button>
                    )}
                  </Menu.Item>
                ) : (
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={onMarkAsUnread}
                        className={cn(
                          'flex items-center w-full px-3 py-2 text-sm',
                          active ? 'bg-neutral-100' : ''
                        )}
                      >
                        <BellIcon className="h-4 w-4 mr-2" />
                        Mark Unread
                      </button>
                    )}
                  </Menu.Item>
                )}
                
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={onArchive}
                      className={cn(
                        'flex items-center w-full px-3 py-2 text-sm',
                        active ? 'bg-neutral-100' : ''
                      )}
                    >
                      <ArchiveBoxIcon className="h-4 w-4 mr-2" />
                      Archive
                    </button>
                  )}
                  </Menu.Item>
                
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={onDelete}
                      className={cn(
                        'flex items-center w-full px-3 py-2 text-sm text-error-600',
                        active ? 'bg-neutral-100' : ''
                      )}
                    >
                      <TrashIcon className="h-4 w-4 mr-2" />
                      Delete
                    </button>
                  )}
                </Menu.Item>
              </Menu.Items>
            </Menu>
          </div>

          {/* Action button */}
          {notification.action_url && notification.action_text && (
            <div className="mt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.href = notification.action_url!}
              >
                {notification.action_text}
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;
