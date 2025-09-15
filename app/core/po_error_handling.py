"""
Standardized error handling for Purchase Orders API
"""
from typing import Any, Dict, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)


class POErrorHandler:
    """Standardized error handler for Purchase Orders operations."""
    
    @staticmethod
    def handle_uuid_validation_error(value: str, field_name: str = "ID") -> HTTPException:
        """Handle UUID validation errors."""
        logger.warning(f"Invalid UUID format for {field_name}: {value}")
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format"
        )
    
    @staticmethod
    def handle_not_found_error(entity_type: str, entity_id: str) -> HTTPException:
        """Handle entity not found errors."""
        logger.warning(f"{entity_type} not found: {entity_id}")
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_type} not found"
        )
    
    @staticmethod
    def handle_permission_error(action: str, entity_type: str = "purchase order") -> HTTPException:
        """Handle permission denied errors."""
        logger.warning(f"Permission denied for {action} on {entity_type}")
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Not authorized to {action} this {entity_type}"
        )
    
    @staticmethod
    def handle_state_error(current_status: str, required_status: str, action: str) -> HTTPException:
        """Handle invalid state errors."""
        logger.warning(f"Invalid state for {action}: current={current_status}, required={required_status}")
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} purchase order in {current_status} state"
        )
    
    @staticmethod
    def handle_validation_error(message: str) -> HTTPException:
        """Handle validation errors."""
        logger.warning(f"Validation error: {message}")
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    @staticmethod
    def handle_database_error(error: SQLAlchemyError, operation: str) -> HTTPException:
        """Handle database errors."""
        logger.error(f"Database error during {operation}: {str(error)}", exc_info=True)
        
        if isinstance(error, IntegrityError):
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data integrity constraint violation"
            )
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {operation}"
        )
    
    @staticmethod
    def handle_generic_error(error: Exception, operation: str) -> HTTPException:
        """Handle generic errors."""
        logger.error(f"Error during {operation}: {str(error)}", exc_info=True)
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {operation}"
        )


def validate_uuid(value: str, field_name: str = "ID") -> UUID:
    """Validate and convert string to UUID."""
    try:
        return UUID(value)
    except ValueError:
        raise POErrorHandler.handle_uuid_validation_error(value, field_name)


def validate_po_state(purchase_order: Any, required_statuses: list, action: str) -> None:
    """Validate purchase order state for specific action."""
    if purchase_order.status not in required_statuses:
        raise POErrorHandler.handle_state_error(
            purchase_order.status, 
            ", ".join(required_statuses), 
            action
        )


def validate_company_access(purchase_order: Any, user_company_id: UUID, required_role: str) -> None:
    """Validate company access for purchase order operations."""
    if required_role == "buyer" and purchase_order.buyer_company_id != user_company_id:
        raise POErrorHandler.handle_permission_error("access", "purchase order")
    elif required_role == "seller" and purchase_order.seller_company_id != user_company_id:
        raise POErrorHandler.handle_permission_error("access", "purchase order")


def handle_database_operation(db: Session, operation: str, func, *args, **kwargs):
    """Handle database operations with proper error handling and rollback."""
    try:
        result = func(*args, **kwargs)
        db.commit()
        return result
    except SQLAlchemyError as e:
        db.rollback()
        raise POErrorHandler.handle_database_error(e, operation)
    except Exception as e:
        db.rollback()
        raise POErrorHandler.handle_generic_error(e, operation)
