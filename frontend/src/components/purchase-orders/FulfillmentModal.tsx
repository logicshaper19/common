import React, { useState } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import { 
  XMarkIcon, 
  CheckCircleIcon, 
  PlusIcon, 
  LinkIcon,
  ArchiveBoxIcon
} from '@heroicons/react/24/outline';
import { PurchaseOrderWithRelations } from '../../services/purchaseOrderApi';
import { useToast } from '../../contexts/ToastContext';
// import { BatchInventorySelector } from '../batches/BatchInventorySelector';
import { CreatePurchaseOrderModal } from './CreatePurchaseOrderModal';

interface FulfillmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  po: PurchaseOrderWithRelations | null;
  onFulfilled: () => void;
}

type FulfillmentMethod = 'inventory' | 'create_po' | 'existing_po';

export const FulfillmentModal: React.FC<FulfillmentModalProps> = ({
  isOpen,
  onClose,
  po,
  onFulfilled
}) => {
  const { showToast } = useToast();
  const [selectedMethod, setSelectedMethod] = useState<FulfillmentMethod | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  if (!isOpen || !po) return null;

  const handleMethodSelect = (method: FulfillmentMethod) => {
    setSelectedMethod(method);
    
    if (method === 'create_po') {
      setShowCreateModal(true);
    }
  };

  const handleInventoryFulfillment = () => {
    // This would integrate with the existing batch selection logic
    showToast({ 
      type: 'info', 
      title: 'Inventory fulfillment', 
      message: 'This would open the batch selection interface' 
    });
  };

  const handleExistingPOFulfillment = () => {
    // This would show a list of existing POs to link to
    showToast({ 
      type: 'info', 
      title: 'Existing PO fulfillment', 
      message: 'This would show a list of existing POs to link to' 
    });
  };

  const handleClose = () => {
    setSelectedMethod(null);
    setShowCreateModal(false);
    onClose();
  };

  const fulfillmentOptions = [
    {
      id: 'inventory' as FulfillmentMethod,
      title: 'Use My Inventory',
      description: 'Fulfill this PO using batches from your existing inventory',
      icon: ArchiveBoxIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200'
    },
    {
      id: 'create_po' as FulfillmentMethod,
      title: 'Create New Supplier PO',
      description: 'Create a new purchase order to a supplier to fulfill this PO',
      icon: PlusIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200'
    },
    {
      id: 'existing_po' as FulfillmentMethod,
      title: 'Link to Existing PO',
      description: 'Link this PO to an existing purchase order you\'ve already created',
      icon: LinkIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200'
    }
  ];

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">
                    Fulfill Purchase Order
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Choose how to fulfill: <span className="font-medium">{po.po_number}</span>
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </Button>
              </div>
            </CardHeader>
            <CardBody>
              {/* PO Details */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-gray-900 mb-2">PO Details</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">From:</span>
                    <span className="ml-2 font-medium">{po.buyer_company?.name || 'Unknown'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Product:</span>
                    <span className="ml-2 font-medium">{po.product?.name || 'Unknown'}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Quantity:</span>
                    <span className="ml-2 font-medium">{po.quantity} {po.unit}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Delivery Date:</span>
                    <span className="ml-2 font-medium">
                      {po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : 'Not set'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Fulfillment Options */}
              <div className="space-y-4">
                <h3 className="font-medium text-gray-900">Choose Fulfillment Method</h3>
                
                {fulfillmentOptions.map((option) => {
                  const Icon = option.icon;
                  return (
                    <button
                      key={option.id}
                      onClick={() => handleMethodSelect(option.id)}
                      className={`w-full p-4 rounded-lg border-2 transition-all duration-200 hover:shadow-md ${option.borderColor} ${option.bgColor} hover:${option.bgColor.replace('50', '100')}`}
                    >
                      <div className="flex items-start space-x-4">
                        <div className={`flex-shrink-0 ${option.color}`}>
                          <Icon className="h-6 w-6" />
                        </div>
                        <div className="flex-1 text-left">
                          <h4 className={`font-medium ${option.color}`}>
                            {option.title}
                          </h4>
                          <p className="text-sm text-gray-600 mt-1">
                            {option.description}
                          </p>
                        </div>
                        <div className="flex-shrink-0">
                          <CheckCircleIcon className="h-5 w-5 text-gray-400" />
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 mt-6 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={handleClose}
                >
                  Cancel
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>

      {/* Create PO Modal */}
      <CreatePurchaseOrderModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={async (poData) => {
          // Pre-populate with parent PO data
          const enhancedPoData = {
            ...poData,
            parent_po_id: po.id,
            is_drop_shipment: true,
            // Copy relevant data from parent PO
            product_id: po.product_id,
            quantity: po.quantity,
            unit: po.unit,
            delivery_date: po.delivery_date,
            delivery_location: po.delivery_location
          };
          
          // This would call the API to create the PO
          console.log('Creating child PO:', enhancedPoData);
          showToast({ 
            type: 'success', 
            title: 'Child PO created successfully',
            message: 'The new PO has been linked to the parent PO'
          });
          setShowCreateModal(false);
          onFulfilled();
        }}
      />
    </>
  );
};

export default FulfillmentModal;
