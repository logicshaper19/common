/**
 * Enhanced Dashboard Router Component
 * Routes users to appropriate dashboard with real-time updates and error boundaries
 */
import React, { Suspense } from 'react';
import { Navigate } from 'react-router-dom';
import { useDashboardConfig } from '../../hooks/useDashboardConfig';
import LoadingSpinner from '../ui/LoadingSpinner';
import { RealTimeProvider } from './shared/RealTimeUpdates';
import DashboardLayout, { DashboardEmptyState } from './shared/DashboardLayout';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

// Lazy load dashboard components for better performance
const LegacyDashboard = React.lazy(() => import('../../pages/Dashboard'));

// V2 Dashboard Content Components (work with main layout)
const OriginatorLayout = React.lazy(() => import('./v2/OriginatorLayout'));
const BrandLayout = React.lazy(() => import('./v2/BrandLayout'));
const ProcessorLayout = React.lazy(() => import('./v2/ProcessorLayout'));
const TraderLayout = React.lazy(() => import('./v2/TraderLayout'));
const PlatformAdminLayout = React.lazy(() => import('./v2/PlatformAdminLayout'));

interface DashboardRouterProps {
  className?: string;
}

export const DashboardRouter: React.FC<DashboardRouterProps> = ({ className = '' }) => {
  const { config, loading, error } = useDashboardConfig();

  // Show loading state while configuration loads
  if (loading) {
    return (
      <div className={`dashboard-loading ${className}`}>
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-gray-600">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  // Show error state if configuration failed to load
  if (error) {
    return (
      <div className={`dashboard-error ${className}`}>
        <div className="flex flex-col items-center justify-center h-64">
          <div className="text-red-600 mb-2">Failed to load dashboard configuration</div>
          <div className="text-gray-600 text-sm">{error}</div>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Redirect to login if no configuration (shouldn't happen with ProtectedRoute)
  if (!config) {
    return <Navigate to="/login" replace />;
  }

  // Determine which dashboard to show
  const dashboardType = config.dashboard_type;
  const shouldUseV2 = config.should_use_v2;

  // If V2 is enabled for this dashboard type, render V2 content directly
  if (shouldUseV2) {
    return (
      <RealTimeProvider>
        <DashboardErrorBoundary>
          <Suspense fallback={<DashboardLoadingFallback />}>
            <div className={`dashboard-v2-content ${className}`}>
              {getDashboardV2Layout(dashboardType)}
            </div>
          </Suspense>
        </DashboardErrorBoundary>
      </RealTimeProvider>
    );
  }

  // Otherwise, show legacy dashboard
  return (
    <RealTimeProvider>
      <DashboardErrorBoundary>
        <Suspense fallback={<DashboardLoadingFallback />}>
          <div className={`dashboard-v1 ${className}`}>
            <LegacyDashboard />
          </div>
        </Suspense>
      </DashboardErrorBoundary>
    </RealTimeProvider>
  );
};

/**
 * Get the appropriate V2 dashboard content based on dashboard type
 */
const getDashboardV2Layout = (dashboardType: string): React.ReactElement => {
  switch (dashboardType) {
    case 'brand':
      return <BrandLayout />;
    case 'processor':
      return <ProcessorLayout />;
    case 'originator':
      return <OriginatorLayout />;
    case 'trader':
      return <TraderLayout />;
    case 'platform_admin':
      return <PlatformAdminLayout />;
    default:
      // Fallback to brand for unknown types
      return <BrandLayout />;
  }
};

/**
 * Enhanced loading fallback component for dashboard lazy loading
 */
const DashboardLoadingFallback: React.FC = () => (
  <DashboardLayout title="Loading Dashboard" showRealTimeStatus={false}>
    <div className="flex items-center justify-center h-64">
      <LoadingSpinner size="lg" />
      <span className="ml-3 text-gray-600">Loading dashboard...</span>
    </div>
  </DashboardLayout>
);

/**
 * Error boundary for dashboard components
 */
class DashboardErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Dashboard error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <DashboardLayout title="Dashboard Error" showRealTimeStatus={false}>
          <DashboardEmptyState
            icon={ExclamationTriangleIcon}
            title="Something went wrong"
            description="We encountered an error while loading your dashboard. Please try refreshing the page."
            action={
              <button
                onClick={() => window.location.reload()}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Refresh Page
              </button>
            }
          />
        </DashboardLayout>
      );
    }

    return this.props.children;
  }
}

export default DashboardRouter;
