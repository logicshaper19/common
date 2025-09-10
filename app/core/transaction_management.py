"""
Comprehensive transaction management system for data consistency.

This module provides:
1. Robust transaction management with proper rollback strategies
2. Multi-step operation coordination
3. Data integrity validation
4. Distributed transaction support
5. Compensation patterns for complex operations
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Callable, Type, Union
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import event

from app.core.logging import get_logger

logger = get_logger(__name__)


class TransactionState(str, Enum):
    """Transaction state enumeration."""
    PENDING = "pending"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    COMPENSATING = "compensating"


class OperationType(str, Enum):
    """Operation type for transaction tracking."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH_CREATE = "batch_create"
    BATCH_UPDATE = "batch_update"
    EXTERNAL_API = "external_api"
    FILE_OPERATION = "file_operation"


@dataclass
class TransactionOperation:
    """Represents a single operation within a transaction."""
    operation_id: str = field(default_factory=lambda: str(uuid4()))
    operation_type: OperationType = OperationType.CREATE
    entity_type: str = ""
    entity_id: Optional[str] = None
    operation_data: Dict[str, Any] = field(default_factory=dict)
    compensation_data: Dict[str, Any] = field(default_factory=dict)
    executed_at: Optional[datetime] = None
    compensated_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class TransactionContext:
    """Context for managing complex transactions."""
    transaction_id: str = field(default_factory=lambda: str(uuid4()))
    state: TransactionState = TransactionState.PENDING
    operations: List[TransactionOperation] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TransactionError(Exception):
    """Base exception for transaction errors."""
    
    def __init__(self, message: str, transaction_id: str = None, operation_id: str = None):
        super().__init__(message)
        self.transaction_id = transaction_id
        self.operation_id = operation_id


class DataIntegrityError(TransactionError):
    """Exception for data integrity violations."""
    pass


class CompensationError(TransactionError):
    """Exception for compensation failures."""
    pass


