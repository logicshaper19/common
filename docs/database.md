# Database Documentation

## Overview
The platform uses PostgreSQL as the primary database with SQLAlchemy ORM.

## Connection
- **Host**: localhost
- **Port**: 5432
- **Database**: common_db
- **Username**: common_user
- **Password**: common_password

## Core Tables

### Companies
```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    company_type VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    company_id UUID REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Products
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Purchase Orders
```sql
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY,
    po_number VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    buyer_company_id UUID REFERENCES companies(id),
    seller_company_id UUID REFERENCES companies(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Setup Commands

### Create Database
```bash
python setup_postgres_local.py
```

### Reset Test Data
```bash
python reset_test_data.py
```

### Direct Database Access
```bash
psql -h localhost -U common_user -d common_db
```

## Data Models

All models are defined in `app/models/`:
- `Company` - Company/organization data
- `User` - User accounts and authentication
- `Product` - Product catalog
- `PurchaseOrder` - Purchase order management

## Migrations

The platform uses Alembic for database migrations:
- **Location**: `alembic/versions/`
- **Config**: `alembic.ini`
- **Commands**:
  - `alembic upgrade head` - Apply migrations
  - `alembic revision --autogenerate -m "message"` - Create migration
  - `alembic downgrade -1` - Rollback migration

## Indexes

Key indexes for performance:
- `companies_email_idx` - Company email lookup
- `users_email_idx` - User email lookup
- `purchase_orders_po_number_idx` - PO number lookup
- `purchase_orders_status_idx` - PO status filtering

## Backup & Recovery

### Backup
```bash
pg_dump -h localhost -U common_user -d common_db > backup.sql
```

### Restore
```bash
psql -h localhost -U common_user -d common_db < backup.sql
```

