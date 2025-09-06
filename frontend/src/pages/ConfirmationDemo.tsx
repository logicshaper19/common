/**
 * Confirmation Demo Page
 * Demonstrates the dual confirmation interfaces for processors and originators
 */
import React, { useState } from 'react';
import { 
  CogIcon, 
  BuildingOfficeIcon,
  DocumentTextIcon,
  MapPinIcon
} from '@heroicons/react/24/outline';
import ConfirmationInterface from '../components/confirmation/ConfirmationInterface';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { PurchaseOrder } from '../lib/api';
import { ProcessorConfirmationData, OriginatorConfirmationData } from '../types/confirmation';

const ConfirmationDemo: React.FC = () => {
  const [selectedDemo, setSelectedDemo] = useState<'processor' | 'originator' | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Mock purchase order data
  const mockPurchaseOrder: PurchaseOrder = {
    id: 'PO-2024-001',
    buyer_company_id: 'buyer-1',
    seller_company_id: 'seller-1',
    product_id: 'product-1',
    quantity: 1000,
    unit: 'KG',
    status: 'pending',
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    product: {
      id: 'product-1',
      common_product_id: 'cp-cotton-001',
      name: 'Organic Cotton Fiber',
      category: 'raw_material',
      description: 'Premium organic cotton fiber for textile production',
      default_unit: 'KG',
      can_have_composition: true,
      sustainability_certifications: ['GOTS', 'OCS'],
      origin_data_requirements: {
        harvest_location: true,
        cultivation_method: true,
        certifications: ['organic']
      }
    },
    buyer_company: {
      id: 'buyer-1',
      name: 'EcoFashion Co.',
      company_type: 'brand',
      email: 'orders@ecofashion.com',
      phone: '+1-555-0123',
      address: '123 Fashion Ave, New York, NY 10001',
      country: 'USA',
      website: 'https://ecofashion.com'
    },
    seller_company: {
      id: 'seller-1',
      name: 'Green Processing Mills',
      company_type: 'processor',
      email: 'sales@greenmills.com',
      phone: '+1-555-0456',
      address: '456 Mill Road, Austin, TX 78701',
      country: 'USA',
      website: 'https://greenmills.com'
    }
  };

  // Handle confirmation submission
  const handleConfirmationSubmit = async (data: ProcessorConfirmationData | OriginatorConfirmationData) => {
    setIsSubmitting(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('Confirmation submitted:', data);
      alert('Confirmation submitted successfully!');
      setSelectedDemo(null);
    } catch (error) {
      console.error('Submission error:', error);
      alert('Failed to submit confirmation. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle demo cancellation
  const handleCancel = () => {
    setSelectedDemo(null);
  };

  // Demo selection view
  if (!selectedDemo) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-neutral-900 mb-2">
            Dual Confirmation Interfaces Demo
          </h1>
          <p className="text-lg text-neutral-600 mb-8">
            Experience how different company types confirm purchase orders with tailored interfaces
          </p>
        </div>

        {/* Demo options */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Processor Demo */}
          <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedDemo('processor')}>
            <CardHeader
              title="Processor Confirmation"
              action={<Badge variant="primary">Processor Interface</Badge>}
            />
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <CogIcon className="h-8 w-8 text-primary-600" />
                  <div>
                    <h3 className="font-semibold text-neutral-900">Processing Company</h3>
                    <p className="text-sm text-neutral-600">Green Processing Mills</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium text-neutral-900">Key Features:</h4>
                  <ul className="space-y-2 text-sm text-neutral-600">
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-primary-600 rounded-full"></span>
                      <span>Input material composition tracking</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-primary-600 rounded-full"></span>
                      <span>Real-time percentage validation</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-primary-600 rounded-full"></span>
                      <span>Processing information capture</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-primary-600 rounded-full"></span>
                      <span>Quality metrics recording</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-primary-600 rounded-full"></span>
                      <span>Auto-balance composition tools</span>
                    </li>
                  </ul>
                </div>

                <div className="pt-4 border-t border-neutral-200">
                  <Button variant="primary" fullWidth>
                    Try Processor Interface
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Originator Demo */}
          <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => setSelectedDemo('originator')}>
            <CardHeader
              title="Originator Confirmation"
              action={<Badge variant="success">Originator Interface</Badge>}
            />
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <BuildingOfficeIcon className="h-8 w-8 text-success-600" />
                  <div>
                    <h3 className="font-semibold text-neutral-900">Origin Company</h3>
                    <p className="text-sm text-neutral-600">Organic Cotton Farms Co.</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="font-medium text-neutral-900">Key Features:</h4>
                  <ul className="space-y-2 text-sm text-neutral-600">
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-success-600 rounded-full"></span>
                      <span>Farm and cultivation data capture</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-success-600 rounded-full"></span>
                      <span>Interactive map location input</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-success-600 rounded-full"></span>
                      <span>Certification tracking</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-success-600 rounded-full"></span>
                      <span>Geographic coordinate validation</span>
                    </li>
                    <li className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 bg-success-600 rounded-full"></span>
                      <span>Origin traceability codes</span>
                    </li>
                  </ul>
                </div>

                <div className="pt-4 border-t border-neutral-200">
                  <Button variant="success" fullWidth>
                    Try Originator Interface
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Purchase Order Details */}
        <Card>
          <CardHeader title="Sample Purchase Order" />
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="flex items-center space-x-3">
                <DocumentTextIcon className="h-6 w-6 text-neutral-400" />
                <div>
                  <p className="text-sm text-neutral-500">Order ID</p>
                  <p className="font-medium">{mockPurchaseOrder.id}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <CogIcon className="h-6 w-6 text-neutral-400" />
                <div>
                  <p className="text-sm text-neutral-500">Product</p>
                  <p className="font-medium">{mockPurchaseOrder.product?.name}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-2xl">⚖️</span>
                <div>
                  <p className="text-sm text-neutral-500">Quantity</p>
                  <p className="font-medium">{mockPurchaseOrder.quantity} {mockPurchaseOrder.unit}</p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <BuildingOfficeIcon className="h-6 w-6 text-neutral-400" />
                <div>
                  <p className="text-sm text-neutral-500">Buyer</p>
                  <p className="font-medium">{mockPurchaseOrder.buyer_company?.name}</p>
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Features Overview */}
        <Card>
          <CardHeader title="Interface Features Comparison" />
          <CardBody>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-neutral-200">
                    <th className="text-left py-3 px-4 font-medium text-neutral-900">Feature</th>
                    <th className="text-center py-3 px-4 font-medium text-primary-900">Processor</th>
                    <th className="text-center py-3 px-4 font-medium text-success-900">Originator</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200">
                  <tr>
                    <td className="py-3 px-4">Basic confirmation data</td>
                    <td className="text-center py-3 px-4">✅</td>
                    <td className="text-center py-3 px-4">✅</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">Input material composition</td>
                    <td className="text-center py-3 px-4">✅</td>
                    <td className="text-center py-3 px-4">❌</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">Processing information</td>
                    <td className="text-center py-3 px-4">✅</td>
                    <td className="text-center py-3 px-4">❌</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">Farm and cultivation data</td>
                    <td className="text-center py-3 px-4">❌</td>
                    <td className="text-center py-3 px-4">✅</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">Geographic location input</td>
                    <td className="text-center py-3 px-4">❌</td>
                    <td className="text-center py-3 px-4">✅</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">Quality metrics</td>
                    <td className="text-center py-3 px-4">✅</td>
                    <td className="text-center py-3 px-4">✅</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">Document attachments</td>
                    <td className="text-center py-3 px-4">✅</td>
                    <td className="text-center py-3 px-4">✅</td>
                  </tr>
                  <tr>
                    <td className="py-3 px-4">Real-time validation</td>
                    <td className="text-center py-3 px-4">✅</td>
                    <td className="text-center py-3 px-4">✅</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  // Confirmation interface view
  return (
    <div className="min-h-screen bg-neutral-50 py-6">
      <ConfirmationInterface
        purchaseOrder={mockPurchaseOrder}
        onSubmit={handleConfirmationSubmit}
        onCancel={handleCancel}
      />
    </div>
  );
};

export default ConfirmationDemo;
