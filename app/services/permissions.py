"""
Permission Service for Common Supply Chain Platform
Handles role-based access control using dual-layer architecture:
- Layer 1: Company Type (what the company IS in supply chain)
- Layer 2: User Role (what the user can DO within their company)
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from enum import Enum

from app.models.user import User
from app.models.company import Company
from app.models.purchase_order import PurchaseOrder


class CompanyType(str, Enum):
    """Company types in the supply chain"""
    BRAND = "brand"           # Issues POs, monitors compliance
    PROCESSOR = "processor"   # Confirms POs, processes goods
    ORIGINATOR = "originator" # Reports farm data, confirms POs
    TRADER = "trader"         # Links POs, facilitates transactions
    AUDITOR = "auditor"       # Certifies compliance
    REGULATOR = "regulator"   # Oversees compliance


class UserRole(str, Enum):
    """User roles within their company"""
    ADMIN = "admin"                           # Manage team, configure company
    SUPPLY_CHAIN_MANAGER = "supply_chain_manager"  # Create/manage POs
    PRODUCTION_MANAGER = "production_manager"      # Confirm POs, manage production
    VIEWER = "viewer"                         # Read-only access
    AUDITOR = "auditor"                       # Cross-company read access


class PermissionService:
    """Central service for role-based access control"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================================
    # COMPANY ACCESS PERMISSIONS
    # ============================================================================
    
    def can_user_access_company(self, user: User, target_company_id: UUID) -> bool:
        """
        Can this user view data from another company?
        - Users can always see their own company's data
        - Auditors can see companies they are assigned to audit
        - Regulators can see companies within their jurisdiction
        """
        if user.company_id == target_company_id:
            return True  # Always allow access to your own company
        
        if user.role == UserRole.AUDITOR:
            return self._is_auditor_for_company(user.company_id, target_company_id)
        
        if user.role == UserRole.REGULATOR:
            return self._is_regulator_for_company(user.company_id, target_company_id)
        
        # Traders might need access to their suppliers/customers
        if user.company.company_type == CompanyType.TRADER:
            return self._is_trader_connected_to_company(user.company_id, target_company_id)
        
        return False
    
    def can_user_manage_company(self, user: User, target_company_id: UUID) -> bool:
        """Can this user manage (edit) another company's data?"""
        # Only admins can manage their own company
        return (user.company_id == target_company_id and 
                user.role == UserRole.ADMIN)
    
    # ============================================================================
    # PURCHASE ORDER PERMISSIONS
    # ============================================================================
    
    def can_user_create_po(self, user: User) -> bool:
        """
        Can the user create a purchase order?
        - Brands, Traders, and Processors issue POs DOWNSTREAM
        - Originators are the source - they don't create POs, they only receive them
        """
        return (user.role == UserRole.SUPPLY_CHAIN_MANAGER and 
                user.company.company_type in [CompanyType.BRAND, CompanyType.TRADER, CompanyType.PROCESSOR])
    
    def can_user_confirm_po(self, user: User) -> bool:
        """
        Can the user confirm a purchase order?
        - Processors and Originators confirm POs received from UPSTREAM
        """
        return (user.role == UserRole.PRODUCTION_MANAGER and 
                user.company.company_type in [CompanyType.PROCESSOR, CompanyType.ORIGINATOR])
    
    def can_user_view_po(self, user: User, po: PurchaseOrder) -> bool:
        """
        Can the user view a specific purchase order?
        - Users can view POs where their company is buyer or seller
        - Auditors can view POs for companies they audit
        """
        # Direct participants can always view
        if (user.company_id == po.buyer_company_id or 
            user.company_id == po.seller_company_id):
            return True
        
        # Auditors can view POs for companies they audit
        if user.role == UserRole.AUDITOR:
            return (self._is_auditor_for_company(user.company_id, po.buyer_company_id) or
                    self._is_auditor_for_company(user.company_id, po.seller_company_id))
        
        return False
    
    def can_user_edit_po(self, user: User, po: PurchaseOrder) -> bool:
        """
        Can the user edit a specific purchase order?
        - Supply chain managers can edit POs where their company is the buyer
        - Production managers can edit POs where their company is the seller
        """
        if user.role == UserRole.SUPPLY_CHAIN_MANAGER:
            return user.company_id == po.buyer_company_id
        
        if user.role == UserRole.PRODUCTION_MANAGER:
            return user.company_id == po.seller_company_id
        
        return False
    
    # ============================================================================
    # USER MANAGEMENT PERMISSIONS
    # ============================================================================
    
    def can_user_invite_team_members(self, user: User) -> bool:
        """Can the user invite new team members to their company?"""
        return user.role == UserRole.ADMIN
    
    def can_user_manage_team_members(self, user: User, target_user_id: UUID) -> bool:
        """Can the user manage (edit/delete) a specific team member?"""
        if user.role != UserRole.ADMIN:
            return False
        
        # Get target user
        target_user = self.db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            return False
        
        # Can only manage users in the same company
        return target_user.company_id == user.company_id
    
    # ============================================================================
    # DASHBOARD PERMISSIONS
    # ============================================================================
    
    def get_user_dashboard_config(self, user: User) -> Dict[str, Any]:
        """
        Get dashboard configuration based on user's role and company type
        Returns which sections/features the user should see
        """
        config = {
            "can_create_po": self.can_user_create_po(user),
            "can_confirm_po": self.can_user_confirm_po(user),
            "can_manage_team": self.can_user_invite_team_members(user),
            "can_view_analytics": True,  # Most users can view analytics
            "can_manage_settings": user.role == UserRole.ADMIN,
            "can_audit_companies": user.role == UserRole.AUDITOR,
            "can_regulate_platform": user.role == UserRole.REGULATOR,
            "dashboard_type": self.get_dashboard_type(user),
        }

        # Company-type specific features
        if user.company.company_type == CompanyType.TRADER:
            config["can_manage_trader_chain"] = True
            config["can_view_margin_analysis"] = True

        if user.company.company_type == CompanyType.ORIGINATOR:
            config["can_report_farm_data"] = True
            config["can_manage_certifications"] = True

        return config

    def get_dashboard_type(self, user: User) -> str:
        """
        Determine which dashboard type to show based on user's company type
        Returns dashboard type string for routing decisions
        """
        # Map company types to dashboard types
        company_type_mapping = {
            CompanyType.BRAND: "brand",
            CompanyType.PROCESSOR: "processor",
            CompanyType.ORIGINATOR: "originator",
            CompanyType.TRADER: "trader",
            CompanyType.AUDITOR: "auditor",
            CompanyType.REGULATOR: "regulator"
        }

        # Special handling for platform admin roles
        if user.role in ["super_admin", "support"]:
            return "platform_admin"

        # Return dashboard type based on company type
        return company_type_mapping.get(user.company.company_type, "default")
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    def _is_auditor_for_company(self, auditor_company_id: UUID, target_company_id: UUID) -> bool:
        """Check if an auditor company is assigned to audit a target company"""
        # TODO: Implement when we add auditor assignment system
        # For now, return False
        return False
    
    def _is_regulator_for_company(self, regulator_company_id: UUID, target_company_id: UUID) -> bool:
        """Check if a regulator has jurisdiction over a target company"""
        # TODO: Implement when we add regulatory jurisdiction system
        # For now, return False
        return False
    
    def _is_trader_connected_to_company(self, trader_company_id: UUID, target_company_id: UUID) -> bool:
        """Check if a trader has business relationship with a target company"""
        # TODO: Implement when we add trader relationship system
        # For now, return False
        return False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_permission_service(db: Session) -> PermissionService:
    """Get a PermissionService instance"""
    return PermissionService(db)


def check_permission(user: User, permission_func, *args, **kwargs) -> bool:
    """
    Convenience function to check a permission
    Usage: check_permission(user, permission_service.can_user_create_po)
    """
    # This would need to be called with a db session in practice
    # For now, this is a placeholder for the pattern
    pass
