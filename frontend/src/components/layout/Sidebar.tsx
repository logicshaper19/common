/**
 * Sidebar Component - Main navigation sidebar
 * Single source of truth - all permissions come from backend PermissionService
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  BuildingOfficeIcon,
  CubeIcon,
  DocumentTextIcon,
  ChartBarIcon,
  UsersIcon,
  Cog6ToothIcon,
  XMarkIcon,
  BeakerIcon,
  UserPlusIcon,
  UserGroupIcon,
  ArchiveBoxIcon,
  QueueListIcon,
  MapIcon,
  ShieldCheckIcon,
  SunIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  CheckCircleIcon,
  CogIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/utils';
import Button from '../ui/Button';
import { usePurchaseOrderCount } from '../../hooks/usePurchaseOrderCount';
import { useDashboardConfig, DashboardPermissions } from '../../hooks/useDashboardConfig';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
}

// Loading skeleton component
const SidebarSkeleton: React.FC = () => (
  <div className="space-y-1">
    <div className="h-8 bg-gray-200 rounded animate-pulse" />
    <div className="h-6 bg-gray-200 rounded animate-pulse" />
    <div className="h-6 bg-gray-200 rounded animate-pulse" />
    <div className="h-6 bg-gray-200 rounded animate-pulse" />
    <div className="h-6 bg-gray-200 rounded animate-pulse" />
  </div>
);

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const { pendingCount } = usePurchaseOrderCount();
  const { config, loading, error } = useDashboardConfig();
  
  if (!user) return null;
  
  // Get permissions from backend - single source of truth
  const permissions = config?.permissions || {} as DashboardPermissions;

  // Navigation items with backend-driven permissions
  const navigation: NavigationItem[] = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
    },
    // Purchase Order Management - Backend driven
    ...(permissions.can_create_po ? [{
      name: 'Create Purchase Order',
      href: '/purchase-orders/outgoing',
      icon: DocumentTextIcon,
    }] : []),
    ...(permissions.can_confirm_po ? [{
      name: 'Incoming Purchase Orders',
      href: '/purchase-orders/incoming',
      icon: ArrowLeftIcon,
      badge: pendingCount > 0 ? pendingCount : undefined,
    }] : []),
    // Confirmed Orders - Show for users who can create or confirm POs
    ...((permissions.can_create_po || permissions.can_confirm_po) ? [{
      name: 'Confirmed Orders',
      href: '/purchase-orders/confirmed',
      icon: CheckCircleIcon,
    }] : []),
    // Transformations - Backend driven
    ...(permissions.can_manage_transformations ? [{
      name: 'Transformations',
      href: '/transformations',
      icon: CogIcon,
    }] : []),
    // Inventory Management - Available for all roles that have batches
    ...(permissions.can_create_po || permissions.can_confirm_po || permissions.can_manage_transformations ? [{
      name: '📦 Inventory',
      href: '/inventory',
      icon: ArchiveBoxIcon,
    }] : []),
    // Farm Management - Backend driven
    ...(permissions.can_report_farm_data ? [{
      name: 'Farm Management',
      href: '/originator/farms',
      icon: BuildingOfficeIcon,
    }] : []),
    ...(permissions.can_report_farm_data ? [{
      name: 'Production Tracking',
      href: '/harvest',
      icon: SunIcon,
    }] : []),
    // Certifications - Backend driven
    ...(permissions.can_manage_certifications ? [{
      name: 'Certifications',
      href: '/originator/certifications',
      icon: ShieldCheckIcon,
    }] : []),
    // Team Management - Backend driven
    ...(permissions.can_manage_team ? [{
      name: 'Team Management',
      href: '/team',
      icon: UserGroupIcon,
    }] : []),
    // Settings - Backend driven
    ...(permissions.can_manage_settings ? [{
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
    }] : []),
    // Trader-specific features - Backend driven
    ...(permissions.can_manage_trader_chain ? [{
      name: 'Supply Chain',
      href: '/trader-chain',
      icon: QueueListIcon,
    }] : []),
    ...(permissions.can_view_margin_analysis ? [{
      name: 'Margin Analysis',
      href: '/margin-analysis',
      icon: ChartBarIcon,
    }] : []),
    // Analytics - Backend driven
    ...(permissions.can_view_analytics ? [{
      name: 'Traceability',
      href: '/transparency',
      icon: ChartBarIcon,
    }] : []),
    // Admin features - Backend driven
    ...(permissions.can_audit_companies ? [{
      name: 'Company Audit',
      href: '/admin/companies',
      icon: BuildingOfficeIcon,
    }] : []),
    ...(permissions.can_regulate_platform ? [{
      name: 'Platform Admin',
      href: '/admin/platform',
      icon: UsersIcon,
    }] : []),
  ];

  // Show loading skeleton during API call
  if (loading) {
    return (
      <>
        {/* Mobile overlay */}
        {isOpen && (
          <div
            className="fixed inset-0 z-40 lg:hidden"
            onClick={onClose}
          >
            <div className="fixed inset-0 bg-neutral-600 bg-opacity-75" />
          </div>
        )}

        {/* Sidebar with loading state */}
        <div
          className={cn(
            'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-neutral-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
            isOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex flex-col h-full">
            {/* Logo section */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-200">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">C</span>
                </div>
                <div className="ml-3">
                  <h1 className="text-lg font-semibold text-neutral-900">Common</h1>
                  <p className="text-xs text-neutral-500">Supply Chain Platform</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                aria-label="Close sidebar"
                className="lg:hidden"
              >
                <XMarkIcon className="h-6 w-6" />
              </Button>
            </div>

            {/* Loading skeleton */}
            <nav className="flex-1 px-4 pb-4 space-y-1 overflow-y-auto">
              <div className="mb-6 p-3 bg-neutral-50 rounded-lg">
                <div className="flex items-center">
                  <div className="h-10 w-10 bg-gray-200 rounded-full animate-pulse" />
                  <div className="ml-3 space-y-2">
                    <div className="h-4 bg-gray-200 rounded animate-pulse w-24" />
                    <div className="h-3 bg-gray-200 rounded animate-pulse w-32" />
                    <div className="h-3 bg-gray-200 rounded animate-pulse w-16" />
                  </div>
                </div>
              </div>
              <SidebarSkeleton />
            </nav>
          </div>
        </div>
      </>
    );
  }

  // Show error state
  if (error) {
    return (
      <>
        {/* Mobile overlay */}
        {isOpen && (
          <div
            className="fixed inset-0 z-40 lg:hidden"
            onClick={onClose}
          >
            <div className="fixed inset-0 bg-neutral-600 bg-opacity-75" />
          </div>
        )}

        {/* Sidebar with error state */}
        <div
          className={cn(
            'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-neutral-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
            isOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex flex-col h-full">
            {/* Logo section */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-200">
              <div className="flex items-center">
                <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">C</span>
                </div>
                <div className="ml-3">
                  <h1 className="text-lg font-semibold text-neutral-900">Common</h1>
                  <p className="text-xs text-neutral-500">Supply Chain Platform</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                aria-label="Close sidebar"
                className="lg:hidden"
              >
                <XMarkIcon className="h-6 w-6" />
              </Button>
            </div>

            {/* Error message */}
            <div className="flex-1 px-4 pb-4 flex items-center justify-center">
              <div className="text-center">
                <p className="text-red-600 mb-2">Error loading navigation</p>
                <button 
                  onClick={() => window.location.reload()} 
                  className="text-sm underline text-primary-600 hover:text-primary-800"
                >
                  Retry
                </button>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  // Navigation link component
  const NavigationLink: React.FC<{ item: NavigationItem }> = ({ item }) => (
    <NavLink
      to={item.href}
      onClick={onClose}
      className={({ isActive }) =>
        cn(
          'group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors duration-200',
          isActive
            ? 'bg-primary-100 text-primary-700 border-r-2 border-primary-600'
            : 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900'
        )
      }
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={cn(
              'mr-3 h-5 w-5 flex-shrink-0',
              isActive ? 'text-primary-600' : 'text-neutral-400 group-hover:text-neutral-500'
            )}
          />
          <span className="flex-1">{item.name}</span>
          {item.badge && (
            <span
              className={cn(
                'ml-3 inline-block py-0.5 px-2 text-xs rounded-full',
                isActive
                  ? 'bg-primary-200 text-primary-800'
                  : 'bg-neutral-200 text-neutral-700'
              )}
            >
              {item.badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  );

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 lg:hidden"
          onClick={onClose}
        >
          <div className="fixed inset-0 bg-neutral-600 bg-opacity-75" />
        </div>
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-neutral-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo section - Always visible */}
          <div className="flex items-center justify-between p-4 border-b border-neutral-200">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <div className="ml-3">
                <h1 className="text-lg font-semibold text-neutral-900">
                  Common
                </h1>
                <p className="text-xs text-neutral-500">
                  Supply Chain Platform
                </p>
              </div>
            </div>
            {/* Mobile close button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              aria-label="Close sidebar"
              className="lg:hidden"
            >
              <XMarkIcon className="h-6 w-6" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 pb-4 space-y-1 overflow-y-auto">
            {/* User info section */}
            <div className="mb-6 p-3 bg-neutral-50 rounded-lg">
              <div className="flex items-center">
                <div className="h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-primary-700 font-medium">
                    {user?.full_name?.charAt(0) || 'U'}
                  </span>
                </div>
                <div className="ml-3 min-w-0 flex-1">
                  <p className="text-sm font-medium text-neutral-900 truncate">
                    {user?.full_name || 'User'}
                  </p>
                  <p className="text-xs text-neutral-500 truncate">
                    {user?.company?.name || 'Company'}
                  </p>
                  <p className="text-xs text-neutral-400 capitalize">
                    {user?.role || 'Role'}
                  </p>
                </div>
              </div>
            </div>

            {/* Navigation links */}
            <div className="space-y-1">
              {navigation.map((item) => (
                <NavigationLink key={item.name} item={item} />
              ))}
            </div>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-neutral-200">
            <div className="text-xs text-neutral-500 text-center">
              <p>Common Platform v1.0.0</p>
              <p className="mt-1">
                © 2024 Common Supply Chain
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
