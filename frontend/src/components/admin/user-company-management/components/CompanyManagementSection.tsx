/**
 * Company management section component
 */
import React, { useState } from 'react';
import { Company, CompanyUpdate } from '../../../../types/admin';
import { useCompanyManagement } from '../hooks/useCompanyManagement';
import { CompanyFilters } from './CompanyFilters';
import { CompanyTable } from './CompanyTable';
import { CompanyBulkActions } from './CompanyBulkActions';
import { CompanyModal } from './CompanyModal';
import { Pagination } from './Pagination';

export function CompanyManagementSection() {
  const {
    companies,
    loading,
    error,
    selectedCompanies,
    totalPages,
    totalCompanies,
    filters,
    loadCompanies,
    handleFilterChange,
    handlePageChange,
    handleSelectCompany,
    handleSelectAllCompanies,
    updateCompany,
    bulkOperation,
    clearSelection,
    clearError,
  } = useCompanyManagement();

  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  const handleEditCompany = async (companyData: CompanyUpdate) => {
    if (!selectedCompany) return;

    try {
      await updateCompany(selectedCompany.id, companyData);
      setShowEditModal(false);
      setSelectedCompany(null);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const openEditModal = (company: Company) => {
    setSelectedCompany(company);
    setShowEditModal(true);
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setSelectedCompany(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Company Management</h2>
          <p className="text-sm text-gray-500">
            Manage company accounts and settings ({totalCompanies} total)
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
              <div className="mt-4">
                <button
                  onClick={clearError}
                  className="text-sm font-medium text-red-800 hover:text-red-600"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <CompanyFilters filters={filters} onFilterChange={handleFilterChange} />

      {/* Bulk Actions */}
      {selectedCompanies.size > 0 && (
        <CompanyBulkActions
          selectedCount={selectedCompanies.size}
          onBulkOperation={bulkOperation}
          onClearSelection={clearSelection}
        />
      )}

      {/* Company Table */}
      <CompanyTable
        companies={companies}
        selectedCompanies={selectedCompanies}
        onSelectCompany={handleSelectCompany}
        onSelectAllCompanies={handleSelectAllCompanies}
        onEditCompany={openEditModal}
        loading={loading}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={filters.page}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      )}

      {/* Edit Company Modal */}
      <CompanyModal
        isOpen={showEditModal}
        onClose={handleCloseEditModal}
        onSubmit={handleEditCompany}
        company={selectedCompany}
      />
    </div>
  );
}
