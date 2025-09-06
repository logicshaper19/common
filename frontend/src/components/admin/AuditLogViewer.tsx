/**
 * Audit Log Viewer with Advanced Filtering
 * Comprehensive audit log interface with security monitoring and export capabilities
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  ShieldExclamationIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  UserIcon,
  BuildingOfficeIcon,
  ComputerDesktopIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import { adminApi } from '../../api/admin';
import {
  AuditLogEntry,
  AuditFilter,
  AuditExportRequest,
  AuditAction,
  ResourceType,
  RiskLevel,
} from '../../types/admin';
import { formatTimeAgo } from '../../lib/utils';

interface AuditLogViewerProps {
  className?: string;
}

export function AuditLogViewer({ className = '' }: AuditLogViewerProps) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Filters and pagination
  const [filters, setFilters] = useState<AuditFilter>({
    page: 1,
    per_page: 50,
  });
  const [totalPages, setTotalPages] = useState(1);
  const [totalLogs, setTotalLogs] = useState(0);

  // Export form state
  const [exportData, setExportData] = useState<AuditExportRequest>({
    filters: filters,
    format: 'csv',
    include_details: true,
    date_range: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
      end: new Date().toISOString().split('T')[0], // today
    },
  });

  const loadLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.getAuditLogs(filters);
      setLogs(response.data);
      setTotalPages(Math.ceil(response.total / filters.per_page));
      setTotalLogs(response.total);
    } catch (err) {
      setError('Failed to load audit logs');
      console.error('Error loading audit logs:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  const handleFilterChange = (newFilters: Partial<AuditFilter>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleExport = async () => {
    try {
      setError(null);
      const exportRequest: AuditExportRequest = {
        ...exportData,
        filters: {
          ...filters,
          start_date: exportData.date_range.start,
          end_date: exportData.date_range.end,
        },
      };

      const response = await adminApi.exportAuditLogs(exportRequest);
      
      // Create download link
      const link = document.createElement('a');
      link.href = response.download_url;
      link.download = `audit_logs_${new Date().toISOString().split('T')[0]}.${exportData.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      setShowExportModal(false);
    } catch (err) {
      setError('Failed to export audit logs');
      console.error('Error exporting logs:', err);
    }
  };

  const openDetailsModal = (log: AuditLogEntry) => {
    setSelectedLog(log);
    setShowDetailsModal(true);
  };

  const getRiskLevelBadge = (riskLevel: RiskLevel) => {
    const styles = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800',
    };

    const icons = {
      low: CheckCircleIcon,
      medium: ExclamationTriangleIcon,
      high: ExclamationTriangleIcon,
      critical: ShieldExclamationIcon,
    };

    const Icon = icons[riskLevel];

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[riskLevel]}`}>
        <Icon className="h-3 w-3 mr-1" />
        {riskLevel}
      </span>
    );
  };

  const getActionBadge = (action: AuditAction) => {
    const styles = {
      create: 'bg-green-100 text-green-800',
      read: 'bg-blue-100 text-blue-800',
      update: 'bg-yellow-100 text-yellow-800',
      delete: 'bg-red-100 text-red-800',
      login: 'bg-purple-100 text-purple-800',
      logout: 'bg-gray-100 text-gray-800',
      password_reset: 'bg-orange-100 text-orange-800',
      password_change: 'bg-orange-100 text-orange-800',
      invite_user: 'bg-blue-100 text-blue-800',
      activate_user: 'bg-green-100 text-green-800',
      deactivate_user: 'bg-red-100 text-red-800',
      export_data: 'bg-purple-100 text-purple-800',
      import_data: 'bg-purple-100 text-purple-800',
      bulk_operation: 'bg-yellow-100 text-yellow-800',
      permission_change: 'bg-orange-100 text-orange-800',
      role_change: 'bg-orange-100 text-orange-800',
      company_change: 'bg-blue-100 text-blue-800',
      api_access: 'bg-gray-100 text-gray-800',
      file_upload: 'bg-green-100 text-green-800',
      file_download: 'bg-blue-100 text-blue-800',
      system_config: 'bg-red-100 text-red-800',
      backup_create: 'bg-green-100 text-green-800',
      backup_restore: 'bg-orange-100 text-orange-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[action] || 'bg-gray-100 text-gray-800'}`}>
        {action.replace('_', ' ')}
      </span>
    );
  };

  const getResourceTypeBadge = (resourceType: ResourceType) => {
    const styles = {
      user: 'bg-blue-100 text-blue-800',
      company: 'bg-purple-100 text-purple-800',
      product: 'bg-green-100 text-green-800',
      purchase_order: 'bg-yellow-100 text-yellow-800',
      notification: 'bg-indigo-100 text-indigo-800',
      support_ticket: 'bg-orange-100 text-orange-800',
      audit_log: 'bg-gray-100 text-gray-800',
      system_config: 'bg-red-100 text-red-800',
      backup: 'bg-emerald-100 text-emerald-800',
      api_key: 'bg-pink-100 text-pink-800',
      session: 'bg-cyan-100 text-cyan-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[resourceType] || 'bg-gray-100 text-gray-800'}`}>
        {resourceType.replace('_', ' ')}
      </span>
    );
  };

  const getSuccessIcon = (success: boolean) => {
    return success ? (
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
          <h1 className="text-2xl font-bold text-gray-900">Audit Log Viewer</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor system activities and security events
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <FunnelIcon className="h-4 w-4 mr-2" />
            Filters
          </button>
          <button
            onClick={() => setShowExportModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
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

      {/* Filters */}
      {showFilters && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search
              </label>
              <div className="relative">
                <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search logs..."
                  value={filters.search || ''}
                  onChange={(e) => handleFilterChange({ search: e.target.value })}
                  className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Action
              </label>
              <select
                value={filters.action || ''}
                onChange={(e) => handleFilterChange({ action: e.target.value as AuditAction || undefined })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="">All Actions</option>
                <option value="create">Create</option>
                <option value="read">Read</option>
                <option value="update">Update</option>
                <option value="delete">Delete</option>
                <option value="login">Login</option>
                <option value="logout">Logout</option>
                <option value="export_data">Export Data</option>
                <option value="bulk_operation">Bulk Operation</option>
                <option value="system_config">System Config</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Resource Type
              </label>
              <select
                value={filters.resource_type || ''}
                onChange={(e) => handleFilterChange({ resource_type: e.target.value as ResourceType || undefined })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="">All Resources</option>
                <option value="user">User</option>
                <option value="company">Company</option>
                <option value="product">Product</option>
                <option value="purchase_order">Purchase Order</option>
                <option value="support_ticket">Support Ticket</option>
                <option value="system_config">System Config</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Risk Level
              </label>
              <select
                value={filters.risk_level || ''}
                onChange={(e) => handleFilterChange({ risk_level: e.target.value as RiskLevel || undefined })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="">All Risk Levels</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={filters.start_date || ''}
                onChange={(e) => handleFilterChange({ start_date: e.target.value })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={filters.end_date || ''}
                onChange={(e) => handleFilterChange({ end_date: e.target.value })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Success Status
              </label>
              <select
                value={filters.success?.toString() || ''}
                onChange={(e) => handleFilterChange({ 
                  success: e.target.value ? e.target.value === 'true' : undefined 
                })}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
              >
                <option value="">All Events</option>
                <option value="true">Successful</option>
                <option value="false">Failed</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Audit Logs ({totalLogs})
          </h3>
        </div>

        {loading ? (
          <div className="p-8 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="mt-2 text-sm text-gray-500">Loading audit logs...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">No audit logs found</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Resource
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Risk Level
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div>{formatTimeAgo(log.timestamp)}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-8 w-8">
                            <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                              <UserIcon className="h-5 w-5 text-gray-600" />
                            </div>
                          </div>
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">
                              {log.user_name}
                            </div>
                            <div className="text-sm text-gray-500 flex items-center">
                              <BuildingOfficeIcon className="h-3 w-3 mr-1" />
                              {log.company_name}
                            </div>
                            <div className="text-xs text-gray-400 flex items-center">
                              <GlobeAltIcon className="h-3 w-3 mr-1" />
                              {log.ip_address}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getActionBadge(log.action)}
                        {log.duration_ms && (
                          <div className="mt-1 text-xs text-gray-500">
                            {log.duration_ms}ms
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          {getResourceTypeBadge(log.resource_type)}
                          <div className="mt-1 text-sm text-gray-900">
                            {log.resource_name || log.resource_id}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getRiskLevelBadge(log.risk_level)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center">
                          {getSuccessIcon(log.success)}
                          <span className="ml-2 text-sm text-gray-900">
                            {log.success ? 'Success' : 'Failed'}
                          </span>
                        </div>
                        {!log.success && log.error_message && (
                          <div className="mt-1 text-xs text-red-600">
                            {log.error_message}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => openDetailsModal(log)}
                          className="text-primary-400 hover:text-primary-600"
                          title="View Details"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1 flex justify-between sm:hidden">
                    <button
                      onClick={() => handlePageChange(filters.page - 1)}
                      disabled={filters.page <= 1}
                      className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => handlePageChange(filters.page + 1)}
                      disabled={filters.page >= totalPages}
                      className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                  <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                    <div>
                      <p className="text-sm text-gray-700">
                        Showing{' '}
                        <span className="font-medium">
                          {(filters.page - 1) * filters.per_page + 1}
                        </span>{' '}
                        to{' '}
                        <span className="font-medium">
                          {Math.min(filters.page * filters.per_page, totalLogs)}
                        </span>{' '}
                        of{' '}
                        <span className="font-medium">{totalLogs}</span>{' '}
                        results
                      </p>
                    </div>
                    <div>
                      <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <button
                          onClick={() => handlePageChange(filters.page - 1)}
                          disabled={filters.page <= 1}
                          className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Previous
                        </button>
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          const page = i + 1;
                          return (
                            <button
                              key={page}
                              onClick={() => handlePageChange(page)}
                              className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                page === filters.page
                                  ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                                  : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                              }`}
                            >
                              {page}
                            </button>
                          );
                        })}
                        <button
                          onClick={() => handlePageChange(filters.page + 1)}
                          disabled={filters.page >= totalPages}
                          className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Next
                        </button>
                      </nav>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowExportModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Export Audit Logs
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Export Format
                        </label>
                        <select
                          value={exportData.format}
                          onChange={(e) => setExportData(prev => ({ ...prev, format: e.target.value as 'csv' | 'json' | 'xlsx' }))}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                        >
                          <option value="csv">CSV</option>
                          <option value="json">JSON</option>
                          <option value="xlsx">Excel (XLSX)</option>
                        </select>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Start Date
                          </label>
                          <input
                            type="date"
                            value={exportData.date_range.start}
                            onChange={(e) => setExportData(prev => ({
                              ...prev,
                              date_range: { ...prev.date_range, start: e.target.value }
                            }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            End Date
                          </label>
                          <input
                            type="date"
                            value={exportData.date_range.end}
                            onChange={(e) => setExportData(prev => ({
                              ...prev,
                              date_range: { ...prev.date_range, end: e.target.value }
                            }))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={exportData.include_details}
                            onChange={(e) => setExportData(prev => ({ ...prev, include_details: e.target.checked }))}
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                          <span className="ml-2 text-sm text-gray-700">
                            Include detailed metadata and changes
                          </span>
                        </label>
                      </div>

                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                        <div className="flex">
                          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                          <div className="ml-3">
                            <h4 className="text-sm font-medium text-yellow-800">Export Notice</h4>
                            <p className="mt-1 text-sm text-yellow-700">
                              Audit log exports contain sensitive information. Ensure proper handling and storage of exported data.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleExport}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Export Logs
                </button>
                <button
                  onClick={() => setShowExportModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Details Modal */}
      {showDetailsModal && selectedLog && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowDetailsModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <div className="flex justify-between items-start mb-6">
                      <div>
                        <h3 className="text-lg leading-6 font-medium text-gray-900">
                          Audit Log Details
                        </h3>
                        <p className="text-sm text-gray-500">#{selectedLog.id}</p>
                      </div>
                      <div className="flex space-x-2">
                        {getRiskLevelBadge(selectedLog.risk_level)}
                        {getActionBadge(selectedLog.action)}
                        {getSuccessIcon(selectedLog.success)}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Basic Information */}
                      <div className="space-y-4">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">Event Information</h4>
                          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-500">Timestamp:</span>
                              <span className="text-gray-900">{new Date(selectedLog.timestamp).toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Action:</span>
                              <span className="text-gray-900">{selectedLog.action}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Resource:</span>
                              <span className="text-gray-900">{selectedLog.resource_type}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Resource ID:</span>
                              <span className="text-gray-900 font-mono text-xs">{selectedLog.resource_id}</span>
                            </div>
                            {selectedLog.resource_name && (
                              <div className="flex justify-between">
                                <span className="text-gray-500">Resource Name:</span>
                                <span className="text-gray-900">{selectedLog.resource_name}</span>
                              </div>
                            )}
                            <div className="flex justify-between">
                              <span className="text-gray-500">Success:</span>
                              <span className={selectedLog.success ? 'text-green-600' : 'text-red-600'}>
                                {selectedLog.success ? 'Yes' : 'No'}
                              </span>
                            </div>
                            {selectedLog.duration_ms && (
                              <div className="flex justify-between">
                                <span className="text-gray-500">Duration:</span>
                                <span className="text-gray-900">{selectedLog.duration_ms}ms</span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">User Information</h4>
                          <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-500">User:</span>
                              <span className="text-gray-900">{selectedLog.user_name}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Email:</span>
                              <span className="text-gray-900">{selectedLog.user_email}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Company:</span>
                              <span className="text-gray-900">{selectedLog.company_name}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">IP Address:</span>
                              <span className="text-gray-900 font-mono text-xs">{selectedLog.ip_address}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">Session ID:</span>
                              <span className="text-gray-900 font-mono text-xs">{selectedLog.session_id}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Detailed Information */}
                      <div className="space-y-4">
                        {/* Error Message */}
                        {!selectedLog.success && selectedLog.error_message && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Error Details</h4>
                            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                              <p className="text-sm text-red-700">{selectedLog.error_message}</p>
                            </div>
                          </div>
                        )}

                        {/* Changes */}
                        {selectedLog.details.changes && selectedLog.details.changes.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Changes Made</h4>
                            <div className="bg-gray-50 rounded-lg p-4">
                              <div className="space-y-3">
                                {selectedLog.details.changes.map((change, index) => (
                                  <div key={index} className="border-l-4 border-blue-400 pl-3">
                                    <div className="text-sm font-medium text-gray-900">{change.field}</div>
                                    <div className="text-xs text-gray-600 mt-1">
                                      <div className="flex items-center">
                                        <span className="text-red-600">- {JSON.stringify(change.old_value)}</span>
                                      </div>
                                      <div className="flex items-center">
                                        <span className="text-green-600">+ {JSON.stringify(change.new_value)}</span>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Metadata */}
                        {selectedLog.details.metadata && Object.keys(selectedLog.details.metadata).length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Additional Metadata</h4>
                            <div className="bg-gray-50 rounded-lg p-4">
                              <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                                {JSON.stringify(selectedLog.details.metadata, null, 2)}
                              </pre>
                            </div>
                          </div>
                        )}

                        {/* User Agent */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-2">Browser Information</h4>
                          <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-xs text-gray-700 break-all">{selectedLog.user_agent}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:w-auto sm:text-sm"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
