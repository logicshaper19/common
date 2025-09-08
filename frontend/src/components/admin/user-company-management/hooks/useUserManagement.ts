/**
 * Custom hook for user management operations
 */
import { useState, useCallback, useEffect } from 'react';
import { adminApi } from '../../../../api/admin';
import {
  AdminUser,
  UserFilter,
  UserCreate,
  UserUpdate,
  UserBulkOperation,
} from '../../../../types/admin';

export interface UseUserManagementReturn {
  // State
  users: AdminUser[];
  loading: boolean;
  error: string | null;
  selectedUsers: Set<string>;
  totalPages: number;
  totalUsers: number;
  filters: UserFilter;
  
  // Actions
  loadUsers: () => Promise<void>;
  handleFilterChange: (newFilters: Partial<UserFilter>) => void;
  handlePageChange: (page: number) => void;
  handleSelectUser: (userId: string) => void;
  handleSelectAllUsers: () => void;
  createUser: (userData: UserCreate) => Promise<void>;
  updateUser: (userId: string, userData: UserUpdate) => Promise<void>;
  deleteUser: (userId: string) => Promise<void>;
  bulkOperation: (operation: UserBulkOperation['operation']) => Promise<void>;
  clearSelection: () => void;
  clearError: () => void;
}

export function useUserManagement(): UseUserManagementReturn {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const [filters, setFilters] = useState<UserFilter>({
    page: 1,
    per_page: 20,
  });

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getUsers(filters);
      setUsers(response.data);
      setTotalPages(Math.ceil(response.total / filters.per_page));
      setTotalUsers(response.total);
    } catch (err) {
      setError('Failed to load users');
      console.error('Error loading users:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const handleFilterChange = useCallback((newFilters: Partial<UserFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  }, []);

  const handlePageChange = useCallback((page: number) => {
    setFilters(prev => ({ ...prev, page }));
  }, []);

  const handleSelectUser = useCallback((userId: string) => {
    setSelectedUsers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(userId)) {
        newSet.delete(userId);
      } else {
        newSet.add(userId);
      }
      return newSet;
    });
  }, []);

  const handleSelectAllUsers = useCallback(() => {
    if (selectedUsers.size === users.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(users.map(user => user.id)));
    }
  }, [selectedUsers.size, users]);

  const createUser = useCallback(async (userData: UserCreate) => {
    try {
      setError(null);
      await adminApi.createUser(userData);
      await loadUsers(); // Reload users after creation
    } catch (err) {
      setError('Failed to create user');
      console.error('Error creating user:', err);
      throw err;
    }
  }, [loadUsers]);

  const updateUser = useCallback(async (userId: string, userData: UserUpdate) => {
    try {
      setError(null);
      await adminApi.updateUser(userId, userData);
      await loadUsers(); // Reload users after update
    } catch (err) {
      setError('Failed to update user');
      console.error('Error updating user:', err);
      throw err;
    }
  }, [loadUsers]);

  const deleteUser = useCallback(async (userId: string) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;

    try {
      setError(null);
      await adminApi.deleteUser(userId);
      await loadUsers(); // Reload users after deletion
    } catch (err) {
      setError('Failed to delete user');
      console.error('Error deleting user:', err);
    }
  }, [loadUsers]);

  const bulkOperation = useCallback(async (operation: UserBulkOperation['operation']) => {
    if (selectedUsers.size === 0) return;

    const reason = prompt(`Please provide a reason for ${operation}:`);
    if (!reason) return;

    try {
      setError(null);
      await adminApi.bulkUserOperation({
        operation,
        user_ids: Array.from(selectedUsers),
        reason,
      });
      setSelectedUsers(new Set()); // Clear selection
      await loadUsers(); // Reload users
    } catch (err) {
      setError(`Failed to ${operation} users`);
      console.error(`Error performing bulk ${operation}:`, err);
    }
  }, [selectedUsers, loadUsers]);

  const clearSelection = useCallback(() => {
    setSelectedUsers(new Set());
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load users when filters change
  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  return {
    // State
    users,
    loading,
    error,
    selectedUsers,
    totalPages,
    totalUsers,
    filters,
    
    // Actions
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
  };
}
