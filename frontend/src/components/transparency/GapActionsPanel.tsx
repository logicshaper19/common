/**
 * Gap Actions Panel Component
 * Provides actionable buttons for resolving transparency gaps
 */
import React, { useState } from 'react';
import {
  EnvelopeIcon,
  PhoneIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { TransparencyGap } from '../../hooks/useDeterministicTransparency';
import { useToast } from '../../contexts/ToastContext';
import Button from '../ui/Button';
import { GapActionModal } from './GapActionModal';
import { gapActionsApi } from '../../services/gapActionsApi';
import { useAuth } from '../../contexts/AuthContext';

export interface GapActionRequest {
  action_type: 'request_data' | 'contact_supplier' | 'mark_resolved';
  target_company_id?: string;
  message?: string;
}

interface GapActionsPanelProps {
  gap: TransparencyGap;
  onActionCreated: () => void;
  className?: string;
}

export const GapActionsPanel: React.FC<GapActionsPanelProps> = ({
  gap,
  onActionCreated,
  className = ''
}) => {
  const { showToast } = useToast();
  const { user } = useAuth();
  const [showActionModal, setShowActionModal] = useState(false);
  const [actionType, setActionType] = useState<GapActionRequest['action_type']>('request_data');
  const [loading, setLoading] = useState(false);

  const handleCreateAction = async (actionData: GapActionRequest) => {
    if (!user?.company?.id) {
      showToast({
        type: 'error',
        title: 'Authentication Error',
        message: 'User company information not available.'
      });
      return;
    }

    try {
      setLoading(true);

      // Use actual API call
      await gapActionsApi.createGapAction(
        user.company.id,
        gap.po_id, // Using po_id as gap_id
        actionData
      );

      showToast({
        type: 'success',
        title: 'Action Created',
        message: `Gap action "${actionData.action_type}" created successfully`
      });

      setShowActionModal(false);
      onActionCreated();
    } catch (error: any) {
      console.error('Failed to create gap action:', error);
      showToast({
        type: 'error',
        title: 'Action Failed',
        message: error.response?.data?.detail || 'Failed to create gap action. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const getActionButtons = () => {
    const buttons = [];
    
    // Request Data button - for gaps that need more information
    if (gap.gap_type === 'not_traced_to_mill' || gap.gap_type === 'not_traced_to_plantation') {
      buttons.push(
        <Button
          key="request-data"
          size="sm"
          variant="outline"
          onClick={() => {
            setActionType('request_data');
            setShowActionModal(true);
          }}
          className="flex items-center space-x-1 text-xs"
        >
          <EnvelopeIcon className="h-3 w-3" />
          <span>Request Data</span>
        </Button>
      );
      
      // Contact Supplier button - for direct communication
      buttons.push(
        <Button
          key="contact-supplier"
          size="sm"
          variant="outline"
          onClick={() => {
            setActionType('contact_supplier');
            setShowActionModal(true);
          }}
          className="flex items-center space-x-1 text-xs"
        >
          <PhoneIcon className="h-3 w-3" />
          <span>Contact</span>
        </Button>
      );
    }
    
    // Mark Resolved button - always available
    buttons.push(
      <Button
        key="mark-resolved"
        size="sm"
        variant="secondary"
        onClick={() => {
          setActionType('mark_resolved');
          setShowActionModal(true);
        }}
        className="flex items-center space-x-1 text-xs"
      >
        <CheckCircleIcon className="h-3 w-3" />
        <span>Resolve</span>
      </Button>
    );
    
    return buttons;
  };

  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {getActionButtons()}
      
      {showActionModal && (
        <GapActionModal
          isOpen={showActionModal}
          onClose={() => setShowActionModal(false)}
          actionType={actionType}
          gap={gap}
          onSubmit={handleCreateAction}
          loading={loading}
        />
      )}
    </div>
  );
};

export default GapActionsPanel;
