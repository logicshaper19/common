/**
 * Tests for confirmation configuration system
 */
import {
  getConfirmationConfig,
  getFieldConfig,
  validateConfirmationData,
  isStepComplete,
  getFormProgress
} from '../confirmationConfig';

describe('getConfirmationConfig', () => {
  it('returns processor configuration', () => {
    const config = getConfirmationConfig('processor', 'processed');

    expect(config.company_type).toBe('processor');
    expect(config.product_category).toBe('processed');
    expect(config.steps).toHaveLength(5);
    expect(config.required_fields).toContain('input_materials');
    expect(config.steps.some(step => step.id === 'input_materials')).toBe(true);
  });

  it('returns originator configuration', () => {
    const config = getConfirmationConfig('originator', 'raw_material');

    expect(config.company_type).toBe('originator');
    expect(config.product_category).toBe('raw_material');
    expect(config.steps).toHaveLength(5);
    expect(config.required_fields).toContain('origin_data');
    expect(config.required_fields).toContain('harvest_location');
    expect(config.steps.some(step => step.id === 'origin_data')).toBe(true);
    expect(config.steps.some(step => step.id === 'location_data')).toBe(true);
  });

  it('includes common required fields for both types', () => {
    const processorConfig = getConfirmationConfig('processor', 'processed');
    const originatorConfig = getConfirmationConfig('originator', 'raw_material');

    expect(processorConfig.required_fields).toContain('confirmed_quantity');
    expect(processorConfig.required_fields).toContain('confirmation_date');
    expect(originatorConfig.required_fields).toContain('confirmed_quantity');
    expect(originatorConfig.required_fields).toContain('confirmation_date');
  });

  it('includes optional fields for both types', () => {
    const processorConfig = getConfirmationConfig('processor', 'processed');
    const originatorConfig = getConfirmationConfig('originator', 'raw_material');

    expect(processorConfig.optional_fields).toContain('quality_metrics');
    expect(processorConfig.optional_fields).toContain('attachments');
    expect(originatorConfig.optional_fields).toContain('quality_metrics');
    expect(originatorConfig.optional_fields).toContain('attachments');
  });
});

describe('getFieldConfig', () => {
  it('returns processor field configuration', () => {
    const fields = getFieldConfig('processor');

    expect(fields.some(field => field.id === 'input_materials')).toBe(true);
    expect(fields.some(field => field.id === 'processing_info')).toBe(true);
    expect(fields.some(field => field.id === 'confirmed_quantity')).toBe(true);
  });

  it('returns originator field configuration', () => {
    const fields = getFieldConfig('originator');

    expect(fields.some(field => field.id === 'origin_data')).toBe(true);
    expect(fields.some(field => field.id === 'harvest_location')).toBe(true);
    expect(fields.some(field => field.id === 'storage_location')).toBe(true);
    expect(fields.some(field => field.id === 'confirmed_quantity')).toBe(true);
  });

  it('includes common fields for both types', () => {
    const processorFields = getFieldConfig('processor');
    const originatorFields = getFieldConfig('originator');

    const commonFieldIds = ['confirmed_quantity', 'unit', 'confirmation_date', 'notes', 'quality_metrics', 'attachments'];
    
    commonFieldIds.forEach(fieldId => {
      expect(processorFields.some(field => field.id === fieldId)).toBe(true);
      expect(originatorFields.some(field => field.id === fieldId)).toBe(true);
    });
  });
});

