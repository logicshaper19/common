/**
 * Simple Transformation Manager Component
 * Just shows the create form without confusing tabs
 */
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { useAuth } from '../../contexts/AuthContext';
import { RoleSpecificTransformationForm } from './RoleSpecificTransformationForm';

interface SimpleTransformationManagerProps {
  transformationEventId?: string;
  onTransformationUpdate?: (transformation: any) => void;
  className?: string;
}

export const SimpleTransformationManager: React.FC<SimpleTransformationManagerProps> = ({
  transformationEventId,
  onTransformationUpdate,
  className = ''
}) => {
  const { user } = useAuth();
  const [newTransformation, setNewTransformation] = useState({
    event_id: '',
    transformation_type: 'MILLING',
    company_id: '',
    facility_id: '',
    input_batches: [] as any[],
    output_batches: [] as any[],
    process_description: '',
    total_input_quantity: 0,
    auto_apply_template: true,
    auto_calculate_costs: true,
    auto_inherit_quality: true
  });

  useEffect(() => {
    // Set default values
    setNewTransformation(prev => ({
      ...prev,
      company_id: user?.company?.id || '',
      event_id: `TRANS-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`
    }));
  }, [user]);

  const handleCreateCompleteTransformation = async (formData: any) => {
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${API_BASE_URL}/api/v1/transformation-enhanced/create-complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const result = await response.json();
        onTransformationUpdate?.(result);
      } else {
        throw new Error('Failed to create transformation');
      }
    } catch (error) {
      console.error('Error creating transformation:', error);
      throw error;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Create New Transformation</h2>
          <p className="text-gray-600">
            Create a new transformation with industry-specific parameters
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="outline">Enhanced</Badge>
          <Badge variant="outline">{newTransformation.transformation_type}</Badge>
        </div>
      </div>

      {/* Create Form */}
      <RoleSpecificTransformationForm
        transformationType={newTransformation.transformation_type}
        onSave={handleCreateCompleteTransformation}
        onCancel={() => onTransformationUpdate?.(null)}
        className="w-full"
      />
    </div>
  );
};
