/**
 * Constants for Four-Pillar Dashboard Components
 */

export const INVENTORY_CONSTANTS = {
  LOW_STOCK_THRESHOLD: 100,
  EXPIRY_WARNING_DAYS: 7,
  DEFAULT_MAX_ITEMS: 5
} as const;

export const STATUS_CONFIGS = {
  PO_STATUS: {
    'draft': { variant: 'neutral' as const, label: 'Draft' },
    'pending': { variant: 'warning' as const, label: 'Pending' },
    'confirmed': { variant: 'success' as const, label: 'Confirmed' },
    'in_transit': { variant: 'primary' as const, label: 'In Transit' },
    'delivered': { variant: 'success' as const, label: 'Delivered' },
    'cancelled': { variant: 'error' as const, label: 'Cancelled' }
  },
  BATCH_STATUS: {
    'active': { variant: 'success' as const, label: 'Active' },
    'expired': { variant: 'error' as const, label: 'Expired' },
    'low_stock': { variant: 'warning' as const, label: 'Low Stock' },
    'allocated': { variant: 'primary' as const, label: 'Allocated' }
  },
  CHAIN_TYPE: {
    'COMMERCIAL': { variant: 'primary' as const, label: 'Commercial' },
    'PHYSICAL': { variant: 'success' as const, label: 'Physical' }
  }
} as const;

