"""
Data access control service for the Common supply chain platform.
"""
from typing import Optional, Dict, Any, List, Union, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import Request
import re
import json

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.data_access import (
    DataAccessPermission,
    AccessAttempt,
    DataClassification,
    DataAccessPolicy,
    DataSensitivityLevel,
    DataCategory,
    AccessType,
    AccessResult
)
from app.models.business_relationship import BusinessRelationship
from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.services.audit_logger import AuditLogger
from app.models.audit_event import AuditEventType, AuditEventSeverity

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
        self.db = db
        self.audit_logger = AuditLogger(db)
    
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
            # Log the access attempt
            access_attempt = self._log_access_attempt(
                requesting_user_id=requesting_user_id,
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                entity_type=entity_type,
                entity_id=entity_id,
                request=request
            )
            
            # Check if accessing own company's data
            if target_company_id is None or target_company_id == requesting_company_id:
                self._update_access_attempt(access_attempt, AccessResult.GRANTED, None)
                return AccessResult.GRANTED, None, None
            
            # Check for explicit permission
            permission = self._find_active_permission(
                grantee_company_id=requesting_company_id,
                grantor_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                sensitivity_level=sensitivity_level
            )
            
            if permission:
                # Check if permission covers the specific entity
                if self._permission_covers_entity(permission, entity_type, entity_id):
                    self._update_access_attempt(access_attempt, AccessResult.GRANTED, permission.id)
                    return AccessResult.GRANTED, permission, None
            
            # Check for business relationship-based access
            relationship_access = self._check_relationship_access(
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                sensitivity_level=sensitivity_level
            )
            
            if relationship_access[0] != AccessResult.DENIED:
                self._update_access_attempt(access_attempt, relationship_access[0], None)
                return relationship_access
            
            # Access denied
            denial_reason = "No permission found for cross-company data access"
            self._update_access_attempt(access_attempt, AccessResult.DENIED, None, denial_reason)
            
            # Log unauthorized access attempt
            self._log_unauthorized_access(
                requesting_user_id=requesting_user_id,
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                entity_type=entity_type,
                entity_id=entity_id,
                denial_reason=denial_reason
            )
            
            return AccessResult.DENIED, None, denial_reason
            
        except Exception as e:
            logger.error(
                "Error checking access permission",
                requesting_user_id=str(requesting_user_id),
                requesting_company_id=str(requesting_company_id),
                target_company_id=str(target_company_id) if target_company_id else None,
                data_category=data_category.value,
                error=str(e)
            )
            return AccessResult.DENIED, None, f"Access check failed: {str(e)}"
    
    def filter_sensitive_data(
        self,
        data: Dict[str, Any],
        requesting_company_id: UUID,
        target_company_id: UUID,
        data_category: DataCategory,
        entity_type: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Filter sensitive data based on permissions and data classification.
        
        Args:
            data: Original data dictionary
            requesting_company_id: Company requesting the data
            target_company_id: Company that owns the data
            data_category: Category of data
            entity_type: Type of entity
            
        Returns:
            Tuple of (filtered_data, filtered_fields)
        """
        try:
            if requesting_company_id == target_company_id:
                # No filtering for own company data
                return data, []
            
            filtered_data = {}
            filtered_fields = []
            
            # Get data classifications for this entity type
            classifications = self._get_data_classifications(entity_type)
            
            for field_name, field_value in data.items():
                # Determine field sensitivity level
                sensitivity_level = self._classify_field_sensitivity(
                    field_name, field_value, entity_type, classifications
                )
                
                # Check if user has access to this sensitivity level
                has_access = self._check_field_access(
                    requesting_company_id=requesting_company_id,
                    target_company_id=target_company_id,
                    data_category=data_category,
                    sensitivity_level=sensitivity_level
                )
                
                if has_access:
                    filtered_data[field_name] = field_value
                else:
                    filtered_fields.append(field_name)
                    # Add placeholder for filtered commercial data
                    if sensitivity_level == DataSensitivityLevel.COMMERCIAL:
                        filtered_data[field_name] = "[COMMERCIAL_DATA_FILTERED]"
                    elif sensitivity_level == DataSensitivityLevel.CONFIDENTIAL:
                        filtered_data[field_name] = "[CONFIDENTIAL_DATA_FILTERED]"
                    elif sensitivity_level == DataSensitivityLevel.RESTRICTED:
                        filtered_data[field_name] = "[RESTRICTED_DATA_FILTERED]"
            
            logger.debug(
                "Data filtered for cross-company access",
                requesting_company_id=str(requesting_company_id),
                target_company_id=str(target_company_id),
                entity_type=entity_type,
                total_fields=len(data),
                filtered_fields_count=len(filtered_fields)
            )
            
            return filtered_data, filtered_fields
            
        except Exception as e:
            logger.error(
                "Error filtering sensitive data",
                requesting_company_id=str(requesting_company_id),
                target_company_id=str(target_company_id),
                entity_type=entity_type,
                error=str(e)
            )
            # Return empty data on error for security
            return {}, list(data.keys())
    
    def grant_permission(
        self,
        grantor_company_id: UUID,
        grantee_company_id: UUID,
        data_category: DataCategory,
        sensitivity_level: DataSensitivityLevel,
        access_types: List[AccessType],
        granted_by_user_id: UUID,
        justification: str,
        expires_at: Optional[datetime] = None,
        entity_filters: Optional[Dict[str, Any]] = None,
        field_restrictions: Optional[Dict[str, Any]] = None
    ) -> DataAccessPermission:
        """
        Grant data access permission between companies.
        
        Args:
            grantor_company_id: Company granting the permission
            grantee_company_id: Company receiving the permission
            data_category: Category of data
            sensitivity_level: Sensitivity level of data
            access_types: Types of access granted
            granted_by_user_id: User granting the permission
            justification: Reason for granting permission
            expires_at: When the permission expires
            entity_filters: Filters for specific entities
            field_restrictions: Restrictions on specific fields
            
        Returns:
            Created DataAccessPermission object
        """
        try:
            # Find business relationship
            relationship = self.db.query(BusinessRelationship).filter(
                or_(
                    and_(
                        BusinessRelationship.buyer_company_id == grantor_company_id,
                        BusinessRelationship.seller_company_id == grantee_company_id
                    ),
                    and_(
                        BusinessRelationship.buyer_company_id == grantee_company_id,
                        BusinessRelationship.seller_company_id == grantor_company_id
                    )
                )
            ).filter(
                BusinessRelationship.status == "active"
            ).first()
            
            if not relationship:
                raise ValueError("No active business relationship found between companies")
            
            # Create permission
            permission = DataAccessPermission(
                id=uuid4(),
                grantor_company_id=grantor_company_id,
                grantee_company_id=grantee_company_id,
                business_relationship_id=relationship.id,
                data_category=data_category,
                sensitivity_level=sensitivity_level,
                access_types=[access_type.value for access_type in access_types],
                entity_filters=entity_filters,
                field_restrictions=field_restrictions,
                granted_by_user_id=granted_by_user_id,
                expires_at=expires_at,
                justification=justification,
                is_active=True,
                auto_granted=False
            )
            
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            
            # Log permission grant
            self.audit_logger.log_event(
                event_type=AuditEventType.PERMISSION_GRANTED,
                entity_type="data_access_permission",
                entity_id=permission.id,
                action="grant",
                description=f"Data access permission granted for {data_category.value} data",
                actor_user_id=granted_by_user_id,
                actor_company_id=grantor_company_id,
                new_values={
                    "grantee_company_id": str(grantee_company_id),
                    "data_category": data_category.value,
                    "sensitivity_level": sensitivity_level.value,
                    "access_types": [at.value for at in access_types],
                    "justification": justification
                },
                business_context={
                    "permission_type": "explicit",
                    "relationship_id": str(relationship.id)
                }
            )
            
            logger.info(
                "Data access permission granted",
                permission_id=str(permission.id),
                grantor_company_id=str(grantor_company_id),
                grantee_company_id=str(grantee_company_id),
                data_category=data_category.value,
                sensitivity_level=sensitivity_level.value
            )
            
            return permission
            
        except Exception as e:
            logger.error(
                "Failed to grant data access permission",
                grantor_company_id=str(grantor_company_id),
                grantee_company_id=str(grantee_company_id),
                data_category=data_category.value,
                error=str(e)
            )
            raise
    
    def revoke_permission(
        self,
        permission_id: UUID,
        revoked_by_user_id: UUID,
        revoked_by_company_id: UUID,
        reason: str
    ) -> bool:
        """
        Revoke a data access permission.
        
        Args:
            permission_id: Permission to revoke
            revoked_by_user_id: User revoking the permission
            revoked_by_company_id: Company revoking the permission
            reason: Reason for revocation
            
        Returns:
            True if successful
        """
        try:
            permission = self.db.query(DataAccessPermission).filter(
                DataAccessPermission.id == permission_id
            ).first()
            
            if not permission:
                return False
            
            # Check if user has authority to revoke
            if (revoked_by_company_id != permission.grantor_company_id and
                revoked_by_company_id != permission.grantee_company_id):
                raise ValueError("Only grantor or grantee can revoke permission")
            
            # Revoke permission
            permission.is_active = False
            permission.revoked_at = datetime.utcnow()
            permission.revoked_by_user_id = revoked_by_user_id
            
            self.db.commit()
            
            # Log permission revocation
            self.audit_logger.log_event(
                event_type=AuditEventType.PERMISSION_REVOKED,
                entity_type="data_access_permission",
                entity_id=permission.id,
                action="revoke",
                description=f"Data access permission revoked: {reason}",
                actor_user_id=revoked_by_user_id,
                actor_company_id=revoked_by_company_id,
                old_values={"is_active": True},
                new_values={"is_active": False, "revocation_reason": reason}
            )
            
            logger.info(
                "Data access permission revoked",
                permission_id=str(permission_id),
                revoked_by_user_id=str(revoked_by_user_id),
                revoked_by_company_id=str(revoked_by_company_id),
                reason=reason
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to revoke data access permission",
                permission_id=str(permission_id),
                revoked_by_user_id=str(revoked_by_user_id),
                error=str(e)
            )
            return False

    def _log_access_attempt(
        self,
        requesting_user_id: UUID,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID],
        data_category: DataCategory,
        access_type: AccessType,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        request: Optional[Request] = None
    ) -> AccessAttempt:
        """Log an access attempt for security monitoring."""
        try:
            # Extract request context
            request_context = {}
            if request:
                request_context = {
                    'api_endpoint': str(request.url.path) if hasattr(request, 'url') else None,
                    'http_method': request.method if hasattr(request, 'method') else None,
                    'ip_address': request.client.host if hasattr(request, 'client') and request.client else None,
                    'user_agent': request.headers.get('user-agent') if hasattr(request, 'headers') else None,
                    'request_id': request.headers.get('x-request-id') if hasattr(request, 'headers') else None
                }

            access_attempt = AccessAttempt(
                id=uuid4(),
                requesting_user_id=requesting_user_id,
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=access_type,
                entity_type=entity_type,
                entity_id=entity_id,
                api_endpoint=request_context.get('api_endpoint'),
                http_method=request_context.get('http_method'),
                request_id=request_context.get('request_id'),
                ip_address=request_context.get('ip_address'),
                user_agent=request_context.get('user_agent'),
                access_result=AccessResult.DENIED  # Default, will be updated
            )

            self.db.add(access_attempt)
            self.db.commit()
            self.db.refresh(access_attempt)

            return access_attempt

        except Exception as e:
            logger.error("Failed to log access attempt", error=str(e))
            # Return a dummy object to prevent breaking the main flow
            return AccessAttempt(id=uuid4())

    def _update_access_attempt(
        self,
        access_attempt: AccessAttempt,
        result: AccessResult,
        permission_id: Optional[UUID] = None,
        denial_reason: Optional[str] = None,
        filtered_fields: Optional[List[str]] = None
    ):
        """Update access attempt with result."""
        try:
            access_attempt.access_result = result
            access_attempt.permission_id = permission_id
            access_attempt.denial_reason = denial_reason
            if filtered_fields:
                access_attempt.filtered_fields = filtered_fields

            self.db.commit()

        except Exception as e:
            logger.error("Failed to update access attempt", error=str(e))

    def _find_active_permission(
        self,
        grantee_company_id: UUID,
        grantor_company_id: UUID,
        data_category: DataCategory,
        access_type: AccessType,
        sensitivity_level: Optional[DataSensitivityLevel] = None
    ) -> Optional[DataAccessPermission]:
        """Find active permission for the given criteria."""
        try:
            query = self.db.query(DataAccessPermission).filter(
                and_(
                    DataAccessPermission.grantee_company_id == grantee_company_id,
                    DataAccessPermission.grantor_company_id == grantor_company_id,
                    DataAccessPermission.data_category == data_category,
                    DataAccessPermission.is_active == True,
                    or_(
                        DataAccessPermission.expires_at.is_(None),
                        DataAccessPermission.expires_at > datetime.utcnow()
                    )
                )
            )

            permissions = query.all()

            # Filter by access type and sensitivity level
            for permission in permissions:
                access_types = permission.access_types or []
                if access_type.value in access_types:
                    # Check sensitivity level compatibility
                    if sensitivity_level is None or self._sensitivity_level_compatible(
                        permission.sensitivity_level, sensitivity_level
                    ):
                        return permission

            return None

        except Exception as e:
            logger.error("Error finding active permission", error=str(e))
            return None

    def _permission_covers_entity(
        self,
        permission: DataAccessPermission,
        entity_type: str,
        entity_id: Optional[UUID]
    ) -> bool:
        """Check if permission covers the specific entity."""
        try:
            if not permission.entity_filters:
                return True  # No filters means covers all entities

            entity_filters = permission.entity_filters

            # Check entity type filter
            if 'entity_types' in entity_filters:
                if entity_type not in entity_filters['entity_types']:
                    return False

            # Check specific entity ID filter
            if entity_id and 'entity_ids' in entity_filters:
                if str(entity_id) not in entity_filters['entity_ids']:
                    return False

            return True

        except Exception as e:
            logger.error("Error checking entity coverage", error=str(e))
            return False

    def _check_relationship_access(
        self,
        requesting_company_id: UUID,
        target_company_id: UUID,
        data_category: DataCategory,
        access_type: AccessType,
        sensitivity_level: Optional[DataSensitivityLevel] = None
    ) -> Tuple[AccessResult, Optional[DataAccessPermission], Optional[str]]:
        """Check access based on business relationship default permissions."""
        try:
            # Find active business relationship
            relationship = self.db.query(BusinessRelationship).filter(
                or_(
                    and_(
                        BusinessRelationship.buyer_company_id == requesting_company_id,
                        BusinessRelationship.seller_company_id == target_company_id
                    ),
                    and_(
                        BusinessRelationship.buyer_company_id == target_company_id,
                        BusinessRelationship.seller_company_id == requesting_company_id
                    )
                )
            ).filter(
                BusinessRelationship.status == "active"
            ).first()

            if not relationship:
                return AccessResult.DENIED, None, "No active business relationship"

            # Check relationship permissions
            permissions = relationship.data_sharing_permissions or {}

            # Map data categories to relationship permission keys
            permission_key = self._map_category_to_permission_key(data_category, sensitivity_level)

            if permission_key and permissions.get(permission_key, False):
                # Check if access type is allowed (read is generally allowed, write may be restricted)
                if access_type in [AccessType.READ]:
                    return AccessResult.GRANTED, None, None
                elif access_type in [AccessType.WRITE, AccessType.DELETE]:
                    # More restrictive for write operations
                    if sensitivity_level in [DataSensitivityLevel.OPERATIONAL, DataSensitivityLevel.PUBLIC]:
                        return AccessResult.GRANTED, None, None

            return AccessResult.DENIED, None, f"Relationship does not permit {permission_key} access"

        except Exception as e:
            logger.error("Error checking relationship access", error=str(e))
            return AccessResult.DENIED, None, f"Error checking relationship access: {str(e)}"

    def _map_category_to_permission_key(
        self,
        data_category: DataCategory,
        sensitivity_level: Optional[DataSensitivityLevel]
    ) -> Optional[str]:
        """Map data category and sensitivity to relationship permission key."""
        if sensitivity_level == DataSensitivityLevel.COMMERCIAL:
            return "commercial_data"
        elif data_category == DataCategory.TRACEABILITY:
            return "traceability_data"
        elif data_category == DataCategory.QUALITY_DATA:
            return "quality_data"
        elif data_category == DataCategory.LOCATION_DATA:
            return "location_data"
        elif sensitivity_level == DataSensitivityLevel.OPERATIONAL:
            return "operational_data"
        else:
            return "operational_data"  # Default to operational

    def _get_data_classifications(self, entity_type: str) -> List[DataClassification]:
        """Get data classification rules for entity type."""
        try:
            return self.db.query(DataClassification).filter(
                and_(
                    DataClassification.entity_type == entity_type,
                    DataClassification.is_active == True
                )
            ).order_by(DataClassification.priority.desc()).all()

        except Exception as e:
            logger.error("Error getting data classifications", error=str(e))
            return []

    def _classify_field_sensitivity(
        self,
        field_name: str,
        field_value: Any,
        entity_type: str,
        classifications: List[DataClassification]
    ) -> DataSensitivityLevel:
        """Classify field sensitivity level based on rules."""
        try:
            # Apply classification rules in priority order
            for classification in classifications:
                if classification.field_pattern:
                    if re.match(classification.field_pattern, field_name, re.IGNORECASE):
                        return classification.sensitivity_level

            # Default classification based on field name patterns
            field_lower = field_name.lower()

            if any(term in field_lower for term in ['price', 'cost', 'margin', 'profit', 'revenue', 'payment', 'amount']):
                return DataSensitivityLevel.COMMERCIAL
            elif any(term in field_lower for term in ['coordinate', 'latitude', 'longitude', 'location', 'address']):
                return DataSensitivityLevel.CONFIDENTIAL
            elif any(term in field_lower for term in ['quantity', 'date', 'status', 'unit']):
                return DataSensitivityLevel.OPERATIONAL
            else:
                return DataSensitivityLevel.PUBLIC

        except Exception as e:
            logger.error("Error classifying field sensitivity", error=str(e))
            return DataSensitivityLevel.CONFIDENTIAL  # Default to most restrictive

    def _check_field_access(
        self,
        requesting_company_id: UUID,
        target_company_id: UUID,
        data_category: DataCategory,
        sensitivity_level: DataSensitivityLevel
    ) -> bool:
        """Check if requesting company has access to field with given sensitivity."""
        try:
            # Always allow access to public data
            if sensitivity_level == DataSensitivityLevel.PUBLIC:
                return True

            # Check for explicit permission
            permission = self._find_active_permission(
                grantee_company_id=requesting_company_id,
                grantor_company_id=target_company_id,
                data_category=data_category,
                access_type=AccessType.READ,
                sensitivity_level=sensitivity_level
            )

            if permission:
                return True

            # Check relationship-based access
            relationship_access = self._check_relationship_access(
                requesting_company_id=requesting_company_id,
                target_company_id=target_company_id,
                data_category=data_category,
                access_type=AccessType.READ,
                sensitivity_level=sensitivity_level
            )

            return relationship_access[0] == AccessResult.GRANTED

        except Exception as e:
            logger.error("Error checking field access", error=str(e))
            return False

    def _sensitivity_level_compatible(
        self,
        permission_level: DataSensitivityLevel,
        requested_level: DataSensitivityLevel
    ) -> bool:
        """Check if permission level covers requested sensitivity level."""
        # Define sensitivity hierarchy (higher includes lower)
        hierarchy = {
            DataSensitivityLevel.PUBLIC: 1,
            DataSensitivityLevel.OPERATIONAL: 2,
            DataSensitivityLevel.COMMERCIAL: 3,
            DataSensitivityLevel.CONFIDENTIAL: 4,
            DataSensitivityLevel.RESTRICTED: 5
        }

        return hierarchy.get(permission_level, 0) >= hierarchy.get(requested_level, 0)

    def _log_unauthorized_access(
        self,
        requesting_user_id: UUID,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID],
        data_category: DataCategory,
        entity_type: str,
        entity_id: Optional[UUID],
        denial_reason: str
    ):
        """Log unauthorized access attempt for security monitoring."""
        try:
            self.audit_logger.log_event(
                event_type=AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                entity_type=entity_type,
                entity_id=entity_id or uuid4(),
                action="unauthorized_access",
                description=f"Unauthorized access attempt to {data_category.value} data",
                actor_user_id=requesting_user_id,
                actor_company_id=requesting_company_id,
                severity=AuditEventSeverity.HIGH,
                metadata={
                    "target_company_id": str(target_company_id) if target_company_id else None,
                    "data_category": data_category.value,
                    "entity_type": entity_type,
                    "denial_reason": denial_reason
                },
                business_context={
                    "security_event": True,
                    "access_violation": True
                }
            )

        except Exception as e:
            logger.error("Failed to log unauthorized access", error=str(e))
