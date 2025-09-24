"""
Optimized Batch Linking Service for Phase 5 Performance Optimization
High-performance batch linking without circular FK overhead.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.models.po_batch_linkage import POBatchLinkage
from app.core.logging import get_logger

logger = get_logger(__name__)


class OptimizedBatchLinkingService:
    """High-performance batch linking without circular FK overhead."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def link_batch_to_po_bulk(self, linkages: List[Dict[str, Any]]) -> List[POBatchLinkage]:
        """Bulk linking with minimal validation overhead."""
        
        if not linkages:
            return []
        
        # Batch validate all references at once
        po_ids = [link["po_id"] for link in linkages]
        batch_ids = [link["batch_id"] for link in linkages]
        
        # Single query to validate all POs exist
        existing_pos = set(
            row[0] for row in self.db.execute(
                text("SELECT id FROM purchase_orders WHERE id = ANY(:po_ids)"),
                {"po_ids": po_ids}
            ).fetchall()
        )
        
        # Single query to validate all batches exist
        existing_batches = set(
            row[0] for row in self.db.execute(
                text("SELECT id FROM batches WHERE id = ANY(:batch_ids)"),
                {"batch_ids": batch_ids}
            ).fetchall()
        )
        
        # Create linkage records in bulk
        new_linkages = []
        po_batch_updates = []
        
        for link in linkages:
            po_id = link["po_id"]
            batch_id = link["batch_id"]
            
            if po_id not in existing_pos:
                raise ValueError(f"Purchase Order {po_id} not found")
            if batch_id not in existing_batches:
                raise ValueError(f"Batch {batch_id} not found")
            
            # Create junction table record
            linkage = POBatchLinkage(
                purchase_order_id=po_id,
                batch_id=batch_id,
                quantity_allocated=link["quantity"],
                unit=link.get("unit", "MT"),
                allocation_reason=link.get("allocation_reason", "bulk_allocation"),
                compliance_notes=link.get("compliance_notes"),
                created_by_user_id=link.get("created_by_user_id")
            )
            new_linkages.append(linkage)
            
            # Prepare PO batch reference update (no FK constraint)
            po_batch_updates.append({
                "po_id": po_id,
                "batch_id": batch_id
            })
        
        # Bulk insert linkages
        self.db.add_all(new_linkages)
        
        # Bulk update PO batch references using a single SQL statement
        if po_batch_updates:
            # Use PostgreSQL's UPDATE ... FROM for bulk updates
            update_query = text("""
                UPDATE purchase_orders 
                SET batch_id = updates.batch_id
                FROM (VALUES :updates) AS updates(po_id, batch_id)
                WHERE purchase_orders.id = updates.po_id::uuid
            """)
            
            update_values = [(str(update["po_id"]), str(update["batch_id"])) 
                           for update in po_batch_updates]
            
            self.db.execute(update_query, {"updates": update_values})
        
        await self.db.commit()
        return new_linkages
    
    async def get_supply_chain_optimized(self, po_id: UUID) -> Dict[str, Any]:
        """Get supply chain data with optimized queries (no circular FK joins)."""
        
        # Single optimized query using the new indexes
        supply_chain_query = text("""
            WITH RECURSIVE supply_chain AS (
                -- Base case: starting PO
                SELECT 
                    po.id, po.po_number, po.buyer_company_id, po.seller_company_id,
                    po.batch_id, po.parent_po_id, po.status,
                    0 as level, ARRAY[po.id] as path
                FROM purchase_orders po
                WHERE po.id = :po_id
                
                UNION ALL
                
                -- Recursive case: parent and child POs
                SELECT 
                    po.id, po.po_number, po.buyer_company_id, po.seller_company_id,
                    po.batch_id, po.parent_po_id, po.status,
                    sc.level + 1, sc.path || po.id
                FROM purchase_orders po
                JOIN supply_chain sc ON (po.id = sc.parent_po_id OR po.parent_po_id = sc.id)
                WHERE NOT po.id = ANY(sc.path)  -- Prevent infinite loops
                AND sc.level < 10  -- Limit recursion depth
            )
            SELECT 
                sc.id, sc.po_number, sc.level,
                bc.name as buyer_name,
                sc.seller_company_id,  
                sc.batch_id,
                b.batch_id as batch_number,
                sc.status
            FROM supply_chain sc
            LEFT JOIN companies bc ON sc.buyer_company_id = bc.id
            LEFT JOIN batches b ON sc.batch_id = b.id  -- No FK constraint, just reference
            ORDER BY sc.level, sc.po_number
        """)
        
        results = self.db.execute(supply_chain_query, {"po_id": po_id}).fetchall()
        
        return {
            "supply_chain": [
                {
                    "po_id": str(result.id),
                    "po_number": result.po_number,
                    "level": result.level,
                    "buyer_name": result.buyer_name,
                    "batch_number": result.batch_number,
                    "status": result.status
                }
                for result in results
            ],
            "total_levels": max(result.level for result in results) if results else 0
        }
    
    async def get_po_batch_allocations(self, po_id: UUID) -> List[Dict[str, Any]]:
        """Get all batch allocations for a PO with optimized query."""
        
        query = text("""
            SELECT 
                pbl.id,
                pbl.quantity_allocated,
                pbl.unit,
                pbl.allocation_reason,
                pbl.compliance_notes,
                pbl.created_at,
                b.batch_id,
                b.batch_type,
                b.production_date,
                b.quantity as batch_quantity,
                b.status as batch_status,
                c.name as batch_company_name
            FROM po_batch_linkages pbl
            JOIN batches b ON pbl.batch_id = b.id
            JOIN companies c ON b.company_id = c.id
            WHERE pbl.purchase_order_id = :po_id
            ORDER BY pbl.created_at DESC
        """)
        
        results = self.db.execute(query, {"po_id": po_id}).fetchall()
        
        return [
            {
                "linkage_id": str(result.id),
                "quantity_allocated": float(result.quantity_allocated),
                "unit": result.unit,
                "allocation_reason": result.allocation_reason,
                "compliance_notes": result.compliance_notes,
                "created_at": result.created_at.isoformat(),
                "batch": {
                    "batch_id": result.batch_id,
                    "batch_type": result.batch_type,
                    "production_date": result.production_date.isoformat(),
                    "quantity": float(result.batch_quantity),
                    "status": result.batch_status,
                    "company_name": result.batch_company_name
                }
            }
            for result in results
        ]
    
    async def unlink_batch_from_po(self, po_id: UUID, batch_id: UUID) -> bool:
        """Remove batch linkage from PO."""
        
        # Delete the linkage record
        delete_query = text("""
            DELETE FROM po_batch_linkages 
            WHERE purchase_order_id = :po_id AND batch_id = :batch_id
        """)
        
        result = self.db.execute(delete_query, {"po_id": po_id, "batch_id": batch_id})
        
        # Clear batch_id reference in PO if it matches
        update_query = text("""
            UPDATE purchase_orders 
            SET batch_id = NULL 
            WHERE id = :po_id AND batch_id = :batch_id
        """)
        
        self.db.execute(update_query, {"po_id": po_id, "batch_id": batch_id})
        
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def get_batch_utilization(self, batch_id: UUID) -> Dict[str, Any]:
        """Get utilization statistics for a batch."""
        
        query = text("""
            SELECT 
                b.batch_id,
                b.quantity as total_quantity,
                b.unit,
                COALESCE(SUM(pbl.quantity_allocated), 0) as allocated_quantity,
                COUNT(pbl.id) as allocation_count,
                b.quantity - COALESCE(SUM(pbl.quantity_allocated), 0) as remaining_quantity
            FROM batches b
            LEFT JOIN po_batch_linkages pbl ON b.id = pbl.batch_id
            WHERE b.id = :batch_id
            GROUP BY b.id, b.batch_id, b.quantity, b.unit
        """)
        
        result = self.db.execute(query, {"batch_id": batch_id}).fetchone()
        
        if not result:
            return {"error": "Batch not found"}
        
        total_quantity = float(result.total_quantity)
        allocated_quantity = float(result.allocated_quantity)
        remaining_quantity = float(result.remaining_quantity)
        
        return {
            "batch_id": result.batch_id,
            "total_quantity": total_quantity,
            "allocated_quantity": allocated_quantity,
            "remaining_quantity": remaining_quantity,
            "allocation_count": result.allocation_count,
            "utilization_percentage": (allocated_quantity / total_quantity * 100) if total_quantity > 0 else 0,
            "unit": result.unit
        }
    
    async def validate_batch_availability(self, batch_id: UUID, requested_quantity: float) -> Dict[str, Any]:
        """Validate if a batch has sufficient quantity for allocation."""
        
        utilization = await self.get_batch_utilization(batch_id)
        
        if "error" in utilization:
            return utilization
        
        available_quantity = utilization["remaining_quantity"]
        is_available = available_quantity >= requested_quantity
        
        return {
            "batch_id": batch_id,
            "requested_quantity": requested_quantity,
            "available_quantity": available_quantity,
            "is_available": is_available,
            "shortfall": max(0, requested_quantity - available_quantity) if not is_available else 0
        }
