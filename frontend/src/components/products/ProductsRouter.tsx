/**
 * Products Router Component
 * Routes to appropriate products interface based on user role
 */
import React from 'react';
// import { useAuth } from '../../contexts/AuthContext';
import { ProductCatalogManagement } from '../admin/product-catalog-management';
// import ProductsPage from '../../pages/ProductsPage';

const ProductsRouter: React.FC = () => {
  // const { user } = useAuth();

  // Temporarily use admin interface for all users since regular API has issues
  // TODO: Fix regular products API endpoint and switch back to role-based routing
  return <ProductCatalogManagement />;

  // Original role-based routing (commented out until regular API is fixed):
  // if (user?.role === 'admin') {
  //   return <ProductCatalogManagement />;
  // }
  // return <ProductsPage />;
};

export default ProductsRouter;
