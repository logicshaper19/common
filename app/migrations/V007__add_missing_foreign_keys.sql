-- Migration: Add missing foreign key constraints and improve data integrity
-- Version: V007
-- Description: Comprehensive foreign key constraint addition and data integrity improvements
-- Created: 2024-01-10
-- Backward Compatible: Yes (with data cleanup)

-- ============================================================================
-- PHASE 1: Data Cleanup - Remove orphaned records before adding constraints
-- ============================================================================

-- Clean up orphaned users (users without valid company_id)
DELETE FROM users 
WHERE company_id IS NOT NULL 
AND company_id NOT IN (SELECT id FROM companies);

-- Clean up orphaned purchase orders
DELETE FROM purchase_orders 
WHERE buyer_company_id NOT IN (SELECT id FROM companies)
   OR seller_company_id NOT IN (SELECT id FROM companies)
   OR product_id NOT IN (SELECT id FROM products);

-- Clean up orphaned batches
DELETE FROM batches 
WHERE company_id NOT IN (SELECT id FROM companies)
   OR product_id NOT IN (SELECT id FROM products)
   OR (purchase_order_id IS NOT NULL AND purchase_order_id NOT IN (SELECT id FROM purchase_orders))
   OR (created_by_user_id IS NOT NULL AND created_by_user_id NOT IN (SELECT id FROM users));

-- Clean up orphaned batch transactions
DELETE FROM batch_transactions 
WHERE company_id NOT IN (SELECT id FROM companies)
   OR (source_batch_id IS NOT NULL AND source_batch_id NOT IN (SELECT id FROM batches))
   OR (destination_batch_id IS NOT NULL AND destination_batch_id NOT IN (SELECT id FROM batches))
   OR (purchase_order_id IS NOT NULL AND purchase_order_id NOT IN (SELECT id FROM purchase_orders))
   OR (created_by_user_id IS NOT NULL AND created_by_user_id NOT IN (SELECT id FROM users));

-- Clean up orphaned business relationships
DELETE FROM business_relationships 
WHERE buyer_company_id NOT IN (SELECT id FROM companies)
   OR seller_company_id NOT IN (SELECT id FROM companies)
   OR (invited_by_company_id IS NOT NULL AND invited_by_company_id NOT IN (SELECT id FROM companies));

-- Clean up orphaned documents
DELETE FROM documents 
WHERE company_id NOT IN (SELECT id FROM companies)
   OR (po_id IS NOT NULL AND po_id NOT IN (SELECT id FROM purchase_orders))
   OR (uploaded_by_user_id IS NOT NULL AND uploaded_by_user_id NOT IN (SELECT id FROM users))
   OR (parent_document_id IS NOT NULL AND parent_document_id NOT IN (SELECT id FROM documents));

-- Clean up orphaned notifications
DELETE FROM notifications 
WHERE user_id NOT IN (SELECT id FROM users)
   OR company_id NOT IN (SELECT id FROM companies);

-- Clean up orphaned audit events
UPDATE audit_events 
SET user_id = NULL 
WHERE user_id IS NOT NULL AND user_id NOT IN (SELECT id FROM users);

UPDATE audit_events 
SET company_id = NULL 
WHERE company_id IS NOT NULL AND company_id NOT IN (SELECT id FROM companies);

-- Clean up orphaned compliance results
DELETE FROM po_compliance_results 
WHERE po_id NOT IN (SELECT id FROM purchase_orders);

-- Clean up orphaned gap actions
DELETE FROM gap_actions 
WHERE company_id NOT IN (SELECT id FROM companies)
   OR (created_by_user_id IS NOT NULL AND created_by_user_id NOT IN (SELECT id FROM users))
   OR (assigned_to_user_id IS NOT NULL AND assigned_to_user_id NOT IN (SELECT id FROM users));

-- ============================================================================
-- PHASE 2: Add missing foreign key constraints
-- ============================================================================

-- Users table foreign keys
ALTER TABLE users 
DROP CONSTRAINT IF EXISTS fk_users_company_id,
ADD CONSTRAINT fk_users_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

-- Purchase orders table foreign keys
ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS fk_purchase_orders_buyer_company_id,
ADD CONSTRAINT fk_purchase_orders_buyer_company_id 
FOREIGN KEY (buyer_company_id) REFERENCES companies(id) ON DELETE RESTRICT;

ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS fk_purchase_orders_seller_company_id,
ADD CONSTRAINT fk_purchase_orders_seller_company_id 
FOREIGN KEY (seller_company_id) REFERENCES companies(id) ON DELETE RESTRICT;

ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS fk_purchase_orders_product_id,
ADD CONSTRAINT fk_purchase_orders_product_id 
FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;

