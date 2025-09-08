/**
 * User management section component
 */
import React, { useState } from 'react';
import { PlusIcon } from '@heroicons/react/24/outline';
import { AdminUser, UserCreate, UserUpdate } from '../../../../types/admin';
import { useUserManagement } from '../hooks/useUserManagement';
import { UserFilters } from './UserFilters';
import { UserTable } from './UserTable';
import { UserBulkActions } from './UserBulkActions';
import { UserModal } from './UserModal';
import { Pagination } from './Pagination';

export function UserManagementSection() {
  const {
    users,
    loading,
    error,
    selectedUsers,
    totalPages,
    totalUsers,
    filters,
    loadUsers,
    handleFilterChange,
    handlePageChange,
    handleSelectUser,
    handleSelectAllUsers,
    createUser,
    updateUser,
    deleteUser,
    bulkOperation,
    clearSelection,
    clearError,
  } = useUserManagement();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [userFormData, setUserFormData] = useState<UserCreate>({
    email: '',
    full_name: '',
    role: 'buyer',
    company_id: '',
    send_invitation: true,
  });

  const handleCreateUser = async () => {
    try {
      await createUser(userFormData);
      setShowCreateModal(false);
      setUserFormData({
        email: '',
        full_name: '',
        role: 'buyer',
        company_id: '',
        send_invitation: true,
      });
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const handleEditUser = async () => {
    if (!selectedUser) return;

    try {
      const updateData: UserUpdate = {
        full_name: userFormData.full_name,
        role: userFormData.role,
        is_active: selectedUser.is_active,
      };
      await updateUser(selectedUser.id, updateData);
      setShowEditModal(false);
      setSelectedUser(null);
    } catch (err) {
      // Error is handled by the hook
    }
  };

  const openEditModal = (user: AdminUser) => {
    setSelectedUser(user);
    setUserFormData({
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      company_id: user.company_id,
      send_invitation: false,
    });
    setShowEditModal(true);
  };

  const handleCloseCreateModal = () => {
    setShowCreateModal(false);
    setUserFormData({
      email: '',
      full_name: '',
      role: 'buyer',
      company_id: '',
      send_invitation: true,
    });
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setSelectedUser(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-medium text-gray-900">User Management</h2>
          <p className="text-sm text-gray-500">
            Manage user accounts and permissions ({totalUsers} total)
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create User
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
      <UserFilters filters={filters} onFilterChange={handleFilterChange} />

      {/* Bulk Actions */}
      {selectedUsers.size > 0 && (
        <UserBulkActions
          selectedCount={selectedUsers.size}
          onBulkOperation={bulkOperation}
          onClearSelection={clearSelection}
        />
      )}

      {/* User Table */}
      <UserTable
        users={users}
        selectedUsers={selectedUsers}
        onSelectUser={handleSelectUser}
        onSelectAllUsers={handleSelectAllUsers}
        onEditUser={openEditModal}
        onDeleteUser={deleteUser}
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

      {/* Create User Modal */}
      <UserModal
        isOpen={showCreateModal}
        onClose={handleCloseCreateModal}
        onSubmit={handleCreateUser}
        title="Create New User"
        submitLabel="Create User"
        formData={userFormData}
        onFormDataChange={setUserFormData}
        mode="create"
      />

      {/* Edit User Modal */}
      <UserModal
        isOpen={showEditModal}
        onClose={handleCloseEditModal}
        onSubmit={handleEditUser}
        title="Edit User"
        submitLabel="Update User"
        formData={userFormData}
        onFormDataChange={setUserFormData}
        selectedUser={selectedUser}
        mode="edit"
      />
    </div>
  );
}
