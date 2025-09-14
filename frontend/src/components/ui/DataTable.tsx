import React, { useState, useMemo, useCallback } from 'react';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon, 
  ChevronUpIcon, 
  ChevronDownIcon,
  ArrowDownTrayIcon,
  ArrowRightIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from './Card';
import { Button } from './Button';
import { Badge } from './Badge';
import Input from './Input';
import Select from './Select';

export interface DataTableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  searchable?: boolean;
  render?: (value: any, row: any) => React.ReactNode;
  tooltip?: string;
  className?: string;
}

export interface DataTableProps {
  title: string;
  data: any[];
  columns: DataTableColumn[];
  searchPlaceholder?: string;
  statusFilterOptions?: { label: string; value: string }[];
  onRowClick?: (row: any) => void;
  onExport?: () => void;
  onSeeMore?: () => void;
  seeMoreLabel?: string;
  className?: string;
  emptyState?: {
    icon: React.ComponentType<{ className?: string }>;
    title: string;
    description: string;
    actionLabel?: string;
    onAction?: () => void;
  };
}

const DataTable: React.FC<DataTableProps> = ({
  title,
  data,
  columns,
  searchPlaceholder = "Search...",
  statusFilterOptions = [],
  onRowClick,
  onExport,
  onSeeMore,
  seeMoreLabel = "See More",
  className = '',
  emptyState
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  // Memoized filter and sort data
  const filteredData = useMemo(() => {
    let filtered = data;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(item => {
        return columns.some(col => {
          if (!col.searchable) return false;
          const value = item[col.key];
          return value && value.toString().toLowerCase().includes(searchTerm.toLowerCase());
        });
      });
    }

    // Apply status filter
    if (statusFilter) {
      filtered = filtered.filter(item => item.status === statusFilter);
    }

    // Apply sorting
    if (sortField) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortField];
        const bValue = b[sortField];
        
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          return sortDirection === 'asc' 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
        }
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
        }
        
        return 0;
      });
    }

    return filtered;
  }, [data, searchTerm, statusFilter, sortField, sortDirection, columns]);

  // Paginated data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    return filteredData.slice(startIndex, startIndex + pageSize);
  }, [filteredData, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredData.length / pageSize);

  const handleSort = useCallback((field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField, sortDirection]);

  const getSortIcon = useCallback((field: string) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' 
      ? <ChevronUpIcon className="h-4 w-4" />
      : <ChevronDownIcon className="h-4 w-4" />;
  }, [sortField, sortDirection]);

  const handleClearFilters = useCallback(() => {
    setSearchTerm('');
    setStatusFilter('');
    setSortField('');
    setSortDirection('asc');
    setCurrentPage(1);
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1); // Reset to first page when searching
  }, []);

  const handleStatusFilterChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
    setCurrentPage(1); // Reset to first page when filtering
  }, []);

  return (
    <Card className={className}>
      <CardHeader>
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      </CardHeader>
      
      {/* Search and Filter Bar */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <Input
                type="text"
                placeholder={searchPlaceholder}
                value={searchTerm}
                onChange={handleSearchChange}
                className="pl-10"
              />
            </div>
          </div>
          <div className="flex gap-2">
            {statusFilterOptions.length > 0 && (
              <Select
                value={statusFilter}
                onChange={handleStatusFilterChange}
                options={[
                  { label: 'All Status', value: '' },
                  ...statusFilterOptions
                ]}
                className="min-w-[120px]"
              />
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearFilters}
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Clear
            </Button>
          </div>
        </div>
      </div>

      <CardBody padding="none">
        {filteredData.length === 0 ? (
          emptyState ? (
            <div className="text-center py-12">
              <emptyState.icon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">{emptyState.title}</p>
              <p className="text-sm text-gray-500 mb-4">{emptyState.description}</p>
              {emptyState.actionLabel && emptyState.onAction && (
                <Button onClick={emptyState.onAction} variant="primary">
                  {emptyState.actionLabel}
                </Button>
              )}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-600">No data found</p>
            </div>
          )
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {columns.map((column) => (
                    <th
                      key={column.key}
                      className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                        column.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                      } ${column.className || ''}`}
                      onClick={column.sortable ? () => handleSort(column.key) : undefined}
                    >
                      <div className="flex items-center space-x-1">
                        <span>{column.label}</span>
                        {column.sortable && getSortIcon(column.key)}
                        {column.tooltip && (
                          <InformationCircleIcon 
                            className="h-4 w-4 text-gray-400" 
                            title={column.tooltip} 
                          />
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedData.map((row, index) => (
                  <tr
                    key={row.id || index}
                    className={`hover:bg-gray-50 ${onRowClick ? 'cursor-pointer' : ''} ${
                      index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                    }`}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                  >
                    {columns.map((column) => (
                      <td key={column.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {column.render ? column.render(row[column.key], row) : row[column.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="text-sm text-gray-600">
              <p>
                Showing {paginatedData.length} of {filteredData.length} items
                {(searchTerm || statusFilter) && (
                  <span className="text-blue-600 ml-1">
                    (filtered)
                  </span>
                )}
                {totalPages > 1 && (
                  <span className="text-gray-500 ml-1">
                    (Page {currentPage} of {totalPages})
                  </span>
                )}
              </p>
            </div>
            <div className="flex gap-2">
              {onExport && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onExport}
                >
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  Export
                </Button>
              )}
              {onSeeMore && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onSeeMore}
                >
                  {seeMoreLabel}
                  <ArrowRightIcon className="h-4 w-4 ml-2" />
                </Button>
              )}
            </div>
          </div>
          
          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center space-x-2 mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              
              <div className="flex space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1;
                  return (
                    <Button
                      key={page}
                      variant={currentPage === page ? "primary" : "outline"}
                      size="sm"
                      onClick={() => handlePageChange(page)}
                    >
                      {page}
                    </Button>
                  );
                })}
                {totalPages > 5 && (
                  <>
                    <span className="px-2 py-1 text-sm text-gray-500">...</span>
                    <Button
                      variant={currentPage === totalPages ? "primary" : "outline"}
                      size="sm"
                      onClick={() => handlePageChange(totalPages)}
                    >
                      {totalPages}
                    </Button>
                  </>
                )}
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
};

export default DataTable;
