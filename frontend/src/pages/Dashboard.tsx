/**
 * Dashboard Page Component
 */
import React from 'react';
import {
  DocumentTextIcon,
  CubeIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { formatDate, snakeToTitle } from '../lib/utils';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // Mock data - in real app, this would come from API
  const stats = [
    {
      name: 'Purchase Orders',
      value: '24',
      change: '+12%',
      changeType: 'increase' as const,
      icon: DocumentTextIcon,
      href: '/purchase-orders',
    },
    {
      name: 'Products',
      value: '156',
      change: '+3%',
      changeType: 'increase' as const,
      icon: CubeIcon,
      href: '/products',
    },
    {
      name: 'Companies',
      value: '8',
      change: '+1',
      changeType: 'increase' as const,
      icon: BuildingOfficeIcon,
      href: '/companies',
    },
    {
      name: 'Avg Transparency',
      value: '78%',
      change: '+5%',
      changeType: 'increase' as const,
      icon: ChartBarIcon,
      href: '/transparency',
    },
  ];

  const recentOrders = [
    {
      id: '1',
      product: 'Organic Cotton',
      buyer: 'EcoFashion Co.',
      seller: 'Green Mills',
      quantity: '500 KG',
      status: 'pending',
      date: '2024-01-15T10:30:00Z',
    },
    {
      id: '2',
      product: 'Recycled Polyester',
      buyer: 'Sustainable Brands',
      seller: 'Eco Processors',
      quantity: '1000 KG',
      status: 'confirmed',
      date: '2024-01-14T14:20:00Z',
    },
    {
      id: '3',
      product: 'Hemp Fiber',
      buyer: 'Natural Textiles',
      seller: 'Hemp Farms Co.',
      quantity: '750 KG',
      status: 'shipped',
      date: '2024-01-13T09:15:00Z',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900">
          Welcome back, {user?.full_name?.split(' ')[0] || 'User'}!
        </h1>
        <p className="text-neutral-600 mt-1">
          Here's what's happening with your supply chain today.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.name} className="hover:shadow-md transition-shadow">
            <CardBody>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                    <stat.icon className="w-5 h-5 text-primary-600" />
                  </div>
                </div>
                <div className="ml-4 flex-1">
                  <p className="text-sm font-medium text-neutral-600">
                    {stat.name}
                  </p>
                  <div className="flex items-baseline">
                    <p className="text-2xl font-semibold text-neutral-900">
                      {stat.value}
                    </p>
                    <p
                      className={`ml-2 text-sm font-medium ${
                        stat.changeType === 'increase'
                          ? 'text-success-600'
                          : 'text-error-600'
                      }`}
                    >
                      {stat.change}
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-4">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-center"
                  onClick={() => window.location.href = stat.href}
                >
                  View Details
                </Button>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Purchase Orders */}
        <Card>
          <CardHeader
            title="Recent Purchase Orders"
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => window.location.href = '/purchase-orders'}
              >
                View All
              </Button>
            }
          />
          <CardBody padding="none">
            <div className="divide-y divide-neutral-200">
              {recentOrders.map((order) => (
                <div key={order.id} className="p-6 hover:bg-neutral-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-900 truncate">
                        {order.product}
                      </p>
                      <p className="text-sm text-neutral-500">
                        {order.buyer} ← {order.seller}
                      </p>
                      <p className="text-xs text-neutral-400 mt-1">
                        {formatDate(order.date)} • {order.quantity}
                      </p>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      <Badge
                        variant={
                          order.status === 'confirmed'
                            ? 'success'
                            : order.status === 'pending'
                            ? 'warning'
                            : order.status === 'shipped'
                            ? 'primary'
                            : 'neutral'
                        }
                      >
                        {snakeToTitle(order.status)}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader title="Quick Actions" />
          <CardBody>
            <div className="space-y-4">
              <Button
                variant="primary"
                fullWidth
                leftIcon={<DocumentTextIcon className="h-4 w-4" />}
                onClick={() => window.location.href = '/purchase-orders/new'}
              >
                Create Purchase Order
              </Button>
              
              <Button
                variant="secondary"
                fullWidth
                leftIcon={<CubeIcon className="h-4 w-4" />}
                onClick={() => window.location.href = '/products/new'}
              >
                Add Product
              </Button>
              
              <Button
                variant="secondary"
                fullWidth
                leftIcon={<ChartBarIcon className="h-4 w-4" />}
                onClick={() => window.location.href = '/transparency'}
              >
                View Transparency Report
              </Button>
              
              {user?.role === 'admin' && (
                <Button
                  variant="secondary"
                  fullWidth
                  leftIcon={<BuildingOfficeIcon className="h-4 w-4" />}
                  onClick={() => window.location.href = '/companies/new'}
                >
                  Add Company
                </Button>
              )}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Company info */}
      {user?.company && (
        <Card>
          <CardHeader title="Your Company" />
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-medium text-neutral-900 mb-2">
                  Company Details
                </h4>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs text-neutral-500">Name</dt>
                    <dd className="text-sm text-neutral-900">
                      {user.company.name}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-neutral-500">Type</dt>
                    <dd className="text-sm text-neutral-900">
                      <Badge variant="primary">
                        {snakeToTitle(user.company.company_type)}
                      </Badge>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-neutral-500">Email</dt>
                    <dd className="text-sm text-neutral-900">
                      {user.company.email}
                    </dd>
                  </div>
                </dl>
              </div>
              
              <div>
                <h4 className="text-sm font-medium text-neutral-900 mb-2">
                  Your Role
                </h4>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-xs text-neutral-500">Position</dt>
                    <dd className="text-sm text-neutral-900">
                      <Badge variant="secondary">
                        {snakeToTitle(user.role)}
                      </Badge>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-neutral-500">Email</dt>
                    <dd className="text-sm text-neutral-900">
                      {user.email}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-neutral-500">Status</dt>
                    <dd className="text-sm text-neutral-900">
                      <Badge variant={user.is_active ? 'success' : 'error'}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
