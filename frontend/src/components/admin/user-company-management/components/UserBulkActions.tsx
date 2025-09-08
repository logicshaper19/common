/**
 * User bulk actions component
 */
import React from 'react';
import {
  CheckCircleIcon,
  XCircleIcon,
  TrashIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { UserBulkOperation } from '../../../../types/admin';

interface UserBulkActionsProps {
  selectedCount: number;
  onBulkOperation: (operation: UserBulkOperation['operation']) => Promise<void>;
  onClearSelection: () => void;
}

export function UserBulkActions({
  selectedCount,
  onBulkOperation,
  onClearSelection,
}: UserBulkActionsProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <CheckCircleIcon className="h-5 w-5 text-blue-600 mr-2" />
          <span className="text-sm font-medium text-blue-900">
            {selectedCount} user{selectedCount !== 1 ? 's' : ''} selected
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
              onClick={() => onBulkOperation('delete')}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <TrashIcon className="h-4 w-4 mr-1" />
              Delete
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
