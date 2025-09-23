"""
Universal Access Control Service
Provides role-agnostic, component-agnostic access control that works across all features.

This service ensures that fixes and features benefit ALL roles and components,
not just specific use cases.
"""
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from enum import Enum
from dataclasses import dataclass

from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder
from app.models.amendment import Amendment
from app.core.logging import get_logger

logger = get_logger(__name__)


class AccessLevel(str, Enum):
    """Universal access levels that work across all components"""
    NONE = "none"           # No access
    READ = "read"           # Can view data
    WRITE = "write"         # Can modify data
    ADMIN = "admin"         # Full administrative access
    AUDIT = "audit"         # Audit/oversight access


class RelationshipType(str, Enum):
    """Types of business relationships"""
    SELF = "self"                           # Same company
    BUYER_SELLER = "buyer_seller"           # Direct trading relationship
    SUPPLY_CHAIN_PARTNER = "supply_chain"   # Connected through supply chain
    AUDITOR_AUDITEE = "auditor_auditee"     # Audit relationship
    REGULATOR_REGULATED = "regulator_regulated"  # Regulatory relationship
    TRADER_CLIENT = "trader_client"         # Trader relationship
    BUSINESS_PARTNER = "business_partner"   # General business relationship


@dataclass
class AccessDecision:
    """Result of an access control decision"""
    allowed: bool
    access_level: AccessLevel
    relationship_type: RelationshipType
    reason: str
    restrictions: List[str] = None
    
    def __post_init__(self):
        if self.restrictions is None:
            self.restrictions = []


