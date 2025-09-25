/**
 * Delivery Tab Component
 * Shows delivery information and allows status updates for purchase orders
 */
import React, { useState, useEffect } from 'react';
import { TruckIcon, MapPinIcon, ClockIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { useToast } from '../../contexts/ToastContext';
import { useAuth } from '../../contexts/AuthContext';
import { formatDate } from '../../lib/utils';

interface DeliveryData {
  delivery_date: string;
  delivery_location: string;
  delivery_status: string;
  delivered_at?: string;
  delivery_notes?: string;
  delivery_confirmed_by?: string;
}

interface DeliveryHistoryEntry {
  timestamp: string;
  note: string;
}

interface DeliveryHistory {
  po_id: string;
  po_number: string;
  current_status: string;
  delivered_at?: string;
  delivery_confirmed_by?: string;
  history: DeliveryHistoryEntry[];
}

interface DeliveryTabProps {
  purchaseOrderId: string;
  onStatusUpdate?: () => void;
}

const DeliveryTab: React.FC<DeliveryTabProps> = ({ purchaseOrderId, onStatusUpdate }) => {
  const [delivery, setDelivery] = useState<DeliveryData | null>(null);
  const [history, setHistory] = useState<DeliveryHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const { showToast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    fetchDelivery();
    fetchHistory();
  }, [purchaseOrderId]);

  const fetchDelivery = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/purchase-orders/${purchaseOrderId}/delivery`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to fetch delivery information: ${response.status} - ${errorData.detail || response.statusText}`);
      }

      const data = await response.json();
      setDelivery(data);
    } catch (error) {
      console.error('Error fetching delivery:', error);
      showToast({
        type: 'error',
        title: 'Error loading delivery information',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/purchase-orders/${purchaseOrderId}/delivery/history`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to fetch delivery history: ${response.status} - ${errorData.detail || response.statusText}`);
      }

      const data = await response.json();
      setHistory(data);
    } catch (error) {
      console.error('Error fetching delivery history:', error);
      // Don't show toast for history errors as it's not critical
    }
  };

  const updateStatus = async (status: string, notes?: string) => {
    try {
      setUpdating(true);
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`/api/v1/purchase-orders/${purchaseOrderId}/delivery`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, notes })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to update delivery status: ${response.status} - ${errorData.detail || response.statusText}`);
      }

      const updatedData = await response.json();
      setDelivery(updatedData);
      
      showToast({
        type: 'success',
        title: 'Delivery status updated',
        message: `Status changed to ${status.replace('_', ' ').toUpperCase()}`
      });

      // Refresh history after status update
      await fetchHistory();

      // Notify parent component of status update
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    } catch (error) {
      console.error('Error updating delivery status:', error);
      showToast({
        type: 'error',
        title: 'Error updating delivery status',
        message: 'Please try again or contact support if the problem persists.'
      });
    } finally {
      setUpdating(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'delivered':
        return 'success';
      case 'in_transit':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
        return CheckCircleIcon;
      case 'in_transit':
        return TruckIcon;
      case 'failed':
        return ClockIcon;
      default:
        return ClockIcon;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
        <span className="ml-2 text-neutral-600">Loading delivery information...</span>
      </div>
    );
  }

  if (!delivery) {
    return (
      <div className="text-center py-8">
        <p className="text-neutral-500">No delivery information available</p>
      </div>
    );
  }

  const StatusIcon = getStatusIcon(delivery.delivery_status);

  return (
    <div className="space-y-6">
      {/* Delivery Status Card */}
      <Card>
        <CardHeader title="Delivery Status" />
        <CardBody className="space-y-4">
          <div className="flex items-center space-x-3">
            <StatusIcon className="h-6 w-6 text-neutral-500" />
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <Badge variant={getStatusColor(delivery.delivery_status)} size="lg">
                  {delivery.delivery_status.replace('_', ' ').toUpperCase()}
                </Badge>
                {delivery.delivered_at && (
                  <span className="text-sm text-neutral-500">
                    Delivered on {formatDate(delivery.delivered_at)}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Status Action Buttons */}
          <div className="flex space-x-3">
            {delivery.delivery_status === 'pending' && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => updateStatus('in_transit')}
                  disabled={updating}
                  className="flex items-center space-x-2"
                >
                  <TruckIcon className="h-4 w-4" />
                  <span>Mark In Transit</span>
                </Button>
                <Button
                  variant="error"
                  size="sm"
                  onClick={() => updateStatus('failed')}
                  disabled={updating}
                  className="flex items-center space-x-2"
                >
                  <ClockIcon className="h-4 w-4" />
                  <span>Mark Failed</span>
                </Button>
              </>
            )}
            
            {delivery.delivery_status === 'in_transit' && (
              <>
                <Button
                  variant="success"
                  size="sm"
                  onClick={() => updateStatus('delivered')}
                  disabled={updating}
                  className="flex items-center space-x-2"
                >
                  <CheckCircleIcon className="h-4 w-4" />
                  <span>Mark Delivered</span>
                </Button>
                <Button
                  variant="error"
                  size="sm"
                  onClick={() => updateStatus('failed')}
                  disabled={updating}
                  className="flex items-center space-x-2"
                >
                  <ClockIcon className="h-4 w-4" />
                  <span>Mark Failed</span>
                </Button>
              </>
            )}
            
            {delivery.delivery_status === 'failed' && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => updateStatus('in_transit')}
                disabled={updating}
                className="flex items-center space-x-2"
              >
                <TruckIcon className="h-4 w-4" />
                <span>Retry Delivery</span>
              </Button>
            )}
            
            {delivery.delivery_status === 'delivered' && (
              <div className="text-sm text-neutral-500 italic">
                Delivery completed - no further actions available
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Delivery Details Card */}
      <Card>
        <CardHeader title="Delivery Details" />
        <CardBody className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-neutral-700">Scheduled Date</label>
              <p className="text-neutral-900">{formatDate(delivery.delivery_date)}</p>
            </div>
            
            <div>
              <label className="text-sm font-medium text-neutral-700">Delivery Location</label>
              <div className="flex items-start space-x-2">
                <MapPinIcon className="h-4 w-4 text-neutral-500 mt-0.5" />
                <p className="text-neutral-900">{delivery.delivery_location}</p>
              </div>
            </div>
          </div>

          {delivery.delivered_at && (
            <div>
              <label className="text-sm font-medium text-neutral-700">Delivered At</label>
              <p className="text-neutral-900">{formatDate(delivery.delivered_at)}</p>
            </div>
          )}

          {delivery.delivery_confirmed_by && (
            <div>
              <label className="text-sm font-medium text-neutral-700">Confirmed By</label>
              <p className="text-neutral-900">User ID: {delivery.delivery_confirmed_by}</p>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Delivery Notes Card */}
      {delivery.delivery_notes && (
        <Card>
          <CardHeader title="Delivery Notes" />
          <CardBody>
            <div className="bg-neutral-50 rounded-lg p-4">
              <pre className="text-sm text-neutral-700 whitespace-pre-wrap font-sans">
                {delivery.delivery_notes}
              </pre>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Delivery History Card */}
      <Card>
        <CardHeader title="Delivery History" />
        <CardBody>
          <div className="space-y-3">
            {/* Order created entry */}
            <div className="flex items-center space-x-3 text-sm">
              <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
              <span className="text-neutral-600">Order created</span>
              <span className="text-neutral-400">•</span>
              <span className="text-neutral-500">Initial status: PENDING</span>
            </div>
            
            {/* Real history entries from API */}
            {history?.history && history.history.length > 0 ? (
              history.history.map((entry, index) => (
                <div key={index} className="flex items-center space-x-3 text-sm">
                  <div className="w-2 h-2 bg-warning-500 rounded-full"></div>
                  <span className="text-neutral-600">{entry.note}</span>
                  <span className="text-neutral-400">•</span>
                  <span className="text-neutral-500">{entry.timestamp}</span>
                </div>
              ))
            ) : (
              delivery.delivery_status !== 'pending' && (
                <div className="flex items-center space-x-3 text-sm">
                  <div className="w-2 h-2 bg-warning-500 rounded-full"></div>
                  <span className="text-neutral-600">Status updated</span>
                  <span className="text-neutral-400">•</span>
                  <span className="text-neutral-500">Current status: {delivery.delivery_status.toUpperCase()}</span>
                </div>
              )
            )}
            
            {/* Delivery completed entry */}
            {delivery.delivered_at && (
              <div className="flex items-center space-x-3 text-sm">
                <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                <span className="text-neutral-600">Delivery completed</span>
                <span className="text-neutral-400">•</span>
                <span className="text-neutral-500">{formatDate(delivery.delivered_at)}</span>
              </div>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default DeliveryTab;
