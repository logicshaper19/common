/**
 * Products Router Component
 * Optimized routing with lazy loading for better performance
 */
import React, { Suspense, lazy } from 'react';
import { useAuth } from '../../contexts/AuthContext';

// Lazy load components for better performance
const ProductCatalogManagement = lazy(() =>
  import('../admin/product-catalog-management').then(module => ({
    default: module.ProductCatalogManagement
  }))
);

const ProductsPage = lazy(() => import('../../pages/ProductsPage'));

// Optimized loading fallback component
const ProductLoadingFallback: React.FC = () => (
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

const ProductsRouter: React.FC = () => {
  const { user } = useAuth();

  return (
    <Suspense fallback={<ProductLoadingFallback />}>
      {/* Role-based routing with lazy loading optimization */}
      {user?.role === 'admin' ? (
        <ProductCatalogManagement />
      ) : (
        <ProductsPage />
      )}
    </Suspense>
  );
};

export default ProductsRouter;
