"""
PO Chaining Service for commercial traceability
Handles automatic creation of child POs when confirming parent POs
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.schemas.purchase_order import PurchaseOrderCreate
from app.services.purchase_order import PurchaseOrderService
from app.core.logging import get_logger

logger = get_logger(__name__)


class POChainingService:
    """Service for managing PO chaining and automatic child PO creation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.po_service = PurchaseOrderService(db)
    
    def confirm_po_and_create_children(
        self, 
        po_id: UUID, 
        confirmation_data: Dict[str, Any],
        confirming_user_id: UUID
    ) -> Dict[str, Any]:
        """
        Confirm a PO and automatically create child POs if needed
        
        Args:
            po_id: ID of the PO being confirmed
            confirmation_data: Confirmation details
            confirming_user_id: ID of user confirming the PO
            
        Returns:
            Dict with confirmation result and created child POs
        """
        # Get the PO being confirmed
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"PO {po_id} not found")
        
        # Confirm the PO
        confirmation_result = self._confirm_po(po, confirmation_data, confirming_user_id)
        
        # Check if we need to create child POs
        child_pos = []
        if self._should_create_child_pos(po):
            child_pos = self._create_child_pos(po, confirming_user_id)
        
        # Update fulfillment status of parent PO
        if child_pos:
            self._update_parent_fulfillment_status(po, child_pos)
        
        return {
            "po_confirmed": confirmation_result,
            "child_pos_created": child_pos,
            "fulfillment_status": po.fulfillment_status,
            "fulfillment_percentage": po.fulfillment_percentage
        }
    
    def _confirm_po(
        self, 
        po: PurchaseOrder, 
        confirmation_data: Dict[str, Any],
        confirming_user_id: UUID
    ) -> Dict[str, Any]:
        """Confirm a single PO"""
        # Update PO with confirmation data
        po.status = 'confirmed'
        po.confirmed_at = confirmation_data.get('confirmed_at')
        po.confirmed_quantity = confirmation_data.get('confirmed_quantity', po.quantity)
        po.confirmed_unit_price = confirmation_data.get('confirmed_unit_price', po.unit_price)
        po.confirmed_delivery_date = confirmation_data.get('confirmed_delivery_date', po.delivery_date)
        po.confirmed_delivery_location = confirmation_data.get('confirmed_delivery_location', po.delivery_location)
        po.seller_notes = confirmation_data.get('seller_notes', '')
        
        self.db.commit()
        
        return {
            "po_id": str(po.id),
            "status": po.status,
            "confirmed_at": po.confirmed_at.isoformat() if po.confirmed_at else None
        }
    
    def _should_create_child_pos(self, po: PurchaseOrder) -> bool:
        """
        Determine if we should create child POs after confirming this PO
        
        Rules:
        - Only create child POs if the confirming company has suppliers
        - Don't create child POs for Originators (they're the source)
        - Don't create child POs if this PO already has children
        """
        # Check if this PO already has children
        existing_children = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == po.id
        ).count()
        
        if existing_children > 0:
            return False
        
        # Check if the confirming company has suppliers
        confirming_company = po.seller_company
        if confirming_company.company_type == 'originator':
            return False  # Originators are the source
        
        # For now, assume all non-originator companies have suppliers
        # In a real system, you'd check actual supplier relationships
        return True
    
    def _create_child_pos(self, parent_po: PurchaseOrder, confirming_user_id: UUID) -> List[Dict[str, Any]]:
        """
        Create child POs for the confirming company's suppliers
        
        This is a simplified implementation. In reality, you'd:
        1. Look up the confirming company's suppliers
        2. Create POs to each supplier
        3. Handle quantity splitting for multiple suppliers
        """
        child_pos = []
        
        # For now, create a single child PO to a hypothetical supplier
        # In reality, you'd query the company's actual suppliers
        supplier_company = self._get_supplier_for_company(parent_po.seller_company)
        
        if supplier_company:
            child_po_data = {
                "po_number": self._generate_child_po_number(parent_po),
                "buyer_company_id": str(parent_po.seller_company_id),
                "seller_company_id": str(supplier_company.id),
                "product_id": str(parent_po.product_id),
                "quantity": parent_po.confirmed_quantity or parent_po.quantity,
                "unit_price": parent_po.confirmed_unit_price or parent_po.unit_price,
                "total_amount": (parent_po.confirmed_quantity or parent_po.quantity) * 
                              (parent_po.confirmed_unit_price or parent_po.unit_price),
                "unit": parent_po.unit,
                "delivery_date": parent_po.confirmed_delivery_date or parent_po.delivery_date,
                "delivery_location": parent_po.confirmed_delivery_location or parent_po.delivery_location,
                "parent_po_id": str(parent_po.id),
                "supply_chain_level": parent_po.supply_chain_level + 1,
                "is_chain_initiated": False,
                "status": "pending",
                "notes": f"Created to fulfill parent PO {parent_po.po_number}"
            }
            
            # Create the child PO
            child_po = self._create_child_po_from_data(child_po_data)
            child_pos.append({
                "po_id": str(child_po.id),
                "po_number": child_po.po_number,
                "supplier": supplier_company.name,
                "quantity": str(child_po.quantity),
                "supply_chain_level": child_po.supply_chain_level
            })
        
        return child_pos
    
    def _get_supplier_for_company(self, company: Company) -> Optional[Company]:
        """
        Get a supplier company for the given company
        
        This is a simplified implementation. In reality, you'd:
        1. Query business relationships
        2. Look up supplier preferences
        3. Handle multiple suppliers
        """
        # For now, return a hypothetical supplier based on company type
        if company.company_type == 'trader':
            # Trader's supplier is typically a processor
            return self.db.query(Company).filter(
                Company.company_type == 'processor'
            ).first()
        elif company.company_type == 'processor':
            # Processor's supplier is typically an originator
            return self.db.query(Company).filter(
                Company.company_type == 'originator'
            ).first()
        
        return None
    
    def _generate_child_po_number(self, parent_po: PurchaseOrder) -> str:
        """Generate a PO number for a child PO"""
        # Simple implementation: add suffix to parent PO number
        base_number = parent_po.po_number
        if '-' in base_number:
            parts = base_number.split('-')
            parts[-1] = str(int(parts[-1]) + 1)
            return '-'.join(parts)
        else:
            return f"{base_number}-CHILD"
    
    def _create_child_po_from_data(self, po_data: Dict[str, Any]) -> PurchaseOrder:
        """Create a child PO from the provided data"""
        child_po = PurchaseOrder(
            po_number=po_data["po_number"],
            buyer_company_id=po_data["buyer_company_id"],
            seller_company_id=po_data["seller_company_id"],
            product_id=po_data["product_id"],
            quantity=po_data["quantity"],
            unit_price=po_data["unit_price"],
            total_amount=po_data["total_amount"],
            unit=po_data["unit"],
            delivery_date=po_data["delivery_date"],
            delivery_location=po_data["delivery_location"],
            parent_po_id=po_data["parent_po_id"],
            supply_chain_level=po_data["supply_chain_level"],
            is_chain_initiated=po_data["is_chain_initiated"],
            status=po_data["status"],
            notes=po_data["notes"]
        )
        
        self.db.add(child_po)
        self.db.commit()
        
        return child_po
    
    def _update_parent_fulfillment_status(self, parent_po: PurchaseOrder, child_pos: List[Dict[str, Any]]):
        """Update the parent PO's fulfillment status based on child POs"""
        if not child_pos:
            parent_po.fulfillment_status = 'pending'
            parent_po.fulfillment_percentage = 0
        else:
            # For now, assume 100% fulfilled if child POs were created
            # In reality, you'd track actual confirmation status of child POs
            parent_po.fulfillment_status = 'fulfilled'
            parent_po.fulfillment_percentage = 100
        
        self.db.commit()
    
    def get_po_chain(self, po_id: UUID) -> Dict[str, Any]:
        """
        Get the complete chain for a PO (upstream and downstream)
        
        Returns:
            Dict with chain information
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"PO {po_id} not found")
        
        # Get upstream chain (parents)
        upstream_chain = self._get_upstream_chain(po)
        
        # Get downstream chain (children)
        downstream_chain = self._get_downstream_chain(po)
        
        return {
            "po": {
                "id": str(po.id),
                "po_number": po.po_number,
                "buyer": po.buyer_company.name,
                "seller": po.seller_company.name,
                "supply_chain_level": po.supply_chain_level,
                "is_chain_initiated": po.is_chain_initiated,
                "fulfillment_status": po.fulfillment_status,
                "fulfillment_percentage": po.fulfillment_percentage
            },
            "upstream_chain": upstream_chain,
            "downstream_chain": downstream_chain
        }
    
    def _get_upstream_chain(self, po: PurchaseOrder) -> List[Dict[str, Any]]:
        """Get the upstream chain (parents)"""
        chain = []
        current_po = po
        
        while current_po.parent_po_id:
            parent_po = self.db.query(PurchaseOrder).filter(
                PurchaseOrder.id == current_po.parent_po_id
            ).first()
            
            if parent_po:
                chain.append({
                    "id": str(parent_po.id),
                    "po_number": parent_po.po_number,
                    "buyer": parent_po.buyer_company.name,
                    "seller": parent_po.seller_company.name,
                    "supply_chain_level": parent_po.supply_chain_level,
                    "is_chain_initiated": parent_po.is_chain_initiated
                })
                current_po = parent_po
            else:
                break
        
        return chain
    
    def _get_downstream_chain(self, po: PurchaseOrder) -> List[Dict[str, Any]]:
        """Get the downstream chain (children)"""
        children = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.parent_po_id == po.id
        ).all()
        
        return [
            {
                "id": str(child.id),
                "po_number": child.po_number,
                "buyer": child.buyer_company.name,
                "seller": child.seller_company.name,
                "supply_chain_level": child.supply_chain_level,
                "is_chain_initiated": child.is_chain_initiated,
                "status": child.status
            }
            for child in children
        ]
