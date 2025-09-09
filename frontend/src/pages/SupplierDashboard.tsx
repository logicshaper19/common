/**
 * Supplier Dashboard Page
 * Main dashboard for suppliers to manage their requirements and profile
 */
import React, { useState, useEffect } from 'react';
import {
  BuildingOfficeIcon,
  DocumentCheckIcon,
  ChartBarIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import AnalyticsCard from '../components/ui/AnalyticsCard';
import SupplierRequirementsDashboard from '../components/supplier/SupplierRequirementsDashboard';

interface SupplierProfile {
  id: string;
  name: string;
  email: string;
  company_type: string;
  sector_id: string;
  tier_level: number;
  transparency_score: number;
  status: string;
}

const SupplierDashboard: React.FC = () => {
  const [profile, setProfile] = useState<SupplierProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'requirements' | 'profile' | 'analytics'>('requirements');

  useEffect(() => {
    loadSupplierProfile();
  }, []);

  const loadSupplierProfile = async () => {
    try {
      setLoading(true);
      // This would typically come from auth context or API
      // For demo purposes, using mock data
      const mockProfile: SupplierProfile = {
        id: 'supplier-123',
        name: 'Sustainable Palm Oil Mill',
        email: 'contact@sustainablepalm.com',
        company_type: 'originator',
        sector_id: 'palm_oil',
        tier_level: 4,
        transparency_score: 75,
        status: 'active'
      };
      setProfile(mockProfile);
    } catch (error) {
      console.error('Failed to load supplier profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'suspended':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTransparencyScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="animate-pulse space-y-6">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
            <div className="h-96 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardBody>
            <div className="text-center py-8">
              <BuildingOfficeIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Profile Not Found</h3>
              <p className="text-gray-600">Unable to load your supplier profile.</p>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Supplier Dashboard</h1>
              <p className="text-sm text-gray-600 mt-1">
                Welcome back, {profile.name}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Badge className={getStatusColor(profile.status)}>
                {profile.status.charAt(0).toUpperCase() + profile.status.slice(1)}
              </Badge>
              <Button variant="outline" size="sm">
                <Cog6ToothIcon className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardBody>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BuildingOfficeIcon className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-500">Company Type</div>
                  <div className="text-lg font-semibold text-gray-900 capitalize">
                    {profile.company_type}
                  </div>
                  <div className="text-xs text-gray-500">
                    Tier {profile.tier_level} • {profile.sector_id.replace('_', ' ')} sector
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-500">Transparency Score</div>
                  <div className={`text-lg font-semibold ${getTransparencyScoreColor(profile.transparency_score)}`}>
                    {profile.transparency_score}%
                  </div>
                  <div className="text-xs text-gray-500">
                    Based on completed requirements
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <DocumentCheckIcon className="h-8 w-8 text-purple-600" />
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-500">Requirements Status</div>
                  <div className="text-lg font-semibold text-gray-900">
                    In Progress
                  </div>
                  <div className="text-xs text-gray-500">
                    Complete all requirements to improve score
                  </div>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Navigation Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('requirements')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'requirements'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Requirements
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'profile'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Profile
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analytics'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Analytics
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'requirements' && (
          <SupplierRequirementsDashboard
            companyType={profile.company_type}
            sectorId={profile.sector_id}
          />
        )}

        {activeTab === 'profile' && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium text-gray-900">Company Profile</h3>
              <p className="text-sm text-gray-600">Manage your company information and settings</p>
            </CardHeader>
            <CardBody>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Company Name
                    </label>
                    <input
                      type="text"
                      value={profile.name}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={profile.email}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Company Type
                    </label>
                    <input
                      type="text"
                      value={profile.company_type}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 capitalize"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sector
                    </label>
                    <input
                      type="text"
                      value={profile.sector_id.replace('_', ' ')}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 capitalize"
                    />
                  </div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Profile Information</h4>
                  <p className="text-sm text-blue-800">
                    Your company type and sector determine your tier-specific requirements. 
                    Contact your buyer if you need to update this information.
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        )}

        {activeTab === 'analytics' && (
          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium text-gray-900">Transparency Analytics</h3>
              <p className="text-sm text-gray-600">Track your transparency score and compliance metrics</p>
            </CardHeader>
            <CardBody>
              <div className="text-center py-12">
                <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h4 className="text-lg font-medium text-gray-900 mb-2">Analytics Coming Soon</h4>
                <p className="text-gray-600">
                  Detailed analytics and reporting features will be available here.
                </p>
              </div>
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
};

export default SupplierDashboard;