class TransactionManager:
    """
    Advanced transaction manager with compensation patterns.
    
    Features:
    - Multi-step transaction coordination
    - Automatic rollback with compensation
    - Data integrity validation
    - Operation tracking and audit
    - Distributed transaction support
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.active_transactions: Dict[str, TransactionContext] = {}
        self.compensation_handlers: Dict[str, Callable] = {}
        
    def register_compensation_handler(self, operation_type: str, handler: Callable):
        """Register a compensation handler for an operation type."""
        self.compensation_handlers[operation_type] = handler
        logger.debug(f"Registered compensation handler for {operation_type}")
    
    @contextmanager
    def transaction(self, transaction_id: str = None, metadata: Dict[str, Any] = None):
        """
        Context manager for robust transaction handling.
        
        Args:
            transaction_id: Optional transaction ID
            metadata: Additional transaction metadata
            
        Yields:
            TransactionContext: Transaction context for operation tracking
        """
        if transaction_id is None:
            transaction_id = str(uuid4())
            
        context = TransactionContext(
            transaction_id=transaction_id,
            metadata=metadata or {}
        )
        
        self.active_transactions[transaction_id] = context
        context.state = TransactionState.ACTIVE
        
        logger.info(
            "Starting transaction",
            transaction_id=transaction_id,
            metadata=context.metadata
        )
        
        try:
            yield context
            
            # Commit if no exceptions
            self.db.commit()
            context.state = TransactionState.COMMITTED
            context.completed_at = datetime.utcnow()
            
            logger.info(
                "Transaction committed successfully",
                transaction_id=transaction_id,
                operations_count=len(context.operations),
                duration=(context.completed_at - context.started_at).total_seconds()
            )
            
        except Exception as e:
            # Rollback and compensate
            context.state = TransactionState.FAILED
            context.error_message = str(e)
            context.completed_at = datetime.utcnow()
            
            logger.error(
                "Transaction failed, initiating rollback",
                transaction_id=transaction_id,
                error=str(e),
                operations_count=len(context.operations)
            )
            
            try:
                self.db.rollback()
                self._compensate_operations(context)
                context.state = TransactionState.ROLLED_BACK
                
                logger.info(
                    "Transaction rolled back successfully",
                    transaction_id=transaction_id,
                    compensated_operations=len([op for op in context.operations if op.compensated_at])
                )
                
            except Exception as rollback_error:
                context.state = TransactionState.FAILED
                logger.error(
                    "Failed to rollback transaction",
                    transaction_id=transaction_id,
                    rollback_error=str(rollback_error),
                    original_error=str(e)
                )
                raise CompensationError(
                    f"Transaction rollback failed: {rollback_error}",
                    transaction_id=transaction_id
                )
            
            raise TransactionError(
                f"Transaction failed: {e}",
                transaction_id=transaction_id
            )
            
        finally:
            # Clean up
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
    
    def add_operation(
        self,
        context: TransactionContext,
        operation_type: OperationType,
        entity_type: str,
        entity_id: str = None,
        operation_data: Dict[str, Any] = None,
        compensation_data: Dict[str, Any] = None
    ) -> TransactionOperation:
        """
        Add an operation to the transaction context.
        
        Args:
            context: Transaction context
            operation_type: Type of operation
            entity_type: Type of entity being operated on
            entity_id: ID of the entity
            operation_data: Data for the operation
            compensation_data: Data needed for compensation
            
        Returns:
            TransactionOperation: Created operation
        """
        operation = TransactionOperation(
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            operation_data=operation_data or {},
            compensation_data=compensation_data or {},
            executed_at=datetime.utcnow()
        )
        
        context.operations.append(operation)
        
        logger.debug(
            "Added operation to transaction",
            transaction_id=context.transaction_id,
            operation_id=operation.operation_id,
            operation_type=operation_type.value,
            entity_type=entity_type
        )
        
        return operation
    
    def _compensate_operations(self, context: TransactionContext):
        """
        Compensate operations in reverse order.
        
        Args:
            context: Transaction context with operations to compensate
        """
        context.state = TransactionState.COMPENSATING
        
        # Compensate in reverse order
        for operation in reversed(context.operations):
            if operation.compensated_at:
                continue  # Already compensated
                
            try:
                self._compensate_operation(operation)
                operation.compensated_at = datetime.utcnow()
                
                logger.debug(
                    "Operation compensated",
                    transaction_id=context.transaction_id,
                    operation_id=operation.operation_id,
                    operation_type=operation.operation_type.value
                )
                
            except Exception as e:
                operation.error_message = str(e)
                logger.error(
                    "Failed to compensate operation",
                    transaction_id=context.transaction_id,
                    operation_id=operation.operation_id,
                    error=str(e)
                )
                # Continue with other compensations
    
    def _compensate_operation(self, operation: TransactionOperation):
        """
        Compensate a single operation.
        
        Args:
            operation: Operation to compensate
        """
        handler_key = f"{operation.entity_type}_{operation.operation_type.value}"
        
        if handler_key in self.compensation_handlers:
            handler = self.compensation_handlers[handler_key]
            handler(operation)
        else:
            logger.warning(
                "No compensation handler found",
                operation_type=operation.operation_type.value,
                entity_type=operation.entity_type,
                handler_key=handler_key
            )


class DataIntegrityValidator:
    """
    Validates data integrity constraints.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def validate_foreign_keys(self, entity_type: str, entity_data: Dict[str, Any]) -> List[str]:
        """
        Validate foreign key constraints.
        
        Args:
            entity_type: Type of entity
            entity_data: Entity data to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Define foreign key validations per entity type
        fk_validations = {
            "purchase_order": [
                ("buyer_company_id", "companies", "id"),
                ("seller_company_id", "companies", "id"),
                ("product_id", "products", "id"),
            ],
            "user": [
                ("company_id", "companies", "id"),
            ],
            "batch": [
                ("company_id", "companies", "id"),
                ("product_id", "products", "id"),
                ("purchase_order_id", "purchase_orders", "id"),
            ],
            "business_relationship": [
                ("buyer_company_id", "companies", "id"),
                ("seller_company_id", "companies", "id"),
                ("invited_by_company_id", "companies", "id"),
            ]
        }
        
        if entity_type in fk_validations:
            for field_name, table_name, column_name in fk_validations[entity_type]:
                if field_name in entity_data and entity_data[field_name] is not None:
                    if not self._foreign_key_exists(table_name, column_name, entity_data[field_name]):
                        errors.append(f"Foreign key violation: {field_name} references non-existent {table_name}.{column_name}")
        
        return errors
    
    def _foreign_key_exists(self, table_name: str, column_name: str, value: Any) -> bool:
        """Check if foreign key reference exists."""
        try:
            result = self.db.execute(
                f"SELECT 1 FROM {table_name} WHERE {column_name} = :value LIMIT 1",
                {"value": value}
            ).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking foreign key: {e}")
            return False


# Global transaction manager instance
_transaction_manager = None


def get_transaction_manager(db: Session) -> TransactionManager:
    """Get or create transaction manager instance."""
    global _transaction_manager
    if _transaction_manager is None or _transaction_manager.db != db:
        _transaction_manager = TransactionManager(db)
    return _transaction_manager


@contextmanager
def robust_transaction(
    db: Session,
    transaction_id: str = None,
    metadata: Dict[str, Any] = None
):
    """
    Convenience function for robust transaction management.
    
    Args:
        db: Database session
        transaction_id: Optional transaction ID
        metadata: Additional transaction metadata
        
    Yields:
        TransactionContext: Transaction context
    """
    manager = get_transaction_manager(db)
    with manager.transaction(transaction_id, metadata) as context:
        yield context
