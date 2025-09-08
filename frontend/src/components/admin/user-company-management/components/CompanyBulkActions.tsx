/**
 * Company bulk actions component
 */
import React from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { CompanyBulkOperation } from '../../../../types/admin';

interface CompanyBulkActionsProps {
  selectedCount: number;
  onBulkOperation: (operation: CompanyBulkOperation['operation']) => Promise<void>;
  onClearSelection: () => void;
}

export function CompanyBulkActions({
  selectedCount,
  onBulkOperation,
  onClearSelection,
}: CompanyBulkActionsProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <CheckCircleIcon className="h-5 w-5 text-blue-600 mr-2" />
          <span className="text-sm font-medium text-blue-900">
            {selectedCount} compan{selectedCount !== 1 ? 'ies' : 'y'} selected
          </span>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex space-x-2">
            <button
              onClick={() => onBulkOperation('activate')}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              <CheckCircleIcon className="h-4 w-4 mr-1" />
              Activate
            </button>
            
            <button
              onClick={() => onBulkOperation('deactivate')}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-yellow-700 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
            >
              <XCircleIcon className="h-4 w-4 mr-1" />
              Deactivate
            </button>
            
            <button
              onClick={() => onBulkOperation('verify')}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <CheckCircleIcon className="h-4 w-4 mr-1" />
              Verify
            </button>
          </div>
          
          <button
            onClick={onClearSelection}
            className="inline-flex items-center px-2 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
