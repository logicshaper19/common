/**
 * Enhanced Dashboard Layout - Unified layout for all V2 dashboards
 * Provides consistent structure, real-time updates, and responsive design
 */
import React, { useState, useEffect } from 'react';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import RealTimeUpdates, { RealTimeToast, useRealTimeUpdates } from './RealTimeUpdates';
import { 
  Bars3Icon,
  BellIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface DashboardLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  headerActions?: React.ReactNode;
  showRealTimeStatus?: boolean;
  refreshable?: boolean;
  onRefresh?: () => void;
  className?: string;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  title,
  subtitle,
  children,
  headerActions,
  showRealTimeStatus = true,
  refreshable = true,
  onRefresh,
  className = ''
}) => {
  const [showToast, setShowToast] = useState(false);
  const [toastUpdate, setToastUpdate] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Real-time updates integration
  const { connected, updateCount, lastUpdate, subscribe } = useRealTimeUpdates();

  useEffect(() => {
    const unsubscribe = subscribe((update) => {
      setToastUpdate(update);
      setShowToast(true);
    });

    return unsubscribe;
  }, [subscribe]);

  const handleRefresh = async () => {
    if (onRefresh && !refreshing) {
      setRefreshing(true);
      try {
        await onRefresh();
      } finally {
        setRefreshing(false);
      }
    }
  };

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      {/* Enhanced Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-40">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Left side - Title and navigation */}
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" className="lg:hidden">
                <Bars3Icon className="h-5 w-5" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
                {subtitle && (
                  <p className="text-sm text-gray-600">{subtitle}</p>
                )}
              </div>
            </div>

            {/* Right side - Actions and status */}
            <div className="flex items-center space-x-4">
              {/* Real-time status */}
              {showRealTimeStatus && (
                <RealTimeUpdates className="hidden sm:flex" />
              )}

              {/* Refresh button */}
              {refreshable && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="hidden sm:flex"
                >
                  <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                </Button>
              )}

              {/* Update counter */}
              {updateCount > 0 && (
                <Badge color="blue" size="sm" className="hidden sm:inline-flex">
                  {updateCount} updates
                </Badge>
              )}

              {/* Header actions */}
              {headerActions}

              {/* User menu */}
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm">
                  <BellIcon className="h-5 w-5" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Cog6ToothIcon className="h-5 w-5" />
                </Button>
                <Button variant="ghost" size="sm">
                  <UserCircleIcon className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile real-time status */}
        {showRealTimeStatus && (
          <div className="px-4 pb-2 sm:hidden">
            <RealTimeUpdates />
          </div>
        )}
      </div>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Real-time update toast */}
      {showToast && toastUpdate && (
        <RealTimeToast
          update={toastUpdate}
          onDismiss={() => setShowToast(false)}
        />
      )}
    </div>
  );
};

/**
 * Dashboard Section - Reusable section component for dashboard content
 */
interface DashboardSectionProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const DashboardSection: React.FC<DashboardSectionProps> = ({
  title,
  subtitle,
  children,
  actions,
  className = '',
  padding = 'md'
}) => {
  const getPaddingClass = (padding: string) => {
    switch (padding) {
      case 'none':
        return '';
      case 'sm':
        return 'p-4';
      case 'lg':
        return 'p-8';
      default:
        return 'p-6';
    }
  };

  return (
    <div className={`${getPaddingClass(padding)} ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between mb-6">
          <div>
            {title && (
              <h2 className="text-lg font-medium text-gray-900">{title}</h2>
            )}
            {subtitle && (
              <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
            )}
          </div>
          {actions && (
            <div className="flex items-center space-x-3">
              {actions}
            </div>
          )}
        </div>
      )}
      {children}
    </div>
  );
};

/**
 * Dashboard Grid - Responsive grid layout for dashboard content
 */
interface DashboardGridProps {
  children: React.ReactNode;
  columns?: 1 | 2 | 3 | 4;
  gap?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const DashboardGrid: React.FC<DashboardGridProps> = ({
  children,
  columns = 3,
  gap = 'md',
  className = ''
}) => {
  const getGridClasses = (cols: number) => {
    switch (cols) {
      case 1:
        return 'grid-cols-1';
      case 2:
        return 'grid-cols-1 lg:grid-cols-2';
      case 3:
        return 'grid-cols-1 lg:grid-cols-3';
      case 4:
        return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4';
      default:
        return 'grid-cols-1 lg:grid-cols-3';
    }
  };

  const getGapClass = (gap: string) => {
    switch (gap) {
      case 'sm':
        return 'gap-4';
      case 'lg':
        return 'gap-8';
      default:
        return 'gap-6';
    }
  };

  return (
    <div className={`grid ${getGridClasses(columns)} ${getGapClass(gap)} ${className}`}>
      {children}
    </div>
  );
};

/**
 * Dashboard Sidebar Layout - Two-column layout with sidebar
 */
interface DashboardSidebarLayoutProps {
  children: React.ReactNode;
  sidebar: React.ReactNode;
  sidebarPosition?: 'left' | 'right';
  sidebarWidth?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const DashboardSidebarLayout: React.FC<DashboardSidebarLayoutProps> = ({
  children,
  sidebar,
  sidebarPosition = 'right',
  sidebarWidth = 'md',
  className = ''
}) => {
  const getSidebarWidthClass = (width: string) => {
    switch (width) {
      case 'sm':
        return 'lg:w-80';
      case 'lg':
        return 'lg:w-96';
      default:
        return 'lg:w-84';
    }
  };

  const isLeftSidebar = sidebarPosition === 'left';

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-4 gap-6 ${className}`}>
      {isLeftSidebar && (
        <div className={`lg:col-span-1 ${getSidebarWidthClass(sidebarWidth)}`}>
          {sidebar}
        </div>
      )}
      <div className={isLeftSidebar ? 'lg:col-span-3' : 'lg:col-span-3'}>
        {children}
      </div>
      {!isLeftSidebar && (
        <div className={`lg:col-span-1 ${getSidebarWidthClass(sidebarWidth)}`}>
          {sidebar}
        </div>
      )}
    </div>
  );
};

/**
 * Dashboard Empty State - Consistent empty state component
 */
interface DashboardEmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const DashboardEmptyState: React.FC<DashboardEmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  className = ''
}) => {
  return (
    <div className={`text-center py-12 ${className}`}>
      {Icon && (
        <Icon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      {description && (
        <p className="text-gray-600 mb-6 max-w-sm mx-auto">{description}</p>
      )}
      {action}
    </div>
  );
};

export default DashboardLayout;
