/**
 * User and Company Management Dashboard
 * Comprehensive admin interface for user and company oversight
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  UserIcon,
  BuildingOfficeIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EnvelopeIcon,
  PhoneIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { adminApi } from '../../api/admin';
import {
  AdminUser,
  Company,
  UserFilter,
  CompanyFilter,
  UserCreate,
  UserUpdate,
  CompanyUpdate,
  UserBulkOperation,
  CompanyBulkOperation,
  UserRole,
  CompanyType,
  SubscriptionTier,
  ComplianceStatus,
} from '../../types/admin';
import { formatTimeAgo } from '../../lib/utils';

interface UserCompanyManagementProps {
  className?: string;
}

export function UserCompanyManagement({ className = '' }: UserCompanyManagementProps) {
  const [activeTab, setActiveTab] = useState<'users' | 'companies'>('users');
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());
  const [selectedCompanies, setSelectedCompanies] = useState<Set<string>>(new Set());
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showEditCompanyModal, setShowEditCompanyModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  // Filters and pagination
  const [userFilters, setUserFilters] = useState<UserFilter>({
    page: 1,
    per_page: 20,
  });
  const [companyFilters, setCompanyFilters] = useState<CompanyFilter>({
    page: 1,
    per_page: 20,
  });
  const [userTotalPages, setUserTotalPages] = useState(1);
  const [companyTotalPages, setCompanyTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [totalCompanies, setTotalCompanies] = useState(0);

  // Form state
  const [userFormData, setUserFormData] = useState<UserCreate>({
    email: '',
    full_name: '',
    role: 'buyer',
    company_id: '',
    send_invitation: true,
  });

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getUsers(userFilters);
      setUsers(response.data);
      setUserTotalPages(Math.ceil(response.total / userFilters.per_page));
      setTotalUsers(response.total);
    } catch (err) {
      setError('Failed to load users');
      console.error('Error loading users:', err);
    } finally {
      setLoading(false);
    }
  }, [userFilters]);

  const loadCompanies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getCompanies(companyFilters);
      setCompanies(response.data);
      setCompanyTotalPages(Math.ceil(response.total / companyFilters.per_page));
      setTotalCompanies(response.total);
    } catch (err) {
      setError('Failed to load companies');
      console.error('Error loading companies:', err);
    } finally {
      setLoading(false);
    }
  }, [companyFilters]);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    } else {
      loadCompanies();
    }
  }, [activeTab, loadUsers, loadCompanies]);

  const handleUserFilterChange = (newFilters: Partial<UserFilter>) => {
    setUserFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handleCompanyFilterChange = (newFilters: Partial<CompanyFilter>) => {
    setCompanyFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handleUserPageChange = (page: number) => {
    setUserFilters(prev => ({ ...prev, page }));
  };

  const handleCompanyPageChange = (page: number) => {
    setCompanyFilters(prev => ({ ...prev, page }));
  };

  const handleSelectUser = (userId: string) => {
    setSelectedUsers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(userId)) {
        newSet.delete(userId);
      } else {
        newSet.add(userId);
      }
      return newSet;
    });
  };

  const handleSelectCompany = (companyId: string) => {
    setSelectedCompanies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(companyId)) {
        newSet.delete(companyId);
      } else {
        newSet.add(companyId);
      }
      return newSet;
    });
  };

  const handleSelectAllUsers = () => {
    if (selectedUsers.size === users.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(users.map(u => u.id)));
    }
  };

  const handleSelectAllCompanies = () => {
    if (selectedCompanies.size === companies.length) {
      setSelectedCompanies(new Set());
    } else {
      setSelectedCompanies(new Set(companies.map(c => c.id)));
    }
  };

  const handleCreateUser = async () => {
    try {
      setError(null);
      await adminApi.createUser(userFormData);
      setShowCreateUserModal(false);
      setUserFormData({
        email: '',
        full_name: '',
        role: 'buyer',
        company_id: '',
        send_invitation: true,
      });
      await loadUsers();
    } catch (err) {
      setError('Failed to create user');
      console.error('Error creating user:', err);
    }
  };

  const handleEditUser = async () => {
    if (!selectedUser) return;

    try {
      setError(null);
      const updateData: UserUpdate = {
        full_name: userFormData.full_name,
        role: userFormData.role,
        is_active: selectedUser.is_active,
      };

      await adminApi.updateUser(selectedUser.id, updateData);
      setShowEditUserModal(false);
      setSelectedUser(null);
      await loadUsers();
    } catch (err) {
      setError('Failed to update user');
      console.error('Error updating user:', err);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;

    try {
      setError(null);
      await adminApi.deleteUser(userId);
      await loadUsers();
    } catch (err) {
      setError('Failed to delete user');
      console.error('Error deleting user:', err);
    }
  };

  const handleUserBulkOperation = async (operation: UserBulkOperation['operation']) => {
    if (selectedUsers.size === 0) return;

    const reason = prompt(`Please provide a reason for ${operation}:`);
    if (!reason) return;

    try {
      setError(null);
      const bulkOp: UserBulkOperation = {
        operation,
        user_ids: Array.from(selectedUsers),
        reason,
        notify_users: true,
      };

      await adminApi.bulkUserOperation(bulkOp);
      setSelectedUsers(new Set());
      await loadUsers();
    } catch (err) {
      setError(`Failed to ${operation} users`);
      console.error(`Error with bulk ${operation}:`, err);
    }
  };

  const handleCompanyBulkOperation = async (operation: CompanyBulkOperation['operation']) => {
    if (selectedCompanies.size === 0) return;

    const reason = prompt(`Please provide a reason for ${operation}:`);
    if (!reason) return;

    try {
      setError(null);
      const bulkOp: CompanyBulkOperation = {
        operation,
        company_ids: Array.from(selectedCompanies),
        reason,
        notify_admins: true,
      };

      await adminApi.bulkCompanyOperation(bulkOp);
      setSelectedCompanies(new Set());
      await loadCompanies();
    } catch (err) {
      setError(`Failed to ${operation} companies`);
      console.error(`Error with bulk ${operation}:`, err);
    }
  };

  const openEditUserModal = (user: AdminUser) => {
    setSelectedUser(user);
    setUserFormData({
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      company_id: user.company_id,
      send_invitation: false,
    });
    setShowEditUserModal(true);
  };

  const openEditCompanyModal = (company: Company) => {
    setSelectedCompany(company);
    setShowEditCompanyModal(true);
  };

  const getRoleBadge = (role: UserRole) => {
    const styles = {
      admin: 'bg-red-100 text-red-800',
      buyer: 'bg-blue-100 text-blue-800',
      seller: 'bg-green-100 text-green-800',
      viewer: 'bg-gray-100 text-gray-800',
      support: 'bg-purple-100 text-purple-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[role]}`}>
        {role}
      </span>
    );
  };

  const getCompanyTypeBadge = (type: CompanyType) => {
    const styles = {
      brand: 'bg-purple-100 text-purple-800',
      processor: 'bg-blue-100 text-blue-800',
      originator: 'bg-green-100 text-green-800',
      trader: 'bg-yellow-100 text-yellow-800',
      plantation: 'bg-emerald-100 text-emerald-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[type]}`}>
        {type}
      </span>
    );
  };

  const getSubscriptionBadge = (tier: SubscriptionTier) => {
    const styles = {
      free: 'bg-gray-100 text-gray-800',
      basic: 'bg-blue-100 text-blue-800',
      premium: 'bg-purple-100 text-purple-800',
      enterprise: 'bg-yellow-100 text-yellow-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[tier]}`}>
        {tier}
      </span>
    );
  };

  const getComplianceBadge = (status: ComplianceStatus) => {
    const styles = {
      compliant: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      non_compliant: 'bg-red-100 text-red-800',
      pending_review: 'bg-blue-100 text-blue-800',
    };

    const icons = {
      compliant: CheckCircleIcon,
      warning: ExclamationTriangleIcon,
      non_compliant: XCircleIcon,
      pending_review: ClockIcon,
    };

    const Icon = icons[status];

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status.replace('_', ' ')}
      </span>
    );
  };

  const getStatusIcon = (isActive: boolean) => {
    return isActive ? (
      <CheckCircleIcon className="h-5 w-5 text-green-500" />
    ) : (
      <XCircleIcon className="h-5 w-5 text-red-500" />
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User & Company Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage users, companies, roles, and account status
          </p>
        </div>
        <button
          onClick={() => setShowCreateUserModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Add User
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('users')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <UserIcon className="h-5 w-5 inline mr-2" />
            Users ({totalUsers})
          </button>
          <button
            onClick={() => setActiveTab('companies')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'companies'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <BuildingOfficeIcon className="h-5 w-5 inline mr-2" />
            Companies ({totalCompanies})
          </button>
        </nav>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          {/* User Filters */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <div className="relative">
                  <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search users..."
                    value={userFilters.search || ''}
                    onChange={(e) => handleUserFilterChange({ search: e.target.value })}
                    className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Role
                </label>
                <select
                  value={userFilters.role || ''}
                  onChange={(e) => handleUserFilterChange({ role: e.target.value as UserRole || undefined })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">All Roles</option>
                  <option value="admin">Admin</option>
                  <option value="buyer">Buyer</option>
                  <option value="seller">Seller</option>
                  <option value="viewer">Viewer</option>
                  <option value="support">Support</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={userFilters.is_active?.toString() || ''}
                  onChange={(e) => handleUserFilterChange({ 
                    is_active: e.target.value ? e.target.value === 'true' : undefined 
                  })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="true">Active</option>
                  <option value="false">Inactive</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  2FA Status
                </label>
                <select
                  value={userFilters.has_two_factor?.toString() || ''}
                  onChange={(e) => handleUserFilterChange({ 
                    has_two_factor: e.target.value ? e.target.value === 'true' : undefined 
                  })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">All Users</option>
                  <option value="true">2FA Enabled</option>
                  <option value="false">2FA Disabled</option>
                </select>
              </div>
            </div>
          </div>

          {/* User Bulk Actions */}
          {selectedUsers.size > 0 && (
            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">
                  {selectedUsers.size} user{selectedUsers.size !== 1 ? 's' : ''} selected
                </span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleUserBulkOperation('activate')}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Activate
                  </button>
                  <button
                    onClick={() => handleUserBulkOperation('deactivate')}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <XCircleIcon className="h-4 w-4 mr-1" />
                    Deactivate
                  </button>
                  <button
                    onClick={() => handleUserBulkOperation('reset_password')}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <ShieldCheckIcon className="h-4 w-4 mr-1" />
                    Reset Password
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Users Table */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Users ({totalUsers})
              </h3>
            </div>

            {loading ? (
              <div className="p-8 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <p className="mt-2 text-sm text-gray-500">Loading users...</p>
              </div>
            ) : users.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500">No users found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left">
                        <input
                          type="checkbox"
                          checked={selectedUsers.size === users.length && users.length > 0}
                          onChange={handleSelectAllUsers}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Company
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Login
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <input
                            type="checkbox"
                            checked={selectedUsers.has(user.id)}
                            onChange={() => handleSelectUser(user.id)}
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                <UserIcon className="h-6 w-6 text-gray-600" />
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {user.full_name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {user.email}
                              </div>
                              {user.two_factor_enabled && (
                                <div className="mt-1">
                                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                    <ShieldCheckIcon className="h-3 w-3 mr-1" />
                                    2FA
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {user.company_name}
                        </td>
                        <td className="px-6 py-4">
                          {getRoleBadge(user.role)}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            {getStatusIcon(user.is_active)}
                            <span className="ml-2 text-sm text-gray-900">
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {user.last_login ? formatTimeAgo(user.last_login) : 'Never'}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => openEditUserModal(user)}
                              className="text-primary-400 hover:text-primary-600"
                              title="Edit User"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(user.id)}
                              className="text-red-400 hover:text-red-600"
                              title="Delete User"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Companies Tab */}
      {activeTab === 'companies' && (
        <div className="space-y-6">
          {/* Company Filters */}
          <div className="bg-white shadow rounded-lg p-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Search
                </label>
                <div className="relative">
                  <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search companies..."
                    value={companyFilters.search || ''}
                    onChange={(e) => handleCompanyFilterChange({ search: e.target.value })}
                    className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Type
                </label>
                <select
                  value={companyFilters.company_type || ''}
                  onChange={(e) => handleCompanyFilterChange({ company_type: e.target.value as CompanyType || undefined })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">All Types</option>
                  <option value="brand">Brand</option>
                  <option value="processor">Processor</option>
                  <option value="originator">Originator</option>
                  <option value="trader">Trader</option>
                  <option value="plantation">Plantation</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subscription
                </label>
                <select
                  value={companyFilters.subscription_tier || ''}
                  onChange={(e) => handleCompanyFilterChange({ subscription_tier: e.target.value as SubscriptionTier || undefined })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">All Tiers</option>
                  <option value="free">Free</option>
                  <option value="basic">Basic</option>
                  <option value="premium">Premium</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Compliance
                </label>
                <select
                  value={companyFilters.compliance_status || ''}
                  onChange={(e) => handleCompanyFilterChange({ compliance_status: e.target.value as ComplianceStatus || undefined })}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="compliant">Compliant</option>
                  <option value="warning">Warning</option>
                  <option value="non_compliant">Non-Compliant</option>
                  <option value="pending_review">Pending Review</option>
                </select>
              </div>
            </div>
          </div>

          {/* Company Bulk Actions */}
          {selectedCompanies.size > 0 && (
            <div className="bg-white shadow rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">
                  {selectedCompanies.size} compan{selectedCompanies.size !== 1 ? 'ies' : 'y'} selected
                </span>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleCompanyBulkOperation('activate')}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Activate
                  </button>
                  <button
                    onClick={() => handleCompanyBulkOperation('deactivate')}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <XCircleIcon className="h-4 w-4 mr-1" />
                    Deactivate
                  </button>
                  <button
                    onClick={() => handleCompanyBulkOperation('compliance_review')}
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                  >
                    <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                    Review Compliance
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Companies Table */}
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Companies ({totalCompanies})
              </h3>
            </div>

            {loading ? (
              <div className="p-8 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <p className="mt-2 text-sm text-gray-500">Loading companies...</p>
              </div>
            ) : companies.length === 0 ? (
              <div className="p-8 text-center">
                <p className="text-gray-500">No companies found</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left">
                        <input
                          type="checkbox"
                          checked={selectedCompanies.size === companies.length && companies.length > 0}
                          onChange={handleSelectAllCompanies}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Company
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Subscription
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Compliance
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Activity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {companies.map((company) => (
                      <tr key={company.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <input
                            type="checkbox"
                            checked={selectedCompanies.has(company.id)}
                            onChange={() => handleSelectCompany(company.id)}
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10">
                              <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                <BuildingOfficeIcon className="h-6 w-6 text-gray-600" />
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900">
                                {company.name}
                              </div>
                              <div className="text-sm text-gray-500 flex items-center">
                                <EnvelopeIcon className="h-4 w-4 mr-1" />
                                {company.email}
                              </div>
                              {company.website && (
                                <div className="text-sm text-gray-500 flex items-center">
                                  <GlobeAltIcon className="h-4 w-4 mr-1" />
                                  <a href={company.website} target="_blank" rel="noopener noreferrer" className="hover:text-primary-600">
                                    {company.website}
                                  </a>
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {getCompanyTypeBadge(company.company_type)}
                        </td>
                        <td className="px-6 py-4">
                          {getSubscriptionBadge(company.subscription_tier)}
                        </td>
                        <td className="px-6 py-4">
                          {getComplianceBadge(company.compliance_status)}
                          {company.transparency_score && (
                            <div className="mt-1 text-xs text-gray-500">
                              Transparency: {company.transparency_score}%
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          <div>{company.user_count} users</div>
                          <div className="text-xs text-gray-500">{company.po_count} POs</div>
                          {company.last_activity && (
                            <div className="text-xs text-gray-500">
                              Last: {formatTimeAgo(company.last_activity)}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => openEditCompanyModal(company)}
                              className="text-primary-400 hover:text-primary-600"
                              title="Edit Company"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUserModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowCreateUserModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Create New User
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Email Address *
                        </label>
                        <input
                          type="email"
                          value={userFormData.email}
                          onChange={(e) => setUserFormData(prev => ({ ...prev, email: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="user@company.com"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Full Name *
                        </label>
                        <input
                          type="text"
                          value={userFormData.full_name}
                          onChange={(e) => setUserFormData(prev => ({ ...prev, full_name: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          placeholder="John Smith"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Role *
                          </label>
                          <select
                            value={userFormData.role}
                            onChange={(e) => setUserFormData(prev => ({ ...prev, role: e.target.value as UserRole }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          >
                            <option value="buyer">Buyer</option>
                            <option value="seller">Seller</option>
                            <option value="viewer">Viewer</option>
                            <option value="admin">Admin</option>
                            <option value="support">Support</option>
                          </select>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Company *
                          </label>
                          <select
                            value={userFormData.company_id}
                            onChange={(e) => setUserFormData(prev => ({ ...prev, company_id: e.target.value }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          >
                            <option value="">Select Company</option>
                            {companies.map((company) => (
                              <option key={company.id} value={company.id}>
                                {company.name}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={userFormData.send_invitation}
                            onChange={(e) => setUserFormData(prev => ({ ...prev, send_invitation: e.target.checked }))}
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">
                            Send invitation email to user
                          </span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleCreateUser}
                  disabled={!userFormData.email || !userFormData.full_name || !userFormData.company_id}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create User
                </button>
                <button
                  onClick={() => setShowCreateUserModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditUserModal && selectedUser && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowEditUserModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Edit User: {selectedUser.full_name}
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Email Address
                        </label>
                        <input
                          type="email"
                          value={userFormData.email}
                          disabled
                          className="block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
                        />
                        <p className="mt-1 text-xs text-gray-500">Email cannot be changed</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Full Name *
                        </label>
                        <input
                          type="text"
                          value={userFormData.full_name}
                          onChange={(e) => setUserFormData(prev => ({ ...prev, full_name: e.target.value }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Role *
                        </label>
                        <select
                          value={userFormData.role}
                          onChange={(e) => setUserFormData(prev => ({ ...prev, role: e.target.value as UserRole }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        >
                          <option value="buyer">Buyer</option>
                          <option value="seller">Seller</option>
                          <option value="viewer">Viewer</option>
                          <option value="admin">Admin</option>
                          <option value="support">Support</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Company
                        </label>
                        <input
                          type="text"
                          value={selectedUser.company_name}
                          disabled
                          className="block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
                        />
                        <p className="mt-1 text-xs text-gray-500">Company cannot be changed</p>
                      </div>

                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Account Status</h4>
                        <div className="space-y-2 text-sm text-gray-600">
                          <div className="flex justify-between">
                            <span>Status:</span>
                            <span className={selectedUser.is_active ? 'text-green-600' : 'text-red-600'}>
                              {selectedUser.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>2FA:</span>
                            <span className={selectedUser.two_factor_enabled ? 'text-green-600' : 'text-gray-600'}>
                              {selectedUser.two_factor_enabled ? 'Enabled' : 'Disabled'}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Last Login:</span>
                            <span>{selectedUser.last_login ? formatTimeAgo(selectedUser.last_login) : 'Never'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleEditUser}
                  disabled={!userFormData.full_name}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Update User
                </button>
                <button
                  onClick={() => setShowEditUserModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
