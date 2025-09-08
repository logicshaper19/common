import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardBody } from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import TextArea from '../ui/Textarea';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { PurchaseOrderCreate } from '../../services/purchaseOrderApi';
import { productsApi, Product } from '../../services/productsApi';
import { companiesApi, Company } from '../../services/companiesApi';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

interface CreatePurchaseOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: PurchaseOrderCreate) => Promise<void>;
  isLoading?: boolean;
}



export const CreatePurchaseOrderModal: React.FC<CreatePurchaseOrderModalProps> = ({
  isOpen,
  onClose,
  onCreate,
  isLoading = false
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  const [formData, setFormData] = useState<PurchaseOrderCreate>({
    buyer_company_id: user?.company?.id || '',
    seller_company_id: '',
    product_id: '',
    quantity: 0,
    unit_price: 0,
    unit: 'KGM',
    delivery_date: '',
    delivery_location: '',
    notes: ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [companies, setCompanies] = useState<Company[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  // Load companies and products when modal opens
  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    setLoadingData(true);
    try {
      // Load companies and products in parallel
      const [companiesResponse, productsResponse] = await Promise.all([
        companiesApi.getBusinessPartners(),
        productsApi.getProducts({ per_page: 100 }) // Get first 100 products
      ]);

      setCompanies(companiesResponse);
      setProducts(productsResponse.products);
    } catch (error) {
      console.error('Error loading data:', error);
      showToast({ type: 'error', title: 'Failed to load companies and products' });

      // Fallback to mock data
      setCompanies([
        {
          id: 'a5287fd6-15cf-4a93-9237-a9d52e1a1428',
          name: 'Sustainable Mill Co',
          email: 'operations@sustainablemill.com',
          company_type: 'mill_processor',
          address: '',
          industry_sector: '',
          industry_subcategory: '',
          created_at: '',
          updated_at: ''
        }
      ]);

      setProducts([
        {
          id: '37e7784c-aa94-41a4-89a3-651130c292a5',
          name: 'Crude Palm Oil (CPO)',
          common_product_id: 'CPO-001',
          category: 'processed',
          default_unit: 'KGM',
          description: '',
          can_have_composition: true,
          hs_code: '',
          created_at: '',
          updated_at: ''
        }
      ]);
    } finally {
      setLoadingData(false);
    }
  };

  const handleInputChange = (field: keyof PurchaseOrderCreate, value: string | number) => {
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

    if (!formData.seller_company_id) {
      newErrors.seller_company_id = 'Please select a seller company';
    }

    if (!formData.product_id) {
      newErrors.product_id = 'Please select a product';
    }

    if (!formData.quantity || formData.quantity <= 0) {
      newErrors.quantity = 'Please enter a valid quantity';
    }

    if (!formData.unit_price || formData.unit_price <= 0) {
      newErrors.unit_price = 'Please enter a valid unit price';
    }

    if (!formData.delivery_date) {
      newErrors.delivery_date = 'Please select a delivery date';
    }

    if (!formData.delivery_location?.trim()) {
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
      await onCreate(formData);
      handleClose();
      showToast({ type: 'success', title: 'Purchase order created successfully' });
    } catch (error) {
      console.error('Error creating purchase order:', error);
      showToast({ type: 'error', title: 'Failed to create purchase order' });
    }
  };

  const handleClose = () => {
    setFormData({
      buyer_company_id: user?.company?.id || '',
      seller_company_id: '',
      product_id: '',
      quantity: 0,
      unit_price: 0,
      unit: 'KGM',
      delivery_date: '',
      delivery_location: '',
      notes: ''
    });
    setErrors({});
    onClose();
  };

  const totalAmount = formData.quantity * formData.unit_price;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <Card>
          <CardHeader
            title="Create Purchase Order"
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
                {/* Company Information */}
                <div className="space-y-4">
                  <h3 className="text-lg font-medium text-gray-900">Company Information</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Buyer Company
                      </label>
                      <Input
                        value={user?.company?.name || 'Unknown Company'}
                        disabled
                        className="bg-gray-50"
                      />
                    </div>
                    
                    <div>
                      <Select
                        label="Seller Company"
                        value={formData.seller_company_id}
                        onChange={(e) => handleInputChange('seller_company_id', e.target.value)}
                        options={[
                          { label: 'Select a seller...', value: '' },
                          ...companies
                            .filter(c => c.id !== user?.company?.id)
                            .map(company => ({
                              label: `${company.name} (${company.email})`,
                              value: company.id
                            }))
                        ]}
                        errorMessage={errors.seller_company_id}
                        required
                        disabled={isLoading}
                      />
                    </div>
                  </div>
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
                    errorMessage={errors.product_id}
                    required
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

                {/* Notes */}
                <div>
                  <TextArea
                    label="Notes (Optional)"
                    value={formData.notes || ''}
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
                        Creating...
                      </>
                    ) : (
                      <>
                        <PlusIcon className="h-4 w-4 mr-2" />
                        Create Purchase Order
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

export default CreatePurchaseOrderModal;
