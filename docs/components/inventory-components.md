# Inventory Components Documentation

## Overview

The inventory components provide a warehouse-like interface for selecting batches to fulfill purchase orders. These components transform the abstract "enter quantity" experience into a physical "select from warehouse shelves" experience.

## Component Architecture

```
BatchInventorySelector (Main Component)
├── BatchValidationDisplay (Validation feedback)
├── InventoryBatchCard (Individual batch display)
└── useBatchValidation (Validation hook)
```

---

## BatchInventorySelector

### Purpose
The main component that displays available inventory and allows users to select specific quantities from each batch. Provides FIFO auto-allocation and real-time validation.

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `companyId` | `string` | ✅ | ID of the company whose inventory to display |
| `productId` | `string` | ✅ | ID of the product to filter inventory by |
| `targetQuantity` | `number` | ❌ | Target quantity for auto-allocation |
| `onBatchesSelected` | `function` | ✅ | Callback when batch selections change |
| `disabled` | `boolean` | ❌ | Whether the component is disabled |
| `className` | `string` | ❌ | Additional CSS classes |

### Usage Examples

#### Basic Usage
```tsx
import BatchInventorySelector from '../inventory/BatchInventorySelector';

function PurchaseOrderConfirmation() {
  const [selectedBatches, setSelectedBatches] = useState([]);
  const [totalQuantity, setTotalQuantity] = useState(0);

  const handleBatchSelection = (selections, total) => {
    setSelectedBatches(selections);
    setTotalQuantity(total);
  };

  return (
    <BatchInventorySelector
      companyId="company-123"
      productId="product-456"
      targetQuantity={1950}
      onBatchesSelected={handleBatchSelection}
    />
  );
}
```

#### With Validation
```tsx
import BatchInventorySelector from '../inventory/BatchInventorySelector';
import useBatchValidation from '../../hooks/useBatchValidation';

function ValidatedInventorySelector() {
  const [selections, setSelections] = useState([]);
  const validation = useBatchValidation(selections, 1950);

  return (
    <div>
      <BatchInventorySelector
        companyId="company-123"
        productId="product-456"
        targetQuantity={1950}
        onBatchesSelected={(selections, total) => setSelections(selections)}
        disabled={!validation.isValid}
      />
      
      {!validation.isValid && (
        <div className="text-red-600">
          Please fix validation errors before proceeding
        </div>
      )}
    </div>
  );
}
```

### Key Features

1. **FIFO Auto-Allocation**: Automatically suggests optimal batch selection
2. **Real-time Validation**: Validates selections as user makes changes
3. **Expiry Warnings**: Highlights batches that expire soon
4. **Utilization Tracking**: Shows how much of each batch is being used
5. **Responsive Design**: Works on desktop and mobile devices

### State Management

The component manages several pieces of state:

```typescript
// Available batches from API
const [availableBatches, setAvailableBatches] = useState<Batch[]>([]);

// User selections: { batchId: quantitySelected }
const [selectedBatches, setSelectedBatches] = useState<Record<string, number>>({});

// Loading state
const [isLoading, setIsLoading] = useState(true);

// Auto-allocation flag
const [autoAllocated, setAutoAllocated] = useState(false);
```

---

## BatchValidationDisplay

### Purpose
Displays validation results, errors, and warnings for batch selections.

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `validation` | `ValidationResult` | ✅ | Validation result object |
| `targetQuantity` | `number` | ❌ | Target quantity for comparison |
| `className` | `string` | ❌ | Additional CSS classes |

### Usage Example

```tsx
import BatchValidationDisplay from '../inventory/BatchValidationDisplay';
import useBatchValidation from '../../hooks/useBatchValidation';

function ValidatedBatchSelector() {
  const [selections, setSelections] = useState([]);
  const validation = useBatchValidation(selections, 1950);

  return (
    <div>
      {/* Batch selection UI */}
      
      <BatchValidationDisplay
        validation={validation}
        targetQuantity={1950}
      />
    </div>
  );
}
```

---

## InventoryBatchCard

### Purpose
Displays individual batch information with selection controls.

### Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `batch` | `Batch` | ✅ | Batch object to display |
| `selectedQuantity` | `number` | ✅ | Currently selected quantity |
| `onQuantityChange` | `function` | ✅ | Callback when quantity changes |
| `disabled` | `boolean` | ❌ | Whether controls are disabled |
| `showFifoPriority` | `boolean` | ❌ | Whether to show FIFO priority |

### Usage Example

```tsx
import InventoryBatchCard from '../inventory/InventoryBatchCard';

function BatchList({ batches, selections, onSelectionChange }) {
  return (
    <div className="space-y-3">
      {batches.map(batch => (
        <InventoryBatchCard
          key={batch.id}
          batch={batch}
          selectedQuantity={selections[batch.id] || 0}
          onQuantityChange={(qty) => onSelectionChange(batch.id, qty)}
          showFifoPriority={true}
        />
      ))}
    </div>
  );
}
```

---

## useBatchValidation Hook

### Purpose
Custom hook that validates batch selections and provides detailed feedback.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `selections` | `BatchSelection[]` | ✅ | Array of batch selections |
| `targetQuantity` | `number` | ❌ | Target quantity for validation |

### Return Value

```typescript
interface ValidationResult {
  isValid: boolean;                    // Overall validation status
  errors: string[];                    // Array of error messages
  warnings: string[];                  // Array of warning messages
  totalQuantity: number;               // Total selected quantity
  utilizationByBatch: Record<string, number>; // Utilization % per batch
}
```

