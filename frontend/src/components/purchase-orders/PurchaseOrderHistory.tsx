import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  User, 
  CheckCircle, 
  AlertTriangle, 
  FileText, 
  Package,
  UserCheck,
  XCircle,
  Edit
} from 'lucide-react';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';

interface HistoryEntry {
  id: string;
  action_type: string;
  action_description: string;
  user_id: string;
  company_id: string;
  changes_data?: Record<string, any>;
  created_at: string;
}

interface PurchaseOrderHistoryProps {
  purchaseOrderId: string;
  className?: string;
}

const PurchaseOrderHistory: React.FC<PurchaseOrderHistoryProps> = ({
  purchaseOrderId,
  className = ''
}) => {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, [purchaseOrderId]);

  const fetchHistory = async () => {
    try {
      setIsLoading(true);
      const response = await api.get(`/api/v1/purchase-orders/${purchaseOrderId}/history`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching PO history:', error);
      toast.error('Failed to load order history');
    } finally {
      setIsLoading(false);
    }
  };

  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'created':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'seller_confirmed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'seller_confirmed_with_discrepancies':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'buyer_approved':
        return <UserCheck className="h-4 w-4 text-green-500" />;
      case 'buyer_rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'confirmed':
        return <CheckCircle className="h-4 w-4 text-emerald-500" />;
      case 'batch_created':
        return <Package className="h-4 w-4 text-purple-500" />;
      case 'amendment_proposed':
        return <Edit className="h-4 w-4 text-orange-500" />;
      case 'amendment_approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'amendment_rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getActionColor = (actionType: string) => {
    switch (actionType) {
      case 'created':
        return 'border-blue-200 bg-blue-50';
      case 'seller_confirmed':
      case 'buyer_approved':
      case 'confirmed':
        return 'border-green-200 bg-green-50';
      case 'seller_confirmed_with_discrepancies':
        return 'border-amber-200 bg-amber-50';
      case 'buyer_rejected':
        return 'border-red-200 bg-red-50';
      case 'batch_created':
        return 'border-purple-200 bg-purple-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Order History</h3>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const displayedHistory = isExpanded ? history : history.slice(0, 5);

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Order History</h3>
        {history.length > 5 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {isExpanded ? 'Show Less' : `Show All (${history.length})`}
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <p className="text-gray-500 text-center py-4">No history available</p>
      ) : (
        <div className="space-y-4">
          {displayedHistory.map((entry, index) => (
            <div
              key={entry.id}
              className={`flex space-x-3 p-3 rounded-lg border ${getActionColor(entry.action_type)}`}
            >
              <div className="flex-shrink-0 mt-0.5">
                {getActionIcon(entry.action_type)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {entry.action_description}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {formatDate(entry.created_at)}
                </p>
                {entry.changes_data && Object.keys(entry.changes_data).length > 0 && (
                  <div className="mt-2 text-xs text-gray-600">
                    {entry.action_type === 'seller_confirmed_with_discrepancies' && 
                     entry.changes_data.discrepancies && (
                      <div className="space-y-1">
                        <span className="font-medium">Changes:</span>
                        {entry.changes_data.discrepancies.map((disc: any, i: number) => (
                          <div key={i} className="ml-2">
                            • {disc.field}: {disc.original} → {disc.confirmed}
                          </div>
                        ))}
                      </div>
                    )}
                    {entry.action_type === 'batch_created' && entry.changes_data.batch_id && (
                      <span>Batch ID: {entry.changes_data.batch_id}</span>
                    )}
                    {(entry.action_type === 'buyer_approved' || entry.action_type === 'buyer_rejected') && 
                     entry.changes_data.buyer_notes && (
                      <div>
                        <span className="font-medium">Notes:</span> {entry.changes_data.buyer_notes}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PurchaseOrderHistory;
