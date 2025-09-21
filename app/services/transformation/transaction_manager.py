"""
Database transaction management for transformation services.

This module provides robust transaction management with proper rollback handling,
retry logic, and data integrity guarantees.
"""
from typing import Any, Callable, Optional, Dict, List
from uuid import UUID
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
import time
import random

from app.core.logging import get_logger
from ..exceptions import TransactionError, DataIntegrityError

logger = get_logger(__name__)


class TransactionManager:
    """
    Manages database transactions with proper error handling and retry logic.
    
    This class provides:
    - Atomic transaction management
    - Automatic rollback on errors
    - Retry logic for transient failures
    - Data integrity validation
    - Comprehensive logging
    """
    
    def __init__(self, db: Session, max_retries: int = 3, retry_delay: float = 1.0):
        self.db = db
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = get_logger(self.__class__.__name__)
    
    @contextmanager
    def atomic_transaction(self, operation_name: str = "database_operation"):
        """
        Context manager for atomic database transactions.
        
        Args:
            operation_name: Name of the operation for logging
            
        Yields:
            Session: Database session for the transaction
            
        Raises:
            TransactionError: If transaction fails after retries
            DataIntegrityError: If data integrity is compromised
        """
        retry_count = 0
        last_exception = None
        
        while retry_count <= self.max_retries:
            try:
                self.logger.info(
                    f"Starting atomic transaction: {operation_name}",
                    retry_count=retry_count,
                    max_retries=self.max_retries
                )
                
                # Begin transaction
                self.db.begin()
                
                try:
                    yield self.db
                    
                    # Commit transaction
                    self.db.commit()
                    
                    self.logger.info(
                        f"Transaction committed successfully: {operation_name}",
                        retry_count=retry_count
                    )
                    return
                    
                except Exception as e:
                    # Rollback on any error
                    self.db.rollback()
                    raise e
                    
            except IntegrityError as e:
                last_exception = e
                self.logger.error(
                    f"Data integrity error in transaction: {operation_name}",
                    error=str(e),
                    retry_count=retry_count,
                    exc_info=True
                )
                raise DataIntegrityError(
                    message=f"Data integrity error in {operation_name}: {str(e)}",
                    entity_type="transaction",
                    details={"operation": operation_name, "error": str(e)}
                )
                
            except OperationalError as e:
                last_exception = e
                retry_count += 1
                
                if retry_count <= self.max_retries:
                    delay = self.retry_delay * (2 ** (retry_count - 1)) + random.uniform(0, 1)
                    self.logger.warning(
                        f"Transient error in transaction, retrying: {operation_name}",
                        error=str(e),
                        retry_count=retry_count,
                        delay=delay,
                        exc_info=True
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Transaction failed after {self.max_retries} retries: {operation_name}",
                        error=str(e),
                        exc_info=True
                    )
                    raise TransactionError(
                        message=f"Transaction failed after {self.max_retries} retries: {str(e)}",
                        operation=operation_name,
                        details={"retry_count": retry_count, "error": str(e)}
                    )
                    
            except SQLAlchemyError as e:
                last_exception = e
                self.logger.error(
                    f"SQLAlchemy error in transaction: {operation_name}",
                    error=str(e),
                    retry_count=retry_count,
                    exc_info=True
                )
                raise TransactionError(
                    message=f"Database error in {operation_name}: {str(e)}",
                    operation=operation_name,
                    details={"error": str(e)}
                )
                
            except Exception as e:
                last_exception = e
                self.logger.error(
                    f"Unexpected error in transaction: {operation_name}",
                    error=str(e),
                    retry_count=retry_count,
                    exc_info=True
                )
                raise TransactionError(
                    message=f"Unexpected error in {operation_name}: {str(e)}",
                    operation=operation_name,
                    details={"error": str(e)}
                )
        
        # If we get here, all retries failed
        raise TransactionError(
            message=f"Transaction failed after {self.max_retries} retries: {str(last_exception)}",
            operation=operation_name,
            details={"retry_count": retry_count, "last_error": str(last_exception)}
        )
    
    def execute_with_retry(
        self, 
        operation: Callable[[Session], Any], 
        operation_name: str = "database_operation"
    ) -> Any:
        """
        Execute a database operation with retry logic.
        
        Args:
            operation: Function to execute with database session
            operation_name: Name of the operation for logging
            
        Returns:
            Result of the operation
            
        Raises:
            TransactionError: If operation fails after retries
        """
        with self.atomic_transaction(operation_name) as db:
            return operation(db)
    
    def batch_operations(
        self, 
        operations: List[Callable[[Session], Any]], 
        operation_name: str = "batch_operations"
    ) -> List[Any]:
        """
        Execute multiple operations in a single transaction.
        
        Args:
            operations: List of functions to execute
            operation_name: Name of the batch operation for logging
            
        Returns:
            List of results from each operation
            
        Raises:
            TransactionError: If any operation fails
        """
        results = []
        
        def batch_operation(db: Session) -> List[Any]:
            for i, operation in enumerate(operations):
                self.logger.debug(
                    f"Executing operation {i+1}/{len(operations)} in batch",
                    operation_name=operation_name,
                    operation_index=i
                )
                result = operation(db)
                results.append(result)
            return results
        
        return self.execute_with_retry(batch_operation, f"{operation_name}_batch")
    
    def validate_data_integrity(
        self, 
        validation_checks: List[Callable[[Session], bool]], 
        operation_name: str = "data_integrity_check"
    ) -> bool:
        """
        Validate data integrity before committing transaction.
        
        Args:
            validation_checks: List of validation functions
            operation_name: Name of the validation operation
            
        Returns:
            True if all validations pass
            
        Raises:
            DataIntegrityError: If validation fails
        """
        def validate_operation(db: Session) -> bool:
            for i, check in enumerate(validation_checks):
                try:
                    if not check(db):
                        raise DataIntegrityError(
                            message=f"Data integrity check {i+1} failed",
                            entity_type="validation",
                            details={"check_index": i, "operation": operation_name}
                        )
                except Exception as e:
                    raise DataIntegrityError(
                        message=f"Data integrity validation error: {str(e)}",
                        entity_type="validation",
                        details={"check_index": i, "operation": operation_name, "error": str(e)}
                    )
            return True
        
        return self.execute_with_retry(validate_operation, f"{operation_name}_validation")
    
    def create_entity_with_validation(
        self, 
        entity_creator: Callable[[Session], Any],
        validators: List[Callable[[Session, Any], bool]],
        operation_name: str = "create_entity"
    ) -> Any:
        """
        Create an entity with validation in a single transaction.
        
        Args:
            entity_creator: Function to create the entity
            validators: List of validation functions
            operation_name: Name of the operation
            
        Returns:
            Created entity
            
        Raises:
            TransactionError: If creation fails
            DataIntegrityError: If validation fails
        """
        def create_and_validate(db: Session) -> Any:
            # Create entity
            entity = entity_creator(db)
            db.flush()  # Flush to get ID
            
            # Validate created entity
            for i, validator in enumerate(validators):
                if not validator(db, entity):
                    raise DataIntegrityError(
                        message=f"Entity validation {i+1} failed after creation",
                        entity_type="entity",
                        entity_id=str(getattr(entity, 'id', 'unknown')),
                        details={"check_index": i, "operation": operation_name}
                    )
            
            return entity
        
        return self.execute_with_retry(create_and_validate, operation_name)
    
    def update_entity_with_validation(
        self, 
        entity_id: UUID,
        entity_updater: Callable[[Session, Any], Any],
        validators: List[Callable[[Session, Any], bool]],
        operation_name: str = "update_entity"
    ) -> Any:
        """
        Update an entity with validation in a single transaction.
        
        Args:
            entity_id: ID of the entity to update
            entity_updater: Function to update the entity
            validators: List of validation functions
            operation_name: Name of the operation
            
        Returns:
            Updated entity
            
        Raises:
            TransactionError: If update fails
            DataIntegrityError: If validation fails
        """
        def update_and_validate(db: Session) -> Any:
            # Get entity
            entity = db.get(entity_id)
            if not entity:
                raise DataIntegrityError(
                    message=f"Entity not found: {entity_id}",
                    entity_type="entity",
                    entity_id=str(entity_id),
                    details={"operation": operation_name}
                )
            
            # Update entity
            updated_entity = entity_updater(db, entity)
            db.flush()
            
            # Validate updated entity
            for i, validator in enumerate(validators):
                if not validator(db, updated_entity):
                    raise DataIntegrityError(
                        message=f"Entity validation {i+1} failed after update",
                        entity_type="entity",
                        entity_id=str(entity_id),
                        details={"check_index": i, "operation": operation_name}
                    )
            
            return updated_entity
        
        return self.execute_with_retry(update_and_validate, operation_name)
    
    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics for monitoring."""
        return {
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "db_url": str(self.db.bind.url) if self.db.bind else "unknown",
            "is_active": self.db.is_active if hasattr(self.db, 'is_active') else False
        }