describe('validateConfirmationData', () => {
  const processorConfig = getConfirmationConfig('processor', 'processed');
  const originatorConfig = getConfirmationConfig('originator', 'raw_material');

  it('validates complete processor data', () => {
    const data = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01',
      input_materials: [
        {
          source_po_id: 'po-001',
          quantity_used: 1000,
          percentage_contribution: 100
        }
      ],
      total_input_percentage: 100
    };

    const result = validateConfirmationData(data, processorConfig);
    expect(result.isValid).toBe(true);
    expect(Object.keys(result.errors)).toHaveLength(0);
  });

  it('validates complete originator data', () => {
    const data = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01',
      origin_data: {
        cultivation_method: 'organic',
        harvest_date: '2024-01-01'
      },
      harvest_location: {
        coordinates: { latitude: 40.7128, longitude: -74.0060 },
        country: 'USA'
      }
    };

    const result = validateConfirmationData(data, originatorConfig);
    expect(result.isValid).toBe(true);
    expect(Object.keys(result.errors)).toHaveLength(0);
  });

  it('detects missing required fields', () => {
    const data = {
      confirmed_quantity: 1000
      // Missing confirmation_date and other required fields
    };

    const result = validateConfirmationData(data, processorConfig);
    expect(result.isValid).toBe(false);
    expect(result.errors['confirmation_date']).toBeDefined();
  });

  it('validates quantity constraints', () => {
    const data = {
      confirmed_quantity: -100, // Invalid negative quantity
      confirmation_date: '2024-01-01',
      input_materials: []
    };

    const result = validateConfirmationData(data, processorConfig);
    expect(result.isValid).toBe(false);
  });

  it('validates future dates', () => {
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 1);
    
    const data = {
      confirmed_quantity: 1000,
      confirmation_date: futureDate.toISOString().split('T')[0],
      input_materials: []
    };

    const result = validateConfirmationData(data, processorConfig);
    expect(result.isValid).toBe(false);
    expect(result.errors['confirmation_date']).toContain('cannot be in the future');
  });

  it('validates processor composition percentage', () => {
    const data = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01',
      input_materials: [
        {
          source_po_id: 'po-001',
          quantity_used: 500,
          percentage_contribution: 50
        }
      ],
      total_input_percentage: 75 // Doesn't match sum of percentages
    };

    const result = validateConfirmationData(data, processorConfig);
    expect(result.isValid).toBe(false);
    expect(result.errors['total_input_percentage']).toContain('must equal 100%');
  });

  it('validates originator location coordinates', () => {
    const data = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01',
      origin_data: {
        cultivation_method: 'organic',
        harvest_date: '2024-01-01'
      },
      harvest_location: {
        // Missing coordinates
        country: 'USA'
      }
    };

    const result = validateConfirmationData(data, originatorConfig);
    expect(result.isValid).toBe(false);
    expect(result.errors['harvest_location']).toContain('coordinates are required');
  });
});

describe('isStepComplete', () => {
  const processorConfig = getConfirmationConfig('processor', 'processed');
  const basicInfoStep = processorConfig.steps.find(step => step.id === 'basic_info')!;

  it('validates complete step', () => {
    const data = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01'
    };

    const result = isStepComplete(basicInfoStep, data);
    expect(result.isComplete).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('detects incomplete step', () => {
    const data = {
      confirmed_quantity: 1000
      // Missing confirmation_date
    };

    const result = isStepComplete(basicInfoStep, data);
    expect(result.isComplete).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  it('handles optional steps', () => {
    const optionalStep = processorConfig.steps.find(step => step.isOptional)!;
    const data = {}; // Empty data

    const result = isStepComplete(optionalStep, data);
    // Optional steps can be complete even with missing data
    expect(result.isComplete).toBe(true);
  });
});

describe('getFormProgress', () => {
  const processorConfig = getConfirmationConfig('processor', 'processed');

  it('calculates progress for completed steps', () => {
    const data = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01',
      input_materials: [
        {
          source_po_id: 'po-001',
          quantity_used: 1000,
          percentage_contribution: 100
        }
      ]
    };

    const progress = getFormProgress(processorConfig.steps, 2, data);
    expect(progress).toBeGreaterThan(0);
    expect(progress).toBeLessThanOrEqual(100);
  });

  it('returns 0 progress for no completed steps', () => {
    const data = {}; // Empty data

    const progress = getFormProgress(processorConfig.steps, 0, data);
    expect(progress).toBe(0);
  });

  it('returns 100 progress for all completed steps', () => {
    const completeData = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01',
      input_materials: [
        {
          source_po_id: 'po-001',
          quantity_used: 1000,
          percentage_contribution: 100
        }
      ],
      processing_info: {},
      quality_metrics: {},
      attachments: []
    };

    const progress = getFormProgress(processorConfig.steps, processorConfig.steps.length, completeData);
    expect(progress).toBe(100);
  });

  it('handles optional steps in progress calculation', () => {
    const dataWithOptionalSteps = {
      confirmed_quantity: 1000,
      confirmation_date: '2024-01-01',
      input_materials: [
        {
          source_po_id: 'po-001',
          quantity_used: 1000,
          percentage_contribution: 100
        }
      ]
      // Missing optional fields
    };

    const progress = getFormProgress(processorConfig.steps, 3, dataWithOptionalSteps);
    expect(progress).toBeGreaterThan(0);
  });
});
