import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { 
  Package, 
  TrendingUp, 
  History, 
  Settings, 
  Plus,
  Eye,
  FileText,
  BarChart3
} from 'lucide-react';
import { InventoryLevelTransformationForm } from './InventoryLevelTransformationForm';
import { useToast } from '../../contexts/ToastContext';

interface InventoryTransformationManagerProps {
  className?: string;
}

interface Transformation {
  id: string;
  event_id: string;
  transformation_type: string;
  transformation_mode: string;
  status: string;
  input_quantity_requested: number;
  total_output_quantity: number;
  created_at: string;
  mass_balance_validation: {
    is_balanced: boolean;
    balance_ratio: number;
    deviation_percentage: number;
  };
  provenance_records: Array<{
    source_batch_number: string;
    contribution_percentage: number;
  }>;
}

export const InventoryTransformationManager: React.FC<InventoryTransformationManagerProps> = ({
  className = ''
}) => {
  const { showToast } = useToast();
  const [transformations, setTransformations] = useState<Transformation[]>([]);
  const [selectedTransformation, setSelectedTransformation] = useState<Transformation | null>(null);

  const handleCreateTransformation = async (formData: any) => {
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_BASE_URL}/api/v1/inventory-transformations/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const result = await response.json();
        setTransformations(prev => [result, ...prev]);
        // Tab will be managed by the Tabs component
        showToast({
          type: 'success',
          title: 'Transformation Created',
          message: `Transformation ${result.event_id} created successfully`
        });
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create transformation');
      }
    } catch (error) {
      console.error('Error creating transformation:', error);
      throw error;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'PLANNED': { variant: 'outline' as const, color: 'text-blue-600' },
      'IN_PROGRESS': { variant: 'outline' as const, color: 'text-yellow-600' },
      'COMPLETED': { variant: 'success' as const, color: 'text-green-600' },
      'PENDING_VALIDATION': { variant: 'outline' as const, color: 'text-orange-600' },
      'FAILED': { variant: 'error' as const, color: 'text-red-600' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig['PLANNED'];
    
    return (
      <Badge variant={config.variant} className={config.color}>
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const getBalanceBadge = (isBalanced: boolean, deviation: number) => {
    if (isBalanced) {
      return <Badge variant="success">Balanced ({deviation.toFixed(1)}%)</Badge>;
    } else {
      return <Badge variant="error">Out of Balance ({deviation.toFixed(1)}%)</Badge>;
    }
  };

  const renderCreateTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Create Inventory-Level Transformation</h2>
          <p className="text-gray-600">
            Create a transformation that automatically draws from your inventory pool with proportional provenance tracking
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Package className="h-6 w-6 text-blue-600" />
          <span className="text-sm font-medium text-blue-600">Inventory-Level</span>
        </div>
      </div>

      <InventoryLevelTransformationForm
        onSave={handleCreateTransformation}
        onCancel={() => {}}
      />
    </div>
  );

  const renderListTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Inventory Transformations</h2>
          <p className="text-gray-600">
            View and manage your inventory-level transformations
          </p>
        </div>
            <Button onClick={() => {}} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              New Transformation
            </Button>
      </div>

      {transformations.length === 0 ? (
        <Card>
          <CardBody className="text-center py-12">
            <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Transformations Yet</h3>
            <p className="text-gray-600 mb-4">
              Create your first inventory-level transformation to get started
            </p>
            <Button onClick={() => {}} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Create Transformation
            </Button>
          </CardBody>
        </Card>
      ) : (
        <div className="grid gap-4">
          {transformations.map((transformation) => (
            <Card key={transformation.id} className="hover:shadow-md transition-shadow">
              <CardBody>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold">{transformation.event_id}</h3>
                      {getStatusBadge(transformation.status)}
                      {getBalanceBadge(
                        transformation.mass_balance_validation.is_balanced,
                        transformation.mass_balance_validation.deviation_percentage
                      )}
                    </div>
                    
                    <div className="grid grid-cols-4 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Type:</span> {transformation.transformation_type}
                      </div>
                      <div>
                        <span className="font-medium">Input:</span> {transformation.input_quantity_requested} KGM
                      </div>
                      <div>
                        <span className="font-medium">Output:</span> {transformation.total_output_quantity} KGM
                      </div>
                      <div>
                        <span className="font-medium">Created:</span> {new Date(transformation.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="mt-2">
                      <span className="text-sm text-gray-600">
                        <span className="font-medium">Source Batches:</span> {transformation.provenance_records.length} batches
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedTransformation(transformation);
                      }}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const renderDetailsTab = () => {
    if (!selectedTransformation) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">{selectedTransformation.event_id}</h2>
            <p className="text-gray-600">Transformation Details</p>
          </div>
          <Button variant="outline" onClick={() => {}}>
            Back to List
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Basic Information
              </CardTitle>
            </CardHeader>
            <CardBody className="space-y-3">
              <div className="flex justify-between">
                <span className="font-medium">Event ID:</span>
                <span>{selectedTransformation.event_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Type:</span>
                <span>{selectedTransformation.transformation_type}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Mode:</span>
                <Badge variant="outline">{selectedTransformation.transformation_mode}</Badge>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Status:</span>
                {getStatusBadge(selectedTransformation.status)}
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Created:</span>
                <span>{new Date(selectedTransformation.created_at).toLocaleString()}</span>
              </div>
            </CardBody>
          </Card>

          {/* Mass Balance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Mass Balance
              </CardTitle>
            </CardHeader>
            <CardBody className="space-y-3">
              <div className="flex justify-between">
                <span className="font-medium">Input Quantity:</span>
                <span>{selectedTransformation.input_quantity_requested} KGM</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Output Quantity:</span>
                <span>{selectedTransformation.total_output_quantity} KGM</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Balance Ratio:</span>
                <span>{selectedTransformation.mass_balance_validation.balance_ratio.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Status:</span>
                {getBalanceBadge(
                  selectedTransformation.mass_balance_validation.is_balanced,
                  selectedTransformation.mass_balance_validation.deviation_percentage
                )}
              </div>
            </CardBody>
          </Card>

          {/* Provenance Records */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Source Batch Provenance
              </CardTitle>
            </CardHeader>
            <CardBody>
              <div className="space-y-2">
                {selectedTransformation.provenance_records.map((record, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                    <div>
                      <span className="font-medium">{record.source_batch_number}</span>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">{record.contribution_percentage.toFixed(1)}%</div>
                      <div className="text-sm text-gray-500">Contribution</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <Tabs defaultValue="create">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="create" className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Create
          </TabsTrigger>
          <TabsTrigger value="list" className="flex items-center gap-2">
            <Package className="h-4 w-4" />
            Transformations
          </TabsTrigger>
          <TabsTrigger value="details" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Details
          </TabsTrigger>
        </TabsList>

        <TabsContent value="create" className="mt-6">
          {renderCreateTab()}
        </TabsContent>

        <TabsContent value="list" className="mt-6">
          {renderListTab()}
        </TabsContent>

        <TabsContent value="details" className="mt-6">
          {renderDetailsTab()}
        </TabsContent>
      </Tabs>
    </div>
  );
};
