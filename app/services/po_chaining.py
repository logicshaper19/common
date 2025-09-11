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
        Confirm a PO and optionally create child POs based on fulfillment method
        
        Args:
            po_id: ID of the PO being confirmed
            confirmation_data: Confirmation details including fulfillment_method
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
        
        # Check fulfillment method
        fulfillment_method = confirmation_data.get('fulfillment_method', 'create_child_pos')
        child_pos = []
        
        if fulfillment_method == 'create_child_pos' and self._should_create_child_pos(po):
            # Create child POs to suppliers
            child_pos = self._create_child_pos(po, confirming_user_id)
        elif fulfillment_method == 'fulfill_from_stock':
            # Fulfill from existing inventory - no child POs needed
            child_pos = []
            # Mark as fulfilled from stock
            po.fulfillment_status = 'fulfilled'
            po.fulfillment_percentage = 100
            po.fulfillment_notes = "Fulfilled from existing stock"
            self.db.commit()
        elif fulfillment_method == 'partial_stock_partial_po':
            # Partial fulfillment from stock + partial child POs
            stock_quantity = confirmation_data.get('stock_quantity', 0)
            po_quantity = confirmation_data.get('po_quantity', 0)
            
            if po_quantity > 0:
                # Create child POs for the portion that needs to be purchased
                child_pos = self._create_child_pos(po, confirming_user_id, po_quantity)
            
            # Update fulfillment status
            po.fulfillment_status = 'partial'
            po.fulfillment_percentage = int((stock_quantity / po.quantity) * 100)
            po.fulfillment_notes = f"Partial fulfillment: {stock_quantity} from stock, {po_quantity} from new POs"
            self.db.commit()
        
        # Update fulfillment status of parent PO
        if child_pos:
            self._update_parent_fulfillment_status(po, child_pos)
        
        return {
            "po_confirmed": confirmation_result,
            "child_pos_created": child_pos,
            "fulfillment_status": po.fulfillment_status,
            "fulfillment_percentage": po.fulfillment_percentage,
            "fulfillment_method": fulfillment_method
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
    
    def _create_child_pos(self, parent_po: PurchaseOrder, confirming_user_id: UUID, quantity: float = None) -> List[Dict[str, Any]]:
        """
        Create child POs for the confirming company's suppliers
        
        Supports flexible flows and Trader fan-out:
        - Single supplier: Brand → Processor → Originator
        - Multiple suppliers: Trader → [Processor1, Processor2] → [Originator1, Originator2]
        - Direct flows: Brand → Originator
        """
        child_pos = []
        
        # Get suppliers for the confirming company
        suppliers = self._get_suppliers_for_company(parent_po.seller_company)
        
        if not suppliers:
            return child_pos
        
        # Handle Trader fan-out: create multiple child POs
        if parent_po.seller_company.company_type == 'trader' and len(suppliers) > 1:
            # Split quantity among multiple suppliers
            total_quantity = quantity or (parent_po.confirmed_quantity or parent_po.quantity)
            quantity_per_supplier = total_quantity / len(suppliers)
            
            for i, supplier_company in enumerate(suppliers):
                child_po_data = self._create_child_po_data(
                    parent_po, supplier_company, quantity_per_supplier, i
                )
                child_po = self._create_child_po_from_data(child_po_data)
                child_pos.append({
                    "po_id": str(child_po.id),
                    "po_number": child_po.po_number,
                    "supplier": supplier_company.name,
                    "quantity": str(child_po.quantity),
                    "supply_chain_level": child_po.supply_chain_level
                })
        else:
            # Single supplier: create one child PO
            supplier_company = suppliers[0]
            child_po_data = self._create_child_po_data(
                parent_po, supplier_company, 
                quantity or (parent_po.confirmed_quantity or parent_po.quantity), 0
            )
            child_po = self._create_child_po_from_data(child_po_data)
            child_pos.append({
                "po_id": str(child_po.id),
                "po_number": child_po.po_number,
                "supplier": supplier_company.name,
                "quantity": str(child_po.quantity),
                "supply_chain_level": child_po.supply_chain_level
            })
        
        return child_pos
    
    def _get_suppliers_for_company(self, company: Company) -> List[Company]:
        """
        Get all suppliers for a company
        
        In production, this would query business_relationships table
        """
        # For now, return all companies that could be suppliers
        # In production, you'd query actual business relationships
        potential_suppliers = self.db.query(Company).filter(
            Company.id != company.id
        ).all()
        
        return potential_suppliers
    
    def _create_child_po_data(
        self, 
        parent_po: PurchaseOrder, 
        supplier_company: Company, 
        quantity: float, 
        supplier_index: int
    ) -> Dict[str, Any]:
        """Create child PO data for a specific supplier"""
        return {
            "po_number": self._generate_child_po_number(parent_po, supplier_index),
            "buyer_company_id": str(parent_po.seller_company_id),
            "seller_company_id": str(supplier_company.id),
            "product_id": str(parent_po.product_id),
            "quantity": quantity,
            "unit_price": parent_po.confirmed_unit_price or parent_po.unit_price,
            "total_amount": quantity * (parent_po.confirmed_unit_price or parent_po.unit_price),
            "unit": parent_po.unit,
            "delivery_date": parent_po.confirmed_delivery_date or parent_po.delivery_date,
            "delivery_location": parent_po.confirmed_delivery_location or parent_po.delivery_location,
            "parent_po_id": str(parent_po.id),
            "supply_chain_level": self._calculate_supply_chain_level(parent_po, supplier_company),
            "is_chain_initiated": False,
            "status": "pending",
            "notes": f"Created to fulfill parent PO {parent_po.po_number}"
        }
    
    def _get_supplier_for_company(self, company: Company) -> Optional[Company]:
        """
        Get a supplier company for the given company
        
        This supports ALL possible supply chain flows:
        - Brand → Trader → Processor → Originator
        - Brand → Processor → Originator  
        - Brand → Originator (direct)
        - Trader → Processor → Originator
        - Trader → Originator (direct)
        - Processor → Originator
        """
        # Query actual business relationships
        # For now, find any company that could be a supplier
        # In production, you'd query business_relationships table
        
        # Get all companies that could be suppliers (not the same company)
        potential_suppliers = self.db.query(Company).filter(
            Company.id != company.id
        ).all()
        
        if not potential_suppliers:
            return None
        
        # For now, return the first available supplier
        # In production, you'd implement proper supplier selection logic:
        # 1. Check business_relationships table
        # 2. Check supplier preferences
        # 3. Check company capabilities
        # 4. Handle multiple suppliers for fan-out
        
        return potential_suppliers[0]
    
    def _calculate_supply_chain_level(self, parent_po: PurchaseOrder, supplier_company: Company) -> int:
        """
        Calculate supply chain level based on supplier company type
        
        This supports flexible flows:
        - Brand (1) → Trader (2) → Processor (3) → Originator (4)
        - Brand (1) → Processor (2) → Originator (3)
        - Brand (1) → Originator (2)
        - Trader (2) → Processor (3) → Originator (4)
        - Trader (2) → Originator (3)
        - Processor (3) → Originator (4)
        """
        # Get the parent company type
        parent_company_type = parent_po.buyer_company.company_type
        
        # Calculate level based on supplier type
        if supplier_company.company_type == 'originator':
            # Originator is always the final level (highest number)
            return 4
        elif supplier_company.company_type == 'processor':
            # Processor is typically level 3, but could be 2 if coming from Brand
            if parent_company_type == 'brand':
                return 2  # Brand → Processor
            else:
                return 3  # Trader → Processor
        elif supplier_company.company_type == 'trader':
            # Trader is typically level 2, but could be 3 if coming from another Trader
            if parent_company_type == 'brand':
                return 2  # Brand → Trader
            else:
                return 3  # Trader → Trader
        else:
            # Default: increment by 1
            return parent_po.supply_chain_level + 1
    
    def _generate_child_po_number(self, parent_po: PurchaseOrder, supplier_index: int = 0) -> str:
        """Generate a PO number for a child PO"""
        base_number = parent_po.po_number
        
        if supplier_index > 0:
            # Multiple suppliers: add supplier index
            return f"{base_number}-S{supplier_index + 1}"
        else:
            # Single supplier: add suffix
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
