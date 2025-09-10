/**
 * Inventory Router Component
 * Optimized routing with lazy loading for inventory management features
 */
import React, { Suspense, lazy } from 'react';
import { useAuth } from '../../contexts/AuthContext';

// Lazy load components for better performance
const InventoryDashboard = lazy(() => import('../../pages/InventoryDashboard'));
const BatchManagement = lazy(() => import('../../pages/BatchManagement'));
const BatchAnalytics = lazy(() => import('../../pages/BatchAnalytics'));

// Optimized loading fallback component
const InventoryLoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-pulse space-y-4 w-full max-w-md">
      <div className="h-8 bg-gray-200 rounded"></div>
      <div className="space-y-2">
        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
      <div className="h-32 bg-gray-200 rounded"></div>
    </div>
  </div>
);

interface InventoryRouterProps {
  view?: 'dashboard' | 'batches' | 'analytics';
}

const InventoryRouter: React.FC<InventoryRouterProps> = ({ view = 'dashboard' }) => {
  const { user } = useAuth();

  const renderView = () => {
    switch (view) {
      case 'batches':
        return <BatchManagement />;
      case 'analytics':
        return <BatchAnalytics />;
      case 'dashboard':
      default:
        return <InventoryDashboard />;
    }
  };

  return (
    <Suspense fallback={<InventoryLoadingFallback />}>
      {renderView()}
    </Suspense>
  );
};

export default InventoryRouter;
