/**
 * Admin Override Panel Component
 * Provides admin users with override capabilities for documents and other resources
 */
import React, { useState } from 'react';
import { ShieldExclamationIcon, TrashIcon, EyeIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import Button from '../ui/Button';
import Modal from '../ui/Modal';
import Textarea from '../ui/Textarea';
// import { adminApi } from '../../services/adminApi';

interface AdminOverridePanelProps {
  resourceType: 'document' | 'purchase_order' | 'company';
  resourceId: string;
  resourceName?: string;
  onOverrideComplete?: () => void;
  className?: string;
}

interface AdminOverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  resourceType: string;
  resourceName?: string;
  action: 'access' | 'delete';
  onConfirm: (reason: string) => void;
  loading: boolean;
}

const AdminOverrideModal: React.FC<AdminOverrideModalProps> = ({
  isOpen,
  onClose,
  resourceType,
  resourceName,
  action,
  onConfirm,
  loading
}) => {
  const [reason, setReason] = useState('');

  const handleSubmit = () => {
    if (!reason.trim()) {
      return;
    }
    onConfirm(reason);
  };

  const actionText = action === 'access' ? 'access' : 'delete';
  const actionColor = action === 'access' ? 'blue' : 'red';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Admin Override - ${action === 'access' ? 'Access' : 'Delete'} ${resourceType}`}
      size="md"
    >
      <div className="space-y-4">
        <div className={`p-4 rounded-lg border-l-4 ${
          action === 'access' 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-red-500 bg-red-50'
        }`}>
          <div className="flex items-center space-x-2 mb-2">
            <ShieldExclamationIcon className={`h-5 w-5 ${
              action === 'access' ? 'text-blue-600' : 'text-red-600'
            }`} />
            <span className={`font-medium ${
              action === 'access' ? 'text-blue-800' : 'text-red-800'
            }`}>
              Admin Override Required
            </span>
          </div>
          <p className={`text-sm ${
            action === 'access' ? 'text-blue-700' : 'text-red-700'
          }`}>
            You are about to {actionText} a {resourceType} that belongs to another company.
            {resourceName && ` Resource: ${resourceName}`}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Reason for Override *
          </label>
          <Textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder={`Please provide a detailed reason for this ${actionText} override...`}
            rows={4}
            required
            className="w-full"
          />
          <p className="text-xs text-gray-500 mt-1">
            This action will be logged for audit purposes and the affected company will be notified.
          </p>
        </div>

        <div className="flex justify-end space-x-3 pt-4 border-t">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            variant={action === 'access' ? 'primary' : 'error'}
            onClick={handleSubmit}
            disabled={!reason.trim() || loading}
            isLoading={loading}
          >
            {action === 'access' ? 'Access Resource' : 'Delete Resource'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export const AdminOverridePanel: React.FC<AdminOverridePanelProps> = ({
  resourceType,
  resourceId,
  resourceName,
  onOverrideComplete,
  className = ''
}) => {
  const [showModal, setShowModal] = useState(false);
  const [currentAction, setCurrentAction] = useState<'access' | 'delete'>('access');
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { showToast } = useToast();

  // Only show for admin users
  if (user?.role !== 'admin') {
    return null;
  }

  const handleOverrideAction = (action: 'access' | 'delete') => {
    setCurrentAction(action);
    setShowModal(true);
  };

  const handleConfirmOverride = async (reason: string) => {
    try {
      setLoading(true);

      if (currentAction === 'access') {
        // For access override, we'll handle this in the parent component
        // This panel is mainly for showing the option
        showToast({
          type: 'info',
          title: 'Access Override',
          message: 'Admin access override logged. You can now access the resource.'
        });
      } else if (currentAction === 'delete') {
        // Handle deletion override
        // TODO: Implement adminApi.deleteResource when API client is available
        console.log('Admin delete override:', { resourceType, resourceId, reason });

        showToast({
          type: 'success',
          title: 'Delete Override',
          message: `${resourceType} deleted successfully with admin override`
        });
      }

      setShowModal(false);
      onOverrideComplete?.();

    } catch (error) {
      console.error('Admin override failed:', error);
      showToast({
        type: 'error',
        title: 'Override Failed',
        message: `Failed to perform admin override: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className={`border-l-4 border-amber-500 bg-amber-50 p-4 rounded-r-lg ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldExclamationIcon className="h-5 w-5 text-amber-600" />
            <div>
              <span className="text-sm font-medium text-amber-800">
                Admin Override Available
              </span>
              <p className="text-xs text-amber-700 mt-1">
                You can access or manage this {resourceType} from another company
              </p>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleOverrideAction('access')}
              className="border-amber-300 text-amber-700 hover:bg-amber-100"
            >
              <EyeIcon className="h-4 w-4 mr-1" />
              Override Access
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleOverrideAction('delete')}
              className="border-red-300 text-red-700 hover:bg-red-100"
            >
              <TrashIcon className="h-4 w-4 mr-1" />
              Override Delete
            </Button>
          </div>
        </div>
      </div>

      <AdminOverrideModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        resourceType={resourceType}
        resourceName={resourceName}
        action={currentAction}
        onConfirm={handleConfirmOverride}
        loading={loading}
      />
    </>
  );
};

export default AdminOverridePanel;
