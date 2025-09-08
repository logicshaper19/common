/**
 * Admin Dashboard
 * Main admin interface that orchestrates all admin and support functionality
 */
import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  CubeIcon,
  UserGroupIcon,
  ShoppingCartIcon,
  LifebuoyIcon,
  DocumentTextIcon,
  CogIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import { adminApi } from '../../api/admin';
import { AdminDashboardData } from '../../types/admin';
import { ProductCatalogManagement } from './product-catalog-management';
import { UserCompanyManagement } from './user-company-management';
import { PurchaseOrderManagement } from './purchase-order-management';
import { SupportTicketSystem } from './SupportTicketSystem';
import { AuditLogViewer } from './AuditLogViewer';
import { SystemMonitoring } from './SystemMonitoring';

interface AdminDashboardProps {
  className?: string;
}

export function AdminDashboard({ className = '' }: AdminDashboardProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'users' | 'purchase-orders' | 'support' | 'audit' | 'system'>('overview');
  const [dashboardData, setDashboardData] = useState<AdminDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminApi.getDashboardData();
        setDashboardData(data);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Error loading dashboard:', err);
      } finally {
        setLoading(false);
      }
    };

    if (activeTab === 'overview') {
      loadDashboardData();
    }
  }, [activeTab]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'compliant':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'critical':
      case 'down':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Comprehensive platform administration and monitoring
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ChartBarIcon className="h-5 w-5 inline mr-2" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('products')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'products'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CubeIcon className="h-5 w-5 inline mr-2" />
            Product Catalog
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <UserGroupIcon className="h-5 w-5 inline mr-2" />
            Users & Companies
          </button>
          <button
            onClick={() => setActiveTab('purchase-orders')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'purchase-orders'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <ShoppingCartIcon className="h-5 w-5 inline mr-2" />
            Purchase Orders
          </button>
          <button
            onClick={() => setActiveTab('support')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'support'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <LifebuoyIcon className="h-5 w-5 inline mr-2" />
            Support
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'audit'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <DocumentTextIcon className="h-5 w-5 inline mr-2" />
            Audit Logs
          </button>
          <button
            onClick={() => setActiveTab('system')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'system'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <CogIcon className="h-5 w-5 inline mr-2" />
            System
          </button>
        </nav>
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

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="mt-2 text-sm text-gray-500">Loading dashboard data...</p>
            </div>
          ) : dashboardData ? (
            <>
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <UserGroupIcon className="h-6 w-6 text-gray-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Total Users</dt>
                          <dd className="text-lg font-medium text-gray-900">{formatNumber(dashboardData.overview.total_users)}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-5 py-3">
                    <div className="text-sm">
                      <span className="text-green-600 font-medium">+{dashboardData.user_stats.new_users_today}</span>
                      <span className="text-gray-500"> today</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <CubeIcon className="h-6 w-6 text-gray-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Companies</dt>
                          <dd className="text-lg font-medium text-gray-900">{formatNumber(dashboardData.overview.total_companies)}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-5 py-3">
                    <div className="text-sm">
                      <span className="text-green-600 font-medium">+{dashboardData.company_stats.new_companies_today}</span>
                      <span className="text-gray-500"> today</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <LifebuoyIcon className="h-6 w-6 text-gray-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Open Tickets</dt>
                          <dd className="text-lg font-medium text-gray-900">{dashboardData.overview.open_tickets}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-5 py-3">
                    <div className="text-sm">
                      <span className="text-blue-600 font-medium">{dashboardData.support_stats.tickets_today}</span>
                      <span className="text-gray-500"> today</span>
                    </div>
                  </div>
                </div>

                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        {getStatusIcon(dashboardData.system_health.status)}
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">System Health</dt>
                          <dd className="text-lg font-medium text-gray-900 capitalize">{dashboardData.system_health.status}</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                  <div className="bg-gray-50 px-5 py-3">
                    <div className="text-sm">
                      <span className="text-green-600 font-medium">{dashboardData.overview.system_uptime}%</span>
                      <span className="text-gray-500"> uptime</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Activity and System Status */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Activity */}
                <div className="bg-white shadow rounded-lg">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
                  </div>
                  <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                    {dashboardData.recent_activity.slice(0, 10).map((activity) => (
                      <div key={activity.id} className="px-6 py-4">
                        <div className="flex items-start">
                          <div className="flex-shrink-0">
                            <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                              <UserGroupIcon className="h-5 w-5 text-gray-600" />
                            </div>
                          </div>
                          <div className="ml-3 flex-1">
                            <div className="text-sm text-gray-900">
                              <span className="font-medium">{activity.user_name}</span> {activity.action} {activity.resource_type}
                              {activity.resource_name && <span className="font-medium"> "{activity.resource_name}"</span>}
                            </div>
                            <div className="text-sm text-gray-500">
                              {activity.company_name} • {new Date(activity.timestamp).toLocaleString()}
                            </div>
                          </div>
                          <div className="flex-shrink-0">
                            {activity.success ? (
                              <CheckCircleIcon className="h-5 w-5 text-green-500" />
                            ) : (
                              <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* System Alerts */}
                <div className="bg-white shadow rounded-lg">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">System Alerts</h3>
                  </div>
                  <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                    {dashboardData.alerts.length === 0 ? (
                      <div className="px-6 py-8 text-center">
                        <CheckCircleIcon className="mx-auto h-8 w-8 text-green-400" />
                        <p className="mt-2 text-sm text-gray-500">No active alerts</p>
                      </div>
                    ) : (
                      dashboardData.alerts.map((alert) => (
                        <div key={alert.id} className="px-6 py-4">
                          <div className="flex items-start">
                            <div className="flex-shrink-0">
                              {getStatusIcon(alert.severity)}
                            </div>
                            <div className="ml-3 flex-1">
                              <div className="text-sm font-medium text-gray-900">{alert.title}</div>
                              <div className="text-sm text-gray-500">{alert.description}</div>
                              <div className="text-xs text-gray-400 mt-1">
                                {new Date(alert.created_at).toLocaleString()}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>

              {/* Statistics Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* User Statistics */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">User Statistics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Active Sessions</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.user_stats.active_sessions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">New This Week</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.user_stats.new_users_week}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Login Failures Today</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.user_stats.login_failures_today}</span>
                    </div>
                  </div>
                </div>

                {/* Company Statistics */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Company Statistics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Active Companies</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.overview.active_companies}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Avg Transparency</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.company_stats.average_transparency_score}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">New This Week</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.company_stats.new_companies_week}</span>
                    </div>
                  </div>
                </div>

                {/* Support Statistics */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Support Statistics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Avg Response Time</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.support_stats.average_response_time}h</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Satisfaction Rating</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.support_stats.satisfaction_rating}/5</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">Tickets This Week</span>
                      <span className="text-sm font-medium text-gray-900">{dashboardData.support_stats.tickets_week}</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500">No dashboard data available</p>
            </div>
          )}
        </div>
      )}

      {/* Product Catalog Tab */}
      {activeTab === 'products' && <ProductCatalogManagement />}

      {/* Users & Companies Tab */}
      {activeTab === 'users' && <UserCompanyManagement />}

      {/* Purchase Orders Tab */}
      {activeTab === 'purchase-orders' && <PurchaseOrderManagement />}

      {/* Support Tab */}
      {activeTab === 'support' && <SupportTicketSystem />}

      {/* Audit Logs Tab */}
      {activeTab === 'audit' && <AuditLogViewer />}

      {/* System Tab */}
      {activeTab === 'system' && <SystemMonitoring />}
    </div>
  );
}
