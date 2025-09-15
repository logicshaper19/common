"""
Main data access control service orchestrating all components.
"""
from typing import Optional, Dict, Any, List, Union, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.data_access import (
    DataAccessPermission,
    DataCategory,
    AccessType,
    DataSensitivityLevel,
    AccessResult
)
from .domain.models import AccessRequest, AccessDecision
from .permissions import PermissionManager, PermissionEvaluator
from .filtering import DataFilterEngine
from .logging import AccessLogger
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataAccessControlService:
    """
    Comprehensive data access control service for cross-company data sharing.
    
    Features:
    - Permission checking based on business relationships
    - Data filtering based on sensitivity levels
    - Distinction between operational and commercial data
    - Access logging for security monitoring
    - Automatic permission management
    """
    
    def __init__(self, db: Session):
        """Initialize data access control service."""
        self.db = db
        self.permission_manager = PermissionManager(db)
        self.permission_evaluator = PermissionEvaluator(db)
        self.filter_engine = DataFilterEngine(db)
        self.access_logger = AccessLogger(db)
    
    def check_access_permission(
        self,
        requesting_user_id: UUID,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID],
        data_category: DataCategory,
        access_type: AccessType,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        sensitivity_level: Optional[DataSensitivityLevel] = None,
        request: Optional[Request] = None
    ) -> Tuple[AccessResult, Optional[DataAccessPermission], Optional[str]]:
        """
        Check if a user/company has permission to access specific data.
        
        Args:
            requesting_user_id: User requesting access
            requesting_company_id: Company of the requesting user
            target_company_id: Company that owns the data (None for own data)
            data_category: Category of data being accessed
            access_type: Type of access requested
            entity_type: Type of entity being accessed
            entity_id: Specific entity ID (optional)
            sensitivity_level: Sensitivity level of the data
            request: HTTP request object for context
            
        Returns:
            Tuple of (access_result, permission, denial_reason)
        """
        try:
            # Create access request
            access_request = AccessRequest.from_request(
                requesting_user_id=requesting_user_id,
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                entity_type=entity_type,
                entity_id=entity_id,
                sensitivity_level=sensitivity_level,
                http_request=request
            )
            
            # Evaluate access request
            access_decision, existing_permission = self.permission_evaluator.evaluate_access_request(
                access_request
            )
            
            # Log access attempt
            self.access_logger.log_access_attempt(
                access_request,
                access_decision,
                existing_permission
            )
            
            return (
                access_decision.access_result,
                existing_permission,
                access_decision.denial_reason
            )
            
        except Exception as e:
            logger.error(f"Error checking access permission: {str(e)}", exc_info=True)
            
            # Log failed attempt
            self.access_logger.log_error_attempt(
                requesting_user_id,
                requesting_company_id,
                target_company_id,
                str(e)
            )
            
            return AccessResult.DENIED, None, f"Internal error during permission check: {str(e)}"
    
    def filter_sensitive_data(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        requesting_user_id: UUID,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID],
        entity_type: str,
        data_category: DataCategory,
        access_type: AccessType = AccessType.READ
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Filter sensitive data based on access permissions.
        
        Args:
            data: Data to filter
            requesting_user_id: User requesting the data
            requesting_company_id: Company of the requesting user
            target_company_id: Company that owns the data
            entity_type: Type of entity
            data_category: Category of data
            access_type: Type of access
            
        Returns:
            Filtered data
        """
        try:
            # Check access permission first
            access_result, permission, denial_reason = self.check_access_permission(
                requesting_user_id=requesting_user_id,
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                entity_type=entity_type
            )
            
            # If access is denied, return empty result
            if access_result == AccessResult.DENIED:
                logger.warning(f"Access denied for data filtering: {denial_reason}")
                return [] if isinstance(data, list) else {}
            
            # Create access request for filtering context
            access_request = AccessRequest(
                requesting_user_id=requesting_user_id,
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                entity_type=entity_type
            )
            
            # Re-evaluate to get filtering decision
            access_decision, _ = self.permission_evaluator.evaluate_access_request(access_request)
            
            # Apply filtering
            filtered_data = self.filter_engine.filter_data(
                data=data,
                access_decision=access_decision,
                entity_type=entity_type,
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id
            )
            
            # Log data access
            self.access_logger.log_data_access(
                access_request,
                access_decision,
                data_size=len(data) if isinstance(data, list) else 1,
                filtered=access_decision.requires_filtering
            )
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error filtering sensitive data: {str(e)}")
            return [] if isinstance(data, list) else {}
    
    def grant_permission(
        self,
        requesting_user_id: UUID,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID],
        data_category: DataCategory,
        access_type: AccessType,
        entity_type: str,
        granted_by_user_id: UUID,
        entity_id: Optional[UUID] = None,
        duration_days: Optional[int] = None,
        conditions: Optional[List[str]] = None,
        max_sensitivity_level: Optional[DataSensitivityLevel] = None
    ) -> DataAccessPermission:
        """
        Grant a data access permission.
        
        Args:
            requesting_user_id: User requesting access
            requesting_company_id: Company of the requesting user
            target_company_id: Company that owns the data
            data_category: Category of data
            access_type: Type of access
            entity_type: Type of entity
            granted_by_user_id: User granting the permission
            entity_id: Specific entity ID (optional)
            duration_days: Duration in days (optional)
            conditions: Additional conditions (optional)
            max_sensitivity_level: Maximum sensitivity level (optional)
            
        Returns:
            Created permission
        """
        # Create access request for context
        access_request = AccessRequest(
            requesting_user_id=requesting_user_id,
            requesting_company_id=requesting_company_id,
            target_company_id=target_company_id,
            data_category=data_category,
            access_type=access_type,
            entity_type=entity_type,
            entity_id=entity_id
        )
        
        # Grant permission
        permission = self.permission_manager.grant_permission(
            access_request=access_request,
            granted_by_user_id=granted_by_user_id,
            duration_days=duration_days,
            conditions=conditions,
            max_sensitivity_level=max_sensitivity_level
        )
        
        # Log permission grant
        self.access_logger.log_permission_granted(
            access_request,
            permission,
            granted_by_user_id
        )
        
        return permission
    
    def revoke_permission(
        self,
        permission_id: UUID,
        revoked_by_user_id: UUID,
        reason: Optional[str] = None
    ) -> bool:
        """
        Revoke a data access permission.
        
        Args:
            permission_id: ID of permission to revoke
            revoked_by_user_id: User revoking the permission
            reason: Reason for revocation
            
        Returns:
            True if revoked successfully
        """
        success = self.permission_manager.revoke_permission(
            permission_id=permission_id,
            revoked_by_user_id=revoked_by_user_id,
            reason=reason
        )
        
        if success:
            # Log permission revocation
            self.access_logger.log_permission_revoked(
                permission_id,
                revoked_by_user_id,
                reason
            )
        
        return success
    
    def get_user_permissions(
        self,
        user_id: UUID,
        company_id: UUID,
        include_expired: bool = False
    ) -> List[DataAccessPermission]:
        """Get all permissions for a user."""
        return self.permission_manager.get_user_permissions(
            user_id=user_id,
            company_id=company_id,
            include_expired=include_expired
        )
    
    def get_company_permissions(
        self,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID] = None,
        include_expired: bool = False
    ) -> List[DataAccessPermission]:
        """Get all permissions for a company."""
        return self.permission_manager.get_company_permissions(
            requesting_company_id=requesting_company_id,
            target_company_id=target_company_id,
            include_expired=include_expired
        )
    
    def cleanup_expired_permissions(self) -> int:
        """Clean up expired permissions."""
        return self.permission_manager.cleanup_expired_permissions()
    
    def get_access_summary(
        self,
        company_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get access summary for a company.
        
        Args:
            company_id: Company ID
            days: Number of days to include in summary
            
        Returns:
            Access summary
        """
        # Get permission summary
        permission_summary = self.permission_manager.get_permission_summary(company_id)
        
        # Get access log summary
        access_summary = self.access_logger.get_access_summary(company_id, days)
        
        return {
            'company_id': str(company_id),
            'summary_period_days': days,
            'permissions': permission_summary,
            'access_activity': access_summary,
            'generated_at': permission_summary['last_updated']
        }
