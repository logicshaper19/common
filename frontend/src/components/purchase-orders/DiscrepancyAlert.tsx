import React from 'react';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface DiscrepancyDetail {
  field_name: string;
  original_value: any;
  confirmed_value: any;
  difference?: string;
}

interface DiscrepancyAlertProps {
  discrepancies: DiscrepancyDetail[];
  sellerCompanyName: string;
  onApprove: () => void;
  onReject: () => void;
  isLoading?: boolean;
}

const DiscrepancyAlert: React.FC<DiscrepancyAlertProps> = ({
  discrepancies,
  sellerCompanyName,
  onApprove,
  onReject,
  isLoading = false
}) => {
  const formatFieldName = (fieldName: string): string => {
    const fieldMap: Record<string, string> = {
      quantity: 'Quantity',
      unit_price: 'Unit Price',
      delivery_date: 'Delivery Date',
      delivery_location: 'Delivery Location'
    };
    return fieldMap[fieldName] || fieldName;
  };

  const formatValue = (fieldName: string, value: any): string => {
    if (value === null || value === undefined) return 'Not specified';
    
    switch (fieldName) {
      case 'quantity':
        return `${parseFloat(value).toLocaleString()} kg`;
      case 'unit_price':
        return `$${parseFloat(value).toFixed(2)}`;
      case 'delivery_date':
        return new Date(value).toLocaleDateString();
      case 'delivery_location':
        return value.toString();
      default:
        return value.toString();
    }
  };

  const getDiscrepancyIcon = (fieldName: string) => {
    switch (fieldName) {
      case 'quantity':
      case 'unit_price':
        return <AlertTriangle className="h-4 w-4 text-amber-500" />;
      case 'delivery_date':
      case 'delivery_location':
        return <AlertTriangle className="h-4 w-4 text-blue-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 mb-6">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="h-6 w-6 text-amber-600 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-amber-800 mb-2">
            🔄 Amendment Request from {sellerCompanyName}
          </h3>
          <p className="text-amber-700 mb-4">
            The seller has proposed the following changes to this purchase order:
          </p>

          <div className="space-y-4 mb-6">
            {discrepancies.map((discrepancy, index) => (
              <div key={index} className="bg-white rounded-lg border border-amber-200 p-4">
                <div className="flex items-center space-x-2 mb-3">
                  {getDiscrepancyIcon(discrepancy.field_name)}
                  <h4 className="font-medium text-gray-900">
                    {formatFieldName(discrepancy.field_name)}
                  </h4>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 block mb-1">Original:</span>
                    <span className="font-medium text-gray-900">
                      {formatValue(discrepancy.field_name, discrepancy.original_value)}
                    </span>
                  </div>
                  
                  <div>
                    <span className="text-gray-500 block mb-1">Proposed:</span>
                    <span className="font-medium text-blue-600">
                      {formatValue(discrepancy.field_name, discrepancy.confirmed_value)}
                    </span>
                  </div>
                  
                  {discrepancy.difference && (
                    <div>
                      <span className="text-gray-500 block mb-1">Change:</span>
                      <span className={`font-medium ${
                        discrepancy.difference.startsWith('+') ? 'text-green-600' : 
                        discrepancy.difference.startsWith('-') ? 'text-red-600' : 
                        'text-gray-600'
                      }`}>
                        {discrepancy.difference}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={onApprove}
              disabled={isLoading}
              className="flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <CheckCircle className="h-4 w-4" />
              <span>{isLoading ? 'Approving...' : 'Approve Changes'}</span>
            </button>
            
            <button
              onClick={onReject}
              disabled={isLoading}
              className="flex items-center justify-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <XCircle className="h-4 w-4" />
              <span>{isLoading ? 'Rejecting...' : 'Request Revision'}</span>
            </button>
          </div>

          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-700">
              <strong>Note:</strong> Approving these changes will update the purchase order with the seller's proposed values. 
              Requesting a revision will return the order to the seller for modification.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiscrepancyAlert;
