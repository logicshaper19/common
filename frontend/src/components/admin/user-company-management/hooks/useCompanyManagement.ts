/**
 * Custom hook for company management operations
 */
import { useState, useCallback, useEffect } from 'react';
import { adminApi } from '../../../../api/admin';
import {
  Company,
  CompanyFilter,
  CompanyUpdate,
  CompanyBulkOperation,
} from '../../../../types/admin';

export interface UseCompanyManagementReturn {
  // State
  companies: Company[];
  loading: boolean;
  error: string | null;
  selectedCompanies: Set<string>;
  totalPages: number;
  totalCompanies: number;
  filters: CompanyFilter;
  
  // Actions
  loadCompanies: () => Promise<void>;
  handleFilterChange: (newFilters: Partial<CompanyFilter>) => void;
  handlePageChange: (page: number) => void;
  handleSelectCompany: (companyId: string) => void;
  handleSelectAllCompanies: () => void;
  updateCompany: (companyId: string, companyData: CompanyUpdate) => Promise<void>;
  bulkOperation: (operation: CompanyBulkOperation['operation']) => Promise<void>;
  clearSelection: () => void;
  clearError: () => void;
}

export function useCompanyManagement(): UseCompanyManagementReturn {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCompanies, setSelectedCompanies] = useState<Set<string>>(new Set());
  const [totalPages, setTotalPages] = useState(1);
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [filters, setFilters] = useState<CompanyFilter>({
    page: 1,
    per_page: 20,
  });

  const loadCompanies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getCompanies(filters);
      setCompanies(response.data);
      setTotalPages(Math.ceil(response.total / filters.per_page));
      setTotalCompanies(response.total);
    } catch (err) {
      setError('Failed to load companies');
      console.error('Error loading companies:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const handleFilterChange = useCallback((newFilters: Partial<CompanyFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setFilters(prev => ({ ...prev, page }));
  }, []);

  const handleSelectCompany = useCallback((companyId: string) => {
    setSelectedCompanies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(companyId)) {
        newSet.delete(companyId);
      } else {
        newSet.add(companyId);
      }
      return newSet;
    });
  }, []);

  const handleSelectAllCompanies = useCallback(() => {
    if (selectedCompanies.size === companies.length) {
      setSelectedCompanies(new Set());
    } else {
      setSelectedCompanies(new Set(companies.map(company => company.id)));
    }
  }, [selectedCompanies.size, companies]);

  const updateCompany = useCallback(async (companyId: string, companyData: CompanyUpdate) => {
    try {
      setError(null);
      await adminApi.updateCompany(companyId, companyData);
      await loadCompanies(); // Reload companies after update
    } catch (err) {
      setError('Failed to update company');
      console.error('Error updating company:', err);
      throw err;
    }
  }, [loadCompanies]);

  const bulkOperation = useCallback(async (operation: CompanyBulkOperation['operation']) => {
    if (selectedCompanies.size === 0) return;

    const reason = prompt(`Please provide a reason for ${operation}:`);
    if (!reason) return;

    try {
      setError(null);
      await adminApi.bulkCompanyOperation({
        operation,
        company_ids: Array.from(selectedCompanies),
        reason,
      });
      setSelectedCompanies(new Set()); // Clear selection
      await loadCompanies(); // Reload companies
    } catch (err) {
      setError(`Failed to ${operation} companies`);
      console.error(`Error performing bulk ${operation}:`, err);
    }
  }, [selectedCompanies, loadCompanies]);

  const clearSelection = useCallback(() => {
    setSelectedCompanies(new Set());
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load companies when filters change
  useEffect(() => {
    loadCompanies();
  }, [loadCompanies]);

  return {
    // State
    companies,
    loading,
    error,
    selectedCompanies,
    totalPages,
    totalCompanies,
    filters,
    
    // Actions
    loadCompanies,
    handleFilterChange,
    handlePageChange,
    handleSelectCompany,
    handleSelectAllCompanies,
    updateCompany,
    bulkOperation,
    clearSelection,
    clearError,
  };
}
