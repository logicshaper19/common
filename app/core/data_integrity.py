"""
Data integrity management system.

This module provides:
1. Foreign key constraint validation
2. Data consistency checks
3. Referential integrity enforcement
4. Constraint violation detection
5. Data quality validation
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, inspect

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConstraintType(str, Enum):
    """Types of database constraints."""
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    CHECK = "check"
    NOT_NULL = "not_null"
    PRIMARY_KEY = "primary_key"


class ViolationSeverity(str, Enum):
    """Severity levels for constraint violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation."""
    constraint_type: ConstraintType
    table_name: str
    column_name: str
    violation_message: str
    severity: ViolationSeverity
    entity_id: Optional[str] = None
    related_entity_id: Optional[str] = None
    detected_at: datetime = None
    
    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.utcnow()


@dataclass
class ForeignKeyDefinition:
    """Definition of a foreign key relationship."""
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    is_nullable: bool = False
    on_delete: str = "RESTRICT"
    on_update: str = "CASCADE"


class DataIntegrityManager:
    """
    Comprehensive data integrity management.
    
    Features:
    - Foreign key validation
    - Referential integrity checks
    - Constraint violation detection
    - Data consistency validation
    - Orphaned record detection
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.foreign_keys = self._load_foreign_key_definitions()
        
    def _load_foreign_key_definitions(self) -> Dict[str, List[ForeignKeyDefinition]]:
        """Load foreign key definitions for all tables."""
        return {
            "users": [
                ForeignKeyDefinition("users", "company_id", "companies", "id", False, "CASCADE"),
            ],
            "purchase_orders": [
                ForeignKeyDefinition("purchase_orders", "buyer_company_id", "companies", "id", False, "RESTRICT"),
                ForeignKeyDefinition("purchase_orders", "seller_company_id", "companies", "id", False, "RESTRICT"),
                ForeignKeyDefinition("purchase_orders", "product_id", "products", "id", False, "RESTRICT"),
                ForeignKeyDefinition("purchase_orders", "confirmed_by_user_id", "users", "id", True, "SET NULL"),
            ],
            "products": [
                ForeignKeyDefinition("products", "company_id", "companies", "id", False, "CASCADE"),
            ],
            "batches": [
                ForeignKeyDefinition("batches", "company_id", "companies", "id", False, "CASCADE"),
                ForeignKeyDefinition("batches", "product_id", "products", "id", False, "RESTRICT"),
                ForeignKeyDefinition("batches", "purchase_order_id", "purchase_orders", "id", True, "SET NULL"),
                ForeignKeyDefinition("batches", "created_by_user_id", "users", "id", True, "SET NULL"),
            ],
            "batch_transactions": [
                ForeignKeyDefinition("batch_transactions", "source_batch_id", "batches", "id", True, "SET NULL"),
                ForeignKeyDefinition("batch_transactions", "destination_batch_id", "batches", "id", True, "SET NULL"),
                ForeignKeyDefinition("batch_transactions", "company_id", "companies", "id", False, "CASCADE"),
                ForeignKeyDefinition("batch_transactions", "purchase_order_id", "purchase_orders", "id", True, "SET NULL"),
                ForeignKeyDefinition("batch_transactions", "created_by_user_id", "users", "id", True, "SET NULL"),
            ],
            "business_relationships": [
                ForeignKeyDefinition("business_relationships", "buyer_company_id", "companies", "id", False, "CASCADE"),
                ForeignKeyDefinition("business_relationships", "seller_company_id", "companies", "id", False, "CASCADE"),
                ForeignKeyDefinition("business_relationships", "invited_by_company_id", "companies", "id", True, "SET NULL"),
            ],
            "documents": [
                ForeignKeyDefinition("documents", "company_id", "companies", "id", False, "CASCADE"),
                ForeignKeyDefinition("documents", "po_id", "purchase_orders", "id", True, "CASCADE"),
                ForeignKeyDefinition("documents", "uploaded_by_user_id", "users", "id", True, "SET NULL"),
                ForeignKeyDefinition("documents", "parent_document_id", "documents", "id", True, "SET NULL"),
            ],
            "notifications": [
                ForeignKeyDefinition("notifications", "user_id", "users", "id", False, "CASCADE"),
                ForeignKeyDefinition("notifications", "company_id", "companies", "id", False, "CASCADE"),
            ],
            "audit_events": [
                ForeignKeyDefinition("audit_events", "user_id", "users", "id", True, "SET NULL"),
                ForeignKeyDefinition("audit_events", "company_id", "companies", "id", True, "SET NULL"),
            ],
            "po_compliance_results": [
                ForeignKeyDefinition("po_compliance_results", "po_id", "purchase_orders", "id", False, "CASCADE"),
            ],
            "gap_actions": [
                ForeignKeyDefinition("gap_actions", "company_id", "companies", "id", False, "CASCADE"),
                ForeignKeyDefinition("gap_actions", "created_by_user_id", "users", "id", True, "SET NULL"),
                ForeignKeyDefinition("gap_actions", "assigned_to_user_id", "users", "id", True, "SET NULL"),
            ]
        }
    
    def validate_entity_integrity(self, table_name: str, entity_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """
        Validate integrity constraints for an entity.
        
        Args:
            table_name: Name of the table
            entity_data: Entity data to validate
            
        Returns:
            List of constraint violations
        """
        violations = []
        
        # Validate foreign keys
        violations.extend(self._validate_foreign_keys(table_name, entity_data))
        
        # Validate business rules
        violations.extend(self._validate_business_rules(table_name, entity_data))
        
        # Validate data consistency
        violations.extend(self._validate_data_consistency(table_name, entity_data))
        
        return violations
    
    def _validate_foreign_keys(self, table_name: str, entity_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """Validate foreign key constraints."""
        violations = []
        
        if table_name not in self.foreign_keys:
            return violations
            
        for fk in self.foreign_keys[table_name]:
            if fk.source_column in entity_data:
                value = entity_data[fk.source_column]
                
                # Skip validation for nullable fields with None values
                if value is None and fk.is_nullable:
                    continue
                    
                # Check if foreign key exists
                if not self._foreign_key_exists(fk.target_table, fk.target_column, value):
                    violations.append(ConstraintViolation(
                        constraint_type=ConstraintType.FOREIGN_KEY,
                        table_name=table_name,
                        column_name=fk.source_column,
                        violation_message=f"Foreign key violation: {fk.source_column} references non-existent {fk.target_table}.{fk.target_column} = {value}",
                        severity=ViolationSeverity.CRITICAL,
                        entity_id=str(entity_data.get('id', 'unknown')),
                        related_entity_id=str(value)
                    ))
        
        return violations
    
    def _validate_business_rules(self, table_name: str, entity_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """Validate business-specific rules."""
        violations = []
        
        if table_name == "purchase_orders":
            violations.extend(self._validate_purchase_order_rules(entity_data))
        elif table_name == "business_relationships":
            violations.extend(self._validate_business_relationship_rules(entity_data))
        elif table_name == "batches":
            violations.extend(self._validate_batch_rules(entity_data))
        
        return violations
    
    def _validate_purchase_order_rules(self, po_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """Validate purchase order business rules."""
        violations = []
        
        # Buyer and seller cannot be the same
        if po_data.get('buyer_company_id') == po_data.get('seller_company_id'):
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.CHECK,
                table_name="purchase_orders",
                column_name="buyer_company_id",
                violation_message="Buyer and seller companies cannot be the same",
                severity=ViolationSeverity.CRITICAL,
                entity_id=str(po_data.get('id', 'unknown'))
            ))
        
        # Quantity must be positive
        if po_data.get('quantity', 0) <= 0:
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.CHECK,
                table_name="purchase_orders",
                column_name="quantity",
                violation_message="Quantity must be positive",
                severity=ViolationSeverity.HIGH,
                entity_id=str(po_data.get('id', 'unknown'))
            ))
        
        # Unit price must be positive
        if po_data.get('unit_price', 0) <= 0:
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.CHECK,
                table_name="purchase_orders",
                column_name="unit_price",
                violation_message="Unit price must be positive",
                severity=ViolationSeverity.HIGH,
                entity_id=str(po_data.get('id', 'unknown'))
            ))
        
        # Total amount should match quantity * unit_price
        expected_total = po_data.get('quantity', 0) * po_data.get('unit_price', 0)
        actual_total = po_data.get('total_amount', 0)
        if abs(float(expected_total) - float(actual_total)) > 0.01:
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.CHECK,
                table_name="purchase_orders",
                column_name="total_amount",
                violation_message=f"Total amount {actual_total} does not match quantity * unit_price = {expected_total}",
                severity=ViolationSeverity.MEDIUM,
                entity_id=str(po_data.get('id', 'unknown'))
            ))
        
        return violations
    
    def _validate_business_relationship_rules(self, br_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """Validate business relationship rules."""
        violations = []
        
        # Buyer and seller cannot be the same
        if br_data.get('buyer_company_id') == br_data.get('seller_company_id'):
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.CHECK,
                table_name="business_relationships",
                column_name="buyer_company_id",
                violation_message="Buyer and seller companies cannot be the same",
                severity=ViolationSeverity.CRITICAL,
                entity_id=str(br_data.get('id', 'unknown'))
            ))
        
        # Check for duplicate relationships
        existing = self.db.execute(text("""
            SELECT id FROM business_relationships 
            WHERE buyer_company_id = :buyer_id 
            AND seller_company_id = :seller_id 
            AND id != :current_id
        """), {
            'buyer_id': br_data.get('buyer_company_id'),
            'seller_id': br_data.get('seller_company_id'),
            'current_id': br_data.get('id', '00000000-0000-0000-0000-000000000000')
        }).fetchone()
        
        if existing:
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.UNIQUE,
                table_name="business_relationships",
                column_name="buyer_company_id",
                violation_message="Duplicate business relationship already exists",
                severity=ViolationSeverity.HIGH,
                entity_id=str(br_data.get('id', 'unknown')),
                related_entity_id=str(existing[0])
            ))
        
        return violations
    
    def _validate_batch_rules(self, batch_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """Validate batch business rules."""
        violations = []
        
        # Quantity must be positive
        if batch_data.get('quantity', 0) <= 0:
            violations.append(ConstraintViolation(
                constraint_type=ConstraintType.CHECK,
                table_name="batches",
                column_name="quantity",
                violation_message="Batch quantity must be positive",
                severity=ViolationSeverity.HIGH,
                entity_id=str(batch_data.get('id', 'unknown'))
            ))
        
        return violations
    
    def _validate_data_consistency(self, table_name: str, entity_data: Dict[str, Any]) -> List[ConstraintViolation]:
        """Validate data consistency rules."""
        violations = []
        
        # Add table-specific consistency checks
        if table_name == "purchase_orders":
            # Check if delivery date is in the future (warning only)
            delivery_date = entity_data.get('delivery_date')
            if delivery_date and delivery_date < datetime.now().date():
                violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.CHECK,
                    table_name="purchase_orders",
                    column_name="delivery_date",
                    violation_message="Delivery date is in the past",
                    severity=ViolationSeverity.WARNING,
                    entity_id=str(entity_data.get('id', 'unknown'))
                ))
        
        return violations
    
    def _foreign_key_exists(self, table_name: str, column_name: str, value: Any) -> bool:
        """Check if foreign key reference exists."""
        try:
            result = self.db.execute(text(
                f"SELECT 1 FROM {table_name} WHERE {column_name} = :value LIMIT 1"
            ), {"value": value}).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking foreign key: {e}")
            return False
    
    def detect_orphaned_records(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect orphaned records across all tables.
        
        Returns:
            Dictionary mapping table names to lists of orphaned records
        """
        orphaned_records = {}
        
        for table_name, foreign_keys in self.foreign_keys.items():
            for fk in foreign_keys:
                if fk.is_nullable:
                    continue  # Skip nullable foreign keys
                    
                try:
                    # Find records with invalid foreign key references
                    query = text(f"""
                        SELECT s.id, s.{fk.source_column}
                        FROM {fk.source_table} s
                        LEFT JOIN {fk.target_table} t ON s.{fk.source_column} = t.{fk.target_column}
                        WHERE s.{fk.source_column} IS NOT NULL 
                        AND t.{fk.target_column} IS NULL
                        LIMIT 100
                    """)
                    
                    result = self.db.execute(query).fetchall()
                    
                    if result:
                        if table_name not in orphaned_records:
                            orphaned_records[table_name] = []
                            
                        for row in result:
                            orphaned_records[table_name].append({
                                'id': str(row[0]),
                                'invalid_foreign_key': fk.source_column,
                                'invalid_value': str(row[1]),
                                'target_table': fk.target_table
                            })
                            
                except Exception as e:
                    logger.error(f"Error detecting orphaned records in {table_name}: {e}")
        
        return orphaned_records
    
    def fix_orphaned_records(self, table_name: str, action: str = "set_null") -> int:
        """
        Fix orphaned records in a table.
        
        Args:
            table_name: Name of the table to fix
            action: Action to take ("set_null", "delete")
            
        Returns:
            Number of records fixed
        """
        fixed_count = 0
        
        if table_name not in self.foreign_keys:
            return fixed_count
            
        for fk in self.foreign_keys[table_name]:
            try:
                if action == "set_null" and fk.is_nullable:
                    # Set invalid foreign keys to NULL
                    query = text(f"""
                        UPDATE {fk.source_table} 
                        SET {fk.source_column} = NULL
                        WHERE {fk.source_column} IS NOT NULL 
                        AND {fk.source_column} NOT IN (
                            SELECT {fk.target_column} FROM {fk.target_table}
                        )
                    """)
                    result = self.db.execute(query)
                    fixed_count += result.rowcount
                    
                elif action == "delete":
                    # Delete records with invalid foreign keys
                    query = text(f"""
                        DELETE FROM {fk.source_table}
                        WHERE {fk.source_column} IS NOT NULL 
                        AND {fk.source_column} NOT IN (
                            SELECT {fk.target_column} FROM {fk.target_table}
                        )
                    """)
                    result = self.db.execute(query)
                    fixed_count += result.rowcount
                    
            except Exception as e:
                logger.error(f"Error fixing orphaned records in {table_name}: {e}")
        
        if fixed_count > 0:
            self.db.commit()
            logger.info(f"Fixed {fixed_count} orphaned records in {table_name}")
        
        return fixed_count


def get_data_integrity_manager(db: Session) -> DataIntegrityManager:
    """Get data integrity manager instance."""
    return DataIntegrityManager(db)
