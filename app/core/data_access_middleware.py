"""
Data access control middleware and decorators for the Common supply chain platform.
"""
from typing import Optional, Dict, Any, List, Callable, Union
from uuid import UUID
from functools import wraps
from fastapi import HTTPException, status, Request, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.data_access_control import DataAccessControlService
from app.models.data_access import (
    DataCategory,
    DataSensitivityLevel,
    AccessType,
    AccessResult
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def require_data_access(
    data_category: DataCategory,
    access_type: AccessType = AccessType.READ,
    entity_type: str = "unknown",
    sensitivity_level: Optional[DataSensitivityLevel] = None,
    allow_own_company: bool = True
):
    """
    Decorator to require specific data access permissions.
    
    Usage:
        @require_data_access(
            data_category=DataCategory.PURCHASE_ORDER,
            access_type=AccessType.READ,
            entity_type="purchase_order"
        )
        def get_purchase_order(po_id: UUID, current_user: User = Depends(get_current_user)):
            # Function implementation
            pass
    
    Args:
        data_category: Category of data being accessed
        access_type: Type of access required
        entity_type: Type of entity being accessed
        sensitivity_level: Required sensitivity level
        allow_own_company: Whether to allow access to own company data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            request = kwargs.get('request')
            
            if not current_user or not db:
                # Try to get from args if not in kwargs
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                    elif hasattr(arg, 'query'):  # Database session
                        db = arg
                    elif hasattr(arg, 'method'):  # Request object
                        request = arg
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Extract entity ID from common parameter names
            entity_id = kwargs.get('po_id') or kwargs.get('entity_id') or kwargs.get('id')
            if not entity_id and args:
                # Try to find UUID in args
                for arg in args:
                    if isinstance(arg, UUID):
                        entity_id = arg
                        break
            
            # Determine target company ID
            target_company_id = None
            if entity_id:
                target_company_id = _get_entity_owner_company(db, entity_type, entity_id)
            
            # Check if accessing own company data
            if allow_own_company and target_company_id == current_user.company_id:
                return await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
            
            # Check data access permission
            access_control = DataAccessControlService(db)
            access_result, permission, denial_reason = access_control.check_access_permission(
                requesting_user_id=current_user.id,
                requesting_company_id=current_user.company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                entity_type=entity_type,
                entity_id=entity_id,
                sensitivity_level=sensitivity_level,
                request=request
            )
            
            if access_result == AccessResult.DENIED:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: {denial_reason or 'Insufficient permissions'}"
                )
            
            # Execute the function
            return await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
        
        return wrapper
    return decorator


def filter_response_data(
    data_category: DataCategory,
    entity_type: str,
    target_company_field: str = "company_id"
):
    """
    Decorator to automatically filter sensitive data in API responses.
    
    Usage:
        @filter_response_data(
            data_category=DataCategory.PURCHASE_ORDER,
            entity_type="purchase_order",
            target_company_field="seller_company_id"
        )
        def get_purchase_order(po_id: UUID):
            # Function returns PO data that will be automatically filtered
            return po_data
    
    Args:
        data_category: Category of data being returned
        entity_type: Type of entity being returned
        target_company_field: Field name containing the target company ID
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')
            
            if not current_user or not db:
                # Try to get from args
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                    elif hasattr(arg, 'query'):
                        db = arg
            
            # Execute the original function
            result = await func(*args, **kwargs) if hasattr(func, '__await__') else func(*args, **kwargs)
            
            if not current_user or not db or not result:
                return result
            
            # Filter the result data
            filtered_result = _filter_result_data(
                result=result,
                current_user=current_user,
                db=db,
                data_category=data_category,
                entity_type=entity_type,
                target_company_field=target_company_field
            )
            
            return filtered_result
        
        return wrapper
    return decorator


class DataAccessMiddleware:
    """
    Middleware for automatic data access control and logging.
    
    This middleware automatically logs data access attempts and can
    enforce access controls at the API level.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # Extract request information
            request = Request(scope, receive)
            
            # Log API access attempt
            await self._log_api_access(request)
            
            # Check for data access patterns
            await self._check_data_access_patterns(request)
        
        # Continue with the request
        await self.app(scope, receive, send)
    
    async def _log_api_access(self, request: Request):
        """Log API access for monitoring."""
        try:
            # Extract user information from token if available
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Log the API access attempt
                logger.debug(
                    "API access attempt",
                    method=request.method,
                    path=str(request.url.path),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                )
        except Exception as e:
            logger.error("Failed to log API access", error=str(e))
    
    async def _check_data_access_patterns(self, request: Request):
        """Check for suspicious data access patterns."""
        try:
            # Implement rate limiting and anomaly detection here
            # This is a placeholder for advanced security features
            pass
        except Exception as e:
            logger.error("Failed to check data access patterns", error=str(e))


def _get_entity_owner_company(db: Session, entity_type: str, entity_id: UUID) -> Optional[UUID]:
    """Get the company that owns a specific entity."""
    try:
        if entity_type == "purchase_order":
            from app.models.purchase_order import PurchaseOrder
            po = db.query(PurchaseOrder).filter(PurchaseOrder.id == entity_id).first()
            if po:
                # For PO, we need to determine which company's data is being accessed
                # This could be either buyer or seller - context dependent
                return po.seller_company_id  # Default to seller for data access
        
        elif entity_type == "batch":
            from app.models.batch import Batch
            batch = db.query(Batch).filter(Batch.id == entity_id).first()
            if batch:
                return batch.company_id
        
        elif entity_type == "user":
            from app.models.user import User
            user = db.query(User).filter(User.id == entity_id).first()
            if user:
                return user.company_id
        
        return None
        
    except Exception as e:
        logger.error("Error getting entity owner company", error=str(e))
        return None


def _filter_result_data(
    result: Any,
    current_user: User,
    db: Session,
    data_category: DataCategory,
    entity_type: str,
    target_company_field: str
) -> Any:
    """Filter sensitive data from API response."""
    try:
        if not result:
            return result
        
        access_control = DataAccessControlService(db)
        
        # Handle different result types
        if isinstance(result, dict):
            # Single entity
            target_company_id = result.get(target_company_field)
            if target_company_id and target_company_id != current_user.company_id:
                filtered_data, filtered_fields = access_control.filter_sensitive_data(
                    data=result,
                    requesting_company_id=current_user.company_id,
                    target_company_id=UUID(target_company_id),
                    data_category=data_category,
                    entity_type=entity_type
                )
                return filtered_data
        
        elif isinstance(result, list):
            # List of entities
            filtered_results = []
            for item in result:
                if isinstance(item, dict):
                    target_company_id = item.get(target_company_field)
                    if target_company_id and target_company_id != current_user.company_id:
                        filtered_data, _ = access_control.filter_sensitive_data(
                            data=item,
                            requesting_company_id=current_user.company_id,
                            target_company_id=UUID(target_company_id),
                            data_category=data_category,
                            entity_type=entity_type
                        )
                        filtered_results.append(filtered_data)
                    else:
                        filtered_results.append(item)
                else:
                    filtered_results.append(item)
            return filtered_results
        
        # Return original result if no filtering needed
        return result
        
    except Exception as e:
        logger.error("Error filtering result data", error=str(e))
        return result  # Return original on error


# Convenience decorators for common use cases
def require_po_access(access_type: AccessType = AccessType.READ):
    """Require access to purchase order data."""
    return require_data_access(
        data_category=DataCategory.PURCHASE_ORDER,
        access_type=access_type,
        entity_type="purchase_order"
    )


def require_traceability_access(access_type: AccessType = AccessType.READ):
    """Require access to traceability data."""
    return require_data_access(
        data_category=DataCategory.TRACEABILITY,
        access_type=access_type,
        entity_type="traceability"
    )


def require_commercial_access(access_type: AccessType = AccessType.READ):
    """Require access to commercial sensitive data."""
    return require_data_access(
        data_category=DataCategory.PURCHASE_ORDER,
        access_type=access_type,
        entity_type="purchase_order",
        sensitivity_level=DataSensitivityLevel.COMMERCIAL
    )
