/**
 * Types and interfaces for dual confirmation system
 */

// Purchase Order interface (simplified for confirmation)
export interface PurchaseOrder {
  id: string;
  po_number: string;
  product_name: string;
  quantity: number;
  unit: string;
  buyer_company: string;
  seller_company: string;
  status: string;
  created_at: string;
}

// Geographic coordinates
export interface Coordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

// Location information
export interface Location {
  coordinates: Coordinates;
  address?: string;
  country: string;
  region?: string;
  city?: string;
  postalCode?: string;
}

// Input material for processors
export interface InputMaterial {
  id: string;
  source_po_id: string;
  product_name: string;
  quantity_used: number;
  unit: string;
  percentage_contribution: number;
  supplier_name: string;
  lot_number?: string;
  received_date: string;
}

// Origin data for originators
export interface OriginData {
  farm_name?: string;
  farmer_name?: string;
  harvest_date?: string;
  planting_date?: string;
  field_size?: number;
  field_size_unit?: string;
  cultivation_method: 'organic' | 'conventional' | 'transitional';
  irrigation_method?: 'rain_fed' | 'drip' | 'sprinkler' | 'flood' | 'other';
  soil_type?: string;
  climate_zone?: string;
  elevation?: number;
  certifications: string[];
  processing_notes?: string;
}

// Quality metrics
export interface QualityMetrics {
  moisture_content?: number;
  purity_percentage?: number;
  grade?: string;
  color?: string;
  defect_rate?: number;
  test_results?: Record<string, any>;
  quality_notes?: string;
}

// Processing information
export interface ProcessingInfo {
  processing_method?: string;
  processing_date?: string;
  processing_location?: Location;
  equipment_used?: string[];
  temperature_range?: {
    min: number;
    max: number;
    unit: 'celsius' | 'fahrenheit';
  };
  duration_hours?: number;
  yield_percentage?: number;
  processing_notes?: string;
}

// Base confirmation data
export interface BaseConfirmationData {
  purchase_order_id: string;
  confirmed_quantity: number;
  unit: string;
  confirmation_date: string;
  quality_metrics?: QualityMetrics;
  notes?: string;
  attachments?: File[];
}

// Processor confirmation data
export interface ProcessorConfirmationData extends BaseConfirmationData {
  input_materials: InputMaterial[];
  processing_info?: ProcessingInfo;
  composition_validated: boolean;
  total_input_percentage: number;
}

// Originator confirmation data
export interface OriginatorConfirmationData extends BaseConfirmationData {
  origin_data: OriginData;
  harvest_location: Location;
  storage_location?: Location;
  traceability_code?: string;
}

// Confirmation form state
export interface ConfirmationFormState {
  step: number;
  isValid: boolean;
  errors: Record<string, string>;
  isSubmitting: boolean;
  isDirty: boolean;
}

// Validation rules
export interface ValidationRule {
  field: string;
  required?: boolean;
  min?: number;
  max?: number;
  pattern?: RegExp;
  custom?: (value: any, data: any) => string | null;
}

// Form step configuration
export interface FormStep {
  id: string;
  title: string;
  description: string;
  fields: string[];
  validationRules: ValidationRule[];
  isOptional?: boolean;
}

// Confirmation interface configuration
export interface ConfirmationConfig {
  company_type: 'processor' | 'originator';
  product_category: 'raw_material' | 'processed' | 'finished_good';
  steps: FormStep[];
  required_fields: string[];
  optional_fields: string[];
  validation_rules: ValidationRule[];
}

// API response types
export interface ConfirmationResponse {
  id: string;
  purchase_order_id: string;
  status: 'pending' | 'confirmed' | 'rejected';
  confirmed_quantity: number;
  confirmation_data: ProcessorConfirmationData | OriginatorConfirmationData;
  created_at: string;
  updated_at: string;
}

// Map integration types
export interface MapConfig {
  center: Coordinates;
  zoom: number;
  markers: MapMarker[];
  interactive: boolean;
}

export interface MapMarker {
  id: string;
  coordinates: Coordinates;
  title: string;
  description?: string;
  type: 'farm' | 'processing' | 'storage' | 'other';
}

// File upload types
export interface FileUpload {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  uploadProgress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  url?: string;
  error?: string;
}

// Composition validation
export interface CompositionValidation {
  isValid: boolean;
  totalPercentage: number;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

// Auto-complete suggestions
export interface AutocompleteSuggestion {
  id: string;
  label: string;
  value: string;
  category?: string;
  metadata?: Record<string, any>;
}

// Form field types
export type ConfirmationFieldType = 
  | 'text'
  | 'number'
  | 'date'
  | 'select'
  | 'multiselect'
  | 'textarea'
  | 'coordinates'
  | 'file'
  | 'composition'
  | 'quality_metrics';

// Form field configuration
export interface ConfirmationField {
  id: string;
  type: ConfirmationFieldType;
  label: string;
  placeholder?: string;
  required: boolean;
  validation?: ValidationRule[];
  options?: { label: string; value: string }[];
  dependencies?: string[];
  conditional?: {
    field: string;
    value: any;
    operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than';
  };
}

// All types are already exported individually above
