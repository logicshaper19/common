/**
 * Originator Dashboard Page
 * Specialized dashboard for originator companies with harvest tracking,
 * farm performance metrics, certification status, and quality trends
 */
import React, { useState, useEffect } from 'react';
import {
  MapPinIcon,
  ShieldCheckIcon,
  BeakerIcon,
  ChartBarIcon,
  CalendarIcon,
  TruckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  CubeIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import AnalyticsCard from '../components/ui/AnalyticsCard';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { formatDate, formatCurrency } from '../lib/utils';

interface HarvestMetrics {
  total_harvests: number;
  total_volume: number;
  average_quality: number;
  active_batches: number;
  pending_shipments: number;
  revenue_this_month: number;
}

interface FarmPerformance {
  farm_id: string;
  farm_name: string;
  total_harvests: number;
  total_volume: number;
  average_quality: number;
  last_harvest_date: string;
  certification_status: string[];
  performance_trend: 'up' | 'down' | 'stable';
}

interface CertificationStatus {
  certification_type: string;
  status: 'active' | 'expiring' | 'expired' | 'pending';
  expiry_date?: string;
  days_until_expiry?: number;
  coverage_percentage: number;
}

interface QualityTrend {
  date: string;
  oil_content: number;
  moisture_content: number;
  free_fatty_acid: number;
  batch_count: number;
}

interface RecentHarvest {
  id: string;
  batch_id: string;
  farm_name: string;
  harvest_date: string;
  volume: number;
  quality_score: number;
  status: 'harvested' | 'processed' | 'shipped';
  gps_coordinates: { latitude: number; longitude: number };
}

const OriginatorDashboard: React.FC = () => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // State
  const [metrics, setMetrics] = useState<HarvestMetrics | null>(null);
  const [farmPerformance, setFarmPerformance] = useState<FarmPerformance[]>([]);
  const [certifications, setCertifications] = useState<CertificationStatus[]>([]);
  const [qualityTrends, setQualityTrends] = useState<QualityTrend[]>([]);
  const [recentHarvests, setRecentHarvests] = useState<RecentHarvest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load dashboard data
  useEffect(() => {
    loadOriginatorData();
  }, [user?.company?.id]);

  const loadOriginatorData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Replace with actual API calls
      // Simulated data for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setMetrics({
        total_harvests: 45,
        total_volume: 12500,
        average_quality: 87.5,
        active_batches: 12,
        pending_shipments: 3,
        revenue_this_month: 125000
      });

      setFarmPerformance([
        {
          farm_id: 'FARM-KAL-001',
          farm_name: 'Kalimantan Estate Block A',
          total_harvests: 15,
          total_volume: 4200,
          average_quality: 89.2,
          last_harvest_date: '2025-01-08',
          certification_status: ['RSPO', 'NDPE'],
          performance_trend: 'up'
        },
        {
          farm_id: 'FARM-KAL-002',
          farm_name: 'Kalimantan Estate Block B',
          total_harvests: 18,
          total_volume: 5100,
          average_quality: 85.8,
          last_harvest_date: '2025-01-09',
          certification_status: ['RSPO'],
          performance_trend: 'stable'
        },
        {
          farm_id: 'FARM-SUM-001',
          farm_name: 'Sumatra Smallholder Cooperative',
          total_harvests: 12,
          total_volume: 3200,
          average_quality: 88.1,
          last_harvest_date: '2025-01-07',
          certification_status: ['ISPO', 'Rainforest Alliance'],
          performance_trend: 'up'
        }
      ]);

      setCertifications([
        {
          certification_type: 'RSPO',
          status: 'active',
          expiry_date: '2025-12-15',
          days_until_expiry: 348,
          coverage_percentage: 85
        },
        {
          certification_type: 'NDPE',
          status: 'expiring',
          expiry_date: '2025-03-20',
          days_until_expiry: 69,
          coverage_percentage: 60
        },
        {
          certification_type: 'ISPO',
          status: 'active',
          expiry_date: '2026-06-30',
          days_until_expiry: 506,
          coverage_percentage: 40
        },
        {
          certification_type: 'Rainforest Alliance',
          status: 'pending',
          coverage_percentage: 25
        }
      ]);

      setQualityTrends([
        { date: '2025-01-01', oil_content: 22.1, moisture_content: 18.5, free_fatty_acid: 2.3, batch_count: 8 },
        { date: '2025-01-02', oil_content: 22.8, moisture_content: 17.9, free_fatty_acid: 2.1, batch_count: 12 },
        { date: '2025-01-03', oil_content: 23.2, moisture_content: 18.1, free_fatty_acid: 1.9, batch_count: 10 },
        { date: '2025-01-04', oil_content: 22.9, moisture_content: 18.3, free_fatty_acid: 2.0, batch_count: 15 },
        { date: '2025-01-05', oil_content: 23.5, moisture_content: 17.8, free_fatty_acid: 1.8, batch_count: 11 }
      ]);

      setRecentHarvests([
        {
          id: '1',
          batch_id: 'HARVEST-2025-045',
          farm_name: 'Kalimantan Estate Block A',
          harvest_date: '2025-01-10',
          volume: 850,
          quality_score: 89.2,
          status: 'harvested',
          gps_coordinates: { latitude: -2.5489, longitude: 118.0149 }
        },
        {
          id: '2',
          batch_id: 'HARVEST-2025-044',
          farm_name: 'Sumatra Smallholder Cooperative',
          harvest_date: '2025-01-09',
          volume: 620,
          quality_score: 87.8,
          status: 'processed',
          gps_coordinates: { latitude: -0.7893, longitude: 113.9213 }
        },
        {
          id: '3',
          batch_id: 'HARVEST-2025-043',
          farm_name: 'Kalimantan Estate Block B',
          harvest_date: '2025-01-08',
          volume: 920,
          quality_score: 88.5,
          status: 'shipped',
          gps_coordinates: { latitude: -1.2379, longitude: 116.8227 }
        }
      ]);

    } catch (err) {
      console.error('Error loading originator data:', err);
      setError('Failed to load dashboard data. Please try again.');
      showToast({
        type: 'error',
        title: 'Error loading dashboard',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Get status badge variant
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'expiring':
        return 'warning';
      case 'expired':
        return 'error';
      case 'pending':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  // Get harvest status badge
  const getHarvestStatusBadge = (status: string) => {
    switch (status) {
      case 'harvested':
        return <Badge variant="primary">Harvested</Badge>;
      case 'processed':
        return <Badge variant="warning">Processed</Badge>;
      case 'shipped':
        return <Badge variant="success">Shipped</Badge>;
      default:
        return <Badge variant="neutral">Unknown</Badge>;
    }
  };

  // Get performance trend icon
  const getPerformanceTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <ChartBarIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ChartBarIcon className="h-4 w-4 text-red-500" />;
      default:
        return <ChartBarIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadOriginatorData} variant="primary">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <>
      {/* Page Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Originator Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Monitor your harvest operations, farm performance, and certification status.
          </p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" leftIcon={<MapPinIcon className="h-4 w-4" />}>
            View Farm Map
          </Button>
          <Button variant="primary" leftIcon={<CubeIcon className="h-4 w-4" />}>
            New Harvest
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <AnalyticsCard
            title="Total Harvests"
            value={metrics.total_harvests.toString()}
            subtitle="This month"
            icon={<CalendarIcon className="h-6 w-6" />}
            trend={{ value: 12, isPositive: true }}
          />
          <AnalyticsCard
            title="Total Volume"
            value={`${metrics.total_volume.toLocaleString()} KG`}
            subtitle="Fresh fruit bunches"
            icon={<CubeIcon className="h-6 w-6" />}
            trend={{ value: 8.5, isPositive: true }}
          />
          <AnalyticsCard
            title="Average Quality"
            value={`${metrics.average_quality}%`}
            subtitle="Quality score"
            icon={<BeakerIcon className="h-6 w-6" />}
            trend={{ value: 2.3, isPositive: true }}
          />
          <AnalyticsCard
            title="Active Batches"
            value={metrics.active_batches.toString()}
            subtitle="In processing"
            icon={<TruckIcon className="h-6 w-6" />}
          />
          <AnalyticsCard
            title="Pending Shipments"
            value={metrics.pending_shipments.toString()}
            subtitle="Ready for delivery"
            icon={<TruckIcon className="h-6 w-6" />}
          />
          <AnalyticsCard
            title="Revenue"
            value={formatCurrency(metrics.revenue_this_month)}
            subtitle="This month"
            icon={<ChartBarIcon className="h-6 w-6" />}
            trend={{ value: 15.2, isPositive: true }}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Farm Performance */}
        <Card>
          <CardHeader title="Farm Performance" subtitle="Individual farm metrics" />
          <CardBody padding="none">
            <div className="divide-y divide-gray-200">
              {farmPerformance.map((farm) => (
                <div key={farm.farm_id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h4 className="font-medium text-gray-900">{farm.farm_name}</h4>
                        {getPerformanceTrendIcon(farm.performance_trend)}
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        ID: {farm.farm_id} • Last harvest: {formatDate(farm.last_harvest_date)}
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">Harvests:</span>
                          <span className="ml-1 font-medium">{farm.total_harvests}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Volume:</span>
                          <span className="ml-1 font-medium">{farm.total_volume.toLocaleString()} KG</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Quality:</span>
                          <span className="ml-1 font-medium">{farm.average_quality}%</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {farm.certification_status.map((cert) => (
                          <Badge key={cert} variant="secondary" size="sm">
                            {cert}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Certification Status */}
        <Card>
          <CardHeader title="Certification Status" subtitle="Sustainability certifications" />
          <CardBody padding="none">
            <div className="divide-y divide-gray-200">
              {certifications.map((cert) => (
                <div key={cert.certification_type} className="p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <ShieldCheckIcon className="h-5 w-5 text-gray-400" />
                      <span className="font-medium text-gray-900">{cert.certification_type}</span>
                    </div>
                    <Badge variant={getStatusBadgeVariant(cert.status)}>
                      {cert.status.charAt(0).toUpperCase() + cert.status.slice(1)}
                    </Badge>
                  </div>
                  <div className="ml-8">
                    <div className="text-sm text-gray-600 mb-2">
                      Coverage: {cert.coverage_percentage}% of farms
                    </div>
                    {cert.expiry_date && (
                      <div className="text-sm text-gray-600">
                        {cert.status === 'expiring' ? (
                          <span className="text-yellow-600">
                            Expires in {cert.days_until_expiry} days ({formatDate(cert.expiry_date)})
                          </span>
                        ) : (
                          <span>
                            Expires: {formatDate(cert.expiry_date)}
                          </span>
                        )}
                      </div>
                    )}
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                      <div 
                        className={`h-2 rounded-full ${
                          cert.status === 'active' ? 'bg-green-500' :
                          cert.status === 'expiring' ? 'bg-yellow-500' :
                          cert.status === 'expired' ? 'bg-red-500' : 'bg-gray-400'
                        }`}
                        style={{ width: `${cert.coverage_percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Recent Harvests */}
      <Card>
        <CardHeader title="Recent Harvests" subtitle="Latest harvest activities" />
        <CardBody padding="none">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Batch ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Farm
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Harvest Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Volume
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quality Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentHarvests.map((harvest) => (
                  <tr key={harvest.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {harvest.batch_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{harvest.farm_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatDate(harvest.harvest_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {harvest.volume.toLocaleString()} KG
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {harvest.quality_score}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getHarvestStatusBadge(harvest.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {harvest.gps_coordinates.latitude.toFixed(4)}, {harvest.gps_coordinates.longitude.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </>
  );
};

export default OriginatorDashboard;
