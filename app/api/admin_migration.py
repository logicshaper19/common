"""
Admin Migration Endpoint
Temporary endpoint to run database migrations through the API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/migration", tags=["admin-migration"])


@router.post("/run-v020")
async def run_migration_v020(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run Migration V020 to add missing purchase order columns.
    This is a temporary endpoint to fix the database schema.
    """
    
    # Check if user is admin (basic check)
    if not current_user.email.endswith('@common.co'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can run migrations"
        )
    
    logger.info(f"Migration V020 requested by user: {current_user.email}")
    
    try:
        # Check existing columns first
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'purchase_orders' 
            AND column_name IN ('original_quantity', 'original_unit_price', 'original_delivery_date', 'original_delivery_location')
            ORDER BY column_name;
        """))
        
        existing_columns = [row[0] for row in result]
        
        required_columns = ['original_delivery_date', 'original_delivery_location', 'original_quantity', 'original_unit_price']
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if not missing_columns:
            return {
                "success": True,
                "message": "All required columns already exist",
                "existing_columns": existing_columns,
                "missing_columns": []
            }
        
        # Add missing columns
        migration_results = []
        
        column_definitions = {
            'original_quantity': 'DECIMAL(12,3)',
            'original_unit_price': 'DECIMAL(12,2)',
            'original_delivery_date': 'DATE',
            'original_delivery_location': 'VARCHAR(500)',
            'buyer_approved_at': 'TIMESTAMP WITH TIME ZONE',
            'buyer_approval_user_id': 'UUID REFERENCES users(id)',
            'discrepancy_reason': 'TEXT',
            'seller_confirmed_data': 'JSONB'
        }
        
        # Add each missing column
        for column in missing_columns:
            if column in column_definitions:
                try:
                    sql = f"ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS {column} {column_definitions[column]}"
                    db.execute(text(sql))
                    migration_results.append(f"✅ Added column: {column}")
                    logger.info(f"Added column: {column}")
                except Exception as e:
                    migration_results.append(f"❌ Failed to add column {column}: {str(e)}")
                    logger.error(f"Failed to add column {column}: {str(e)}")
        
        # Add additional columns that might be missing
        additional_columns = ['buyer_approved_at', 'buyer_approval_user_id', 'discrepancy_reason', 'seller_confirmed_data', 'confirmed_by_user_id']
        for column in additional_columns:
            if column not in existing_columns:
                try:
                    # Special handling for confirmed_by_user_id
                    if column == 'confirmed_by_user_id':
                        sql = f"ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS {column} UUID REFERENCES users(id)"
                    else:
                        sql = f"ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS {column} {column_definitions[column]}"
                    db.execute(text(sql))
                    migration_results.append(f"✅ Added additional column: {column}")
                    logger.info(f"Added additional column: {column}")
                except Exception as e:
                    migration_results.append(f"❌ Failed to add additional column {column}: {str(e)}")
                    logger.error(f"Failed to add additional column {column}: {str(e)}")
        
        # Migrate existing data to original_* fields
        try:
            db.execute(text("""
                UPDATE purchase_orders 
                SET 
                    original_quantity = quantity,
                    original_unit_price = unit_price,
                    original_delivery_date = delivery_date,
                    original_delivery_location = delivery_location
                WHERE original_quantity IS NULL;
            """))
            migration_results.append("✅ Migrated existing data to original_* fields")
            logger.info("Migrated existing data to original_* fields")
        except Exception as e:
            migration_results.append(f"❌ Failed to migrate existing data: {str(e)}")
            logger.error(f"Failed to migrate existing data: {str(e)}")
        
        # Commit the transaction
        db.commit()
        
        # Verify the results
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'purchase_orders' 
            AND column_name IN ('original_quantity', 'original_unit_price', 'original_delivery_date', 'original_delivery_location')
            ORDER BY column_name;
        """))
        
        final_columns = [row[0] for row in result]
        
        return {
            "success": True,
            "message": "Migration V020 completed",
            "migration_results": migration_results,
            "existing_columns_before": existing_columns,
            "missing_columns_before": missing_columns,
            "final_columns": final_columns,
            "all_required_present": set(required_columns).issubset(set(final_columns))
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Migration V020 failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.get("/check-schema")
async def check_schema(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check the current database schema for purchase_orders table.
    """
    
    try:
        # Get all columns in purchase_orders table
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'purchase_orders' 
            ORDER BY ordinal_position;
        """))
        
        columns = []
        for row in result:
            columns.append({
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "default": row[3]
            })
        
        # Check for required columns
        required_columns = ['original_quantity', 'original_unit_price', 'original_delivery_date', 'original_delivery_location']
        existing_required = [col["name"] for col in columns if col["name"] in required_columns]
        missing_required = [col for col in required_columns if col not in existing_required]
        
        return {
            "table": "purchase_orders",
            "total_columns": len(columns),
            "all_columns": columns,
            "required_columns": required_columns,
            "existing_required": existing_required,
            "missing_required": missing_required,
            "schema_complete": len(missing_required) == 0
        }
        
    except Exception as e:
        logger.error(f"Schema check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema check failed: {str(e)}"
        )


@router.post("/admin/migration/add-confirmed-by-user-id")
async def add_confirmed_by_user_id_column(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add the missing confirmed_by_user_id column to purchase_orders table
    """
    # Check if user is admin (basic check)
    if not current_user.email.endswith('@common.co'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can run migrations"
        )

    logger.info(f"Adding confirmed_by_user_id column requested by user: {current_user.email}")

    try:
        # Check if column exists
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'purchase_orders'
            AND column_name = 'confirmed_by_user_id';
        """))

        existing = result.fetchone()

        if existing:
            return {
                "success": True,
                "message": "confirmed_by_user_id column already exists",
                "column_exists": True
            }

        # Add the column
        db.execute(text("ALTER TABLE purchase_orders ADD COLUMN confirmed_by_user_id UUID REFERENCES users(id);"))
        db.commit()

        logger.info("Successfully added confirmed_by_user_id column")

        return {
            "success": True,
            "message": "Successfully added confirmed_by_user_id column",
            "column_added": True
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add confirmed_by_user_id column: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add column: {str(e)}"
        )
