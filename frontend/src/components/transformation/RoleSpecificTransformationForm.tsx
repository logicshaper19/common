/**
 * Role-Specific Transformation Form Component
 * Provides industry-appropriate inputs for each transformation type
 */
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardBody } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import Input from '../ui/Input';
import Label from '../ui/Label';
import Textarea from '../ui/Textarea';
import Select from '../ui/Select';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';

interface RoleSpecificTransformationFormProps {
  transformationType: string;
  onSave: (data: any) => void;
  onCancel: () => void;
  className?: string;
}

export const RoleSpecificTransformationForm: React.FC<RoleSpecificTransformationFormProps> = ({
  transformationType,
  onSave,
  onCancel,
  className = ''
}) => {
  const { user } = useAuth();
  const { showToast } = useToast();
  
  // Form state based on transformation type
  const [formData, setFormData] = useState<any>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    initializeFormData();
  }, [transformationType]);

  const initializeFormData = () => {
    const baseData = {
      event_id: `TRANS-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
      company_id: user?.company?.id || '',
      facility_id: '',
      start_time: new Date().toISOString().slice(0, 16),
      process_description: ''
    };

    switch (transformationType) {
      case 'MILLING':
        setFormData({
          ...baseData,
          // FFB Input Data
          ffb_quantity: 0,
          ffb_quality_grade: '',
          ffb_moisture_content: 0,
          oil_content_input: 0,
          // Processing Parameters
          extraction_rate: 0,
          processing_capacity: 0,
          processing_time_hours: 0,
          // Output Products
          cpo_quantity: 0,
          cpo_quality_grade: '',
          cpo_ffa_content: 0,
          cpo_moisture_content: 0,
          kernel_quantity: 0,
          // Resource Usage
          energy_consumed: 0,
          water_consumed: 0,
          steam_consumed: 0,
          // Equipment
          equipment_used: '',
          maintenance_status: 'good'
        });
        break;
      
      case 'REFINING':
        setFormData({
          ...baseData,
          // Input Oil Data
          input_oil_quantity: 0,
          input_oil_type: '',
          input_oil_quality: '',
          // Process Parameters
          process_type: 'physical_refining',
          temperature_profile: '',
          pressure_profile: '',
          // Output Products
          output_olein_quantity: 0,
          output_stearin_quantity: 0,
          output_other_quantity: 0,
          // Quality Specifications
          iv_value: 0,
          melting_point: 0,
          solid_fat_content: '',
          color_grade: '',
          // Efficiency Metrics
          refining_loss: 0,
          fractionation_yield_olein: 0,
          fractionation_yield_stearin: 0,
          // Resource Usage
          energy_consumed: 0,
          chemicals_used: ''
        });
        break;
      
      case 'MANUFACTURING':
        setFormData({
          ...baseData,
          // Product Information
          product_type: '',
          product_name: '',
          product_grade: '',
          // Recipe Formulation
          recipe_ratios: '',
          total_recipe_quantity: 0,
          recipe_unit: 'MT',
          input_materials: '',
          // Production Parameters
          production_line: '',
          production_shift: 'day',
          production_speed: 0,
          production_lot_number: '',
          // Output Products
          output_quantity: 0,
          output_unit: 'MT',
          // Packaging
          packaging_type: '',
          packaging_quantity: 0,
          // Quality Control
          quality_control_tests: '',
          quality_parameters: '',
          batch_testing_results: '',
          // Resource Usage
          energy_consumed: 0,
          water_consumed: 0,
          waste_generated: 0
        });
        break;
      
      case 'HARVEST':
        setFormData({
          ...baseData,
          // Harvest Data
          harvest_area_hectares: 0,
          ffb_tonnes: 0,
          oil_yield_percentage: 0,
          // Quality Metrics
          ffb_quality_grade: '',
          ripeness_level: '',
          // Environmental
          weather_conditions: '',
          temperature: 0,
          humidity: 0,
          rainfall: 0,
          // Location
          location_coordinates: '',
          farm_details: '',
          // Sustainability
          sustainability_metrics: ''
        });
        break;
      
      default:
        setFormData(baseData);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev: any) => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await onSave(formData);
      showToast({
        type: 'success',
        title: 'Transformation Created',
        message: 'Your transformation has been created successfully.'
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Error',
        message: 'Failed to create transformation. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const renderMillForm = () => (
    <div className="space-y-6">
      {/* FFB Input Data */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">FFB Input Data</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="ffb_quantity">FFB Quantity (MT)</Label>
              <Input
                id="ffb_quantity"
                type="number"
                value={formData.ffb_quantity}
                onChange={(e) => handleInputChange('ffb_quantity', parseFloat(e.target.value))}
                placeholder="1000"
              />
            </div>
            <div>
              <Label htmlFor="ffb_quality_grade">FFB Quality Grade</Label>
              <Select
                value={formData.ffb_quality_grade}
                onChange={(e) => handleInputChange('ffb_quality_grade', e.target.value)}
                options={[
                  { label: 'Select Grade', value: '' },
                  { label: 'Grade A (Excellent)', value: 'A' },
                  { label: 'Grade B (Good)', value: 'B' },
                  { label: 'Grade C (Fair)', value: 'C' }
                ]}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="ffb_moisture_content">Moisture Content (%)</Label>
              <Input
                id="ffb_moisture_content"
                type="number"
                step="0.1"
                value={formData.ffb_moisture_content}
                onChange={(e) => handleInputChange('ffb_moisture_content', parseFloat(e.target.value))}
                placeholder="25.5"
              />
            </div>
            <div>
              <Label htmlFor="oil_content_input">Oil Content Input (%)</Label>
              <Input
                id="oil_content_input"
                type="number"
                step="0.1"
                value={formData.oil_content_input}
                onChange={(e) => handleInputChange('oil_content_input', parseFloat(e.target.value))}
                placeholder="22.0"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Processing Parameters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Processing Parameters</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="extraction_rate">Oil Extraction Rate - OER (%)</Label>
              <Input
                id="extraction_rate"
                type="number"
                step="0.1"
                value={formData.extraction_rate}
                onChange={(e) => handleInputChange('extraction_rate', parseFloat(e.target.value))}
                placeholder="20.5"
              />
            </div>
            <div>
              <Label htmlFor="processing_capacity">Processing Capacity (MT/hour)</Label>
              <Input
                id="processing_capacity"
                type="number"
                step="0.1"
                value={formData.processing_capacity}
                onChange={(e) => handleInputChange('processing_capacity', parseFloat(e.target.value))}
                placeholder="50.0"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="processing_time_hours">Processing Time (hours)</Label>
            <Input
              id="processing_time_hours"
              type="number"
              step="0.1"
              value={formData.processing_time_hours}
              onChange={(e) => handleInputChange('processing_time_hours', parseFloat(e.target.value))}
              placeholder="24.0"
            />
          </div>
        </CardBody>
      </Card>

      {/* Output Products */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Output Products</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="cpo_quantity">CPO Quantity (MT)</Label>
              <Input
                id="cpo_quantity"
                type="number"
                step="0.1"
                value={formData.cpo_quantity}
                onChange={(e) => handleInputChange('cpo_quantity', parseFloat(e.target.value))}
                placeholder="205.0"
              />
            </div>
            <div>
              <Label htmlFor="cpo_quality_grade">CPO Quality Grade</Label>
              <Select
                value={formData.cpo_quality_grade}
                onChange={(e) => handleInputChange('cpo_quality_grade', e.target.value)}
                options={[
                  { label: 'Select Grade', value: '' },
                  { label: 'Grade 1 (Premium)', value: '1' },
                  { label: 'Grade 2 (Standard)', value: '2' },
                  { label: 'Grade 3 (Commercial)', value: '3' }
                ]}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="cpo_ffa_content">CPO FFA Content (%)</Label>
              <Input
                id="cpo_ffa_content"
                type="number"
                step="0.1"
                value={formData.cpo_ffa_content}
                onChange={(e) => handleInputChange('cpo_ffa_content', parseFloat(e.target.value))}
                placeholder="3.5"
              />
            </div>
            <div>
              <Label htmlFor="kernel_quantity">Kernel Quantity (MT)</Label>
              <Input
                id="kernel_quantity"
                type="number"
                step="0.1"
                value={formData.kernel_quantity}
                onChange={(e) => handleInputChange('kernel_quantity', parseFloat(e.target.value))}
                placeholder="150.0"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Resource Usage */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Resource Usage</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="energy_consumed">Energy Consumed (kWh)</Label>
              <Input
                id="energy_consumed"
                type="number"
                value={formData.energy_consumed}
                onChange={(e) => handleInputChange('energy_consumed', parseFloat(e.target.value))}
                placeholder="5000"
              />
            </div>
            <div>
              <Label htmlFor="water_consumed">Water Consumed (m³)</Label>
              <Input
                id="water_consumed"
                type="number"
                step="0.1"
                value={formData.water_consumed}
                onChange={(e) => handleInputChange('water_consumed', parseFloat(e.target.value))}
                placeholder="120.5"
              />
            </div>
            <div>
              <Label htmlFor="steam_consumed">Steam Consumed (MT)</Label>
              <Input
                id="steam_consumed"
                type="number"
                step="0.1"
                value={formData.steam_consumed}
                onChange={(e) => handleInputChange('steam_consumed', parseFloat(e.target.value))}
                placeholder="25.0"
              />
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );

  const renderRefineryForm = () => (
    <div className="space-y-6">
      {/* Input Oil Data */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Input Oil Data</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="input_oil_quantity">Input Oil Quantity (MT)</Label>
              <Input
                id="input_oil_quantity"
                type="number"
                step="0.1"
                value={formData.input_oil_quantity}
                onChange={(e) => handleInputChange('input_oil_quantity', parseFloat(e.target.value))}
                placeholder="100.0"
              />
            </div>
            <div>
              <Label htmlFor="input_oil_type">Input Oil Type</Label>
              <Select
                value={formData.input_oil_type}
                onChange={(e) => handleInputChange('input_oil_type', e.target.value)}
                options={[
                  { label: 'Select Type', value: '' },
                  { label: 'Crude Palm Oil (CPO)', value: 'CPO' },
                  { label: 'Palm Kernel Oil (PKO)', value: 'PKO' },
                  { label: 'Coconut Oil', value: 'CO' }
                ]}
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Process Parameters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Process Parameters</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="process_type">Process Type</Label>
              <Select
                value={formData.process_type}
                onChange={(e) => handleInputChange('process_type', e.target.value)}
                options={[
                  { label: 'Physical Refining', value: 'physical_refining' },
                  { label: 'Chemical Refining', value: 'chemical_refining' },
                  { label: 'Fractionation', value: 'fractionation' }
                ]}
              />
            </div>
            <div>
              <Label htmlFor="temperature_profile">Temperature Profile (°C)</Label>
              <Input
                id="temperature_profile"
                value={formData.temperature_profile}
                onChange={(e) => handleInputChange('temperature_profile', e.target.value)}
                placeholder="80-120°C"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Quality Specifications */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quality Specifications</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="iv_value">Iodine Value (IV)</Label>
              <Input
                id="iv_value"
                type="number"
                step="0.1"
                value={formData.iv_value}
                onChange={(e) => handleInputChange('iv_value', parseFloat(e.target.value))}
                placeholder="52.5"
              />
            </div>
            <div>
              <Label htmlFor="melting_point">Melting Point (°C)</Label>
              <Input
                id="melting_point"
                type="number"
                step="0.1"
                value={formData.melting_point}
                onChange={(e) => handleInputChange('melting_point', parseFloat(e.target.value))}
                placeholder="36.5"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="color_grade">Color Grade</Label>
              <Select
                value={formData.color_grade}
                onChange={(e) => handleInputChange('color_grade', e.target.value)}
                options={[
                  { label: 'Select Grade', value: '' },
                  { label: 'RBD 1 (Lightest)', value: 'RBD1' },
                  { label: 'RBD 2 (Light)', value: 'RBD2' },
                  { label: 'RBD 3 (Standard)', value: 'RBD3' }
                ]}
              />
            </div>
            <div>
              <Label htmlFor="refining_loss">Refining Loss (%)</Label>
              <Input
                id="refining_loss"
                type="number"
                step="0.1"
                value={formData.refining_loss}
                onChange={(e) => handleInputChange('refining_loss', parseFloat(e.target.value))}
                placeholder="2.5"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Output Products */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Output Products</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="output_olein_quantity">Olein Quantity (MT)</Label>
              <Input
                id="output_olein_quantity"
                type="number"
                step="0.1"
                value={formData.output_olein_quantity}
                onChange={(e) => handleInputChange('output_olein_quantity', parseFloat(e.target.value))}
                placeholder="70.0"
              />
            </div>
            <div>
              <Label htmlFor="output_stearin_quantity">Stearin Quantity (MT)</Label>
              <Input
                id="output_stearin_quantity"
                type="number"
                step="0.1"
                value={formData.output_stearin_quantity}
                onChange={(e) => handleInputChange('output_stearin_quantity', parseFloat(e.target.value))}
                placeholder="25.0"
              />
            </div>
            <div>
              <Label htmlFor="fractionation_yield_olein">Olein Yield (%)</Label>
              <Input
                id="fractionation_yield_olein"
                type="number"
                step="0.1"
                value={formData.fractionation_yield_olein}
                onChange={(e) => handleInputChange('fractionation_yield_olein', parseFloat(e.target.value))}
                placeholder="70.0"
              />
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );

  const renderManufacturerForm = () => (
    <div className="space-y-6">
      {/* Product Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Product Information</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="product_type">Product Type</Label>
              <Select
                value={formData.product_type}
                onChange={(e) => handleInputChange('product_type', e.target.value)}
                options={[
                  { label: 'Select Type', value: '' },
                  { label: 'Soap', value: 'soap' },
                  { label: 'Margarine', value: 'margarine' },
                  { label: 'Chocolate', value: 'chocolate' },
                  { label: 'Biofuel', value: 'biofuel' },
                  { label: 'Cosmetics', value: 'cosmetics' }
                ]}
              />
            </div>
            <div>
              <Label htmlFor="product_name">Product Name</Label>
              <Input
                id="product_name"
                value={formData.product_name}
                onChange={(e) => handleInputChange('product_name', e.target.value)}
                placeholder="Premium Palm Oil Soap"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="product_grade">Product Grade</Label>
            <Input
              id="product_grade"
              value={formData.product_grade}
              onChange={(e) => handleInputChange('product_grade', e.target.value)}
              placeholder="Grade A"
            />
          </div>
        </CardBody>
      </Card>

      {/* Recipe Formulation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recipe Formulation</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="total_recipe_quantity">Total Recipe Quantity (MT)</Label>
              <Input
                id="total_recipe_quantity"
                type="number"
                step="0.1"
                value={formData.total_recipe_quantity}
                onChange={(e) => handleInputChange('total_recipe_quantity', parseFloat(e.target.value))}
                placeholder="10.0"
              />
            </div>
            <div>
              <Label htmlFor="recipe_unit">Recipe Unit</Label>
              <Select
                value={formData.recipe_unit}
                onChange={(e) => handleInputChange('recipe_unit', e.target.value)}
                options={[
                  { label: 'MT', value: 'MT' },
                  { label: 'KG', value: 'KG' },
                  { label: 'L', value: 'L' }
                ]}
              />
            </div>
          </div>
          <div>
            <Label htmlFor="recipe_ratios">Recipe Ratios (JSON format)</Label>
            <Textarea
              id="recipe_ratios"
              value={formData.recipe_ratios}
              onChange={(e) => handleInputChange('recipe_ratios', e.target.value)}
              placeholder='{"palm_oil": 0.6, "coconut_oil": 0.3, "additives": 0.1}'
              rows={3}
            />
          </div>
          <div>
            <Label htmlFor="input_materials">Input Materials (JSON format)</Label>
            <Textarea
              id="input_materials"
              value={formData.input_materials}
              onChange={(e) => handleInputChange('input_materials', e.target.value)}
              placeholder='[{"material": "palm_oil", "quantity": 6.0, "unit": "MT"}]'
              rows={3}
            />
          </div>
        </CardBody>
      </Card>

      {/* Production Parameters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Production Parameters</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="production_line">Production Line</Label>
              <Input
                id="production_line"
                value={formData.production_line}
                onChange={(e) => handleInputChange('production_line', e.target.value)}
                placeholder="Line A"
              />
            </div>
            <div>
              <Label htmlFor="production_shift">Production Shift</Label>
              <Select
                value={formData.production_shift}
                onChange={(e) => handleInputChange('production_shift', e.target.value)}
                options={[
                  { label: 'Day Shift', value: 'day' },
                  { label: 'Night Shift', value: 'night' },
                  { label: '24/7', value: 'continuous' }
                ]}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="production_speed">Production Speed (units/hour)</Label>
              <Input
                id="production_speed"
                type="number"
                value={formData.production_speed}
                onChange={(e) => handleInputChange('production_speed', parseFloat(e.target.value))}
                placeholder="1000"
              />
            </div>
            <div>
              <Label htmlFor="production_lot_number">Production Lot Number</Label>
              <Input
                id="production_lot_number"
                value={formData.production_lot_number}
                onChange={(e) => handleInputChange('production_lot_number', e.target.value)}
                placeholder="LOT-2024-001"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Quality Control */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Quality Control</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div>
            <Label htmlFor="quality_control_tests">Quality Control Tests</Label>
            <Textarea
              id="quality_control_tests"
              value={formData.quality_control_tests}
              onChange={(e) => handleInputChange('quality_control_tests', e.target.value)}
              placeholder="pH test, viscosity test, color test"
              rows={2}
            />
          </div>
          <div>
            <Label htmlFor="quality_parameters">Quality Parameters</Label>
            <Textarea
              id="quality_parameters"
              value={formData.quality_parameters}
              onChange={(e) => handleInputChange('quality_parameters', e.target.value)}
              placeholder='{"pH": 7.2, "viscosity": "medium", "color": "white"}'
              rows={2}
            />
          </div>
        </CardBody>
      </Card>

      {/* Resource Usage */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Resource Usage</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="energy_consumed">Energy Consumed (kWh)</Label>
              <Input
                id="energy_consumed"
                type="number"
                value={formData.energy_consumed}
                onChange={(e) => handleInputChange('energy_consumed', parseFloat(e.target.value))}
                placeholder="2000"
              />
            </div>
            <div>
              <Label htmlFor="water_consumed">Water Consumed (m³)</Label>
              <Input
                id="water_consumed"
                type="number"
                step="0.1"
                value={formData.water_consumed}
                onChange={(e) => handleInputChange('water_consumed', parseFloat(e.target.value))}
                placeholder="50.0"
              />
            </div>
            <div>
              <Label htmlFor="waste_generated">Waste Generated (MT)</Label>
              <Input
                id="waste_generated"
                type="number"
                step="0.1"
                value={formData.waste_generated}
                onChange={(e) => handleInputChange('waste_generated', parseFloat(e.target.value))}
                placeholder="0.5"
              />
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );

  const renderHarvestForm = () => (
    <div className="space-y-6">
      {/* Harvest Data */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Harvest Data</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="harvest_area_hectares">Harvest Area (hectares)</Label>
              <Input
                id="harvest_area_hectares"
                type="number"
                step="0.1"
                value={formData.harvest_area_hectares}
                onChange={(e) => handleInputChange('harvest_area_hectares', parseFloat(e.target.value))}
                placeholder="25.5"
              />
            </div>
            <div>
              <Label htmlFor="ffb_tonnes">FFB Tonnes</Label>
              <Input
                id="ffb_tonnes"
                type="number"
                step="0.1"
                value={formData.ffb_tonnes}
                onChange={(e) => handleInputChange('ffb_tonnes', parseFloat(e.target.value))}
                placeholder="150.0"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="oil_yield_percentage">Oil Yield Percentage (%)</Label>
              <Input
                id="oil_yield_percentage"
                type="number"
                step="0.1"
                value={formData.oil_yield_percentage}
                onChange={(e) => handleInputChange('oil_yield_percentage', parseFloat(e.target.value))}
                placeholder="22.5"
              />
            </div>
            <div>
              <Label htmlFor="ffb_quality_grade">FFB Quality Grade</Label>
              <Select
                value={formData.ffb_quality_grade}
                onChange={(e) => handleInputChange('ffb_quality_grade', e.target.value)}
                options={[
                  { label: 'Select Grade', value: '' },
                  { label: 'Grade A (Excellent)', value: 'A' },
                  { label: 'Grade B (Good)', value: 'B' },
                  { label: 'Grade C (Fair)', value: 'C' }
                ]}
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Environmental Conditions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Environmental Conditions</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="temperature">Temperature (°C)</Label>
              <Input
                id="temperature"
                type="number"
                step="0.1"
                value={formData.temperature}
                onChange={(e) => handleInputChange('temperature', parseFloat(e.target.value))}
                placeholder="28.5"
              />
            </div>
            <div>
              <Label htmlFor="humidity">Humidity (%)</Label>
              <Input
                id="humidity"
                type="number"
                step="0.1"
                value={formData.humidity}
                onChange={(e) => handleInputChange('humidity', parseFloat(e.target.value))}
                placeholder="75.0"
              />
            </div>
            <div>
              <Label htmlFor="rainfall">Rainfall (mm)</Label>
              <Input
                id="rainfall"
                type="number"
                step="0.1"
                value={formData.rainfall}
                onChange={(e) => handleInputChange('rainfall', parseFloat(e.target.value))}
                placeholder="15.5"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="weather_conditions">Weather Conditions</Label>
            <Select
              value={formData.weather_conditions}
              onChange={(e) => handleInputChange('weather_conditions', e.target.value)}
              options={[
                { label: 'Select Condition', value: '' },
                { label: 'Sunny', value: 'sunny' },
                { label: 'Cloudy', value: 'cloudy' },
                { label: 'Rainy', value: 'rainy' },
                { label: 'Overcast', value: 'overcast' }
              ]}
            />
          </div>
        </CardBody>
      </Card>

      {/* Location */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Location Details</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div>
            <Label htmlFor="location_coordinates">GPS Coordinates</Label>
            <Input
              id="location_coordinates"
              value={formData.location_coordinates}
              onChange={(e) => handleInputChange('location_coordinates', e.target.value)}
              placeholder="1.2345, 103.6789"
            />
          </div>
          <div>
            <Label htmlFor="farm_details">Farm Details</Label>
            <Textarea
              id="farm_details"
              value={formData.farm_details}
              onChange={(e) => handleInputChange('farm_details', e.target.value)}
              placeholder="Farm name, block number, specific location details"
              rows={2}
            />
          </div>
        </CardBody>
      </Card>
    </div>
  );

  const renderForm = () => {
    switch (transformationType) {
      case 'MILLING':
        return renderMillForm();
      case 'REFINING':
      case 'FRACTIONATION':
        return renderRefineryForm();
      case 'MANUFACTURING':
      case 'BLENDING':
        return renderManufacturerForm();
      case 'HARVEST':
        return renderHarvestForm();
      default:
        return (
          <div className="text-center py-8">
            <p className="text-gray-500">Form for {transformationType} transformation type not yet implemented.</p>
          </div>
        );
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Create {transformationType} Transformation
          </h2>
          <p className="text-gray-600">
            Industry-specific form for {transformationType.toLowerCase()} processes
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          {user?.company?.company_type?.replace('_', ' ').toUpperCase()}
        </Badge>
      </div>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Basic Information</CardTitle>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="event_id">Event ID</Label>
              <Input
                id="event_id"
                value={formData.event_id}
                onChange={(e) => handleInputChange('event_id', e.target.value)}
                placeholder="TRANS-2024-001"
              />
            </div>
            <div>
              <Label htmlFor="facility_id">Facility ID</Label>
              <Input
                id="facility_id"
                value={formData.facility_id}
                onChange={(e) => handleInputChange('facility_id', e.target.value)}
                placeholder="MILL-001, REFINERY-A, etc."
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="start_time">Start Time</Label>
              <Input
                id="start_time"
                type="datetime-local"
                value={formData.start_time}
                onChange={(e) => handleInputChange('start_time', e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="process_description">Process Description</Label>
              <Input
                id="process_description"
                value={formData.process_description}
                onChange={(e) => handleInputChange('process_description', e.target.value)}
                placeholder="Brief description of the process"
              />
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Role-Specific Form */}
      {renderForm()}

      {/* Actions */}
      <div className="flex justify-end space-x-4">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={loading}>
          {loading ? 'Creating...' : 'Create Transformation'}
        </Button>
      </div>
    </div>
  );
};
