# Inventory & Purchase Order Approval API Documentation

## Overview

This document covers the new API endpoints for inventory management and purchase order approval workflows. These endpoints enable the transition from "guessing inventory" to "collaborative inventory selection" with full traceability.

## Key Concepts

### 1. PO-to-Batch Linkage
Every confirmed purchase order automatically creates a linked batch with deterministic ID format: `PO-{po_number}-BATCH-1`

### 2. Discrepancy Detection
When sellers confirm POs with different values than requested, the system detects discrepancies and requires buyer approval.

### 3. Inventory Selection
Sellers can view and select from actual available inventory when confirming purchase orders.

---

## Purchase Order Approval Endpoints

### 1. Seller Confirmation with Discrepancy Detection

**Endpoint:** `POST /api/v1/purchase-orders/{po_id}/seller-confirm`

**Description:** Confirms a purchase order with seller's actual values. Automatically detects discrepancies and triggers approval workflow if needed.

**Request Body:**
```json
{
  "confirmed_quantity": 1950.000,
  "confirmed_unit_price": 2.15,
  "confirmed_delivery_date": "2025-01-18",
  "confirmed_delivery_location": "Port of Rotterdam",
  "seller_notes": "Slight quantity adjustment due to harvest yield",
  "selected_batches": [
    {
      "batch_id": "PO-LOREAL-002-BATCH-1",
      "quantity_to_use": 500.000
    },
    {
      "batch_id": "PO-LOREAL-003-BATCH-1", 
      "quantity_to_use": 1450.000
    }
  ]
}
```

**Response (No Discrepancies):**
```json
{
  "status": "confirmed",
  "message": "Purchase order confirmed successfully",
  "batch_created": {
    "batch_id": "PO-LOREAL-004-BATCH-1",
    "quantity": 1950.000
  }
}
```

**Response (Discrepancies Detected):**
```json
{
  "status": "awaiting_buyer_approval",
  "message": "Discrepancies detected - buyer approval required",
  "discrepancies": {
    "quantity": {
      "original": 2000.000,
      "confirmed": 1950.000,
      "difference": -50.000,
      "percentage_change": -2.5
    },
    "delivery_date": {
      "original": "2025-01-15",
      "confirmed": "2025-01-18",
      "days_difference": 3
    }
  }
}
```

### 2. Buyer Approval

**Endpoint:** `POST /api/v1/purchase-orders/{po_id}/buyer-approve`

**Description:** Allows buyers to approve or reject seller's proposed changes.

**Request Body:**
```json
{
  "action": "approve",  // or "reject"
  "buyer_notes": "Acceptable quantity adjustment for this harvest season"
}
```

**Response:**
```json
{
  "status": "confirmed",
  "message": "Purchase order approved and confirmed",
  "batch_created": {
    "batch_id": "PO-LOREAL-004-BATCH-1",
    "quantity": 1950.000
  }
}
```

### 3. Get Discrepancy Details

**Endpoint:** `GET /api/v1/purchase-orders/{po_id}/discrepancies`

**Description:** Retrieves detailed discrepancy information for buyer review.

**Response:**
```json
{
  "purchase_order_id": "po-uuid",
  "status": "awaiting_buyer_approval",
  "discrepancies": [
    {
      "field": "quantity",
      "original_value": 2000.000,
      "confirmed_value": 1950.000,
      "difference": -50.000,
      "percentage_change": -2.5,
      "severity": "minor",
      "description": "Quantity reduced by 50 kg (2.5%)"
    }
  ],
  "seller_notes": "Slight quantity adjustment due to harvest yield",
  "requires_approval": true
}
```

---

## Inventory Management Endpoints

### 1. Get Company Inventory

**Endpoint:** `GET /api/v1/batches/companies/{company_id}/inventory`

**Description:** Retrieves available inventory for a company, optimized for PO confirmation workflows.

**Query Parameters:**
- `product_id` (optional): Filter by specific product
- `include_expired` (optional, default: false): Include expired batches

**Response:**
```json
[
  {
    "id": "batch-uuid",
    "batch_id": "PO-LOREAL-003-BATCH-1",
    "quantity": 500.000,
    "unit": "kg",
    "production_date": "2024-12-01",
    "expiry_date": "2025-06-01",
    "location_name": "Warehouse A",
    "facility_code": "WH-001",
    "batch_metadata": {
      "days_until_expiry": 127,
      "is_expiring_soon": false,
      "fifo_priority": 1,
      "inventory_status": "available"
    },
    "source_purchase_order_id": "original-po-uuid"
  }
]
```

