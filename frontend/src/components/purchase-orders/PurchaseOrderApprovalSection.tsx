import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import DiscrepancyAlert from './DiscrepancyAlert';
import BuyerApprovalModal from './BuyerApprovalModal';
import { api } from '../../services/api';

interface DiscrepancyDetail {
  field_name: string;
  original_value: any;
  confirmed_value: any;
  difference?: string;
}

interface DiscrepancyResponse {
  has_discrepancies: boolean;
  discrepancies: DiscrepancyDetail[];
  requires_approval: boolean;
  seller_confirmation_data: Record<string, any>;
}

interface PurchaseOrder {
  id: string;
  po_number: string;
  status: string;
  seller_company: {
    id: string;
    name: string;
  };
  buyer_company: {
    id: string;
    name: string;
  };
}

interface PurchaseOrderApprovalSectionProps {
  purchaseOrder: PurchaseOrder;
  currentUserCompanyId: string;
  onOrderUpdated: () => void;
}

const PurchaseOrderApprovalSection: React.FC<PurchaseOrderApprovalSectionProps> = ({
  purchaseOrder,
  currentUserCompanyId,
  onOrderUpdated
}) => {
  const [discrepancies, setDiscrepancies] = useState<DiscrepancyResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [approvalAction, setApprovalAction] = useState<'approve' | 'reject'>('approve');

  // Check if current user is buyer and PO is awaiting approval
  const isBuyer = currentUserCompanyId === purchaseOrder.buyer_company.id;
  const isAwaitingApproval = purchaseOrder.status === 'awaiting_buyer_approval';
  const shouldShowApproval = isBuyer && isAwaitingApproval;

  useEffect(() => {
    if (shouldShowApproval) {
      fetchDiscrepancies();
    }
  }, [shouldShowApproval, purchaseOrder.id]);

  const fetchDiscrepancies = async () => {
    try {
      setIsLoading(true);
      const response = await api.get(`/api/v1/purchase-orders/${purchaseOrder.id}/discrepancies`);
      setDiscrepancies(response.data);
    } catch (error) {
      console.error('Error fetching discrepancies:', error);
      toast.error('Failed to load discrepancy details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprovalAction = (action: 'approve' | 'reject') => {
    setApprovalAction(action);
    setApprovalModalOpen(true);
  };

  const handleApprovalSubmit = async (notes?: string) => {
    try {
      setIsLoading(true);
      
      await api.post(`/api/v1/purchase-orders/${purchaseOrder.id}/buyer-approve`, {
        approve: approvalAction === 'approve',
        buyer_notes: notes
      });

      toast.success(
        approvalAction === 'approve' 
          ? 'Changes approved successfully!' 
          : 'Revision requested successfully!'
      );
      
      setApprovalModalOpen(false);
      onOrderUpdated();
    } catch (error: any) {
      console.error('Error processing approval:', error);
      toast.error(
        error.response?.data?.detail || 
        `Failed to ${approvalAction === 'approve' ? 'approve' : 'reject'} changes`
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Don't render anything if not applicable
  if (!shouldShowApproval || !discrepancies?.has_discrepancies) {
    return null;
  }

  return (
    <>
      <DiscrepancyAlert
        discrepancies={discrepancies.discrepancies}
        sellerCompanyName={purchaseOrder.seller_company.name}
        onApprove={() => handleApprovalAction('approve')}
        onReject={() => handleApprovalAction('reject')}
        isLoading={isLoading}
      />

      <BuyerApprovalModal
        isOpen={approvalModalOpen}
        onClose={() => setApprovalModalOpen(false)}
        onApprove={(notes) => handleApprovalSubmit(notes)}
        onReject={(notes) => handleApprovalSubmit(notes)}
        isLoading={isLoading}
        action={approvalAction}
        sellerCompanyName={purchaseOrder.seller_company.name}
        poNumber={purchaseOrder.po_number}
      />
    </>
  );
};

export default PurchaseOrderApprovalSection;
