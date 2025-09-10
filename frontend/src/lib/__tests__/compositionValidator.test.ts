/**
 * Tests for composition validation system
 */
import {
  validateComposition,
  autoBalanceComposition,
  calculateSuggestedQuantities,
  calculateSuggestedPercentages,
  validateMaterial,
  getCompositionSummary
} from '../compositionValidator';
import { InputMaterial } from '../../types/confirmation';

const mockMaterial1: InputMaterial = {
  id: 'mat-1',
  source_po_id: 'po-001',
  product_name: 'Organic Cotton',
  quantity_used: 500,
  unit: 'KG',
  percentage_contribution: 50,
  supplier_name: 'Cotton Farm Co.',
  received_date: '2024-01-01'
};

const mockMaterial2: InputMaterial = {
  id: 'mat-2',
  source_po_id: 'po-002',
  product_name: 'Recycled Polyester',
  quantity_used: 300,
  unit: 'KG',
  percentage_contribution: 30,
  supplier_name: 'Recycling Corp',
  received_date: '2024-01-02'
};

const mockMaterial3: InputMaterial = {
  id: 'mat-3',
  source_po_id: 'po-003',
  product_name: 'Hemp Fiber',
  quantity_used: 200,
  unit: 'KG',
  percentage_contribution: 20,
  supplier_name: 'Hemp Farms',
  received_date: '2024-01-03'
};

describe('validateComposition', () => {
  it('validates correct composition totaling 100%', () => {
    const materials = [mockMaterial1, mockMaterial2, mockMaterial3];
    const result = validateComposition(materials, 1000);

    expect(result.isValid).toBe(true);
    expect(result.totalPercentage).toBe(100);
    expect(result.errors).toHaveLength(0);
  });

  it('detects percentage total exceeding 100%', () => {
    const materials = [
      { ...mockMaterial1, percentage_contribution: 60 },
      { ...mockMaterial2, percentage_contribution: 50 }
    ];
    const result = validateComposition(materials, 1000);

    expect(result.isValid).toBe(false);
    expect(result.totalPercentage).toBe(110);
    expect(result.errors).toContain('Total percentage (110.00%) exceeds 100%');
  });

  it('detects percentage total below 100%', () => {
    const materials = [
      { ...mockMaterial1, percentage_contribution: 40 },
      { ...mockMaterial2, percentage_contribution: 30 }
    ];
    const result = validateComposition(materials, 1000);

    expect(result.isValid).toBe(false);
    expect(result.totalPercentage).toBe(70);
    expect(result.warnings).toContain('Total percentage (70.00%) is 30.00% below 100%');
  });

  it('validates empty materials list', () => {
    const result = validateComposition([], 1000);

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('At least one input material is required');
  });

  it('detects missing required fields', () => {
    const materials = [
      { ...mockMaterial1, source_po_id: '' }
    ];
    const result = validateComposition(materials, 1000);

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Material 1: Source purchase order is required');
  });

  it('detects quantity vs percentage inconsistency', () => {
    const materials = [
      { ...mockMaterial1, quantity_used: 100, percentage_contribution: 50 } // Should be 500 for 50%
    ];
    const result = validateComposition(materials, 1000);

    expect(result.warnings.some(w => w.includes('Quantity (100) doesn\'t match percentage (50%)'))).toBe(true);
  });

  it('detects duplicate source POs', () => {
    const materials = [
      mockMaterial1,
      { ...mockMaterial2, source_po_id: 'po-001' } // Same as material1
    ];
    const result = validateComposition(materials, 1000);

    expect(result.warnings.some(w => w.includes('Duplicate source PO detected'))).toBe(true);
  });

  it('warns about very small contributions', () => {
    const materials = [
      { ...mockMaterial1, percentage_contribution: 0.5 }
    ];
    const result = validateComposition(materials, 1000);

    expect(result.warnings.some(w => w.includes('Very small contribution (0.5%)'))).toBe(true);
  });
});

describe('autoBalanceComposition', () => {
  it('balances materials to equal 100%', () => {
    const materials = [
      { ...mockMaterial1, percentage_contribution: 60 },
      { ...mockMaterial2, percentage_contribution: 30 }
    ];
    const balanced = autoBalanceComposition(materials);

    const total = balanced.reduce((sum, m) => sum + m.percentage_contribution, 0);
    expect(Math.abs(total - 100)).toBeLessThan(0.01);
  });

  it('distributes equally when no percentages are set', () => {
    const materials = [
      { ...mockMaterial1, percentage_contribution: 0 },
      { ...mockMaterial2, percentage_contribution: 0 },
      { ...mockMaterial3, percentage_contribution: 0 }
    ];
    const balanced = autoBalanceComposition(materials);

    balanced.forEach(material => {
      expect(Math.abs(material.percentage_contribution - 33.33)).toBeLessThan(0.01);
    });
  });

  it('handles empty materials array', () => {
    const balanced = autoBalanceComposition([]);
    expect(balanced).toEqual([]);
  });
});