class UniversalAccessControl:
    """
    Universal access control that works across all components and roles.
    
    This service provides consistent access control logic that can be used by:
    - Amendment system
    - Traceability system  
    - Farm management
    - Purchase order management
    - Any other component that needs access control
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================================
    # UNIVERSAL ACCESS CONTROL METHODS
    # ============================================================================
    
    def can_access_purchase_order(
        self, 
        user: User, 
        purchase_order: PurchaseOrder,
        required_level: AccessLevel = AccessLevel.READ
    ) -> AccessDecision:
        """
        Universal purchase order access control.
        Works for any role, any company type, any component.
        """
        # Self access - always allowed
        if user.company_id in [purchase_order.buyer_company_id, purchase_order.seller_company_id]:
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.ADMIN if user.role in ["admin", "super_admin"] else AccessLevel.WRITE,
                relationship_type=RelationshipType.SELF,
                reason="Direct party to the purchase order"
            )
        
        # Admin access
        if user.role in ["admin", "super_admin"]:
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.ADMIN,
                relationship_type=RelationshipType.SELF,
                reason="Platform administrator"
            )
        
        # Auditor access
        if user.role == "auditor":
            if self._is_auditor_for_po(user.company_id, purchase_order):
                return AccessDecision(
                    allowed=True,
                    access_level=AccessLevel.AUDIT,
                    relationship_type=RelationshipType.AUDITOR_AUDITEE,
                    reason="Assigned auditor for this purchase order"
                )
        
        # Regulator access
        if user.role == "regulator":
            if self._is_regulator_for_po(user.company_id, purchase_order):
                return AccessDecision(
                    allowed=True,
                    access_level=AccessLevel.AUDIT,
                    relationship_type=RelationshipType.REGULATOR_REGULATED,
                    reason="Regulatory oversight of this purchase order"
                )
        
        # Supply chain partner access
        if self._is_supply_chain_partner(user.company_id, purchase_order):
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.READ,
                relationship_type=RelationshipType.SUPPLY_CHAIN_PARTNER,
                reason="Connected through supply chain",
                restrictions=["read_only"]
            )
        
        # Trader access
        if user.company.company_type == "trader":
            if self._is_trader_connected_to_po(user.company_id, purchase_order):
                return AccessDecision(
                    allowed=True,
                    access_level=AccessLevel.READ,
                    relationship_type=RelationshipType.TRADER_CLIENT,
                    reason="Trader relationship with parties",
                    restrictions=["read_only"]
                )
        
        return AccessDecision(
            allowed=False,
            access_level=AccessLevel.NONE,
            relationship_type=RelationshipType.SELF,
            reason="No relationship or permission found"
        )
    
    def can_access_amendment(
        self, 
        user: User, 
        amendment: Amendment,
        required_level: AccessLevel = AccessLevel.READ
    ) -> AccessDecision:
        """
        Universal amendment access control.
        Works for any role, any company type.
        """
        # Get the purchase order for this amendment
        po = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.id == amendment.purchase_order_id
        ).first()
        
        if not po:
            return AccessDecision(
                allowed=False,
                access_level=AccessLevel.NONE,
                relationship_type=RelationshipType.SELF,
                reason="Purchase order not found"
            )
        
        # Use universal PO access control
        po_access = self.can_access_purchase_order(user, po, required_level)
        
        if not po_access.allowed:
            return po_access
        
        # Additional amendment-specific logic
        if amendment.proposed_by_company_id == user.company_id:
            # Proposer can always access their own amendments
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.WRITE,
                relationship_type=RelationshipType.SELF,
                reason="Amendment proposer"
            )
        
        if amendment.requires_approval_from_company_id == user.company_id:
            # Approver can access amendments they need to approve
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.WRITE,
                relationship_type=RelationshipType.BUYER_SELLER,
                reason="Amendment approver"
            )
        
        # Return the PO access decision (with potential restrictions)
        return po_access
    
    def can_access_traceability(
        self, 
        user: User, 
        purchase_order: PurchaseOrder,
        required_level: AccessLevel = AccessLevel.READ
    ) -> AccessDecision:
        """
        Universal traceability access control.
        Works for any role, any company type.
        """
        # Use universal PO access control
        po_access = self.can_access_purchase_order(user, purchase_order, required_level)
        
        if not po_access.allowed:
            return po_access
        
        # Traceability-specific restrictions
        restrictions = po_access.restrictions.copy() if po_access.restrictions else []
        
        # Some roles might have read-only traceability access
        if po_access.relationship_type in [
            RelationshipType.SUPPLY_CHAIN_PARTNER,
            RelationshipType.TRADER_CLIENT
        ]:
            restrictions.append("traceability_read_only")
        
        return AccessDecision(
            allowed=True,
            access_level=po_access.access_level,
            relationship_type=po_access.relationship_type,
            reason=po_access.reason,
            restrictions=restrictions
        )
    
    def can_access_farm_data(
        self, 
        user: User, 
        farm_company_id: UUID,
        required_level: AccessLevel = AccessLevel.READ
    ) -> AccessDecision:
        """
        Universal farm data access control.
        Works for any role, any company type.
        """
        # Self access
        if user.company_id == farm_company_id:
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.ADMIN if user.role in ["admin", "super_admin"] else AccessLevel.WRITE,
                relationship_type=RelationshipType.SELF,
                reason="Own farm data"
            )
        
        # Admin access
        if user.role in ["admin", "super_admin"]:
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.ADMIN,
                relationship_type=RelationshipType.SELF,
                reason="Platform administrator"
            )
        
        # Check if there's a business relationship
        if self._has_business_relationship(user.company_id, farm_company_id):
            return AccessDecision(
                allowed=True,
                access_level=AccessLevel.READ,
                relationship_type=RelationshipType.BUSINESS_PARTNER,
                reason="Business relationship exists",
                restrictions=["read_only"]
            )
        
        # Auditor access
        if user.role == "auditor":
            if self._is_auditor_for_company(user.company_id, farm_company_id):
                return AccessDecision(
                    allowed=True,
                    access_level=AccessLevel.AUDIT,
                    relationship_type=RelationshipType.AUDITOR_AUDITEE,
                    reason="Assigned auditor"
                )
        
        return AccessDecision(
            allowed=False,
            access_level=AccessLevel.NONE,
            relationship_type=RelationshipType.SELF,
            reason="No relationship or permission found"
        )
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _is_auditor_for_po(self, auditor_company_id: UUID, purchase_order: PurchaseOrder) -> bool:
        """Check if auditor is assigned to audit this purchase order"""
        # TODO: Implement when auditor assignment system is added
        # For now, return False
        return False
    
    def _is_regulator_for_po(self, regulator_company_id: UUID, purchase_order: PurchaseOrder) -> bool:
        """Check if regulator has jurisdiction over this purchase order"""
        # TODO: Implement when regulatory system is added
        # For now, return False
        return False
    
    def _is_supply_chain_partner(self, company_id: UUID, purchase_order: PurchaseOrder) -> bool:
        """Check if company is connected through supply chain"""
        # Check if company is in the supply chain path
        # This would involve checking batch relationships, linked POs, etc.
        # For now, return False
        return False
    
    def _is_trader_connected_to_po(self, trader_company_id: UUID, purchase_order: PurchaseOrder) -> bool:
        """Check if trader has relationship with PO parties"""
        # Check if trader has relationships with buyer or seller
        # For now, return False
        return False
    
    def _has_business_relationship(self, company_id_1: UUID, company_id_2: UUID) -> bool:
        """Check if two companies have a business relationship"""
        # Check for any business relationship (POs, contracts, etc.)
        # For now, return False
        return False
    
    def _is_auditor_for_company(self, auditor_company_id: UUID, target_company_id: UUID) -> bool:
        """Check if auditor is assigned to audit target company"""
        # TODO: Implement when auditor assignment system is added
        # For now, return False
        return False
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_access_summary(self, user: User, resource_type: str, resource_id: UUID) -> Dict[str, Any]:
        """
        Get a comprehensive access summary for any resource.
        Useful for debugging and audit trails.
        """
        # This would be implemented based on the specific resource type
        # For now, return a basic structure
        return {
            "user_id": str(user.id),
            "company_id": str(user.company_id),
            "user_role": user.role,
            "company_type": user.company.company_type,
            "resource_type": resource_type,
            "resource_id": str(resource_id),
            "access_granted": False,
            "reason": "Not implemented yet"
        }
    
    def log_access_attempt(
        self, 
        user: User, 
        resource_type: str, 
        resource_id: UUID, 
        decision: AccessDecision
    ) -> None:
        """Log access attempts for audit trails"""
        logger.info(
            f"Access attempt: {resource_type}:{resource_id}",
            user_id=str(user.id),
            company_id=str(user.company_id),
            user_role=user.role,
            company_type=user.company.company_type,
            allowed=decision.allowed,
            access_level=decision.access_level,
            relationship_type=decision.relationship_type,
            reason=decision.reason,
            restrictions=decision.restrictions
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def check_po_access(
    db: Session, 
    user: User, 
    po_id: UUID, 
    required_level: AccessLevel = AccessLevel.READ
) -> AccessDecision:
    """Convenience function for checking PO access"""
    access_control = UniversalAccessControl(db)
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        return AccessDecision(
            allowed=False,
            access_level=AccessLevel.NONE,
            relationship_type=RelationshipType.SELF,
            reason="Purchase order not found"
        )
    
    return access_control.can_access_purchase_order(user, po, required_level)


def check_amendment_access(
    db: Session, 
    user: User, 
    amendment_id: UUID, 
    required_level: AccessLevel = AccessLevel.READ
) -> AccessDecision:
    """Convenience function for checking amendment access"""
    access_control = UniversalAccessControl(db)
    amendment = db.query(Amendment).filter(Amendment.id == amendment_id).first()
    
    if not amendment:
        return AccessDecision(
            allowed=False,
            access_level=AccessLevel.NONE,
            relationship_type=RelationshipType.SELF,
            reason="Amendment not found"
        )
    
    return access_control.can_access_amendment(user, amendment, required_level)


def check_traceability_access(
    db: Session, 
    user: User, 
    po_id: UUID, 
    required_level: AccessLevel = AccessLevel.READ
) -> AccessDecision:
    """Convenience function for checking traceability access"""
    access_control = UniversalAccessControl(db)
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    
    if not po:
        return AccessDecision(
            allowed=False,
            access_level=AccessLevel.NONE,
            relationship_type=RelationshipType.SELF,
            reason="Purchase order not found"
        )
    
    return access_control.can_access_traceability(user, po, required_level)
