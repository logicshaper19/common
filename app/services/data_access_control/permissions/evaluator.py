"""
Permission evaluation logic for data access control.
"""
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.data_access import (
    DataAccessPermission,
    DataCategory,
    AccessType,
    DataSensitivityLevel,
    AccessResult
)
from ..domain.models import AccessRequest, AccessDecision, PermissionContext
from ..domain.enums import AccessDecisionType, FilteringStrategy
from .relationship_checker import RelationshipChecker
from app.core.logging import get_logger

logger = get_logger(__name__)


class PermissionEvaluator:
    """Evaluates access permissions based on business rules."""
    
    def __init__(self, db: Session):
        """Initialize permission evaluator."""
        self.db = db
        self.relationship_checker = RelationshipChecker(db)
    
    def evaluate_access_request(
        self, 
        access_request: AccessRequest
    ) -> Tuple[AccessDecision, Optional[DataAccessPermission]]:
        """
        Evaluate an access request and return a decision.
        
        Args:
            access_request: The access request to evaluate
            
        Returns:
            Tuple of (access_decision, existing_permission)
        """
        logger.debug(
            f"Evaluating access request: user={access_request.requesting_user_id}, "
            f"company={access_request.requesting_company_id}, "
            f"target={access_request.target_company_id}, "
            f"category={access_request.data_category}"
        )
        
        # Build permission context
        context = self._build_permission_context(access_request)
        
        # Check for existing permission
        existing_permission = self._find_active_permission(access_request)
        
        # Evaluate access based on different factors
        decision = self._evaluate_access_factors(access_request, context, existing_permission)
        
        logger.info(
            f"Access decision: {decision.decision_type} for user {access_request.requesting_user_id}"
        )
        
        return decision, existing_permission
    
    def _build_permission_context(self, access_request: AccessRequest) -> PermissionContext:
        """Build context for permission evaluation."""
        context = PermissionContext()
        
        # Check business relationship if cross-company access
        if access_request.is_cross_company_access:
            relationship_info = self.relationship_checker.check_relationship(
                access_request.requesting_company_id,
                access_request.target_company_id
            )
            
            context.business_relationship_exists = relationship_info["exists"]
            context.relationship_type = relationship_info.get("type")
            context.relationship_strength = relationship_info.get("strength", 0.0)
        else:
            # Same company access
            context.business_relationship_exists = True
            context.relationship_type = "same_company"
            context.relationship_strength = 1.0
        
        # Add user context (simplified - would query user details)
        context.user_role = "standard"  # Would be fetched from user record
        
        # Add risk assessment (simplified)
        context.risk_score = self._calculate_risk_score(access_request, context)
        
        return context
    
    def _find_active_permission(self, access_request: AccessRequest) -> Optional[DataAccessPermission]:
        """Find existing active permission for the request."""
        query = self.db.query(DataAccessPermission).filter(
            DataAccessPermission.requesting_user_id == access_request.requesting_user_id,
            DataAccessPermission.requesting_company_id == access_request.requesting_company_id,
            DataAccessPermission.is_active == True
        )
        
        # Add target company filter
        if access_request.target_company_id:
            query = query.filter(
                DataAccessPermission.target_company_id == access_request.target_company_id
            )
        else:
            query = query.filter(DataAccessPermission.target_company_id.is_(None))
        
        # Check if permission covers the requested data
        permissions = query.all()
        
        for permission in permissions:
            if self._permission_covers_request(permission, access_request):
                return permission
        
        return None
    
    def _permission_covers_request(
        self, 
        permission: DataAccessPermission, 
        access_request: AccessRequest
    ) -> bool:
        """Check if a permission covers the access request."""
        # Check data category
        if permission.data_category != access_request.data_category:
            return False
        
        # Check access type
        if permission.access_type != access_request.access_type:
            return False
        
        # Check entity specificity
        if permission.entity_id and access_request.entity_id:
            if permission.entity_id != access_request.entity_id:
                return False
        
        # Check sensitivity level
        if (access_request.sensitivity_level and 
            permission.max_sensitivity_level and
            access_request.sensitivity_level.value > permission.max_sensitivity_level.value):
            return False
        
        return True
    
    def _evaluate_access_factors(
        self,
        access_request: AccessRequest,
        context: PermissionContext,
        existing_permission: Optional[DataAccessPermission]
    ) -> AccessDecision:
        """Evaluate access based on multiple factors."""
        
        # If existing permission exists and is valid
        if existing_permission:
            return AccessDecision(
                decision_type=AccessDecisionType.ALLOW,
                access_result=AccessResult.GRANTED,
                permission_id=existing_permission.id,
                decision_factors=["existing_permission"]
            )
        
        # Same company access - generally allowed with potential filtering
        if not access_request.is_cross_company_access:
            return self._evaluate_same_company_access(access_request, context)
        
        # Cross-company access - requires business relationship
        return self._evaluate_cross_company_access(access_request, context)
    
    def _evaluate_same_company_access(
        self,
        access_request: AccessRequest,
        context: PermissionContext
    ) -> AccessDecision:
        """Evaluate access within the same company."""
        
        # Check for sensitive data
        if access_request.is_sensitive_data:
            # Require additional checks for sensitive data
            if context.user_role in ["admin", "manager"]:
                return AccessDecision(
                    decision_type=AccessDecisionType.ALLOW,
                    access_result=AccessResult.GRANTED,
                    decision_factors=["same_company", "authorized_role"]
                )
            else:
                return AccessDecision(
                    decision_type=AccessDecisionType.CONDITIONAL,
                    access_result=AccessResult.GRANTED_WITH_CONDITIONS,
                    decision_factors=["same_company", "sensitive_data"],
                    filtering_strategy=FilteringStrategy.FIELD_LEVEL,
                    conditions=["Sensitive fields filtered"]
                )
        
        # Non-sensitive data - allow
        return AccessDecision(
            decision_type=AccessDecisionType.ALLOW,
            access_result=AccessResult.GRANTED,
            decision_factors=["same_company", "non_sensitive_data"]
        )
    
    def _evaluate_cross_company_access(
        self,
        access_request: AccessRequest,
        context: PermissionContext
    ) -> AccessDecision:
        """Evaluate cross-company access."""
        
        # No business relationship - deny
        if not context.business_relationship_exists:
            return AccessDecision(
                decision_type=AccessDecisionType.DENY,
                access_result=AccessResult.DENIED,
                denial_reason="No business relationship exists",
                decision_factors=["no_relationship"]
            )
        
        # Check relationship strength and data sensitivity
        if access_request.is_sensitive_data:
            if context.relationship_strength < 0.7:
                return AccessDecision(
                    decision_type=AccessDecisionType.DENY,
                    access_result=AccessResult.DENIED,
                    denial_reason="Insufficient relationship strength for sensitive data",
                    decision_factors=["weak_relationship", "sensitive_data"]
                )
        
        # Check risk score
        if context.risk_score > 0.8:
            return AccessDecision(
                decision_type=AccessDecisionType.REQUIRE_APPROVAL,
                access_result=AccessResult.PENDING_APPROVAL,
                decision_factors=["high_risk_score"],
                conditions=["Requires manual approval due to high risk"]
            )
        
        # Determine filtering strategy
        filtering_strategy = self._determine_filtering_strategy(access_request, context)
        
        if filtering_strategy == FilteringStrategy.NO_FILTERING:
            return AccessDecision(
                decision_type=AccessDecisionType.ALLOW,
                access_result=AccessResult.GRANTED,
                decision_factors=["business_relationship", "low_risk"],
                filtering_strategy=filtering_strategy
            )
        else:
            return AccessDecision(
                decision_type=AccessDecisionType.CONDITIONAL,
                access_result=AccessResult.GRANTED_WITH_CONDITIONS,
                decision_factors=["business_relationship", "data_filtering_required"],
                filtering_strategy=filtering_strategy,
                conditions=["Data filtering applied based on sensitivity"]
            )
    
    def _determine_filtering_strategy(
        self,
        access_request: AccessRequest,
        context: PermissionContext
    ) -> FilteringStrategy:
        """Determine appropriate filtering strategy."""
        
        # High sensitivity data always requires filtering for cross-company access
        if access_request.is_sensitive_data:
            return FilteringStrategy.FIELD_LEVEL
        
        # Weak relationships require filtering
        if context.relationship_strength < 0.5:
            return FilteringStrategy.FIELD_LEVEL
        
        # Analytical queries might only need aggregation
        if access_request.access_type == AccessType.READ and "analytics" in access_request.purpose:
            return FilteringStrategy.AGGREGATION_ONLY
        
        return FilteringStrategy.NO_FILTERING
    
    def _calculate_risk_score(
        self,
        access_request: AccessRequest,
        context: PermissionContext
    ) -> float:
        """Calculate risk score for the access request."""
        risk_score = 0.0
        
        # Base risk for cross-company access
        if access_request.is_cross_company_access:
            risk_score += 0.3
        
        # Risk based on data sensitivity
        if access_request.sensitivity_level == DataSensitivityLevel.RESTRICTED:
            risk_score += 0.4
        elif access_request.sensitivity_level == DataSensitivityLevel.CONFIDENTIAL:
            risk_score += 0.2
        
        # Risk based on relationship strength
        if context.business_relationship_exists:
            risk_score -= context.relationship_strength * 0.2
        else:
            risk_score += 0.3
        
        # Risk based on access type
        if access_request.access_type in [AccessType.WRITE, AccessType.DELETE]:
            risk_score += 0.2
        
        return min(1.0, max(0.0, risk_score))
