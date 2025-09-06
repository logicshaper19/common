/**
 * System Configuration and Monitoring Dashboard
 * Comprehensive system admin interface for configuration and health monitoring
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  CogIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ServerIcon,
  DatabaseIcon,
  CloudIcon,
  ShieldCheckIcon,
  ArrowPathIcon,
  BellIcon,
  DocumentArrowDownIcon,
  PlayIcon,
  StopIcon,
} from '@heroicons/react/24/outline';
import { adminApi } from '../../api/admin';
import {
  SystemConfig,
  SystemHealth,
  SystemAlert,
  BackupStatus,
  ConfigCategory,
  AlertSeverity,
} from '../../types/admin';
import { formatTimeAgo } from '../../lib/utils';

interface SystemMonitoringProps {
  className?: string;
}

export function SystemMonitoring({ className = '' }: SystemMonitoringProps) {
  const [activeTab, setActiveTab] = useState<'health' | 'config' | 'alerts' | 'backups'>('health');
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [systemConfigs, setSystemConfigs] = useState<SystemConfig[]>([]);
  const [systemAlerts, setSystemAlerts] = useState<SystemAlert[]>([]);
  const [backupStatus, setBackupStatus] = useState<BackupStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<SystemConfig | null>(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configValue, setConfigValue] = useState<any>('');

  const loadSystemHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const health = await adminApi.getSystemHealth();
      setSystemHealth(health);
    } catch (err) {
      setError('Failed to load system health');
      console.error('Error loading system health:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSystemConfigs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const configs = await adminApi.getSystemConfigs();
      setSystemConfigs(configs);
    } catch (err) {
      setError('Failed to load system configurations');
      console.error('Error loading configs:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSystemAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const alerts = await adminApi.getSystemAlerts();
      setSystemAlerts(alerts);
    } catch (err) {
      setError('Failed to load system alerts');
      console.error('Error loading alerts:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBackupStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const backups = await adminApi.getBackupStatus();
      setBackupStatus(backups);
    } catch (err) {
      setError('Failed to load backup status');
      console.error('Error loading backups:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    switch (activeTab) {
      case 'health':
        loadSystemHealth();
        break;
      case 'config':
        loadSystemConfigs();
        break;
      case 'alerts':
        loadSystemAlerts();
        break;
      case 'backups':
        loadBackupStatus();
        break;
    }
  }, [activeTab, loadSystemHealth, loadSystemConfigs, loadSystemAlerts, loadBackupStatus]);

  const handleUpdateConfig = async () => {
    if (!selectedConfig) return;

    try {
      setError(null);
      await adminApi.updateSystemConfig(selectedConfig.id, configValue);
      setShowConfigModal(false);
      setSelectedConfig(null);
      setConfigValue('');
      await loadSystemConfigs();
    } catch (err) {
      setError('Failed to update configuration');
      console.error('Error updating config:', err);
    }
  };

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      setError(null);
      await adminApi.acknowledgeAlert(alertId);
      await loadSystemAlerts();
    } catch (err) {
      setError('Failed to acknowledge alert');
      console.error('Error acknowledging alert:', err);
    }
  };

  const handleCreateBackup = async (type: 'full' | 'incremental') => {
    try {
      setError(null);
      await adminApi.createBackup(type);
      await loadBackupStatus();
    } catch (err) {
      setError('Failed to create backup');
      console.error('Error creating backup:', err);
    }
  };

  const openConfigModal = (config: SystemConfig) => {
    setSelectedConfig(config);
    setConfigValue(config.value);
    setShowConfigModal(true);
  };

  const getHealthStatusBadge = (status: SystemHealth['status']) => {
    const styles = {
      healthy: 'bg-green-100 text-green-800',
      warning: 'bg-yellow-100 text-yellow-800',
      critical: 'bg-red-100 text-red-800',
      down: 'bg-gray-100 text-gray-800',
    };

    const icons = {
      healthy: CheckCircleIcon,
      warning: ExclamationTriangleIcon,
      critical: XCircleIcon,
      down: XCircleIcon,
    };

    const Icon = icons[status];

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${styles[status]}`}>
        <Icon className="h-4 w-4 mr-2" />
        {status}
      </span>
    );
  };

  const getServiceStatusIcon = (status: string) => {
    const icons = {
      healthy: CheckCircleIcon,
      warning: ExclamationTriangleIcon,
      critical: XCircleIcon,
      down: XCircleIcon,
    };

    const colors = {
      healthy: 'text-green-500',
      warning: 'text-yellow-500',
      critical: 'text-red-500',
      down: 'text-gray-500',
    };

    const Icon = icons[status as keyof typeof icons] || XCircleIcon;
    const color = colors[status as keyof typeof colors] || 'text-gray-500';

    return <Icon className={`h-5 w-5 ${color}`} />;
  };

  const getAlertSeverityBadge = (severity: AlertSeverity) => {
    const styles = {
      info: 'bg-blue-100 text-blue-800',
      warning: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      critical: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[severity]}`}>
        {severity}
      </span>
    );
  };

  const getBackupStatusBadge = (status: BackupStatus['status']) => {
    const styles = {
      running: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      scheduled: 'bg-gray-100 text-gray-800',
    };

    const icons = {
      running: ArrowPathIcon,
      completed: CheckCircleIcon,
      failed: XCircleIcon,
      scheduled: ClockIcon,
    };

    const Icon = icons[status];

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        <Icon className="h-3 w-3 mr-1" />
        {status}
      </span>
    );
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Monitoring</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor system health, configuration, and performance
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => {
              switch (activeTab) {
                case 'health':
                  loadSystemHealth();
                  break;
                case 'config':
                  loadSystemConfigs();
                  break;
                case 'alerts':
                  loadSystemAlerts();
                  break;
                case 'backups':
                  loadBackupStatus();
                  break;
              }
            }}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <ArrowPathIcon className="h-4 w-4 mr-2" />
            Refresh
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

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('health')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'health'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ChartBarIcon className="h-5 w-5 inline mr-2" />
            System Health
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'config'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CogIcon className="h-5 w-5 inline mr-2" />
            Configuration
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'alerts'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <BellIcon className="h-5 w-5 inline mr-2" />
            Alerts ({systemAlerts.filter(a => !a.acknowledged_at).length})
          </button>
          <button
            onClick={() => setActiveTab('backups')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'backups'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <DocumentArrowDownIcon className="h-5 w-5 inline mr-2" />
            Backups
          </button>
        </nav>
      </div>

      {/* System Health Tab */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading system health...</p>
            </div>
          ) : systemHealth ? (
            <>
              {/* Overall Status */}
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">System Overview</h3>
                  {getHealthStatusBadge(systemHealth.status)}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{systemHealth.uptime}%</div>
                    <div className="text-sm text-gray-500">Uptime</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{systemHealth.version}</div>
                    <div className="text-sm text-gray-500">Version</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{systemHealth.services.length}</div>
                    <div className="text-sm text-gray-500">Services</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">{systemHealth.alerts.length}</div>
                    <div className="text-sm text-gray-500">Active Alerts</div>
                  </div>
                </div>
              </div>

              {/* System Metrics */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">CPU Usage</span>
                      <span className="text-sm text-gray-900">{systemHealth.metrics.cpu_usage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          systemHealth.metrics.cpu_usage > 80 ? 'bg-red-600' :
                          systemHealth.metrics.cpu_usage > 60 ? 'bg-yellow-600' : 'bg-green-600'
                        }`}
                        style={{ width: `${systemHealth.metrics.cpu_usage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Memory Usage</span>
                      <span className="text-sm text-gray-900">{systemHealth.metrics.memory_usage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          systemHealth.metrics.memory_usage > 80 ? 'bg-red-600' :
                          systemHealth.metrics.memory_usage > 60 ? 'bg-yellow-600' : 'bg-green-600'
                        }`}
                        style={{ width: `${systemHealth.metrics.memory_usage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Disk Usage</span>
                      <span className="text-sm text-gray-900">{systemHealth.metrics.disk_usage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          systemHealth.metrics.disk_usage > 80 ? 'bg-red-600' :
                          systemHealth.metrics.disk_usage > 60 ? 'bg-yellow-600' : 'bg-green-600'
                        }`}
                        style={{ width: `${systemHealth.metrics.disk_usage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{systemHealth.metrics.active_connections}</div>
                    <div className="text-sm text-gray-500">Active Connections</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{systemHealth.metrics.requests_per_minute}</div>
                    <div className="text-sm text-gray-500">Requests/min</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{systemHealth.metrics.error_rate}%</div>
                    <div className="text-sm text-gray-500">Error Rate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{systemHealth.metrics.average_response_time}ms</div>
                    <div className="text-sm text-gray-500">Avg Response</div>
                  </div>
                </div>
              </div>

              {/* Services Status */}
              <div className="bg-white shadow rounded-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-medium text-gray-900">Services Status</h3>
                </div>
                <div className="divide-y divide-gray-200">
                  {systemHealth.services.map((service) => (
                    <div key={service.name} className="px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          {getServiceStatusIcon(service.status)}
                          <div className="ml-3">
                            <div className="text-sm font-medium text-gray-900">{service.name}</div>
                            <div className="text-sm text-gray-500">
                              Response time: {service.response_time_ms}ms
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-900">
                            {formatTimeAgo(service.last_check)}
                          </div>
                          {service.error_message && (
                            <div className="text-sm text-red-600">{service.error_message}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No system health data available</p>
            </div>
          )}
        </div>
      )}

      {/* Configuration Tab */}
      {activeTab === 'config' && (
        <div className="space-y-6">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading configurations...</p>
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">System Configuration</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {systemConfigs.map((config) => (
                  <div key={config.id} className="px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center">
                          <div className="text-sm font-medium text-gray-900">{config.key}</div>
                          <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            config.category === 'security' ? 'bg-red-100 text-red-800' :
                            config.category === 'database' ? 'bg-blue-100 text-blue-800' :
                            config.category === 'email' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {config.category}
                          </span>
                          {config.is_sensitive && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                              <ShieldCheckIcon className="h-3 w-3 mr-1" />
                              Sensitive
                            </span>
                          )}
                          {config.requires_restart && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                              Restart Required
                            </span>
                          )}
                        </div>
                        <div className="mt-1 text-sm text-gray-500">{config.description}</div>
                        <div className="mt-1 text-sm text-gray-900">
                          <span className="font-medium">Value:</span>{' '}
                          {config.is_sensitive ? '••••••••' : JSON.stringify(config.value)}
                        </div>
                        <div className="mt-1 text-xs text-gray-500">
                          Last updated by {config.updated_by} on {new Date(config.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        onClick={() => openConfigModal(config)}
                        className="ml-4 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading alerts...</p>
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">System Alerts</h3>
              </div>
              {systemAlerts.length === 0 ? (
                <div className="p-8 text-center">
                  <CheckCircleIcon className="mx-auto h-12 w-12 text-green-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No active alerts</h3>
                  <p className="mt-1 text-sm text-gray-500">All systems are operating normally.</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {systemAlerts.map((alert) => (
                    <div key={alert.id} className={`px-6 py-4 ${alert.acknowledged_at ? 'bg-gray-50' : ''}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            {getAlertSeverityBadge(alert.severity)}
                            <span className="ml-2 text-sm font-medium text-gray-900">{alert.title}</span>
                          </div>
                          <div className="mt-1 text-sm text-gray-700">{alert.description}</div>
                          <div className="mt-2 flex items-center text-xs text-gray-500">
                            <ClockIcon className="h-4 w-4 mr-1" />
                            Created {formatTimeAgo(alert.created_at)}
                            {alert.acknowledged_at && (
                              <>
                                <span className="mx-2">•</span>
                                <CheckCircleIcon className="h-4 w-4 mr-1" />
                                Acknowledged by {alert.acknowledged_by} {formatTimeAgo(alert.acknowledged_at)}
                              </>
                            )}
                          </div>
                        </div>
                        {!alert.acknowledged_at && (
                          <button
                            onClick={() => handleAcknowledgeAlert(alert.id)}
                            className="ml-4 inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                          >
                            Acknowledge
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Backups Tab */}
      {activeTab === 'backups' && (
        <div className="space-y-6">
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => handleCreateBackup('incremental')}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <PlayIcon className="h-4 w-4 mr-2" />
              Incremental Backup
            </button>
            <button
              onClick={() => handleCreateBackup('full')}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <PlayIcon className="h-4 w-4 mr-2" />
              Full Backup
            </button>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading backup status...</p>
            </div>
          ) : (
            <div className="bg-white shadow rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Backup History</h3>
              </div>
              {backupStatus.length === 0 ? (
                <div className="p-8 text-center">
                  <DocumentArrowDownIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No backups found</h3>
                  <p className="mt-1 text-sm text-gray-500">Create your first backup to get started.</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {backupStatus.map((backup) => (
                    <div key={backup.id} className="px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center">
                            {getBackupStatusBadge(backup.status)}
                            <span className="ml-2 text-sm font-medium text-gray-900 capitalize">
                              {backup.type} Backup
                            </span>
                          </div>
                          <div className="mt-1 text-sm text-gray-500">
                            Started: {new Date(backup.started_at).toLocaleString()}
                            {backup.completed_at && (
                              <span className="ml-4">
                                Completed: {new Date(backup.completed_at).toLocaleString()}
                              </span>
                            )}
                          </div>
                          {backup.size_bytes && (
                            <div className="mt-1 text-sm text-gray-500">
                              Size: {formatBytes(backup.size_bytes)}
                              {backup.file_count && (
                                <span className="ml-4">Files: {backup.file_count.toLocaleString()}</span>
                              )}
                            </div>
                          )}
                          <div className="mt-1 text-xs text-gray-400">
                            Location: {backup.location}
                            <span className="ml-4">Retention: {backup.retention_days} days</span>
                          </div>
                          {backup.error_message && (
                            <div className="mt-1 text-sm text-red-600">{backup.error_message}</div>
                          )}
                        </div>
                        <div className="ml-4 flex items-center space-x-2">
                          {backup.status === 'running' && (
                            <div className="flex items-center text-blue-600">
                              <ArrowPathIcon className="h-4 w-4 animate-spin mr-1" />
                              <span className="text-sm">In Progress</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Configuration Modal */}
      {showConfigModal && selectedConfig && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowConfigModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Edit Configuration: {selectedConfig.key}
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Description
                        </label>
                        <p className="text-sm text-gray-600">{selectedConfig.description}</p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Current Value
                        </label>
                        {selectedConfig.data_type === 'boolean' ? (
                          <select
                            value={configValue.toString()}
                            onChange={(e) => setConfigValue(e.target.value === 'true')}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          >
                            <option value="true">True</option>
                            <option value="false">False</option>
                          </select>
                        ) : selectedConfig.data_type === 'number' ? (
                          <input
                            type="number"
                            value={configValue}
                            onChange={(e) => setConfigValue(Number(e.target.value))}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          />
                        ) : selectedConfig.data_type === 'json' ? (
                          <textarea
                            value={JSON.stringify(configValue, null, 2)}
                            onChange={(e) => {
                              try {
                                setConfigValue(JSON.parse(e.target.value));
                              } catch {
                                // Invalid JSON, keep as string for now
                              }
                            }}
                            rows={6}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm font-mono"
                          />
                        ) : (
                          <input
                            type={selectedConfig.is_sensitive ? 'password' : 'text'}
                            value={configValue}
                            onChange={(e) => setConfigValue(e.target.value)}
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
                          />
                        )}
                      </div>

                      {selectedConfig.validation_rules && selectedConfig.validation_rules.length > 0 && (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Validation Rules
                          </label>
                          <div className="bg-gray-50 rounded-lg p-3">
                            <ul className="text-sm text-gray-600 space-y-1">
                              {selectedConfig.validation_rules.map((rule, index) => (
                                <li key={index}>• {rule.message}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}

                      {selectedConfig.requires_restart && (
                        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                          <div className="flex">
                            <ExclamationTriangleIcon className="h-5 w-5 text-orange-400" />
                            <div className="ml-3">
                              <h4 className="text-sm font-medium text-orange-800">Restart Required</h4>
                              <p className="mt-1 text-sm text-orange-700">
                                Changing this configuration requires a system restart to take effect.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleUpdateConfig}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Update Configuration
                </button>
                <button
                  onClick={() => setShowConfigModal(false)}
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
