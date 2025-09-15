"""
Permission management for data access control.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.data_access import (
    DataAccessPermission,
    DataCategory,
    AccessType,
    DataSensitivityLevel
)
from ..domain.models import AccessRequest
from app.core.logging import get_logger

logger = get_logger(__name__)


class PermissionManager:
    """Manages data access permissions."""
    
    def __init__(self, db: Session):
        """Initialize permission manager."""
        self.db = db
    
    def grant_permission(
        self,
        access_request: AccessRequest,
        granted_by_user_id: UUID,
        duration_days: Optional[int] = None,
        conditions: Optional[List[str]] = None,
        max_sensitivity_level: Optional[DataSensitivityLevel] = None
    ) -> DataAccessPermission:
        """
        Grant a data access permission.
        
        Args:
            access_request: The access request to grant
            granted_by_user_id: User who granted the permission
            duration_days: Duration of the permission in days
            conditions: Additional conditions for the permission
            max_sensitivity_level: Maximum sensitivity level allowed
            
        Returns:
            The created permission record
        """
        logger.info(
            f"Granting permission for user {access_request.requesting_user_id} "
            f"to access {access_request.data_category} data"
        )
        
        # Calculate expiry date
        expiry_date = None
        if duration_days:
            expiry_date = datetime.utcnow() + timedelta(days=duration_days)
        
        # Create permission record
        permission = DataAccessPermission(
            id=uuid4(),
            requesting_user_id=access_request.requesting_user_id,
            requesting_company_id=access_request.requesting_company_id,
            target_company_id=access_request.target_company_id,
            data_category=access_request.data_category,
            access_type=access_request.access_type,
            entity_type=access_request.entity_type,
            entity_id=access_request.entity_id,
            granted_by_user_id=granted_by_user_id,
            granted_at=datetime.utcnow(),
            expires_at=expiry_date,
            max_sensitivity_level=max_sensitivity_level,
            conditions=conditions or [],
            is_active=True
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        logger.info(f"Permission granted with ID: {permission.id}")
        
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
            permission_id: ID of the permission to revoke
            revoked_by_user_id: User who revoked the permission
            reason: Reason for revocation
            
        Returns:
            True if permission was revoked, False if not found
        """
        logger.info(f"Revoking permission {permission_id}")
        
        permission = self.db.query(DataAccessPermission).filter(
            DataAccessPermission.id == permission_id,
            DataAccessPermission.is_active == True
        ).first()
        
        if not permission:
            logger.warning(f"Permission {permission_id} not found or already revoked")
            return False
        
        # Update permission record
        permission.is_active = False
        permission.revoked_at = datetime.utcnow()
        permission.revoked_by_user_id = revoked_by_user_id
        permission.revocation_reason = reason
        
        self.db.commit()
        
        logger.info(f"Permission {permission_id} revoked successfully")
        
        return True
    
    def revoke_user_permissions(
        self,
        user_id: UUID,
        company_id: UUID,
        revoked_by_user_id: UUID,
        reason: Optional[str] = None
    ) -> int:
        """
        Revoke all permissions for a specific user.
        
        Args:
            user_id: User whose permissions to revoke
            company_id: Company of the user
            revoked_by_user_id: User who revoked the permissions
            reason: Reason for revocation
            
        Returns:
            Number of permissions revoked
        """
        logger.info(f"Revoking all permissions for user {user_id}")
        
        permissions = self.db.query(DataAccessPermission).filter(
            DataAccessPermission.grantee_company_id == company_id,
            DataAccessPermission.is_active == True
        ).all()
        
        revoked_count = 0
        for permission in permissions:
            permission.is_active = False
            permission.revoked_at = datetime.utcnow()
            permission.revoked_by_user_id = revoked_by_user_id
            permission.revocation_reason = reason
            revoked_count += 1
        
        self.db.commit()
        
        logger.info(f"Revoked {revoked_count} permissions for user {user_id}")
        
        return revoked_count
    
    def get_user_permissions(
        self,
        user_id: UUID,
        company_id: UUID,
        include_expired: bool = False
    ) -> List[DataAccessPermission]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: User ID
            company_id: Company ID
            include_expired: Whether to include expired permissions
            
        Returns:
            List of permissions
        """
        query = self.db.query(DataAccessPermission).filter(
            DataAccessPermission.grantee_company_id == company_id
        )
        
        if not include_expired:
            query = query.filter(
                DataAccessPermission.is_active == True,
                or_(
                    DataAccessPermission.expires_at.is_(None),
                    DataAccessPermission.expires_at > datetime.utcnow()
                )
            )
        
        return query.all()
    
    def get_company_permissions(
        self,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID] = None,
        include_expired: bool = False
    ) -> List[DataAccessPermission]:
        """
        Get all permissions for a company.
        
        Args:
            requesting_company_id: Company requesting access
            target_company_id: Target company (None for all)
            include_expired: Whether to include expired permissions
            
        Returns:
            List of permissions
        """
        query = self.db.query(DataAccessPermission).filter(
            DataAccessPermission.grantee_company_id == requesting_company_id
        )
        
        # Note: DataAccessPermission doesn't have target_company_id field
        # The permission is based on grantor/grantee company relationship
        
        if not include_expired:
            query = query.filter(
                DataAccessPermission.is_active == True,
                or_(
                    DataAccessPermission.expires_at.is_(None),
                    DataAccessPermission.expires_at > datetime.utcnow()
                )
            )
        
        return query.all()
    
    def cleanup_expired_permissions(self) -> int:
        """
        Clean up expired permissions.
        
        Returns:
            Number of permissions cleaned up
        """
        logger.info("Cleaning up expired permissions")
        
        expired_permissions = self.db.query(DataAccessPermission).filter(
            DataAccessPermission.is_active == True,
            DataAccessPermission.expires_at <= datetime.utcnow()
        ).all()
        
        cleanup_count = 0
        for permission in expired_permissions:
            permission.is_active = False
            permission.revoked_at = datetime.utcnow()
            permission.revocation_reason = "Expired"
            cleanup_count += 1
        
        self.db.commit()
        
        logger.info(f"Cleaned up {cleanup_count} expired permissions")
        
        return cleanup_count
    
    def extend_permission(
        self,
        permission_id: UUID,
        additional_days: int,
        extended_by_user_id: UUID
    ) -> bool:
        """
        Extend the duration of a permission.
        
        Args:
            permission_id: ID of the permission to extend
            additional_days: Number of additional days
            extended_by_user_id: User who extended the permission
            
        Returns:
            True if permission was extended, False if not found
        """
        logger.info(f"Extending permission {permission_id} by {additional_days} days")
        
        permission = self.db.query(DataAccessPermission).filter(
            DataAccessPermission.id == permission_id,
            DataAccessPermission.is_active == True
        ).first()
        
        if not permission:
            logger.warning(f"Permission {permission_id} not found or not active")
            return False
        
        # Calculate new expiry date
        if permission.expires_at:
            new_expiry = permission.expires_at + timedelta(days=additional_days)
        else:
            new_expiry = datetime.utcnow() + timedelta(days=additional_days)
        
        permission.expires_at = new_expiry
        permission.last_modified_at = datetime.utcnow()
        permission.last_modified_by_user_id = extended_by_user_id
        
        self.db.commit()
        
        logger.info(f"Permission {permission_id} extended until {new_expiry}")
        
        return True
    
    def get_permission_summary(
        self,
        company_id: UUID
    ) -> Dict[str, Any]:
        """
        Get a summary of permissions for a company.
        
        Args:
            company_id: Company ID
            
        Returns:
            Summary dictionary
        """
        from sqlalchemy import func
        
        # Count active permissions by category
        category_counts = self.db.query(
            DataAccessPermission.data_category,
            func.count(DataAccessPermission.id).label('count')
        ).filter(
            DataAccessPermission.grantee_company_id == company_id,
            DataAccessPermission.is_active == True
        ).group_by(DataAccessPermission.data_category).all()
        
        # Count permissions expiring soon (within 7 days)
        expiring_soon = self.db.query(func.count(DataAccessPermission.id)).filter(
            DataAccessPermission.grantee_company_id == company_id,
            DataAccessPermission.is_active == True,
            DataAccessPermission.expires_at <= datetime.utcnow() + timedelta(days=7),
            DataAccessPermission.expires_at > datetime.utcnow()
        ).scalar()
        
        return {
            "total_active_permissions": sum(count for _, count in category_counts),
            "permissions_by_category": {category: count for category, count in category_counts},
            "permissions_expiring_soon": expiring_soon,
            "last_updated": datetime.utcnow()
        }
