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
import AnalyticsCard from '../components/ui/AnalyticsCard';
import { formatDate, snakeToTitle } from '../lib/utils';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // Mock data - in real app, this would come from API
  const stats = [
    {
      name: 'Orders',
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
      name: 'Transparency',
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
    <>
      {/* Page header - Simple and clean */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-neutral-900">
          Welcome back, {user?.full_name?.split(' ')[0] || 'User'}!
        </h1>
        <p className="text-neutral-600 mt-1">
          Here's what's happening with your supply chain today.
        </p>
      </div>

      <div className="space-y-6">

      {/* Stats grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <AnalyticsCard
            key={stat.name}
            name={stat.name}
            value={stat.value}
            change={stat.change}
            changeType={stat.changeType}
            icon={stat.icon}
            href={stat.href}
          />
        ))}
      </div>

      {/* Recent Purchase Orders - Full Width */}
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
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200">
              <thead className="bg-neutral-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Companies
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-neutral-200">
                {recentOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-neutral-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-neutral-900">
                        {order.product}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-neutral-900">
                        <div className="font-medium">{order.buyer}</div>
                        <div className="text-neutral-500">← {order.seller}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-neutral-900">
                        {order.quantity}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-neutral-500">
                        {formatDate(order.date)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
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
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
      </div>
    </>
  );
};

export default Dashboard;
