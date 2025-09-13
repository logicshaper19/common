/**
 * Sidebar Component - Main navigation sidebar
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
} from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { cn } from '../../lib/utils';
import Button from '../ui/Button';
import { shouldShowNavigationItem, getDashboardConfig } from '../../utils/permissions';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  requiredRole?: string;
  badge?: string | number;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  
  if (!user) return null;
  
  const dashboardConfig = getDashboardConfig(user);

  // Navigation items with permission-based visibility
  const navigation: NavigationItem[] = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: HomeIcon,
    },
    // Purchase Orders - visible to users who can create or confirm POs
    ...(dashboardConfig.can_create_po || dashboardConfig.can_confirm_po ? [{
      name: 'Purchase Orders',
      href: '/purchase-orders',
      icon: DocumentTextIcon,
      badge: '12', // This would come from API
    }] : []),
    // Products - only for brands and processors (not originators)
    ...(user.company?.company_type !== 'originator' && user.company?.company_type !== 'plantation_grower' ? [{
      name: 'Products',
      href: '/products',
      icon: CubeIcon,
    }] : []),
    // Inventory - only for processors and brands (not originators)
    ...(user.company?.company_type !== 'originator' && user.company?.company_type !== 'plantation_grower' ? [{
      name: 'Inventory',
      href: '/inventory',
      icon: ArchiveBoxIcon,
    }] : []),
    // Batches - only for processors (not originators)
    ...(user.company?.company_type === 'processor' ? [{
      name: 'Batches',
      href: '/inventory/batches',
      icon: QueueListIcon,
    }] : []),
    // Originator features - only for originator companies
    ...(dashboardConfig.can_report_farm_data ? [{
      name: 'Farm Management',
      href: '/originator/farms',
      icon: BuildingOfficeIcon,
    }] : []),
    ...(dashboardConfig.can_report_farm_data ? [{
      name: 'Origin Data',
      href: '/originator/origin-data',
      icon: MapIcon,
    }] : []),
    ...(dashboardConfig.can_manage_certifications ? [{
      name: 'Certifications',
      href: '/originator/certifications',
      icon: ShieldCheckIcon,
    }] : []),
    // Team management - only for admins and farm managers
    ...(dashboardConfig.can_manage_team ? [{
      name: 'Team',
      href: '/team',
      icon: UserGroupIcon,
    }] : []),
    // Transparency - visible to most users
    ...(dashboardConfig.can_view_analytics ? [{
      name: 'Transparency',
      href: '/transparency',
      icon: ChartBarIcon,
    }] : []),
    // Supplier Onboarding - only for brands and processors (not originators)
    ...(user.company?.company_type !== 'originator' && user.company?.company_type !== 'plantation_grower' ? [{
      name: 'Supplier Onboarding',
      href: '/onboarding',
      icon: UserPlusIcon,
    }] : []),
    // Admin-specific navigation items
    ...(user.role === 'admin' || user.role === 'super_admin' ? [{
      name: 'Companies',
      href: '/companies',
      icon: BuildingOfficeIcon,
    }] : []),
    ...(user.role === 'admin' || user.role === 'super_admin' ? [{
      name: 'Users',
      href: '/users',
      icon: UsersIcon,
    }] : []),
    ...(user.role === 'admin' || user.role === 'super_admin' ? [{
      name: 'System Monitor',
      href: '/admin/system',
      icon: ChartBarIcon,
    }] : []),
    ...(user.role === 'admin' || user.role === 'super_admin' ? [{
      name: 'Audit Logs',
      href: '/admin/audit',
      icon: DocumentTextIcon,
    }] : []),
    ...(user.role === 'admin' || user.role === 'super_admin' ? [{
      name: 'Support Tickets',
      href: '/admin/support',
      icon: UserGroupIcon,
    }] : []),
    // Settings - only for admins
    ...(dashboardConfig.can_manage_settings ? [{
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
    }] : []),
    // Trader-specific features
    ...(dashboardConfig.can_manage_trader_chain ? [{
      name: 'Trader Chain',
      href: '/trader-chain',
      icon: QueueListIcon,
    }] : []),
    ...(dashboardConfig.can_view_margin_analysis ? [{
      name: 'Margin Analysis',
      href: '/margin-analysis',
      icon: ChartBarIcon,
    }] : []),
    // Demo features - only for development (commented out for production)
    // {
    //   name: 'Confirmation Demo',
    //   href: '/confirmation-demo',
    //   icon: BeakerIcon,
    //   badge: 'New',
    // },
  ];

  // Navigation items are already filtered by permissions in the array definition
  const filteredNavigation = navigation;

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
              {filteredNavigation.map((item) => (
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
