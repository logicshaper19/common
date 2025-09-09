# Inventory Features Setup Guide

## Overview

This guide helps developers set up and test the new inventory and purchase order approval features. These features transform the PO confirmation process from manual quantity entry to warehouse-like inventory selection.

## Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis (for caching)
- Git

---

## Database Setup

### 1. Run Migrations

The new features require two database migrations:

```bash
# Navigate to backend directory
cd app

# Run the PO approval workflow migration
python -m alembic upgrade head

# Verify migrations were applied
python -m alembic current
```

**Expected migrations**:
- `V020__add_po_approval_workflow.sql` - Adds approval workflow fields
- `V021__add_batch_po_linkage.sql` - Adds PO-to-batch linkage

### 2. Verify Schema Changes

Connect to your database and verify the new fields:

```sql
-- Check purchase_orders table
\d purchase_orders;

-- Should include new columns:
-- status (enum with approval states)
-- buyer_approved_at
-- buyer_approval_user_id
-- discrepancy_reason
-- seller_confirmed_data
-- original_quantity, original_unit_price, etc.

-- Check batches table
\d batches;

-- Should include:
-- source_purchase_order_id (UUID foreign key)

-- Check new audit table
\d purchase_order_history;
```

### 3. Seed Test Data

Create test data for development:

```sql
-- Insert test companies
INSERT INTO companies (id, name, company_type) VALUES
('11111111-1111-1111-1111-111111111111', 'Test Buyer Co', 'buyer'),
('22222222-2222-2222-2222-222222222222', 'Test Seller Co', 'seller');

-- Insert test product
INSERT INTO products (id, name, default_unit) VALUES
('33333333-3333-3333-3333-333333333333', 'Premium Cocoa Beans', 'kg');

-- Insert test batches for inventory
INSERT INTO batches (
    id, batch_id, company_id, product_id, quantity, unit,
    production_date, expiry_date, location_name, status
) VALUES
('44444444-4444-4444-4444-444444444444', 'TEST-BATCH-001', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', 500.000, 'kg', '2024-12-01', '2025-06-01', 'Warehouse A', 'active'),
('55555555-5555-5555-5555-555555555555', 'TEST-BATCH-002', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', 750.000, 'kg', '2024-12-15', '2025-06-15', 'Warehouse B', 'active');

-- Insert test purchase order
INSERT INTO purchase_orders (
    id, po_number, buyer_company_id, seller_company_id, product_id,
    quantity, unit_price, delivery_date, delivery_location, status
) VALUES
('66666666-6666-6666-6666-666666666666', 'PO-TEST-001', '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333', 1000.000, 2.50, '2025-02-01', 'Port of Hamburg', 'issued');
```

---

## Backend Setup

### 1. Install Dependencies

```bash
cd app

# Install Python dependencies
pip install -r requirements.txt

# Install new dependencies for inventory features
pip install sqlalchemy-utils  # For enhanced database utilities
```

### 2. Environment Configuration

Add to your `.env` file:

```env
# Inventory feature flags
ENABLE_INVENTORY_SELECTION=true
ENABLE_PO_APPROVAL_WORKFLOW=true

# Discrepancy detection tolerances
QUANTITY_TOLERANCE=0.001  # 1 gram
PRICE_TOLERANCE=0.01      # 1 cent
DATE_TOLERANCE_DAYS=0     # Exact match required

# Batch creation settings
AUTO_CREATE_BATCHES=true
BATCH_ID_FORMAT="PO-{po_number}-BATCH-{sequence}"
```

### 3. Start Backend Server

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Verify server is running
curl http://127.0.0.1:8000/health
```

### 4. Test API Endpoints

```bash
# Test inventory endpoint
curl -X GET "http://127.0.0.1:8000/api/v1/batches/companies/22222222-2222-2222-2222-222222222222/inventory?product_id=33333333-3333-3333-3333-333333333333" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected response: Array of available batches with FIFO ordering

# Test PO confirmation with discrepancies
curl -X POST "http://127.0.0.1:8000/api/v1/purchase-orders/66666666-6666-6666-6666-666666666666/seller-confirm" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "confirmed_quantity": 950.000,
    "confirmed_unit_price": 2.60,
    "seller_notes": "Slight adjustment due to quality grading"
  }'

# Expected response: Discrepancy detected, buyer approval required
```

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend

# Install Node.js dependencies
npm install

# Install new dependencies for inventory components
npm install lucide-react  # For icons
npm install react-hot-toast  # For notifications
```

### 2. Environment Configuration

Add to your `.env.local` file:

```env
# API configuration
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_ENABLE_INVENTORY_SELECTOR=true

# Feature flags
NEXT_PUBLIC_ENABLE_BATCH_VALIDATION=true
NEXT_PUBLIC_ENABLE_FIFO_AUTO_ALLOCATION=true
```

### 3. Start Frontend Server

