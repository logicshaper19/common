/**
 * Products Page Component
 * Regular user interface for viewing products
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Badge from '../components/ui/Badge';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  CubeIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { productsApi, Product, ProductFilter } from '../services/productsApi';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';

const ProductsPage: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // State
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [compositionFilter, setCompositionFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalProducts, setTotalProducts] = useState(0);
  
  const perPage = 20;

  // Load products
  const loadProducts = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const filters: ProductFilter = {
        page: currentPage,
        per_page: perPage,
      };
      
      if (searchTerm.trim()) {
        filters.search = searchTerm.trim();
      }
      
      if (categoryFilter) {
        filters.category = categoryFilter;
      }
      
      if (compositionFilter !== '') {
        filters.can_have_composition = compositionFilter === 'true';
      }
      
      const response = await productsApi.getProducts(filters);
      setProducts(response.products);
      setTotalPages(response.total_pages);
      setTotalProducts(response.total);
    } catch (err) {
      console.error('Error loading products:', err);
      setError('Failed to load products. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading products',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, searchTerm, categoryFilter, compositionFilter, showToast]);

  // Load products when filters change
  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadProducts();
  };

  // Handle filter changes
  const handleCategoryChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setCategoryFilter(event.target.value);
    setCurrentPage(1);
  };

  const handleCompositionChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setCompositionFilter(event.target.value);
    setCurrentPage(1);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Clear filters
  const clearFilters = () => {
    setSearchTerm('');
    setCategoryFilter('');
    setCompositionFilter('');
    setCurrentPage(1);
  };

  // Format category for display
  const formatCategory = (category: string) => {
    return category.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Products</h1>
        <p className="text-gray-600 mt-1">
          Browse and search through available products in the catalog.
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader title="Search & Filter" />
        <CardBody>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <Input
                  type="text"
                  placeholder="Search products..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  leftIcon={<MagnifyingGlassIcon className="h-4 w-4" />}
                />
              </div>
              
              {/* Category Filter */}
              <div>
                <Select
                  value={categoryFilter}
                  onChange={handleCategoryChange}
                  options={[
                    { label: 'All Categories', value: '' },
                    { label: 'Raw Material', value: 'raw_material' },
                    { label: 'Intermediate Product', value: 'intermediate_product' },
                    { label: 'Finished Product', value: 'finished_product' },
                    { label: 'Packaging', value: 'packaging' },
                    { label: 'Component', value: 'component' }
                  ]}
                />
              </div>
              
              {/* Composition Filter */}
              <div>
                <Select
                  value={compositionFilter}
                  onChange={handleCompositionChange}
                  options={[
                    { label: 'All Products', value: '' },
                    { label: 'Has Composition', value: 'true' },
                    { label: 'No Composition', value: 'false' }
                  ]}
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button type="submit" variant="primary" size="sm">
                <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
                Search
              </Button>
              <Button type="button" variant="secondary" size="sm" onClick={clearFilters}>
                <FunnelIcon className="h-4 w-4 mr-2" />
                Clear Filters
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader 
          title={`Products (${totalProducts})`}
          subtitle={`Page ${currentPage} of ${totalPages}`}
        />
        <CardBody padding="none">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner size="lg" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={loadProducts} variant="primary">
                Try Again
              </Button>
            </div>
          ) : !products || products.length === 0 ? (
            <div className="text-center py-12">
              <CubeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">No products found</p>
              <Button onClick={clearFilters} variant="secondary">
                Clear Filters
              </Button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Unit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Composition
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      HS Code
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {products.map((product) => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {product.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            ID: {product.common_product_id}
                          </div>
                          {product.description && (
                            <div className="text-sm text-gray-500 mt-1">
                              {product.description}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant="secondary">
                          {formatCategory(product.category)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.default_unit}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant={product.can_have_composition ? 'success' : 'neutral'}>
                          {product.can_have_composition ? 'Yes' : 'No'}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {product.hs_code || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * perPage) + 1} to {Math.min(currentPage * perPage, totalProducts)} of {totalProducts} products
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage <= 1}
              onClick={() => handlePageChange(currentPage - 1)}
            >
              <ChevronLeftIcon className="h-4 w-4 mr-1" />
              Previous
            </Button>
            
            <span className="text-sm text-gray-700">
              Page {currentPage} of {totalPages}
            </span>
            
            <Button
              variant="outline"
              size="sm"
              disabled={currentPage >= totalPages}
              onClick={() => handlePageChange(currentPage + 1)}
            >
              Next
              <ChevronRightIcon className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </>
  );
};

export default ProductsPage;
