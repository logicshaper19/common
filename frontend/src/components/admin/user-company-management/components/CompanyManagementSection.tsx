/**
 * Company management section component
 */
import React, { useState } from 'react';
import { PlusIcon } from '@heroicons/react/24/outline';
import { Company, CompanyCreate, CompanyUpdate } from '../../../../types/admin';
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
    createCompany,
    updateCompany,
    bulkOperation,
    clearSelection,
    clearError,
  } = useCompanyManagement();

  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('edit');
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  const handleSubmitCompany = async (companyData: CompanyCreate | CompanyUpdate) => {
    try {
      if (modalMode === 'create') {
        await createCompany(companyData as CompanyCreate);
      } else if (selectedCompany) {
        await updateCompany(selectedCompany.id, companyData as CompanyUpdate);
      }
      setShowModal(false);
      setSelectedCompany(null);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const openCreateModal = () => {
    setModalMode('create');
    setSelectedCompany(null);
    setShowModal(true);
  };

  const openEditModal = (company: Company) => {
    setModalMode('edit');
    setSelectedCompany(company);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
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
        <button
          onClick={openCreateModal}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Company
        </button>
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

      {/* Company Modal */}
      <CompanyModal
        isOpen={showModal}
        onClose={handleCloseModal}
        onSubmit={handleSubmitCompany}
        company={selectedCompany}
        mode={modalMode}
      />
    </div>
  );
}
