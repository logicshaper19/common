/**
 * Composition Input Component for processor confirmations
 * Handles input material composition with real-time validation
 */
import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { InputMaterial, CompositionValidation } from '../../types/confirmation';
import { 
  validateComposition, 
  autoBalanceComposition,
  calculateSuggestedQuantities,
  calculateSuggestedPercentages,
  validateMaterial,
  getCompositionSummary
} from '../../lib/compositionValidator';
import { cn } from '../../lib/utils';
import Button from './Button';
import Input from './Input';
import { Card, CardHeader, CardBody } from './Card';
import Badge from './Badge';

interface CompositionInputProps {
  value: InputMaterial[];
  onChange: (materials: InputMaterial[]) => void;
  targetQuantity?: number;
  targetUnit?: string;
  label?: string;
  required?: boolean;
  error?: string;
  className?: string;
  disabled?: boolean;
}

const CompositionInput: React.FC<CompositionInputProps> = ({
  value = [],
  onChange,
  targetQuantity = 0,
  targetUnit = 'KG',
  label,
  required = false,
  error,
  className,
  disabled = false
}) => {
  const [materials, setMaterials] = useState<InputMaterial[]>(value);
  const [validation, setValidation] = useState<CompositionValidation>({
    isValid: true,
    totalPercentage: 0,
    errors: [],
    warnings: [],
    suggestions: []
  });

  // Update internal state when value changes
  useEffect(() => {
    setMaterials(value);
  }, [value]);

  // Validate composition whenever materials change
  useEffect(() => {
    const newValidation = validateComposition(materials, targetQuantity);
    setValidation(prev => {
      // Only update if validation actually changed
      if (JSON.stringify(prev) !== JSON.stringify(newValidation)) {
        return newValidation;
      }
      return prev;
    });
  }, [materials, targetQuantity]);

  // Notify parent of changes
  useEffect(() => {
    onChange(materials);
  }, [materials, onChange]);

  // Add new material
  const addMaterial = () => {
    const newMaterial: InputMaterial = {
      id: `material-${Date.now()}`,
      source_po_id: '',
      product_name: '',
      quantity_used: 0,
      unit: targetUnit,
      percentage_contribution: 0,
      supplier_name: '',
      received_date: new Date().toISOString().split('T')[0]
    };

    setMaterials([...materials, newMaterial]);
  };

  // Remove material
  const removeMaterial = (index: number) => {
    const newMaterials = materials.filter((_, i) => i !== index);
    setMaterials(newMaterials);
  };

  // Update material field
  const updateMaterial = (index: number, field: keyof InputMaterial, value: any) => {
    const newMaterials = [...materials];
    newMaterials[index] = {
      ...newMaterials[index],
      [field]: value
    };
    setMaterials(newMaterials);
  };

  // Auto-balance percentages
  const handleAutoBalance = () => {
    const balanced = autoBalanceComposition(materials);
    setMaterials(balanced);
  };

  // Calculate suggested quantities
  const handleCalculateQuantities = () => {
    const withQuantities = calculateSuggestedQuantities(materials, targetQuantity);
    setMaterials(withQuantities);
  };

  // Calculate suggested percentages
  const handleCalculatePercentages = () => {
    const withPercentages = calculateSuggestedPercentages(materials);
    setMaterials(withPercentages);
  };

  // Get composition summary
  const summary = getCompositionSummary(materials);

  return (
    <div className={cn('w-full', className)}>
      {/* Label */}
      {label && (
        <label className="block text-sm font-medium text-neutral-700 mb-3">
          {label}
          {required && <span className="text-error-500 ml-1">*</span>}
        </label>
      )}

      {/* Summary card */}
      <Card className="mb-4">
        <CardHeader title="Composition Summary" />
        <CardBody>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900">{summary.totalMaterials}</p>
              <p className="text-sm text-neutral-500">Materials</p>
            </div>
            <div className="text-center">
              <p className={cn(
                "text-2xl font-bold",
                summary.isComplete ? "text-success-600" : "text-warning-600"
              )}>
                {summary.totalPercentage}%
              </p>
              <p className="text-sm text-neutral-500">Total %</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900">{summary.totalQuantity}</p>
              <p className="text-sm text-neutral-500">Total {targetUnit}</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900">{summary.uniqueSuppliers}</p>
              <p className="text-sm text-neutral-500">Suppliers</p>
            </div>
          </div>

          {/* Quick actions */}
          <div className="flex flex-wrap gap-2 mt-4">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleAutoBalance}
              disabled={disabled || materials.length === 0}
              leftIcon={<ArrowPathIcon className="h-4 w-4" />}
            >
              Auto Balance %
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCalculateQuantities}
              disabled={disabled || materials.length === 0 || targetQuantity === 0}
              leftIcon={<ArrowPathIcon className="h-4 w-4" />}
            >
              Calculate Quantities
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCalculatePercentages}
              disabled={disabled || materials.length === 0}
              leftIcon={<ArrowPathIcon className="h-4 w-4" />}
            >
              Calculate %
            </Button>
          </div>
        </CardBody>
      </Card>

      {/* Validation feedback */}
      {(validation.errors.length > 0 || validation.warnings.length > 0) && (
        <div className="mb-4 space-y-2">
          {validation.errors.map((error, index) => (
            <div key={index} className="flex items-center space-x-2 text-error-600">
              <ExclamationTriangleIcon className="h-4 w-4 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          ))}
          {validation.warnings.map((warning, index) => (
            <div key={index} className="flex items-center space-x-2 text-warning-600">
              <ExclamationTriangleIcon className="h-4 w-4 flex-shrink-0" />
              <span className="text-sm">{warning}</span>
            </div>
          ))}
        </div>
      )}

      {/* Success message */}
      {validation.isValid && materials.length > 0 && (
        <div className="mb-4 flex items-center space-x-2 text-success-600">
          <CheckCircleIcon className="h-4 w-4" />
          <span className="text-sm">Composition validation passed</span>
        </div>
      )}

      {/* Materials list */}
      <div className="space-y-4">
        {materials.map((material, index) => {
          const materialValidation = validateMaterial(material, index);
          
          return (
            <Card key={material.id} className="relative">
              <CardHeader
                title={`Material ${index + 1}`}
                action={
                  <div className="flex items-center space-x-2">
                    <Badge 
                      variant={materialValidation.isValid ? 'success' : 'error'}
                      size="sm"
                    >
                      {materialValidation.isValid ? 'Valid' : 'Invalid'}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeMaterial(index)}
                      disabled={disabled}
                    >
                      <TrashIcon className="h-4 w-4" />
                    </Button>
                  </div>
                }
              />
              <CardBody>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {/* Source PO */}
                  <Input
                    label="Source Purchase Order"
                    value={material.source_po_id}
                    onChange={(e) => updateMaterial(index, 'source_po_id', e.target.value)}
                    placeholder="PO-2024-001"
                    required
                    disabled={disabled}
                  />

                  {/* Product name */}
                  <Input
                    label="Product Name"
                    value={material.product_name}
                    onChange={(e) => updateMaterial(index, 'product_name', e.target.value)}
                    placeholder="Enter product name"
                    required
                    disabled={disabled}
                  />

                  {/* Supplier */}
                  <Input
                    label="Supplier"
                    value={material.supplier_name}
                    onChange={(e) => updateMaterial(index, 'supplier_name', e.target.value)}
                    placeholder="Supplier name"
                    required
                    disabled={disabled}
                  />

                  {/* Quantity */}
                  <Input
                    label={`Quantity (${material.unit})`}
                    type="number"
                    value={material.quantity_used.toString()}
                    onChange={(e) => updateMaterial(index, 'quantity_used', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    required
                    disabled={disabled}
                    step="0.001"
                    min="0"
                  />

                  {/* Percentage */}
                  <Input
                    label="Percentage (%)"
                    type="number"
                    value={material.percentage_contribution.toString()}
                    onChange={(e) => updateMaterial(index, 'percentage_contribution', parseFloat(e.target.value) || 0)}
                    placeholder="0"
                    required
                    disabled={disabled}
                    step="0.01"
                    min="0"
                    max="100"
                  />

                  {/* Received date */}
                  <Input
                    label="Received Date"
                    type="date"
                    value={material.received_date}
                    onChange={(e) => updateMaterial(index, 'received_date', e.target.value)}
                    disabled={disabled}
                  />

                  {/* Lot number */}
                  <Input
                    label="Lot Number"
                    value={material.lot_number || ''}
                    onChange={(e) => updateMaterial(index, 'lot_number', e.target.value)}
                    placeholder="Optional"
                    disabled={disabled}
                  />
                </div>

                {/* Material validation errors */}
                {materialValidation.errors.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {materialValidation.errors.map((error, errorIndex) => (
                      <p key={errorIndex} className="text-sm text-error-600">
                        {error}
                      </p>
                    ))}
                  </div>
                )}
              </CardBody>
            </Card>
          );
        })}
      </div>

      {/* Add material button */}
      <div className="mt-4">
        <Button
          variant="secondary"
          onClick={addMaterial}
          disabled={disabled}
          leftIcon={<PlusIcon className="h-4 w-4" />}
          fullWidth
        >
          Add Input Material
        </Button>
      </div>

      {/* Global error */}
      {error && (
        <p className="text-sm text-error-600 mt-2">{error}</p>
      )}

      {/* Suggestions */}
      {validation.suggestions.length > 0 && (
        <div className="mt-4 p-3 bg-primary-50 rounded-lg">
          <h4 className="text-sm font-medium text-primary-900 mb-2">Suggestions:</h4>
          <ul className="text-sm text-primary-800 space-y-1">
            {validation.suggestions.map((suggestion, index) => (
              <li key={index}>• {suggestion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CompositionInput;
