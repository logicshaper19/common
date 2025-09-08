/**
 * Refactored Product Catalog Management Interface
 * Clean, modular architecture with focused components and custom hooks
 */
import React from 'react';
import { ProductManagementSection } from './components/ProductManagementSection';

interface ProductCatalogManagementProps {
  className?: string;
}

export function ProductCatalogManagement({ className = '' }: ProductCatalogManagementProps) {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Product Catalog Management</h1>
        <p className="text-gray-600">
          Comprehensive admin interface for product catalog oversight and validation
        </p>
      </div>

      {/* Product Management Section */}
      <ProductManagementSection />
    </div>
  );
}
