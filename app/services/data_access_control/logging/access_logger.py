"""
Access logging for data access control events.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.data_access import AccessAttempt, DataAccessPermission
from app.models.audit_event import AuditEventType, AuditEventSeverity
from app.services.audit_logger import AuditLogger
from ..domain.models import AccessRequest, AccessDecision, AccessAuditEntry
from app.core.logging import get_logger

logger = get_logger(__name__)


class AccessLogger:
    """Logs access control events for security monitoring."""
    
    def __init__(self, db: Session):
        """Initialize access logger."""
        self.db = db
        self.audit_logger = AuditLogger(db)
    
    def log_access_attempt(
        self,
        access_request: AccessRequest,
        access_decision: AccessDecision,
        existing_permission: Optional[DataAccessPermission] = None
    ) -> AccessAttempt:
        """
        Log an access attempt.
        
        Args:
            access_request: The access request
            access_decision: The access decision
            existing_permission: Existing permission if found
            
        Returns:
            Created access attempt record
        """
        # Create access attempt record
        access_attempt = AccessAttempt(
            id=uuid4(),
            requesting_user_id=access_request.requesting_user_id,
            requesting_company_id=access_request.requesting_company_id,
            target_company_id=access_request.target_company_id,
            data_category=access_request.data_category,
            access_type=access_request.access_type,
            entity_type=access_request.entity_type,
            entity_id=access_request.entity_id,
            access_result=access_decision.access_result,
            permission_id=existing_permission.id if existing_permission else None,
            denial_reason=access_decision.denial_reason,
            request_ip=access_request.request_ip,
            user_agent=access_request.user_agent,
            session_id=access_request.session_id,
            attempted_at=access_request.request_timestamp,
            decision_factors=access_decision.decision_factors
        )
        
        self.db.add(access_attempt)
        self.db.commit()
        self.db.refresh(access_attempt)
        
        # Log to audit system
        self._log_to_audit_system(access_request, access_decision)
        
        logger.info(
            f"Logged access attempt: {access_decision.access_result} for user "
            f"{access_request.requesting_user_id}"
        )
        
        return access_attempt
    
    def log_data_access(
        self,
        access_request: AccessRequest,
        access_decision: AccessDecision,
        data_size: int,
        filtered: bool = False
    ) -> None:
        """
        Log successful data access.
        
        Args:
            access_request: The access request
            access_decision: The access decision
            data_size: Size of data accessed
            filtered: Whether data was filtered
        """
        audit_entry = AccessAuditEntry(
            event_type="data_accessed",
            user_id=access_request.requesting_user_id,
            company_id=access_request.requesting_company_id,
            target_company_id=access_request.target_company_id,
            entity_type=access_request.entity_type,
            entity_id=access_request.entity_id,
            access_result=access_decision.access_result,
            request_ip=access_request.request_ip,
            user_agent=access_request.user_agent,
            session_id=access_request.session_id,
            metadata={
                'data_size': data_size,
                'filtered': filtered,
                'filtering_strategy': access_decision.filtering_strategy.value if access_decision.filtering_strategy else None,
                'decision_factors': access_decision.decision_factors
            }
        )
        
        # Log to audit system
        self.audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            severity=AuditEventSeverity.INFO,
            user_id=access_request.requesting_user_id,
            company_id=access_request.requesting_company_id,
            entity_type=access_request.entity_type,
            entity_id=access_request.entity_id,
            details={
                'target_company_id': str(access_request.target_company_id) if access_request.target_company_id else None,
                'data_category': access_request.data_category.value,
                'access_type': access_request.access_type.value,
                'data_size': data_size,
                'filtered': filtered
            }
        )
        
        logger.info(f"Logged data access for user {access_request.requesting_user_id}")
    
    def log_permission_granted(
        self,
        access_request: AccessRequest,
        permission: DataAccessPermission,
        granted_by_user_id: UUID
    ) -> None:
        """
        Log permission grant event.
        
        Args:
            access_request: The original access request
            permission: The granted permission
            granted_by_user_id: User who granted the permission
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.PERMISSION_GRANTED,
            severity=AuditEventSeverity.INFO,
            user_id=granted_by_user_id,
            company_id=access_request.requesting_company_id,
            entity_type=access_request.entity_type,
            entity_id=access_request.entity_id,
            details={
                'permission_id': str(permission.id),
                'requesting_user_id': str(access_request.requesting_user_id),
                'target_company_id': str(access_request.target_company_id) if access_request.target_company_id else None,
                'data_category': access_request.data_category.value,
                'access_type': access_request.access_type.value,
                'expires_at': permission.expires_at.isoformat() if permission.expires_at else None,
                'conditions': permission.conditions
            }
        )
        
        logger.info(f"Logged permission grant: {permission.id}")
    
    def log_permission_revoked(
        self,
        permission_id: UUID,
        revoked_by_user_id: UUID,
        reason: Optional[str] = None
    ) -> None:
        """
        Log permission revocation event.
        
        Args:
            permission_id: ID of revoked permission
            revoked_by_user_id: User who revoked the permission
            reason: Reason for revocation
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.PERMISSION_REVOKED,
            severity=AuditEventSeverity.WARNING,
            user_id=revoked_by_user_id,
            details={
                'permission_id': str(permission_id),
                'revocation_reason': reason
            }
        )
        
        logger.info(f"Logged permission revocation: {permission_id}")
    
    def log_error_attempt(
        self,
        requesting_user_id: UUID,
        requesting_company_id: UUID,
        target_company_id: Optional[UUID],
        error_message: str
    ) -> None:
        """
        Log error during access attempt.
        
        Args:
            requesting_user_id: User who made the request
            requesting_company_id: Company of the user
            target_company_id: Target company
            error_message: Error message
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.ACCESS_ERROR,
            severity=AuditEventSeverity.ERROR,
            user_id=requesting_user_id,
            company_id=requesting_company_id,
            details={
                'target_company_id': str(target_company_id) if target_company_id else None,
                'error_message': error_message
            }
        )
        
        logger.error(f"Logged access error for user {requesting_user_id}: {error_message}")
    
    def log_unauthorized_access(
        self,
        access_request: AccessRequest,
        denial_reason: str
    ) -> None:
        """
        Log unauthorized access attempt.
        
        Args:
            access_request: The access request
            denial_reason: Reason for denial
        """
        self.audit_logger.log_event(
            event_type=AuditEventType.UNAUTHORIZED_ACCESS,
            severity=AuditEventSeverity.WARNING,
            user_id=access_request.requesting_user_id,
            company_id=access_request.requesting_company_id,
            entity_type=access_request.entity_type,
            entity_id=access_request.entity_id,
            details={
                'target_company_id': str(access_request.target_company_id) if access_request.target_company_id else None,
                'data_category': access_request.data_category.value,
                'access_type': access_request.access_type.value,
                'denial_reason': denial_reason,
                'request_ip': access_request.request_ip,
                'user_agent': access_request.user_agent
            }
        )
        
        logger.warning(f"Logged unauthorized access attempt by user {access_request.requesting_user_id}")
    
    def get_access_summary(
        self,
        company_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get access summary for a company.
        
        Args:
            company_id: Company ID
            days: Number of days to include
            
        Returns:
            Access summary
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Count access attempts by result
        access_counts = self.db.query(
            AccessAttempt.access_result,
            func.count(AccessAttempt.id).label('count')
        ).filter(
            AccessAttempt.requesting_company_id == company_id,
            AccessAttempt.attempted_at >= start_date
        ).group_by(AccessAttempt.access_result).all()
        
        # Count unique users
        unique_users = self.db.query(
            func.count(func.distinct(AccessAttempt.requesting_user_id))
        ).filter(
            AccessAttempt.requesting_company_id == company_id,
            AccessAttempt.attempted_at >= start_date
        ).scalar()
        
        # Count cross-company accesses
        cross_company_accesses = self.db.query(
            func.count(AccessAttempt.id)
        ).filter(
            AccessAttempt.requesting_company_id == company_id,
            AccessAttempt.target_company_id.isnot(None),
            AccessAttempt.target_company_id != company_id,
            AccessAttempt.attempted_at >= start_date
        ).scalar()
        
        # Recent denied attempts
        recent_denied = self.db.query(AccessAttempt).filter(
            AccessAttempt.requesting_company_id == company_id,
            AccessAttempt.access_result == 'DENIED',
            AccessAttempt.attempted_at >= start_date
        ).order_by(AccessAttempt.attempted_at.desc()).limit(10).all()
        
        return {
            'period_days': days,
            'total_attempts': sum(count for _, count in access_counts),
            'access_counts_by_result': {result: count for result, count in access_counts},
            'unique_users': unique_users,
            'cross_company_accesses': cross_company_accesses,
            'recent_denied_attempts': [
                {
                    'attempted_at': attempt.attempted_at.isoformat(),
                    'user_id': str(attempt.requesting_user_id),
                    'data_category': attempt.data_category.value,
                    'denial_reason': attempt.denial_reason
                }
                for attempt in recent_denied
            ]
        }
    
    def _log_to_audit_system(
        self,
        access_request: AccessRequest,
        access_decision: AccessDecision
    ) -> None:
        """Log access attempt to audit system."""
        
        # Determine severity based on result
        if access_decision.access_result.value == 'DENIED':
            severity = AuditEventSeverity.WARNING
            event_type = AuditEventType.ACCESS_DENIED
        else:
            severity = AuditEventSeverity.INFO
            event_type = AuditEventType.ACCESS_GRANTED
        
        self.audit_logger.log_event(
            event_type=event_type,
            severity=severity,
            user_id=access_request.requesting_user_id,
            company_id=access_request.requesting_company_id,
            entity_type=access_request.entity_type,
            entity_id=access_request.entity_id,
            details={
                'target_company_id': str(access_request.target_company_id) if access_request.target_company_id else None,
                'data_category': access_request.data_category.value,
                'access_type': access_request.access_type.value,
                'access_result': access_decision.access_result.value,
                'decision_factors': access_decision.decision_factors,
                'denial_reason': access_decision.denial_reason,
                'request_ip': access_request.request_ip
            }
        )