```bash
# Start the React development server
npm run dev

# Verify server is running
open http://localhost:3000
```

### 4. Test Components

Navigate to the purchase order confirmation page and verify:

1. **Inventory Toggle**: Switch between manual entry and inventory selection
2. **Batch Display**: See available batches with expiry dates and locations
3. **Auto-allocation**: Target quantity automatically allocates across batches
4. **Validation**: Real-time validation of batch selections
5. **FIFO Ordering**: Batches sorted by expiry date (First In, First Out)

---

## Testing

### 1. Unit Tests

```bash
# Backend tests
cd app
python -m pytest tests/test_inventory_features.py -v

# Frontend tests
cd frontend
npm test -- --testPathPattern=inventory
```

### 2. Integration Tests

```bash
# Test complete PO confirmation workflow
cd app
python -m pytest tests/integration/test_po_confirmation_flow.py -v

# Test inventory selection UI
cd frontend
npm run test:e2e -- --spec="inventory-selection.spec.ts"
```

### 3. API Testing with Postman

Import the provided Postman collection:

```bash
# Import collection
curl -o inventory-api-tests.json https://raw.githubusercontent.com/your-repo/docs/postman/inventory-api-tests.json

# Run collection
newman run inventory-api-tests.json --environment=development.json
```

---

## Development Workflow

### 1. Feature Development

When working on inventory features:

```bash
# 1. Create feature branch
git checkout -b feature/inventory-enhancement

# 2. Make changes to backend
cd app
# Edit files in app/api/, app/services/, app/models/

# 3. Make changes to frontend
cd frontend
# Edit files in src/components/inventory/

# 4. Run tests
cd app && python -m pytest
cd frontend && npm test

# 5. Test integration
# Start both servers and test manually

# 6. Commit and push
git add .
git commit -m "feat: enhance inventory selection with FIFO validation"
git push origin feature/inventory-enhancement
```

### 2. Database Changes

When modifying the database schema:

```bash
# 1. Create new migration
cd app
alembic revision --autogenerate -m "add_new_inventory_field"

# 2. Review generated migration
# Edit the migration file if needed

# 3. Test migration
alembic upgrade head

# 4. Test rollback
alembic downgrade -1
alembic upgrade head
```

### 3. API Changes

When modifying API endpoints:

```bash
# 1. Update schemas in app/schemas/
# 2. Update models in app/models/
# 3. Update API endpoints in app/api/
# 4. Update tests in tests/
# 5. Update documentation in docs/api/
```

---

## Troubleshooting

### Common Issues

**1. Migration Errors**
```bash
# Check current migration state
alembic current

# Check migration history
alembic history

# Force migration to specific version
alembic stamp head
```

**2. API Connection Issues**
```bash
# Check if backend is running
curl http://127.0.0.1:8000/health

# Check CORS configuration
# Verify CORS_ORIGINS in app/core/config.py includes frontend URL
```

**3. Frontend Component Issues**
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check
```

**4. Database Connection Issues**
```bash
# Test database connection
python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Check database logs
tail -f /var/log/postgresql/postgresql.log
```

### Debug Mode

Enable debug logging:

```python
# In app/core/config.py
LOG_LEVEL = "DEBUG"

# In app/core/logging.py
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

---

## Performance Testing

### 1. Load Testing

```bash
# Install locust
pip install locust

# Run inventory API load test
locust -f tests/load/inventory_load_test.py --host=http://127.0.0.1:8000
```

### 2. Database Performance

```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM batches 
WHERE company_id = '22222222-2222-2222-2222-222222222222' 
AND quantity > 0 
ORDER BY expiry_date ASC NULLS LAST;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE tablename IN ('batches', 'purchase_orders');
```

---

## Deployment

### 1. Production Checklist

- [ ] All migrations applied
- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups configured
- [ ] Monitoring alerts set up
- [ ] Load balancer configured
- [ ] CDN configured for static assets

### 2. Feature Flags

Use feature flags for gradual rollout:

```python
# In app/core/config.py
ENABLE_INVENTORY_SELECTION = os.getenv("ENABLE_INVENTORY_SELECTION", "false").lower() == "true"
ENABLE_AUTO_BATCH_CREATION = os.getenv("ENABLE_AUTO_BATCH_CREATION", "false").lower() == "true"
```

### 3. Monitoring

Set up monitoring for:
- API response times
- Database query performance
- Error rates
- User adoption metrics
- Inventory utilization rates

---

## Support

### Documentation
- API Documentation: `docs/api/inventory-and-po-approval.md`
- Component Documentation: `docs/components/inventory-components.md`
- Architecture Overview: `docs/architecture/po-inventory-architecture.md`

### Getting Help
- Create GitHub issue for bugs
- Use Slack #inventory-features channel for questions
- Schedule code review for complex changes

### Contributing
- Follow existing code style
- Add tests for new features
- Update documentation
- Use conventional commit messages