### Usage Example

```tsx
import useBatchValidation from '../../hooks/useBatchValidation';

function ValidatedComponent() {
  const [selections, setSelections] = useState([]);
  const validation = useBatchValidation(selections, 1950);

  // Check if selections are valid
  if (!validation.isValid) {
    console.log('Errors:', validation.errors);
    console.log('Warnings:', validation.warnings);
  }

  // Get total quantity
  console.log('Total selected:', validation.totalQuantity);

  // Check batch utilization
  Object.entries(validation.utilizationByBatch).forEach(([batchId, utilization]) => {
    console.log(`Batch ${batchId}: ${utilization}% utilized`);
  });

  return (
    <div>
      {/* Component UI */}
    </div>
  );
}
```

### Validation Rules

The hook validates the following:

1. **Quantity Limits**: Selected quantity doesn't exceed available
2. **Positive Values**: All quantities are greater than 0
3. **Target Matching**: Total matches target quantity (within tolerance)
4. **FIFO Compliance**: Warns if not following First In, First Out
5. **Expiry Warnings**: Alerts about soon-to-expire batches
6. **Utilization Efficiency**: Warns about fragmentation or low utilization

---

## Integration with Purchase Orders

### SellerConfirmationModal Integration

The inventory components integrate seamlessly with the purchase order confirmation workflow:

```tsx
import BatchInventorySelector from '../inventory/BatchInventorySelector';

function SellerConfirmationModal({ purchaseOrder, onConfirm }) {
  const [useInventorySelector, setUseInventorySelector] = useState(true);
  const [selectedBatches, setSelectedBatches] = useState([]);
  const [confirmedQuantity, setConfirmedQuantity] = useState(0);

  const handleBatchesSelected = (selections, totalQuantity) => {
    setSelectedBatches(selections);
    setConfirmedQuantity(totalQuantity);
  };

  return (
    <div>
      {/* Toggle between manual entry and inventory selection */}
      <div className="flex items-center space-x-2">
        <label>Use Inventory:</label>
        <button onClick={() => setUseInventorySelector(!useInventorySelector)}>
          {useInventorySelector ? 'ON' : 'OFF'}
        </button>
      </div>

      {useInventorySelector ? (
        <BatchInventorySelector
          companyId={purchaseOrder.seller_company.id}
          productId={purchaseOrder.product.id}
          targetQuantity={purchaseOrder.quantity}
          onBatchesSelected={handleBatchesSelected}
        />
      ) : (
        <input
          type="number"
          value={confirmedQuantity}
          onChange={(e) => setConfirmedQuantity(parseFloat(e.target.value))}
        />
      )}

      <button onClick={() => onConfirm({ 
        confirmed_quantity: confirmedQuantity,
        selected_batches: selectedBatches 
      })}>
        Confirm Order
      </button>
    </div>
  );
}
```

---

## Styling and Theming

### CSS Classes

The components use Tailwind CSS classes for styling:

- **Batch Cards**: `border rounded-lg p-4 transition-colors`
- **Selected State**: `border-blue-300 bg-blue-50`
- **Expiring Soon**: `border-amber-300 bg-amber-50`
- **Validation Errors**: `bg-red-50 border-red-200 text-red-700`
- **Validation Warnings**: `bg-amber-50 border-amber-200 text-amber-700`

### Customization

Components accept `className` props for custom styling:

```tsx
<BatchInventorySelector
  className="my-custom-inventory-selector"
  // ... other props
/>
```

---

## Performance Considerations

1. **Memoization**: Components use `useCallback` for event handlers
2. **Efficient Rendering**: Only re-render when necessary state changes
3. **API Optimization**: Inventory queries are cached and filtered
4. **Validation Debouncing**: Validation runs on state changes, not on every keystroke

---

## Testing

### Unit Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import BatchInventorySelector from '../BatchInventorySelector';

test('auto-allocates batches when target quantity is set', async () => {
  const mockBatches = [
    { id: '1', batch_id: 'BATCH-1', quantity: 500, expiry_date: '2025-01-15' },
    { id: '2', batch_id: 'BATCH-2', quantity: 750, expiry_date: '2025-01-20' }
  ];

  const onBatchesSelected = jest.fn();

  render(
    <BatchInventorySelector
      companyId="company-1"
      productId="product-1"
      targetQuantity={1000}
      onBatchesSelected={onBatchesSelected}
    />
  );

  // Wait for auto-allocation
  await waitFor(() => {
    expect(onBatchesSelected).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ batchId: '1', quantityToUse: 500 }),
        expect.objectContaining({ batchId: '2', quantityToUse: 500 })
      ]),
      1000
    );
  });
});
```

### Integration Tests

```typescript
test('integrates with purchase order confirmation', async () => {
  const mockPO = {
    id: 'po-1',
    quantity: 1950,
    seller_company: { id: 'company-1' },
    product: { id: 'product-1' }
  };

  render(<SellerConfirmationModal purchaseOrder={mockPO} />);

  // Should show inventory selector by default
  expect(screen.getByText('Select from Available Inventory')).toBeInTheDocument();

  // Should auto-allocate to match PO quantity
  await waitFor(() => {
    expect(screen.getByText('1950.000 kg')).toBeInTheDocument();
  });
});
```
