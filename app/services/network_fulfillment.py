"""
Network/DAG Fulfillment Service for Complex Supply Chains

This service handles the network structure where traders can fulfill POs using
existing commitments, inventory, or by creating new chains.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.purchase_order import PurchaseOrder
from app.models.batch import Batch
from app.models.po_fulfillment_allocation import POFulfillmentAllocation
from app.core.logging import get_logger

logger = get_logger(__name__)


class NetworkFulfillmentService:
    """Service for managing network/DAG fulfillment of Purchase Orders"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_fulfillment_options(self, po_id: UUID) -> Dict[str, Any]:
        """
        Get available fulfillment options for a PO
        
        Returns:
            Dict with available options for fulfilling the PO
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"PO {po_id} not found")
        
        # Get available commitment inventory (unfulfilled POs)
        commitment_inventory = self._get_commitment_inventory(po.seller_company_id, po.product_id)
        
        # Get available physical inventory (batches)
        physical_inventory = self._get_physical_inventory(po.seller_company_id, po.product_id)
        
        # Get available suppliers for new chains
        suppliers = self._get_available_suppliers(po.seller_company_id)
        
        return {
            "po": {
                "id": str(po.id),
                "po_number": po.po_number,
                "quantity": float(po.quantity),
                "unit": po.unit,
                "product": po.product.name if po.product else None
            },
            "commitment_inventory": commitment_inventory,
            "physical_inventory": physical_inventory,
            "suppliers": suppliers,
            "total_available": {
                "commitments": sum(c["available_quantity"] for c in commitment_inventory),
                "physical": sum(p["available_quantity"] for p in physical_inventory)
            }
        }
    
    def fulfill_po_with_allocations(
        self, 
        po_id: UUID, 
        allocations: List[Dict[str, Any]], 
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Fulfill a PO using multiple allocation sources
        
        Args:
            po_id: ID of the PO being fulfilled
            allocations: List of allocation sources
            user_id: ID of user making the allocation
            
        Returns:
            Dict with fulfillment result
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise ValueError(f"PO {po_id} not found")
        
        total_allocated = 0
        created_allocations = []
        
        for allocation in allocations:
            allocation_type = allocation.get("allocation_type")
            quantity = allocation.get("quantity", 0)
            
            if allocation_type == "COMMITMENT":
                # Fulfill from existing PO commitment
                source_po_id = allocation.get("source_po_id")
                result = self._allocate_from_commitment(po_id, source_po_id, quantity, user_id)
                created_allocations.append(result)
                
            elif allocation_type == "INVENTORY":
                # Fulfill from existing batch
                source_batch_id = allocation.get("source_batch_id")
                result = self._allocate_from_inventory(po_id, source_batch_id, quantity, user_id)
                created_allocations.append(result)
                
            elif allocation_type == "CHAIN":
                # Create new PO chain
                supplier_id = allocation.get("supplier_id")
                result = self._create_chain_allocation(po_id, supplier_id, quantity, user_id)
                created_allocations.append(result)
            
            total_allocated += quantity
        
        # Update PO state
        self._update_po_state(po, total_allocated)
        
        return {
            "po_id": str(po_id),
            "total_allocated": total_allocated,
            "po_state": po.po_state,
            "fulfillment_percentage": po.fulfillment_percentage,
            "allocations": created_allocations
        }
    
    def _get_commitment_inventory(self, company_id: UUID, product_id: UUID) -> List[Dict[str, Any]]:
        """Get available commitment inventory (unfulfilled POs)"""
        # Get POs issued by this company that are not fully fulfilled
        commitments = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.buyer_company_id == company_id,
                PurchaseOrder.product_id == product_id,
                PurchaseOrder.po_state.in_(['OPEN', 'PARTIALLY_FULFILLED'])
            )
        ).all()
        
        return [
            {
                "po_id": str(po.id),
                "po_number": po.po_number,
                "total_quantity": float(po.quantity),
                "fulfilled_quantity": float(po.fulfilled_quantity),
                "available_quantity": float(po.quantity - po.fulfilled_quantity),
                "unit": po.unit,
                "supplier": po.seller_company.name,
                "created_at": po.created_at.isoformat()
            }
            for po in commitments
            if po.quantity > po.fulfilled_quantity
        ]
    
    def _get_physical_inventory(self, company_id: UUID, product_id: UUID) -> List[Dict[str, Any]]:
        """Get available physical inventory (batches)"""
        # Get batches owned by this company that are available
        batches = self.db.query(Batch).filter(
            and_(
                Batch.company_id == company_id,
                Batch.product_id == product_id,
                Batch.status == 'active'
            )
        ).all()
        
        return [
            {
                "batch_id": str(batch.id),
                "batch_number": batch.batch_id,
                "available_quantity": float(batch.quantity),
                "unit": batch.unit,
                "production_date": batch.production_date.isoformat(),
                "location": batch.location_name,
                "quality_metrics": batch.quality_metrics
            }
            for batch in batches
        ]
    
    def _get_available_suppliers(self, company_id: UUID) -> List[Dict[str, Any]]:
        """Get available suppliers for new chains"""
        # This would query business relationships in a real system
        # For now, return all other companies
        from app.models.company import Company
        
        suppliers = self.db.query(Company).filter(Company.id != company_id).all()
        
        return [
            {
                "company_id": str(company.id),
                "name": company.name,
                "company_type": company.company_type,
                "location": company.location
            }
            for company in suppliers
        ]
    
    def _allocate_from_commitment(
        self, 
        po_id: UUID, 
        source_po_id: UUID, 
        quantity: float, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Allocate from existing PO commitment"""
        source_po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == source_po_id).first()
        if not source_po:
            raise ValueError(f"Source PO {source_po_id} not found")
        
        # Check availability
        available = float(source_po.quantity - source_po.fulfilled_quantity)
        if quantity > available:
            raise ValueError(f"Insufficient commitment. Available: {available}, Requested: {quantity}")
        
        # Create allocation
        allocation = POFulfillmentAllocation(
            po_id=po_id,
            source_po_id=source_po_id,
            quantity_allocated=quantity,
            unit=source_po.unit,
            allocation_type='COMMITMENT',
            allocation_reason='commitment_fulfillment',
            created_by_user_id=user_id
        )
        
        self.db.add(allocation)
        
        # Update source PO
        source_po.fulfilled_quantity += quantity
        if source_po.fulfilled_quantity >= source_po.quantity:
            source_po.po_state = 'FULFILLED'
        else:
            source_po.po_state = 'PARTIALLY_FULFILLED'
        
        self.db.commit()
        
        return {
            "allocation_id": str(allocation.id),
            "allocation_type": "COMMITMENT",
            "source_po_number": source_po.po_number,
            "quantity_allocated": quantity
        }
    
    def _allocate_from_inventory(
        self, 
        po_id: UUID, 
        source_batch_id: UUID, 
        quantity: float, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Allocate from existing batch inventory"""
        source_batch = self.db.query(Batch).filter(Batch.id == source_batch_id).first()
        if not source_batch:
            raise ValueError(f"Source batch {source_batch_id} not found")
        
        # Check availability
        if quantity > float(source_batch.quantity):
            raise ValueError(f"Insufficient inventory. Available: {source_batch.quantity}, Requested: {quantity}")
        
        # Create allocation
        allocation = POFulfillmentAllocation(
            po_id=po_id,
            source_batch_id=source_batch_id,
            quantity_allocated=quantity,
            unit=source_batch.unit,
            allocation_type='INVENTORY',
            allocation_reason='inventory_fulfillment',
            created_by_user_id=user_id
        )
        
        self.db.add(allocation)
        self.db.commit()
        
        return {
            "allocation_id": str(allocation.id),
            "allocation_type": "INVENTORY",
            "source_batch_number": source_batch.batch_id,
            "quantity_allocated": quantity
        }
    
    def _create_chain_allocation(
        self, 
        po_id: UUID, 
        supplier_id: UUID, 
        quantity: float, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Create new PO chain allocation"""
        # This would create a new PO to the supplier
        # For now, return a placeholder
        return {
            "allocation_id": "placeholder",
            "allocation_type": "CHAIN",
            "supplier_id": str(supplier_id),
            "quantity_allocated": quantity,
            "status": "new_po_created"
        }
    
    def _update_po_state(self, po: PurchaseOrder, total_allocated: float):
        """Update PO state based on total allocated quantity"""
        po.fulfilled_quantity = total_allocated
        po.fulfillment_percentage = int((total_allocated / float(po.quantity)) * 100)
        
        if total_allocated >= float(po.quantity):
            po.po_state = 'FULFILLED'
            po.fulfillment_status = 'fulfilled'
        elif total_allocated > 0:
            po.po_state = 'PARTIALLY_FULFILLED'
            po.fulfillment_status = 'partial'
        else:
            po.po_state = 'OPEN'
            po.fulfillment_status = 'pending'
        
        self.db.commit()
