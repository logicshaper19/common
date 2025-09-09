import React from 'react';
import { Package, Calendar, MapPin, AlertTriangle, CheckCircle, Info, Zap } from 'lucide-react';

interface Batch {
  id: string;
  batch_id: string;
  quantity: number;
  unit: string;
  production_date: string;
  expiry_date?: string;
  location_name?: string;
  facility_code?: string;
  quality_metrics?: Record<string, any>;
  batch_metadata?: {
    days_until_expiry?: number;
    is_expiring_soon?: boolean;
    fifo_priority?: number;
  };
}

interface InventoryBatchCardProps {
  batch: Batch;
  selectedQuantity: number;
  onQuantityChange: (quantity: number) => void;
  disabled?: boolean;
  showFifoPriority?: boolean;
}

const InventoryBatchCard: React.FC<InventoryBatchCardProps> = ({
  batch,
  selectedQuantity,
  onQuantityChange,
  disabled = false,
  showFifoPriority = true
}) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getCardStyle = () => {
    if (batch.batch_metadata?.is_expiring_soon) {
      return 'border-amber-300 bg-amber-50 shadow-amber-100';
    }
    if (selectedQuantity > 0) {
      return 'border-blue-300 bg-blue-50 shadow-blue-100';
    }
    return 'border-gray-200 bg-white hover:border-gray-300';
  };

  const getStatusIcon = () => {
    if (batch.batch_metadata?.is_expiring_soon) {
      return <AlertTriangle className="h-4 w-4 text-amber-500" />;
    }
    if (selectedQuantity > 0) {
      return <CheckCircle className="h-4 w-4 text-blue-500" />;
    }
    return <Package className="h-4 w-4 text-gray-400" />;
  };

  const getExpiryWarning = () => {
    if (!batch.batch_metadata?.days_until_expiry) return null;
    
    const days = batch.batch_metadata.days_until_expiry;
    if (days <= 7) {
      return `Expires in ${days} day${days !== 1 ? 's' : ''}`;
    }
    if (days <= 30) {
      return `Expires in ${days} days`;
    }
    return null;
  };

  const handleQuantityInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value) || 0;
    const validQuantity = Math.max(0, Math.min(value, batch.quantity));
    onQuantityChange(validQuantity);
  };

  const handleQuickSelect = (percentage: number) => {
    const quantity = (batch.quantity * percentage) / 100;
    onQuantityChange(Math.round(quantity * 1000) / 1000); // Round to 3 decimal places
  };

  const utilizationPercentage = (selectedQuantity / batch.quantity) * 100;

  return (
    <div className={`border rounded-lg p-4 transition-all duration-200 shadow-sm ${getCardStyle()}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="font-semibold text-gray-900">{batch.batch_id}</span>
          {showFifoPriority && batch.batch_metadata?.fifo_priority && (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full flex items-center space-x-1">
              <Zap className="h-3 w-3" />
              <span>FIFO #{batch.batch_metadata.fifo_priority}</span>
            </span>
          )}
        </div>
        
        {getExpiryWarning() && (
          <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">
            {getExpiryWarning()}
          </span>
        )}
      </div>

      {/* Batch Details */}
      <div className="grid grid-cols-2 gap-3 text-sm text-gray-600 mb-4">
        <div className="flex items-center space-x-1">
          <Package className="h-3 w-3" />
          <span>Available: {batch.quantity.toFixed(3)} {batch.unit}</span>
        </div>
        
        <div className="flex items-center space-x-1">
          <Calendar className="h-3 w-3" />
          <span>Produced: {formatDate(batch.production_date)}</span>
        </div>
        
        {batch.expiry_date && (
          <div className="flex items-center space-x-1">
            <Calendar className="h-3 w-3" />
            <span>Expires: {formatDate(batch.expiry_date)}</span>
          </div>
        )}
        
        {batch.location_name && (
          <div className="flex items-center space-x-1">
            <MapPin className="h-3 w-3" />
            <span>{batch.location_name}</span>
          </div>
        )}
        
        {batch.facility_code && (
          <div className="flex items-center space-x-1 col-span-2">
            <Info className="h-3 w-3" />
            <span>Facility: {batch.facility_code}</span>
          </div>
        )}
      </div>

      {/* Quantity Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Quantity to Use
          </label>
          <div className="flex items-center space-x-1">
            <input
              type="number"
              min="0"
              max={batch.quantity}
              step="0.001"
              value={selectedQuantity || ''}
              onChange={handleQuantityInputChange}
              disabled={disabled}
              className="w-20 px-2 py-1 border border-gray-300 rounded text-sm text-right focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
              placeholder="0"
            />
            <span className="text-sm text-gray-500">{batch.unit}</span>
          </div>
        </div>

        {/* Quick Selection Buttons */}
        {!disabled && (
          <div className="flex space-x-2">
            {[25, 50, 75, 100].map((percentage) => (
              <button
                key={percentage}
                onClick={() => handleQuickSelect(percentage)}
                className="flex-1 px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                {percentage}%
              </button>
            ))}
          </div>
        )}

        {/* Utilization Bar */}
        {selectedQuantity > 0 && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-600">
              <span>Utilization</span>
              <span>{utilizationPercentage.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  utilizationPercentage === 100 
                    ? 'bg-green-500' 
                    : utilizationPercentage > 75 
                    ? 'bg-blue-500' 
                    : 'bg-blue-400'
                }`}
                style={{ width: `${Math.min(utilizationPercentage, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Quality Metrics Preview */}
      {batch.quality_metrics && Object.keys(batch.quality_metrics).length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            Quality: {Object.keys(batch.quality_metrics).slice(0, 2).join(', ')}
            {Object.keys(batch.quality_metrics).length > 2 && '...'}
          </div>
        </div>
      )}
    </div>
  );
};

export default InventoryBatchCard;
