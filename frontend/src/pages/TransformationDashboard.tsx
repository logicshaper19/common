/**
 * Transformation Dashboard Page
 * Role-based transformation management interface that integrates with existing UI patterns
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { SimpleTransformationManager } from '../components/transformation/SimpleTransformationManager';
import { 
  CogIcon, 
  PlusIcon, 
  FunnelIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface Transformation {
  id: string;
  transformation_type: string;
  status: string;
  start_time: string;
  end_time?: string;
  facility_id: string;
  yield_percentage?: number;
  quality_score?: number;
  created_at: string;
  updated_at: string;
  // Role-specific fields will be added dynamically
  [key: string]: any;
}

interface DashboardStats {
  total_transformations: number;
  active_transformations: number;
  completed_transformations: number;
  company_type: string;
  kpis: Record<string, any>;
  last_updated: string;
}

interface TransformationTemplate {
  id: string;
  name: string;
  transformation_type: string;
  description: string;
  fields: Array<{
    name: string;
    label: string;
    type: string;
    required: boolean;
  }>;
}

const TransformationDashboard: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  const [transformations, setTransformations] = useState<Transformation[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [templates, setTemplates] = useState<TransformationTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filters, setFilters] = useState({
    status: '',
    transformation_type: ''
  });

  useEffect(() => {
    loadDashboardData();
  }, [filters]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

      // Load transformations, stats, and templates in parallel
      const [transformationsRes, statsRes, templatesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/transformation-dashboard/my-transformations?${new URLSearchParams(filters)}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE_URL}/api/v1/transformation-dashboard/dashboard-stats`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${API_BASE_URL}/api/v1/transformation-dashboard/transformation-templates`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      // Handle individual response errors gracefully
      if (!transformationsRes.ok) {
        console.error('Transformations API error:', transformationsRes.status, transformationsRes.statusText);
      }
      if (!statsRes.ok) {
        console.error('Stats API error:', statsRes.status, statsRes.statusText);
      }
      if (!templatesRes.ok) {
        console.error('Templates API error:', templatesRes.status, templatesRes.statusText);
      }

      // Parse responses, handling empty or error responses
      const [transformationsData, statsData, templatesData] = await Promise.all([
        transformationsRes.ok ? transformationsRes.json() : { transformations: [] },
        statsRes.ok ? statsRes.json() : { 
          total_transformations: 0, 
          active_transformations: 0, 
          completed_transformations: 0,
          company_type: user?.company?.company_type || 'unknown',
          kpis: {}
        },
        templatesRes.ok ? templatesRes.json() : { templates: [] }
      ]);

      setTransformations(transformationsData.transformations || []);
      setStats(statsData);
      setTemplates(templatesData.templates || []);

      // Show info toast if no transformations exist (elegant empty state)
      if (transformationsData.transformations?.length === 0 && statsData.total_transformations === 0) {
        showToast({ 
          type: 'info', 
          title: 'No Transformations Found', 
          message: 'You don\'t have any transformation data yet. This is normal if you\'re a plantation grower or if no transformations have been created.',
          duration: 5000
        });
      }

    } catch (err) {
      console.error('Error loading transformation dashboard:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load dashboard data';
      setError(errorMessage);
      
      // Only show error toast for actual errors, not empty states
      if (!errorMessage.includes('No Transformations Found')) {
        showToast({ 
          type: 'error', 
          title: 'Error Loading Dashboard', 
          message: 'There was a problem loading the transformation dashboard. Please try again.',
          duration: 7000
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <ClockIcon className="h-5 w-5 text-blue-500" />;
      case 'pending':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <CogIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-white p-6 rounded-lg shadow">
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                  <div className="h-8 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="h-12 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-500 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-red-800">Error Loading Dashboard</h3>
                <p className="text-red-600 mt-1">{error}</p>
                <button
                  onClick={loadDashboardData}
                  className="mt-3 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <CogIcon className="h-8 w-8 mr-3 text-primary-600" />
                Transformations
              </h1>
              <p className="text-gray-600 mt-2">
                Manage your {user?.company?.company_type?.replace('_', ' ')} transformations
              </p>
            </div>
            <button
              onClick={() => setShowCreateForm(true)}
              className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 flex items-center"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              New Transformation
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <ChartBarIcon className="h-8 w-8 text-blue-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Transformations</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_transformations}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <ClockIcon className="h-8 w-8 text-yellow-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.active_transformations}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <CheckCircleIcon className="h-8 w-8 text-green-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.completed_transformations}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <CogIcon className="h-8 w-8 text-purple-500" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Company Type</p>
                  <p className="text-lg font-bold text-gray-900 capitalize">
                    {stats.company_type?.replace('_', ' ')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6">
          <div className="flex items-center space-x-4">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
            </select>
            <select
              value={filters.transformation_type}
              onChange={(e) => setFilters({ ...filters, transformation_type: e.target.value })}
              className="border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Types</option>
              <option value="harvest">Harvest</option>
              <option value="mill_processing">Mill Processing</option>
              <option value="refinery_processing">Refinery Processing</option>
              <option value="manufacturing">Manufacturing</option>
            </select>
          </div>
        </div>

        {/* Transformations Table */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">My Transformations</h3>
          </div>
          
          {transformations.length === 0 ? (
            <div className="p-12 text-center">
              <CogIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Transformations Found</h3>
              <p className="text-gray-600 mb-4 max-w-md mx-auto">
                {user?.company?.company_type === 'plantation_grower' 
                  ? "As a plantation grower, you primarily manage harvest data. Transformations are typically handled by mills, refineries, and manufacturers."
                  : "You don't have any transformation data yet. Transformations track the processing of raw materials into finished products."
                }
              </p>
              {user?.company?.company_type !== 'plantation_grower' && (
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                >
                  Create Your First Transformation
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Start Time
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Facility
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Yield %
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quality Score
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transformations.map((transformation) => (
                    <tr key={transformation.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {transformation.transformation_type?.replace('_', ' ')}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(transformation.status)}`}>
                          {getStatusIcon(transformation.status)}
                          <span className="ml-1 capitalize">{transformation.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(transformation.start_time)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {transformation.facility_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {transformation.yield_percentage ? `${transformation.yield_percentage}%` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {transformation.quality_score || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Transformation Creation Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-900">
                    Create New Transformation
                  </h3>
                  <button
                    onClick={() => setShowCreateForm(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                <SimpleTransformationManager
                  transformationEventId={undefined}
                  onTransformationUpdate={(transformation) => {
                    setShowCreateForm(false);
                    loadDashboardData(); // Refresh the dashboard
                    showToast({
                      type: 'success',
                      title: 'Transformation Created',
                      message: 'Your transformation has been created successfully.'
                    });
                  }}
                  className="w-full"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TransformationDashboard;