describe('calculateSuggestedQuantities', () => {
  it('calculates quantities based on percentages', () => {
    const materials = [mockMaterial1, mockMaterial2, mockMaterial3];
    const withQuantities = calculateSuggestedQuantities(materials, 1000);

    expect(withQuantities[0].quantity_used).toBe(500); // 50% of 1000
    expect(withQuantities[1].quantity_used).toBe(300); // 30% of 1000
    expect(withQuantities[2].quantity_used).toBe(200); // 20% of 1000
  });

  it('handles zero target quantity', () => {
    const materials = [mockMaterial1];
    const withQuantities = calculateSuggestedQuantities(materials, 0);

    expect(withQuantities[0].quantity_used).toBe(0);
  });

  it('handles zero percentages', () => {
    const materials = [{ ...mockMaterial1, percentage_contribution: 0 }];
    const withQuantities = calculateSuggestedQuantities(materials, 1000);

    expect(withQuantities[0].quantity_used).toBe(0);
  });
});

describe('calculateSuggestedPercentages', () => {
  it('calculates percentages based on quantities', () => {
    const materials = [mockMaterial1, mockMaterial2, mockMaterial3];
    const withPercentages = calculateSuggestedPercentages(materials);

    expect(withPercentages[0].percentage_contribution).toBe(50); // 500/1000
    expect(withPercentages[1].percentage_contribution).toBe(30); // 300/1000
    expect(withPercentages[2].percentage_contribution).toBe(20); // 200/1000
  });

  it('handles zero total quantity', () => {
    const materials = [
      { ...mockMaterial1, quantity_used: 0 },
      { ...mockMaterial2, quantity_used: 0 }
    ];
    const withPercentages = calculateSuggestedPercentages(materials);

    withPercentages.forEach(material => {
      expect(material.percentage_contribution).toBe(0);
    });
  });
});

describe('validateMaterial', () => {
  it('validates complete material', () => {
    const result = validateMaterial(mockMaterial1, 0);

    expect(result.isValid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('detects missing source PO', () => {
    const material = { ...mockMaterial1, source_po_id: '' };
    const result = validateMaterial(material, 0);

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Material 1: Source purchase order is required');
  });

  it('detects missing product name', () => {
    const material = { ...mockMaterial1, product_name: '' };
    const result = validateMaterial(material, 0);

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Material 1: Product name is required');
  });

  it('detects invalid quantity', () => {
    const material = { ...mockMaterial1, quantity_used: 0 };
    const result = validateMaterial(material, 0);

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Material 1: Quantity must be greater than 0');
  });

  it('detects invalid percentage', () => {
    const material = { ...mockMaterial1, percentage_contribution: 150 };
    const result = validateMaterial(material, 0);

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Material 1: Percentage cannot exceed 100%');
  });

  it('detects missing supplier', () => {
    const material = { ...mockMaterial1, supplier_name: '' };
    const result = validateMaterial(material, 0);

    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Material 1: Supplier name is required');
  });
});

describe('getCompositionSummary', () => {
  it('calculates summary statistics', () => {
    const materials = [mockMaterial1, mockMaterial2, mockMaterial3];
    const summary = getCompositionSummary(materials);

    expect(summary.totalMaterials).toBe(3);
    expect(summary.totalPercentage).toBe(100);
    expect(summary.totalQuantity).toBe(1000);
    expect(summary.uniqueSuppliers).toBe(3);
    expect(summary.uniqueProducts).toBe(3);
    expect(summary.isComplete).toBe(true);
    expect(summary.averageContribution).toBe(33.33);
  });

  it('handles empty materials array', () => {
    const summary = getCompositionSummary([]);

    expect(summary.totalMaterials).toBe(0);
    expect(summary.totalPercentage).toBe(0);
    expect(summary.totalQuantity).toBe(0);
    expect(summary.uniqueSuppliers).toBe(0);
    expect(summary.uniqueProducts).toBe(0);
    expect(summary.isComplete).toBe(false);
    expect(summary.averageContribution).toBe(0);
  });

  it('counts unique suppliers and products correctly', () => {
    const materials = [
      mockMaterial1,
      { ...mockMaterial2, supplier_name: 'Cotton Farm Co.' }, // Same supplier as material1
      { ...mockMaterial3, product_name: 'Organic Cotton' } // Same product as material1
    ];
    const summary = getCompositionSummary(materials);

    expect(summary.uniqueSuppliers).toBe(2); // Cotton Farm Co. and Hemp Farms
    expect(summary.uniqueProducts).toBe(2); // Organic Cotton and Recycled Polyester
  });

  it('detects incomplete composition', () => {
    const materials = [
      { ...mockMaterial1, percentage_contribution: 40 },
      { ...mockMaterial2, percentage_contribution: 30 }
    ];
    const summary = getCompositionSummary(materials);

    expect(summary.isComplete).toBe(false);
    expect(summary.totalPercentage).toBe(70);
  });
});
