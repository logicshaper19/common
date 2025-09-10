"""
Enhanced base service classes with robust transaction management.

This module provides:
1. Base service classes with transaction support
2. Automatic data integrity validation
3. Rollback and compensation patterns
4. Operation tracking and audit
5. Error handling and recovery
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.transaction_management import (
    TransactionManager,
    TransactionContext,
    TransactionOperation,
    OperationType,
    robust_transaction,
    get_transaction_manager
)
from app.core.data_integrity import (
    DataIntegrityManager,
    ConstraintViolation,
    ViolationSeverity,
    get_data_integrity_manager
)
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ServiceError(Exception):
    """Base exception for service errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class DataIntegrityServiceError(ServiceError):
    """Exception for data integrity violations in services."""
    
    def __init__(self, message: str, violations: List[ConstraintViolation] = None):
        super().__init__(message, "DATA_INTEGRITY_ERROR")
        self.violations = violations or []


class TransactionalServiceError(ServiceError):
    """Exception for transaction-related errors in services."""
    
    def __init__(self, message: str, transaction_id: str = None, operation_id: str = None):
        super().__init__(message, "TRANSACTION_ERROR")
        self.transaction_id = transaction_id
        self.operation_id = operation_id


class BaseService(ABC):
    """
    Enhanced base service class with transaction management.
    
    Features:
    - Automatic transaction management
    - Data integrity validation
    - Operation tracking and audit
    - Error handling and recovery
    - Compensation patterns
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.transaction_manager = get_transaction_manager(db)
        self.integrity_manager = get_data_integrity_manager(db)
        self.service_name = self.__class__.__name__
        
        # Register compensation handlers
        self._register_compensation_handlers()
    
    def _register_compensation_handlers(self):
        """Register compensation handlers for this service."""
        # Override in subclasses to register specific handlers
        pass
    
    def create_entity(
        self,
        entity_type: str,
        entity_data: Dict[str, Any],
        validate_integrity: bool = True,
        transaction_metadata: Dict[str, Any] = None
    ) -> Any:
        """
        Create an entity with full transaction support.
        
        Args:
            entity_type: Type of entity to create
            entity_data: Entity data
            validate_integrity: Whether to validate data integrity
            transaction_metadata: Additional transaction metadata
            
        Returns:
            Created entity
        """
        with robust_transaction(
            self.db,
            metadata={
                "service": self.service_name,
                "operation": "create_entity",
                "entity_type": entity_type,
                **(transaction_metadata or {})
            }
        ) as context:
            
            # Validate data integrity
            if validate_integrity:
                violations = self.integrity_manager.validate_entity_integrity(entity_type, entity_data)
                critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
                
                if critical_violations:
                    raise DataIntegrityServiceError(
                        f"Critical data integrity violations for {entity_type}",
                        violations=critical_violations
                    )
                
                # Log warnings for non-critical violations
                warning_violations = [v for v in violations if v.severity in [ViolationSeverity.WARNING, ViolationSeverity.MEDIUM]]
                if warning_violations:
                    logger.warning(
                        f"Data integrity warnings for {entity_type}",
                        violations=[v.violation_message for v in warning_violations]
                    )
            
            # Create entity
            entity = self._create_entity_impl(entity_type, entity_data)
            
            # Track operation
            operation = self.transaction_manager.add_operation(
                context,
                OperationType.CREATE,
                entity_type,
                str(getattr(entity, 'id', 'unknown')),
                operation_data=entity_data,
                compensation_data={"entity_id": str(getattr(entity, 'id', 'unknown'))}
            )
            
            logger.info(
                f"Created {entity_type}",
                entity_id=str(getattr(entity, 'id', 'unknown')),
                transaction_id=context.transaction_id,
                operation_id=operation.operation_id
            )
            
            return entity
    
    def update_entity(
        self,
        entity_type: str,
        entity_id: str,
        update_data: Dict[str, Any],
        validate_integrity: bool = True,
        transaction_metadata: Dict[str, Any] = None
    ) -> Any:
        """
        Update an entity with full transaction support.
        
        Args:
            entity_type: Type of entity to update
            entity_id: ID of entity to update
            update_data: Update data
            validate_integrity: Whether to validate data integrity
            transaction_metadata: Additional transaction metadata
            
        Returns:
            Updated entity
        """
        with robust_transaction(
            self.db,
            metadata={
                "service": self.service_name,
                "operation": "update_entity",
                "entity_type": entity_type,
                "entity_id": entity_id,
                **(transaction_metadata or {})
            }
        ) as context:
            
            # Get original entity for compensation
            original_entity = self._get_entity_impl(entity_type, entity_id)
            if not original_entity:
                raise ServiceError(f"{entity_type} with ID {entity_id} not found", "ENTITY_NOT_FOUND")
            
            # Prepare full entity data for validation
            full_entity_data = self._merge_entity_data(original_entity, update_data)
            
            # Validate data integrity
            if validate_integrity:
                violations = self.integrity_manager.validate_entity_integrity(entity_type, full_entity_data)
                critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
                
                if critical_violations:
                    raise DataIntegrityServiceError(
                        f"Critical data integrity violations for {entity_type}",
                        violations=critical_violations
                    )
            
            # Update entity
            updated_entity = self._update_entity_impl(entity_type, entity_id, update_data)
            
            # Track operation with compensation data
            operation = self.transaction_manager.add_operation(
                context,
                OperationType.UPDATE,
                entity_type,
                entity_id,
                operation_data=update_data,
                compensation_data=self._extract_entity_data(original_entity)
            )
            
            logger.info(
                f"Updated {entity_type}",
                entity_id=entity_id,
                transaction_id=context.transaction_id,
                operation_id=operation.operation_id
            )
            
            return updated_entity
    
    def delete_entity(
        self,
        entity_type: str,
        entity_id: str,
        soft_delete: bool = True,
        transaction_metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Delete an entity with full transaction support.
        
        Args:
            entity_type: Type of entity to delete
            entity_id: ID of entity to delete
            soft_delete: Whether to perform soft delete
            transaction_metadata: Additional transaction metadata
            
        Returns:
            True if deleted successfully
        """
        with robust_transaction(
            self.db,
            metadata={
                "service": self.service_name,
                "operation": "delete_entity",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "soft_delete": soft_delete,
                **(transaction_metadata or {})
            }
        ) as context:
            
            # Get entity for compensation
            entity = self._get_entity_impl(entity_type, entity_id)
            if not entity:
                raise ServiceError(f"{entity_type} with ID {entity_id} not found", "ENTITY_NOT_FOUND")
            
            # Delete entity
            success = self._delete_entity_impl(entity_type, entity_id, soft_delete)
            
            # Track operation with full entity data for compensation
            operation = self.transaction_manager.add_operation(
                context,
                OperationType.DELETE,
                entity_type,
                entity_id,
                operation_data={"soft_delete": soft_delete},
                compensation_data=self._extract_entity_data(entity)
            )
            
            logger.info(
                f"Deleted {entity_type}",
                entity_id=entity_id,
                soft_delete=soft_delete,
                transaction_id=context.transaction_id,
                operation_id=operation.operation_id
            )
            
            return success
    
    def batch_create_entities(
        self,
        entity_type: str,
        entities_data: List[Dict[str, Any]],
        validate_integrity: bool = True,
        fail_on_first_error: bool = False,
        transaction_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create multiple entities in a single transaction.
        
        Args:
            entity_type: Type of entities to create
            entities_data: List of entity data
            validate_integrity: Whether to validate data integrity
            fail_on_first_error: Whether to fail on first error or continue
            transaction_metadata: Additional transaction metadata
            
        Returns:
            Dictionary with results and statistics
        """
        with robust_transaction(
            self.db,
            metadata={
                "service": self.service_name,
                "operation": "batch_create_entities",
                "entity_type": entity_type,
                "batch_size": len(entities_data),
                **(transaction_metadata or {})
            }
        ) as context:
            
            results = {
                "successful": [],
                "failed": [],
                "total_submitted": len(entities_data),
                "total_successful": 0,
                "total_failed": 0,
                "errors": []
            }
            
            for i, entity_data in enumerate(entities_data):
                try:
                    # Validate data integrity
                    if validate_integrity:
                        violations = self.integrity_manager.validate_entity_integrity(entity_type, entity_data)
                        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
                        
                        if critical_violations:
                            error_msg = f"Item {i+1}: Critical data integrity violations"
                            results["failed"].append({"index": i, "error": error_msg, "data": entity_data})
                            results["errors"].append(error_msg)
                            
                            if fail_on_first_error:
                                raise DataIntegrityServiceError(error_msg, violations=critical_violations)
                            continue
                    
                    # Create entity
                    entity = self._create_entity_impl(entity_type, entity_data)
                    
                    # Track operation
                    operation = self.transaction_manager.add_operation(
                        context,
                        OperationType.BATCH_CREATE,
                        entity_type,
                        str(getattr(entity, 'id', 'unknown')),
                        operation_data=entity_data,
                        compensation_data={"entity_id": str(getattr(entity, 'id', 'unknown'))}
                    )
                    
                    results["successful"].append({
                        "index": i,
                        "entity_id": str(getattr(entity, 'id', 'unknown')),
                        "operation_id": operation.operation_id
                    })
                    results["total_successful"] += 1
                    
                except Exception as e:
                    error_msg = f"Item {i+1}: {str(e)}"
                    results["failed"].append({"index": i, "error": error_msg, "data": entity_data})
                    results["errors"].append(error_msg)
                    results["total_failed"] += 1
                    
                    if fail_on_first_error:
                        raise
            
            logger.info(
                f"Batch created {entity_type}",
                total_submitted=results["total_submitted"],
                total_successful=results["total_successful"],
                total_failed=results["total_failed"],
                transaction_id=context.transaction_id
            )
            
            return results
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def _create_entity_impl(self, entity_type: str, entity_data: Dict[str, Any]) -> Any:
        """Implementation-specific entity creation."""
        pass
    
    @abstractmethod
    def _get_entity_impl(self, entity_type: str, entity_id: str) -> Any:
        """Implementation-specific entity retrieval."""
        pass
    
    @abstractmethod
    def _update_entity_impl(self, entity_type: str, entity_id: str, update_data: Dict[str, Any]) -> Any:
        """Implementation-specific entity update."""
        pass
    
    @abstractmethod
    def _delete_entity_impl(self, entity_type: str, entity_id: str, soft_delete: bool) -> bool:
        """Implementation-specific entity deletion."""
        pass
    
    @abstractmethod
    def _extract_entity_data(self, entity: Any) -> Dict[str, Any]:
        """Extract data from entity for compensation."""
        pass
    
    @abstractmethod
    def _merge_entity_data(self, entity: Any, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge entity data with update data for validation."""
        pass