-- Add confirmed_by_user_id foreign key if column exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'purchase_orders' AND column_name = 'confirmed_by_user_id') THEN
        ALTER TABLE purchase_orders 
        DROP CONSTRAINT IF EXISTS fk_purchase_orders_confirmed_by_user_id,
        ADD CONSTRAINT fk_purchase_orders_confirmed_by_user_id 
        FOREIGN KEY (confirmed_by_user_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Products table foreign keys
ALTER TABLE products 
DROP CONSTRAINT IF EXISTS fk_products_company_id,
ADD CONSTRAINT fk_products_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

-- Batches table foreign keys
ALTER TABLE batches 
DROP CONSTRAINT IF EXISTS fk_batches_company_id,
ADD CONSTRAINT fk_batches_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE batches 
DROP CONSTRAINT IF EXISTS fk_batches_product_id,
ADD CONSTRAINT fk_batches_product_id 
FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT;

ALTER TABLE batches 
DROP CONSTRAINT IF EXISTS fk_batches_purchase_order_id,
ADD CONSTRAINT fk_batches_purchase_order_id 
FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE SET NULL;

ALTER TABLE batches 
DROP CONSTRAINT IF EXISTS fk_batches_created_by_user_id,
ADD CONSTRAINT fk_batches_created_by_user_id 
FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Batch transactions table foreign keys
ALTER TABLE batch_transactions 
DROP CONSTRAINT IF EXISTS fk_batch_transactions_source_batch_id,
ADD CONSTRAINT fk_batch_transactions_source_batch_id 
FOREIGN KEY (source_batch_id) REFERENCES batches(id) ON DELETE SET NULL;

ALTER TABLE batch_transactions 
DROP CONSTRAINT IF EXISTS fk_batch_transactions_destination_batch_id,
ADD CONSTRAINT fk_batch_transactions_destination_batch_id 
FOREIGN KEY (destination_batch_id) REFERENCES batches(id) ON DELETE SET NULL;

ALTER TABLE batch_transactions 
DROP CONSTRAINT IF EXISTS fk_batch_transactions_company_id,
ADD CONSTRAINT fk_batch_transactions_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE batch_transactions 
DROP CONSTRAINT IF EXISTS fk_batch_transactions_purchase_order_id,
ADD CONSTRAINT fk_batch_transactions_purchase_order_id 
FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE SET NULL;

ALTER TABLE batch_transactions 
DROP CONSTRAINT IF EXISTS fk_batch_transactions_created_by_user_id,
ADD CONSTRAINT fk_batch_transactions_created_by_user_id 
FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Business relationships table foreign keys
ALTER TABLE business_relationships 
DROP CONSTRAINT IF EXISTS fk_business_relationships_buyer_company_id,
ADD CONSTRAINT fk_business_relationships_buyer_company_id 
FOREIGN KEY (buyer_company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE business_relationships 
DROP CONSTRAINT IF EXISTS fk_business_relationships_seller_company_id,
ADD CONSTRAINT fk_business_relationships_seller_company_id 
FOREIGN KEY (seller_company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE business_relationships 
DROP CONSTRAINT IF EXISTS fk_business_relationships_invited_by_company_id,
ADD CONSTRAINT fk_business_relationships_invited_by_company_id 
FOREIGN KEY (invited_by_company_id) REFERENCES companies(id) ON DELETE SET NULL;

-- Documents table foreign keys
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS fk_documents_company_id,
ADD CONSTRAINT fk_documents_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS fk_documents_po_id,
ADD CONSTRAINT fk_documents_po_id 
FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE;

ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS fk_documents_uploaded_by_user_id,
ADD CONSTRAINT fk_documents_uploaded_by_user_id 
FOREIGN KEY (uploaded_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Notifications table foreign keys
ALTER TABLE notifications 
DROP CONSTRAINT IF EXISTS fk_notifications_user_id,
ADD CONSTRAINT fk_notifications_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE notifications 
DROP CONSTRAINT IF EXISTS fk_notifications_company_id,
ADD CONSTRAINT fk_notifications_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

-- Audit events table foreign keys (nullable)
ALTER TABLE audit_events 
DROP CONSTRAINT IF EXISTS fk_audit_events_user_id,
ADD CONSTRAINT fk_audit_events_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE audit_events 
DROP CONSTRAINT IF EXISTS fk_audit_events_company_id,
ADD CONSTRAINT fk_audit_events_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL;

-- PO compliance results table foreign keys
ALTER TABLE po_compliance_results 
DROP CONSTRAINT IF EXISTS fk_po_compliance_results_po_id,
ADD CONSTRAINT fk_po_compliance_results_po_id 
FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE;

-- Gap actions table foreign keys
ALTER TABLE gap_actions 
DROP CONSTRAINT IF EXISTS fk_gap_actions_company_id,
ADD CONSTRAINT fk_gap_actions_company_id 
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

ALTER TABLE gap_actions 
DROP CONSTRAINT IF EXISTS fk_gap_actions_created_by_user_id,
ADD CONSTRAINT fk_gap_actions_created_by_user_id 
FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE gap_actions 
DROP CONSTRAINT IF EXISTS fk_gap_actions_assigned_to_user_id,
ADD CONSTRAINT fk_gap_actions_assigned_to_user_id 
FOREIGN KEY (assigned_to_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================================
-- PHASE 3: Add check constraints for business rules
-- ============================================================================

-- Purchase orders: buyer and seller cannot be the same
ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS chk_purchase_orders_different_companies,
ADD CONSTRAINT chk_purchase_orders_different_companies 
CHECK (buyer_company_id != seller_company_id);

-- Purchase orders: positive quantities and prices
ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS chk_purchase_orders_positive_quantity,
ADD CONSTRAINT chk_purchase_orders_positive_quantity 
CHECK (quantity > 0);

ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS chk_purchase_orders_positive_unit_price,
ADD CONSTRAINT chk_purchase_orders_positive_unit_price 
CHECK (unit_price > 0);

ALTER TABLE purchase_orders 
DROP CONSTRAINT IF EXISTS chk_purchase_orders_positive_total_amount,
ADD CONSTRAINT chk_purchase_orders_positive_total_amount 
CHECK (total_amount > 0);

-- Business relationships: buyer and seller cannot be the same
ALTER TABLE business_relationships 
DROP CONSTRAINT IF EXISTS chk_business_relationships_different_companies,
ADD CONSTRAINT chk_business_relationships_different_companies 
CHECK (buyer_company_id != seller_company_id);

-- Batches: positive quantities
ALTER TABLE batches 
DROP CONSTRAINT IF EXISTS chk_batches_positive_quantity,
ADD CONSTRAINT chk_batches_positive_quantity 
CHECK (quantity > 0);

-- Batch transactions: positive quantities
ALTER TABLE batch_transactions 
DROP CONSTRAINT IF EXISTS chk_batch_transactions_positive_quantity,
ADD CONSTRAINT chk_batch_transactions_positive_quantity 
CHECK (quantity_moved > 0);

-- ============================================================================
-- PHASE 4: Create indexes for performance
-- ============================================================================

-- Foreign key indexes for better join performance
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_buyer_company_id ON purchase_orders(buyer_company_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_seller_company_id ON purchase_orders(seller_company_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_product_id ON purchase_orders(product_id);
CREATE INDEX IF NOT EXISTS idx_products_company_id ON products(company_id);
CREATE INDEX IF NOT EXISTS idx_batches_company_id ON batches(company_id);
CREATE INDEX IF NOT EXISTS idx_batches_product_id ON batches(product_id);
CREATE INDEX IF NOT EXISTS idx_batches_purchase_order_id ON batches(purchase_order_id);
CREATE INDEX IF NOT EXISTS idx_batch_transactions_company_id ON batch_transactions(company_id);
CREATE INDEX IF NOT EXISTS idx_business_relationships_buyer_company_id ON business_relationships(buyer_company_id);
CREATE INDEX IF NOT EXISTS idx_business_relationships_seller_company_id ON business_relationships(seller_company_id);
CREATE INDEX IF NOT EXISTS idx_documents_company_id ON documents(company_id);
CREATE INDEX IF NOT EXISTS idx_documents_po_id ON documents(po_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_company_id ON notifications(company_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_company_id ON audit_events(company_id);
CREATE INDEX IF NOT EXISTS idx_po_compliance_results_po_id ON po_compliance_results(po_id);
CREATE INDEX IF NOT EXISTS idx_gap_actions_company_id ON gap_actions(company_id);

-- ============================================================================
-- PHASE 5: Create migration tracking record
-- ============================================================================

-- Insert migration record
INSERT INTO migration_history (
    migration_id,
    name,
    description,
    applied_at,
    checksum,
    execution_time_ms,
    success
) VALUES (
    'V007__add_missing_foreign_keys',
    'Add missing foreign key constraints',
    'Comprehensive foreign key constraint addition and data integrity improvements',
    CURRENT_TIMESTAMP,
    'checksum_placeholder',
    0,
    true
) ON CONFLICT (migration_id) DO NOTHING;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'Migration V007 completed successfully: Added foreign key constraints and improved data integrity';
END $$;
