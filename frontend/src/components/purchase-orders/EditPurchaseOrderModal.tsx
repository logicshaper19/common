import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import TextArea from '../ui/Textarea';
import { XMarkIcon, PencilIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderWithRelations } from '../../services/purchaseOrderApi';
import { productsApi, Product } from '../../services/productsApi';
import { companiesApi, Company } from '../../services/companiesApi';
// import { useAuth } from '../../contexts/AuthContext'; // Not currently used
import { useToast } from '../../contexts/ToastContext';

interface EditPurchaseOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  po: PurchaseOrderWithRelations | null;
  onEdit: (editData: any) => Promise<void>;
  isLoading?: boolean;
}

export const EditPurchaseOrderModal: React.FC<EditPurchaseOrderModalProps> = ({
  isOpen,
  onClose,
  po,
  onEdit,
  isLoading = false
}) => {
  // const { user } = useAuth(); // Not currently used
  const { showToast } = useToast();
  
  const [formData, setFormData] = useState({
    quantity: 0,
    unit_price: 0,
    unit: '',
    delivery_date: '',
    delivery_location: '',
    notes: '',
    product_id: '',
    seller_company_id: '',
    edit_reason: '',
    requires_approval: true,
    edit_notes: ''
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [products, setProducts] = useState<Product[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  const loadData = useCallback(async () => {
    setLoadingData(true);
    try {
      const [productsResponse, companiesResponse] = await Promise.all([
        productsApi.getProducts({ per_page: 100 }),
        companiesApi.getBusinessPartners()
      ]);
      
      setProducts(productsResponse.products || []);
      setCompanies(companiesResponse);
    } catch (error) {
      console.error('Error loading data:', error);
      showToast({ type: 'error', title: 'Failed to load data' });
    } finally {
      setLoadingData(false);
    }
  }, [showToast]);

  // Load data when modal opens
  useEffect(() => {
    if (isOpen && po) {
      loadData();
      // Pre-populate form with PO data
      setFormData({
        quantity: po.quantity || 0,
        unit_price: po.unit_price || 0,
        unit: po.unit || '',
        delivery_date: (po.status === 'confirmed' && po.confirmed_delivery_date) 
          ? new Date(po.confirmed_delivery_date).toISOString().split('T')[0] 
          : (po.delivery_date ? new Date(po.delivery_date).toISOString().split('T')[0] : ''),
        delivery_location: po.delivery_location || '',
        notes: po.notes || '',
        product_id: po.product_id || '',
        seller_company_id: po.seller_company_id || '',
        edit_reason: '',
        requires_approval: true,
        edit_notes: ''
      });
    }
  }, [isOpen, po, loadData]);

  const handleInputChange = (field: string, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }

    // Auto-set unit when product is selected
    if (field === 'product_id') {
      const selectedProduct = products.find(p => p.id === value);
      if (selectedProduct) {
        setFormData(prev => ({
          ...prev,
          unit: selectedProduct.default_unit
        }));
      }
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.edit_reason.trim()) {
      newErrors.edit_reason = 'Please provide a reason for editing';
    }
    if (formData.edit_reason.trim().length < 10) {
      newErrors.edit_reason = 'Edit reason must be at least 10 characters';
    }

    if (formData.quantity <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0';
    }

    if (formData.unit_price <= 0) {
      newErrors.unit_price = 'Unit price must be greater than 0';
    }

    if (!formData.delivery_date) {
      newErrors.delivery_date = 'Please select a delivery date';
    }

    if (!formData.delivery_location.trim()) {
      newErrors.delivery_location = 'Please enter a delivery location';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      // Prepare edit data - only include fields that have changed
      const editData: any = {
        edit_reason: formData.edit_reason,
        requires_approval: formData.requires_approval,
        edit_notes: formData.edit_notes
      };

      // Only include fields that are different from original PO
      if (po) {
        if (formData.quantity !== po.quantity) editData.quantity = formData.quantity;
        if (formData.unit_price !== po.unit_price) editData.unit_price = formData.unit_price;
        if (formData.unit !== po.unit) editData.unit = formData.unit;
        if (formData.delivery_date !== (po.delivery_date ? new Date(po.delivery_date).toISOString().split('T')[0] : '')) {
          // For confirmed orders, update confirmed_delivery_date; for pending orders, update delivery_date
          if (po.status === 'confirmed') {
            editData.confirmed_delivery_date = formData.delivery_date;
          } else {
            editData.delivery_date = formData.delivery_date;
          }
        }
        if (formData.delivery_location !== po.delivery_location) editData.delivery_location = formData.delivery_location;
        if (formData.notes !== po.notes) editData.notes = formData.notes;
        if (formData.product_id !== po.product_id) editData.product_id = formData.product_id;
        if (formData.seller_company_id !== po.seller_company_id) editData.seller_company_id = formData.seller_company_id;
      }

      await onEdit(editData);
      handleClose();
      showToast({ type: 'success', title: 'Purchase order edit submitted successfully' });
    } catch (error) {
      console.error('Error editing purchase order:', error);
      showToast({ type: 'error', title: 'Failed to edit purchase order' });
    }
  };

  const handleClose = () => {
    setFormData({
      quantity: 0,
      unit_price: 0,
      unit: '',
      delivery_date: '',
      delivery_location: '',
      notes: '',
      product_id: '',
      seller_company_id: '',
      edit_reason: '',
      requires_approval: true,
      edit_notes: ''
    });
    setErrors({});
    onClose();
  };

  const totalAmount = formData.quantity * formData.unit_price;

  if (!isOpen || !po) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader
            title={`Edit Purchase Order - ${po.po_number}`}
            action={
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClose}
                disabled={isLoading}
              >
                <XMarkIcon className="h-5 w-5" />
              </Button>
            }
          />
          <CardBody>
            {loadingData ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">Loading...</span>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* Edit Reason */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-yellow-800 mb-2">Edit Information</h3>
                  <TextArea
                    label="Reason for Editing *"
                    value={formData.edit_reason}
                    onChange={(e) => handleInputChange('edit_reason', e.target.value)}
                    placeholder="Please provide a detailed reason for editing this purchase order..."
                    rows={3}
                    errorMessage={errors.edit_reason}
                    required
                  />
                  
                  <div className="mt-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.requires_approval}
                        onChange={(e) => handleInputChange('requires_approval', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        This edit requires approval from the other party
                      </span>
                    </label>
                  </div>
                  
                  <TextArea
                    label="Additional Notes"
                    value={formData.edit_notes}
                    onChange={(e) => handleInputChange('edit_notes', e.target.value)}
                    placeholder="Any additional notes about this edit..."
                    rows={2}
                    className="mt-3"
                  />
                </div>

                {/* Product Information */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Product Information</h3>
                  
                  <Select
                    label="Product"
                    value={formData.product_id}
                    onChange={(e) => handleInputChange('product_id', e.target.value)}
                    options={[
                      { label: 'Select a product...', value: '' },
                      ...products.map(product => ({
                        label: `${product.name} (${product.common_product_id})`,
                        value: product.id
                      }))
                    ]}
                    disabled={isLoading}
                  />
                  
                  <div className="grid grid-cols-3 gap-4">
                    <Input
                      label="Quantity"
                      type="number"
                      value={formData.quantity}
                      onChange={(e) => handleInputChange('quantity', parseFloat(e.target.value) || 0)}
                      errorMessage={errors.quantity}
                      min="0"
                      step="0.001"
                      required
                      disabled={isLoading}
                    />
                    
                    <Input
                      label="Unit"
                      value={formData.unit}
                      onChange={(e) => handleInputChange('unit', e.target.value)}
                      disabled={isLoading}
                    />
                    
                    <Input
                      label="Unit Price ($)"
                      type="number"
                      value={formData.unit_price}
                      onChange={(e) => handleInputChange('unit_price', parseFloat(e.target.value) || 0)}
                      errorMessage={errors.unit_price}
                      min="0"
                      step="0.01"
                      required
                      disabled={isLoading}
                    />
                  </div>
                  
                  {totalAmount > 0 && (
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-sm text-gray-600">
                        Total Amount: <span className="font-semibold text-gray-900">${totalAmount.toFixed(2)}</span>
                      </p>
                    </div>
                  )}
                </div>

                {/* Delivery Information */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Delivery Information</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      label="Delivery Date"
                      type="date"
                      value={formData.delivery_date}
                      onChange={(e) => handleInputChange('delivery_date', e.target.value)}
                      errorMessage={errors.delivery_date}
                      required
                      disabled={isLoading}
                    />
                    
                    <Input
                      label="Delivery Location"
                      value={formData.delivery_location}
                      onChange={(e) => handleInputChange('delivery_location', e.target.value)}
                      errorMessage={errors.delivery_location}
                      placeholder="Enter delivery address"
                      required
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {/* Company Information */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Company Information</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Buyer Company
                      </label>
                      <Input
                        value={po.buyer_company?.name || 'Unknown Company'}
                        disabled
                        className="bg-gray-50"
                      />
                    </div>
                    
                    <Select
                      label="Seller Company"
                      value={formData.seller_company_id}
                      onChange={(e) => handleInputChange('seller_company_id', e.target.value)}
                      options={[
                        { label: 'Select a seller...', value: '' },
                        ...companies
                          .filter(c => c.id !== po.buyer_company_id)
                          .map(company => ({
                            label: `${company.name} (${company.email})`,
                            value: company.id
                          }))
                      ]}
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <TextArea
                    label="Notes"
                    value={formData.notes}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    placeholder="Add any additional notes or requirements..."
                    rows={3}
                    disabled={isLoading}
                  />
                </div>

                {/* Actions */}
                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={handleClose}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <PencilIcon className="h-4 w-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </form>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
};

export default EditPurchaseOrderModal;
