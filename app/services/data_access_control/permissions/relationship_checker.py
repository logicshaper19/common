"""
Business relationship checking for data access control.
"""
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.business_relationship import BusinessRelationship
from app.models.purchase_order import PurchaseOrder
from app.core.logging import get_logger

logger = get_logger(__name__)


class RelationshipChecker:
    """Checks business relationships for access control decisions."""
    
    def __init__(self, db: Session):
        """Initialize relationship checker."""
        self.db = db
    
    def check_relationship(
        self, 
        requesting_company_id: UUID, 
        target_company_id: UUID
    ) -> Dict[str, Any]:
        """
        Check business relationship between two companies.
        
        Args:
            requesting_company_id: Company requesting access
            target_company_id: Company that owns the data
            
        Returns:
            Dictionary with relationship information
        """
        logger.debug(
            f"Checking relationship between {requesting_company_id} and {target_company_id}"
        )
        
        # Check for direct business relationship
        direct_relationship = self._find_direct_relationship(
            requesting_company_id, 
            target_company_id
        )
        
        if direct_relationship:
            return {
                "exists": True,
                "type": "direct",
                "relationship_type": direct_relationship.relationship_type,
                "strength": self._calculate_relationship_strength(direct_relationship),
                "established_date": direct_relationship.created_at,
                "status": direct_relationship.status,
                "relationship_id": direct_relationship.id
            }
        
        # Check for indirect relationship through purchase orders
        indirect_relationship = self._find_indirect_relationship(
            requesting_company_id,
            target_company_id
        )
        
        if indirect_relationship:
            return {
                "exists": True,
                "type": "indirect",
                "relationship_type": "supply_chain",
                "strength": indirect_relationship["strength"],
                "transaction_count": indirect_relationship["transaction_count"],
                "last_transaction": indirect_relationship["last_transaction"],
                "relationship_path": indirect_relationship["path"]
            }
        
        return {
            "exists": False,
            "type": None,
            "strength": 0.0,
            "reason": "No business relationship found"
        }
    
    def _find_direct_relationship(
        self, 
        company1_id: UUID, 
        company2_id: UUID
    ) -> Optional[BusinessRelationship]:
        """Find direct business relationship between companies."""
        
        relationship = self.db.query(BusinessRelationship).filter(
            or_(
                and_(
                    BusinessRelationship.company_id == company1_id,
                    BusinessRelationship.related_company_id == company2_id
                ),
                and_(
                    BusinessRelationship.company_id == company2_id,
                    BusinessRelationship.related_company_id == company1_id
                )
            ),
            BusinessRelationship.is_active == True
        ).first()
        
        return relationship
    
    def _find_indirect_relationship(
        self, 
        requesting_company_id: UUID, 
        target_company_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Find indirect relationship through supply chain connections."""
        
        # Check if companies are connected through purchase orders
        # This is a simplified version - in practice, you might want to do graph traversal
        
        # Check if requesting company is a supplier to target company
        supplier_connection = self._check_supplier_relationship(
            requesting_company_id, 
            target_company_id
        )
        
        if supplier_connection:
            return supplier_connection
        
        # Check if requesting company is a buyer from target company
        buyer_connection = self._check_buyer_relationship(
            requesting_company_id,
            target_company_id
        )
        
        if buyer_connection:
            return buyer_connection
        
        # Check for multi-hop connections (simplified to 2-hop)
        multi_hop_connection = self._check_multi_hop_relationship(
            requesting_company_id,
            target_company_id
        )
        
        return multi_hop_connection
    
    def _check_supplier_relationship(
        self, 
        supplier_id: UUID, 
        buyer_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Check if supplier has relationship with buyer through POs."""
        
        # Count purchase orders where supplier_id is the supplier and buyer_id is the buyer
        po_query = self.db.query(
            func.count(PurchaseOrder.id).label('transaction_count'),
            func.max(PurchaseOrder.created_at).label('last_transaction')
        ).filter(
            PurchaseOrder.seller_company_id == supplier_id,
            PurchaseOrder.buyer_company_id == buyer_id
        )
        
        result = po_query.first()
        
        if result.transaction_count > 0:
            # Calculate strength based on transaction frequency and recency
            strength = self._calculate_supply_chain_strength(
                result.transaction_count,
                result.last_transaction
            )
            
            return {
                "strength": strength,
                "transaction_count": result.transaction_count,
                "last_transaction": result.last_transaction,
                "path": [supplier_id, buyer_id],
                "relationship_nature": "supplier_to_buyer"
            }
        
        return None
    
    def _check_buyer_relationship(
        self, 
        buyer_id: UUID, 
        supplier_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Check if buyer has relationship with supplier through POs."""
        
        # This is essentially the reverse of supplier relationship
        return self._check_supplier_relationship(supplier_id, buyer_id)
    
    def _check_multi_hop_relationship(
        self, 
        company1_id: UUID, 
        company2_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Check for multi-hop relationships (simplified to 2-hop)."""
        
        # Find common companies that both companies have relationships with
        # This is a simplified version - real implementation would use graph algorithms
        
        # Companies that company1 has relationships with
        company1_connections = self.db.query(PurchaseOrder.buyer_company_id).filter(
            PurchaseOrder.seller_company_id == company1_id
        ).union(
            self.db.query(PurchaseOrder.seller_company_id).filter(
                PurchaseOrder.buyer_company_id == company1_id
            )
        ).distinct().subquery()
        
        # Check if any of these companies also have relationships with company2
        common_connections = self.db.query(
            func.count().label('connection_count')
        ).filter(
            or_(
                and_(
                    PurchaseOrder.seller_company_id == company2_id,
                    PurchaseOrder.buyer_company_id.in_(company1_connections)
                ),
                and_(
                    PurchaseOrder.buyer_company_id == company2_id,
                    PurchaseOrder.seller_company_id.in_(company1_connections)
                )
            )
        ).first()
        
        if common_connections.connection_count > 0:
            # Weak indirect relationship
            return {
                "strength": 0.3,  # Lower strength for indirect relationships
                "transaction_count": 0,  # No direct transactions
                "last_transaction": None,
                "path": [company1_id, "intermediate", company2_id],
                "relationship_nature": "indirect_supply_chain"
            }
        
        return None
    
    def _calculate_relationship_strength(self, relationship: BusinessRelationship) -> float:
        """Calculate strength of a direct business relationship."""
        
        base_strength = 0.5
        
        # Adjust based on relationship type
        if relationship.relationship_type == "strategic_partner":
            base_strength = 0.9
        elif relationship.relationship_type == "preferred_supplier":
            base_strength = 0.8
        elif relationship.relationship_type == "regular_supplier":
            base_strength = 0.6
        elif relationship.relationship_type == "occasional_supplier":
            base_strength = 0.4
        
        # Adjust based on relationship age (older = stronger)
        if relationship.created_at:
            from datetime import datetime, timedelta
            age_days = (datetime.utcnow() - relationship.created_at).days
            age_bonus = min(0.2, age_days / 365 * 0.1)  # Up to 0.2 bonus for 2+ years
            base_strength += age_bonus
        
        # Adjust based on verification status
        if hasattr(relationship, 'is_verified') and relationship.is_verified:
            base_strength += 0.1
        
        return min(1.0, base_strength)
    
    def _calculate_supply_chain_strength(
        self, 
        transaction_count: int, 
        last_transaction_date
    ) -> float:
        """Calculate strength based on supply chain transaction history."""
        
        base_strength = 0.3  # Base strength for any transaction history
        
        # Adjust based on transaction frequency
        if transaction_count >= 10:
            base_strength += 0.3
        elif transaction_count >= 5:
            base_strength += 0.2
        elif transaction_count >= 2:
            base_strength += 0.1
        
        # Adjust based on recency
        if last_transaction_date:
            from datetime import datetime, timedelta
            days_since_last = (datetime.utcnow() - last_transaction_date).days
            
            if days_since_last <= 30:
                base_strength += 0.2  # Very recent
            elif days_since_last <= 90:
                base_strength += 0.1  # Recent
            elif days_since_last <= 365:
                base_strength += 0.05  # Within a year
            # No bonus for older transactions
        
        return min(1.0, base_strength)
    
    def get_relationship_permissions(
        self, 
        requesting_company_id: UUID, 
        target_company_id: UUID
    ) -> Dict[str, Any]:
        """Get specific permissions based on relationship type."""
        
        relationship_info = self.check_relationship(requesting_company_id, target_company_id)
        
        if not relationship_info["exists"]:
            return {
                "can_access_basic_info": False,
                "can_access_financial_data": False,
                "can_access_operational_data": False,
                "can_access_strategic_data": False,
                "max_sensitivity_level": None
            }
        
        # Define permissions based on relationship strength
        strength = relationship_info["strength"]
        
        permissions = {
            "can_access_basic_info": strength >= 0.2,
            "can_access_financial_data": strength >= 0.6,
            "can_access_operational_data": strength >= 0.4,
            "can_access_strategic_data": strength >= 0.8,
        }
        
        # Determine maximum sensitivity level
        if strength >= 0.8:
            permissions["max_sensitivity_level"] = "CONFIDENTIAL"
        elif strength >= 0.6:
            permissions["max_sensitivity_level"] = "INTERNAL"
        elif strength >= 0.4:
            permissions["max_sensitivity_level"] = "LIMITED"
        else:
            permissions["max_sensitivity_level"] = "PUBLIC"
        
        return permissions
