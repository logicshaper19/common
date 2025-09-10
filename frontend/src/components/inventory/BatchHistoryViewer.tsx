/**
 * Batch History Viewer Component
 * Displays batch transaction history and audit trail
 */
import React, { useState, useEffect } from 'react';
import {
  ClockIcon,
  ArrowRightIcon,
  UserIcon,
  MapPinIcon,
  CubeIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Badge from '../ui/Badge';
import LoadingSpinner from '../ui/LoadingSpinner';
import { formatDate } from '../../lib/utils';

interface BatchTransaction {
  id: string;
  transaction_type: 'creation' | 'consumption' | 'transformation' | 'transfer' | 'split' | 'merge';
  quantity: number;
  unit: string;
  timestamp: string;
  user_name: string;
  user_role: string;
  location_from?: string;
  location_to?: string;
  notes?: string;
  related_batch_id?: string;
  related_po_id?: string;
  quality_metrics?: Record<string, any>;
}

interface BatchRelationship {
  id: string;
  relationship_type: 'parent' | 'child' | 'split_from' | 'merged_into';
  related_batch_id: string;
  related_batch_name: string;
  quantity_transferred: number;
  unit: string;
  timestamp: string;
}

interface BatchHistoryViewerProps {
  batchId: string;
  className?: string;
}

const BatchHistoryViewer: React.FC<BatchHistoryViewerProps> = ({ 
  batchId, 
  className = '' 
}) => {
  // State
  const [transactions, setTransactions] = useState<BatchTransaction[]>([]);
  const [relationships, setRelationships] = useState<BatchRelationship[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load batch history
  useEffect(() => {
    loadBatchHistory();
  }, [batchId]);

  const loadBatchHistory = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // TODO: Replace with actual API calls
      // Simulated data for now
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setTransactions([
        {
          id: '1',
          transaction_type: 'creation',
          quantity: 1000,
          unit: 'KGM',
          timestamp: '2025-01-10T10:30:00Z',
          user_name: 'John Doe',
          user_role: 'Plantation Manager',
          location_to: 'Plantation A - Sector 1',
          notes: 'Fresh harvest from Block A-12',
          related_po_id: 'PO-2025-001',
          quality_metrics: {
            oil_content: 22.5,
            moisture: 18.2,
            free_fatty_acid: 2.1
          }
        },
        {
          id: '2',
          transaction_type: 'transfer',
          quantity: 1000,
          unit: 'KGM',
          timestamp: '2025-01-10T14:20:00Z',
          user_name: 'Transport Team',
          user_role: 'Logistics',
          location_from: 'Plantation A - Sector 1',
          location_to: 'Mill A - Receiving Bay',
          notes: 'Transported via Truck T-001'
        },
        {
          id: '3',
          transaction_type: 'transformation',
          quantity: 750,
          unit: 'KGM',
          timestamp: '2025-01-11T09:15:00Z',
          user_name: 'Mill Operator',
          user_role: 'Production',
          location_from: 'Mill A - Receiving Bay',
          location_to: 'Mill A - Processing Line 1',
          notes: 'Processed into crude palm oil',
          related_batch_id: 'PROCESS-2025-001',
          quality_metrics: {
            extraction_rate: 75.0,
            oil_quality: 'Grade A'
          }
        },
        {
          id: '4',
          transaction_type: 'consumption',
          quantity: 750,
          unit: 'KGM',
          timestamp: '2025-01-11T16:45:00Z',
          user_name: 'Production Manager',
          user_role: 'Production',
          location_from: 'Mill A - Processing Line 1',
          notes: 'Fully consumed in production process'
        }
      ]);

      setRelationships([
        {
          id: '1',
          relationship_type: 'child',
          related_batch_id: 'PROCESS-2025-001',
          related_batch_name: 'Crude Palm Oil Batch',
          quantity_transferred: 750,
          unit: 'KGM',
          timestamp: '2025-01-11T09:15:00Z'
        }
      ]);

    } catch (err) {
      console.error('Error loading batch history:', err);
      setError('Failed to load batch history. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Get transaction icon
  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'creation':
        return <CubeIcon className="h-5 w-5 text-green-500" />;
      case 'consumption':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'transformation':
        return <ArrowRightIcon className="h-5 w-5 text-blue-500" />;
      case 'transfer':
        return <MapPinIcon className="h-5 w-5 text-purple-500" />;
      case 'split':
        return <DocumentTextIcon className="h-5 w-5 text-yellow-500" />;
      case 'merge':
        return <DocumentTextIcon className="h-5 w-5 text-orange-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  // Get transaction badge variant
  const getTransactionBadgeVariant = (type: string) => {
    switch (type) {
      case 'creation':
        return 'success';
      case 'consumption':
        return 'error';
      case 'transformation':
        return 'primary';
      case 'transfer':
        return 'secondary';
      default:
        return 'neutral';
    }
  };

  // Format transaction type for display
  const formatTransactionType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center py-8 ${className}`}>
        <LoadingSpinner size="md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <p className="text-red-600 mb-4">{error}</p>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Batch Relationships */}
      {relationships.length > 0 && (
        <Card className="mb-6">
          <CardHeader title="Batch Relationships" subtitle="Connected batches" />
          <CardBody padding="none">
            <div className="divide-y divide-gray-200">
              {relationships.map((relationship) => (
                <div key={relationship.id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <Badge variant="secondary">
                        {relationship.relationship_type.replace('_', ' ')}
                      </Badge>
                      <div>
                        <div className="font-medium text-gray-900">
                          {relationship.related_batch_id}
                        </div>
                        <div className="text-sm text-gray-600">
                          {relationship.related_batch_name}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {relationship.quantity_transferred} {relationship.unit}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatDate(relationship.timestamp)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Transaction History */}
      <Card>
        <CardHeader title="Transaction History" subtitle="Complete audit trail" />
        <CardBody padding="none">
          {transactions.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No transaction history available
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {transactions.map((transaction, index) => (
                <div key={transaction.id} className="p-6">
                  <div className="flex items-start space-x-4">
                    {/* Timeline indicator */}
                    <div className="flex flex-col items-center">
                      <div className="flex items-center justify-center w-10 h-10 bg-white border-2 border-gray-300 rounded-full">
                        {getTransactionIcon(transaction.transaction_type)}
                      </div>
                      {index < transactions.length - 1 && (
                        <div className="w-0.5 h-16 bg-gray-200 mt-2"></div>
                      )}
                    </div>

                    {/* Transaction details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <Badge variant={getTransactionBadgeVariant(transaction.transaction_type)}>
                            {formatTransactionType(transaction.transaction_type)}
                          </Badge>
                          <span className="text-sm font-medium text-gray-900">
                            {transaction.quantity} {transaction.unit}
                          </span>
                        </div>
                        <div className="text-sm text-gray-500">
                          {formatDate(transaction.timestamp)}
                        </div>
                      </div>

                      {/* Location information */}
                      {(transaction.location_from || transaction.location_to) && (
                        <div className="flex items-center space-x-2 mb-2">
                          <MapPinIcon className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">
                            {transaction.location_from && (
                              <>
                                From: <span className="font-medium">{transaction.location_from}</span>
                              </>
                            )}
                            {transaction.location_from && transaction.location_to && (
                              <span className="mx-2">→</span>
                            )}
                            {transaction.location_to && (
                              <>
                                To: <span className="font-medium">{transaction.location_to}</span>
                              </>
                            )}
                          </span>
                        </div>
                      )}

                      {/* User information */}
                      <div className="flex items-center space-x-2 mb-2">
                        <UserIcon className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          <span className="font-medium">{transaction.user_name}</span>
                          <span className="text-gray-500"> ({transaction.user_role})</span>
                        </span>
                      </div>

                      {/* Related references */}
                      {(transaction.related_batch_id || transaction.related_po_id) && (
                        <div className="flex items-center space-x-4 mb-2">
                          {transaction.related_batch_id && (
                            <div className="text-sm text-gray-600">
                              Related Batch: <span className="font-medium">{transaction.related_batch_id}</span>
                            </div>
                          )}
                          {transaction.related_po_id && (
                            <div className="text-sm text-gray-600">
                              Purchase Order: <span className="font-medium">{transaction.related_po_id}</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Notes */}
                      {transaction.notes && (
                        <div className="text-sm text-gray-600 mb-2">
                          <span className="font-medium">Notes:</span> {transaction.notes}
                        </div>
                      )}

                      {/* Quality metrics */}
                      {transaction.quality_metrics && (
                        <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                          <div className="text-sm font-medium text-gray-700 mb-2">Quality Metrics:</div>
                          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                            {Object.entries(transaction.quality_metrics).map(([key, value]) => (
                              <div key={key} className="text-xs">
                                <span className="text-gray-500 capitalize">
                                  {key.replace('_', ' ')}:
                                </span>
                                <span className="ml-1 font-medium text-gray-900">
                                  {typeof value === 'number' ? value.toFixed(1) : value}
                                  {key.includes('rate') || key.includes('content') ? '%' : ''}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
};

export default BatchHistoryViewer;
