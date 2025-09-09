import { useMemo } from 'react';

interface Batch {
  id: string;
  batch_id: string;
  quantity: number;
  unit: string;
  expiry_date?: string;
  batch_metadata?: {
    days_until_expiry?: number;
    is_expiring_soon?: boolean;
  };
}

interface BatchSelection {
  batchId: string;
  quantityToUse: number;
  batch: Batch;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  totalQuantity: number;
  utilizationByBatch: Record<string, number>;
}

export const useBatchValidation = (
  selections: BatchSelection[],
  targetQuantity?: number
): ValidationResult => {
  return useMemo(() => {
    const errors: string[] = [];
    const warnings: string[] = [];
    const utilizationByBatch: Record<string, number> = {};
    
    let totalQuantity = 0;

    // Validate each selection
    for (const selection of selections) {
      const { batchId, quantityToUse, batch } = selection;
      
      // Calculate utilization percentage
      const utilization = (quantityToUse / batch.quantity) * 100;
      utilizationByBatch[batchId] = utilization;
      
      // Add to total
      totalQuantity += quantityToUse;
      
      // Validation: Quantity doesn't exceed available
      if (quantityToUse > batch.quantity) {
        errors.push(
          `Batch ${batch.batch_id}: Selected quantity (${quantityToUse.toFixed(3)}) exceeds available (${batch.quantity.toFixed(3)})`
        );
      }
      
      // Validation: Quantity is positive
      if (quantityToUse <= 0) {
        errors.push(`Batch ${batch.batch_id}: Quantity must be greater than 0`);
      }
      
      // Warning: Using expiring batch
      if (batch.batch_metadata?.is_expiring_soon) {
        warnings.push(
          `Batch ${batch.batch_id} expires soon (${batch.batch_metadata.days_until_expiry} days)`
        );
      }
      
      // Warning: High utilization
      if (utilization > 90 && utilization < 100) {
        warnings.push(
          `Batch ${batch.batch_id}: High utilization (${utilization.toFixed(1)}%) - consider using full batch`
        );
      }
      
      // Warning: Low utilization for small batches
      if (utilization < 10 && batch.quantity < 100) {
        warnings.push(
          `Batch ${batch.batch_id}: Low utilization (${utilization.toFixed(1)}%) of small batch`
        );
      }
    }
    
    // Validation: Target quantity matching
    if (targetQuantity && targetQuantity > 0) {
      const difference = Math.abs(totalQuantity - targetQuantity);
      const tolerance = 0.001; // 1 gram tolerance
      
      if (difference > tolerance) {
        if (totalQuantity < targetQuantity) {
          errors.push(
            `Total selected quantity (${totalQuantity.toFixed(3)}) is ${(targetQuantity - totalQuantity).toFixed(3)} short of target (${targetQuantity.toFixed(3)})`
          );
        } else {
          warnings.push(
            `Total selected quantity (${totalQuantity.toFixed(3)}) exceeds target by ${(totalQuantity - targetQuantity).toFixed(3)}`
          );
        }
      }
    }
    
    // Validation: At least one batch selected
    if (selections.length === 0) {
      errors.push('At least one batch must be selected');
    }
    
    // Warning: Many small selections (fragmentation)
    if (selections.length > 5) {
      warnings.push(
        `Using ${selections.length} batches may create fragmentation - consider consolidating`
      );
    }
    
    // Warning: Non-FIFO selection (using newer batches before older ones)
    const sortedByExpiry = [...selections].sort((a, b) => {
      if (!a.batch.expiry_date && !b.batch.expiry_date) return 0;
      if (!a.batch.expiry_date) return 1;
      if (!b.batch.expiry_date) return -1;
      return new Date(a.batch.expiry_date).getTime() - new Date(b.batch.expiry_date).getTime();
    });
    
    const isNonFifo = selections.some((selection, index) => {
      const sortedIndex = sortedByExpiry.findIndex(s => s.batchId === selection.batchId);
      return sortedIndex !== index && selection.quantityToUse > 0;
    });
    
    if (isNonFifo && selections.length > 1) {
      warnings.push('Selection may not follow FIFO (First In, First Out) best practices');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      totalQuantity,
      utilizationByBatch
    };
  }, [selections, targetQuantity]);
};

export default useBatchValidation;