**Key Features:**
- **FIFO Ordering**: Results sorted by expiry date (First In, First Out)
- **Expiry Warnings**: Metadata includes expiry status and days remaining
- **Availability Filter**: Only returns batches with quantity > 0
- **PO Traceability**: Shows which PO originally created each batch

### 2. Get Batches by Purchase Order

**Endpoint:** `GET /api/v1/batches/by-purchase-order/{purchase_order_id}`

**Description:** Retrieves all batches created from a specific purchase order.

**Response:**
```json
[
  {
    "id": "batch-uuid",
    "batch_id": "PO-LOREAL-003-BATCH-1",
    "quantity": 1950.000,
    "source_purchase_order_id": "po-uuid",
    "batch_metadata": {
      "created_from_po": true,
      "auto_created": true
    }
  }
]
```

---

## Error Handling

### Common Error Responses

**400 Bad Request - Invalid Data:**
```json
{
  "error": "validation_error",
  "message": "Invalid request data",
  "details": {
    "confirmed_quantity": "Must be greater than 0"
  }
}
```

**403 Forbidden - Access Denied:**
```json
{
  "error": "access_denied", 
  "message": "You can only view your own company's inventory"
}
```

**404 Not Found - Resource Missing:**
```json
{
  "error": "not_found",
  "message": "Purchase order not found"
}
```

**409 Conflict - Business Logic Error:**
```json
{
  "error": "invalid_state",
  "message": "Purchase order is already confirmed"
}
```

---

## Usage Patterns

### 1. Seller PO Confirmation Workflow

```javascript
// 1. Get available inventory
const inventory = await api.get(`/batches/companies/${companyId}/inventory?product_id=${productId}`);

// 2. Select batches and calculate total
const selectedBatches = [
  { batch_id: "PO-LOREAL-002-BATCH-1", quantity_to_use: 500 },
  { batch_id: "PO-LOREAL-003-BATCH-1", quantity_to_use: 1450 }
];
const totalQuantity = selectedBatches.reduce((sum, b) => sum + b.quantity_to_use, 0);

// 3. Confirm with selected batches
const confirmation = await api.post(`/purchase-orders/${poId}/seller-confirm`, {
  confirmed_quantity: totalQuantity,
  selected_batches: selectedBatches
});

// 4. Handle response based on discrepancies
if (confirmation.status === 'awaiting_buyer_approval') {
  // Show discrepancy details to user
  console.log('Buyer approval required:', confirmation.discrepancies);
} else {
  // PO confirmed, batch created
  console.log('Batch created:', confirmation.batch_created);
}
```

### 2. Buyer Approval Workflow

```javascript
// 1. Get discrepancy details
const discrepancies = await api.get(`/purchase-orders/${poId}/discrepancies`);

// 2. Review and approve/reject
const approval = await api.post(`/purchase-orders/${poId}/buyer-approve`, {
  action: 'approve',
  buyer_notes: 'Acceptable changes'
});
```

---

## Database Schema Changes

### New Fields in `purchase_orders` table:
- `status`: Added `awaiting_buyer_approval`, `declined` states
- `buyer_approved_at`: Timestamp of buyer approval
- `buyer_approval_user_id`: User who approved changes
- `discrepancy_reason`: Reason for discrepancy
- `seller_confirmed_data`: JSON of seller's confirmed values

### New Fields in `batches` table:
- `source_purchase_order_id`: Links batch to originating PO

### New `purchase_order_history` table:
- Complete audit trail of all PO actions and changes

---

## Performance Considerations

1. **Inventory Queries**: Indexed on `company_id`, `quantity > 0`, and `expiry_date`
2. **PO Lookups**: Indexed on `status` and `buyer_approval_user_id`
3. **Batch Traceability**: Indexed on `source_purchase_order_id`
4. **FIFO Ordering**: Optimized sorting by expiry date with null handling

---

## Security Notes

1. **Company Isolation**: Users can only access their own company's inventory
2. **Role-based Access**: Only sellers can confirm POs, only buyers can approve
3. **Audit Trail**: All actions logged with user attribution
4. **Data Validation**: Comprehensive validation on all inputs
