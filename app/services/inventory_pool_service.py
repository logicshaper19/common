"""
Inventory Pool Service for managing inventory pools and proportional allocations.
Handles realistic inventory-level transformations with proportional provenance tracking.
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc

from app.models.batch import Batch
from app.models.inventory_transformation import (
    InventoryPool, 
    InventoryAllocation, 
    AllocationMethod
)
from app.models.transformation import TransformationEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


class InventoryPoolService:
    """Service for managing inventory pools and proportional allocations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_available_inventory(self, company_id: UUID, product_id: UUID) -> Dict[str, Any]:
        """
        Get available inventory for a product from a company.
        
        Args:
            company_id: Company ID to get inventory for
            product_id: Product ID to get inventory for
            
        Returns:
            Dict with available inventory details
        """
        try:
            # Query all active batches for the company/product
            batches = self.db.query(Batch).filter(
                and_(
                    Batch.company_id == company_id,
                    Batch.product_id == product_id,
                    Batch.status == 'active'
                )
            ).order_by(desc(Batch.created_at)).all()
            
            if not batches:
                return {
                    "total_quantity": 0,
                    "unit": "KGM",
                    "batch_count": 0,
                    "batches": [],
                    "pool_composition": []
                }
            
            # Calculate total available quantity
            total_quantity = sum(float(batch.quantity) for batch in batches)
            unit = batches[0].unit if batches else "KGM"
            
            # Create pool composition
            pool_composition = []
            for batch in batches:
                batch_quantity = float(batch.quantity)
                percentage = (batch_quantity / total_quantity) if total_quantity > 0 else 0
                
                pool_composition.append({
                    "batch_id": str(batch.id),
                    "batch_number": batch.batch_id,
                    "quantity": batch_quantity,
                    "percentage": round(percentage, 4),
                    "production_date": batch.production_date.isoformat() if batch.production_date else None,
                    "quality_metrics": batch.quality_metrics,
                    "origin_data": batch.origin_data,
                    "certifications": batch.certifications
                })
            
            return {
                "total_quantity": total_quantity,
                "unit": unit,
                "batch_count": len(batches),
                "batches": [
                    {
                        "id": str(batch.id),
                        "batch_number": batch.batch_id,
                        "quantity": float(batch.quantity),
                        "unit": batch.unit,
                        "production_date": batch.production_date.isoformat() if batch.production_date else None,
                        "quality_metrics": batch.quality_metrics,
                        "origin_data": batch.origin_data,
                        "certifications": batch.certifications
                    }
                    for batch in batches
                ],
                "pool_composition": pool_composition
            }
            
        except Exception as e:
            logger.error(f"Error getting available inventory: {str(e)}")
            raise
    
    def calculate_proportional_allocation(
        self, 
        requested_quantity: float, 
        available_batches: List[Dict[str, Any]],
        method: AllocationMethod = AllocationMethod.PROPORTIONAL
    ) -> List[Dict[str, Any]]:
        """
        Calculate proportional allocation from available batches.
        
        Args:
            requested_quantity: Quantity requested for transformation
            available_batches: List of available batch information
            method: Allocation method to use
            
        Returns:
            List of allocation details
        """
        try:
            if not available_batches:
                return []
            
            total_available = sum(batch['quantity'] for batch in available_batches)
            
            if requested_quantity > total_available:
                raise ValueError(f"Insufficient inventory. Available: {total_available}, Requested: {requested_quantity}")
            
            if method == AllocationMethod.PROPORTIONAL:
                return self._calculate_proportional_allocation(requested_quantity, available_batches)
            elif method == AllocationMethod.FIFO:
                return self._calculate_fifo_allocation(requested_quantity, available_batches)
            elif method == AllocationMethod.LIFO:
                return self._calculate_lifo_allocation(requested_quantity, available_batches)
            elif method == AllocationMethod.ENTIRE_BATCHES_FIRST:
                return self._calculate_entire_batches_first_allocation(requested_quantity, available_batches)
            else:
                # Default to proportional
                return self._calculate_proportional_allocation(requested_quantity, available_batches)
                
        except Exception as e:
            logger.error(f"Error calculating allocation: {str(e)}")
            raise
    
    def _calculate_proportional_allocation(
        self, 
        requested_quantity: float, 
        available_batches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate proportional allocation from available batches."""
        total_available = sum(batch['quantity'] for batch in available_batches)
        allocation = []
        
        for batch in available_batches:
            batch_quantity = batch['quantity']
            contribution_ratio = batch_quantity / total_available
            quantity_used = requested_quantity * contribution_ratio
            
            allocation.append({
                "batch_id": batch['id'],
                "batch_number": batch['batch_number'],
                "available_quantity": batch_quantity,
                "quantity_used": round(quantity_used, 4),
                "contribution_ratio": round(contribution_ratio, 4),
                "contribution_percentage": round(contribution_ratio * 100, 2),
                "unit": batch.get('unit', 'KGM'),
                "production_date": batch.get('production_date'),
                "quality_metrics": batch.get('quality_metrics'),
                "origin_data": batch.get('origin_data'),
                "certifications": batch.get('certifications')
            })
        
        return allocation
    
    def _calculate_fifo_allocation(
        self, 
        requested_quantity: float, 
        available_batches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate FIFO (First-In-First-Out) allocation."""
        # Sort by production date (oldest first)
        sorted_batches = sorted(
            available_batches, 
            key=lambda x: x.get('production_date', '1900-01-01')
        )
        
        allocation = []
        remaining_quantity = requested_quantity
        
        for batch in sorted_batches:
            if remaining_quantity <= 0:
                break
                
            batch_quantity = batch['quantity']
            quantity_used = min(remaining_quantity, batch_quantity)
            contribution_ratio = quantity_used / requested_quantity if requested_quantity > 0 else 0
            
            allocation.append({
                "batch_id": batch['id'],
                "batch_number": batch['batch_number'],
                "available_quantity": batch_quantity,
                "quantity_used": round(quantity_used, 4),
                "contribution_ratio": round(contribution_ratio, 4),
                "contribution_percentage": round(contribution_ratio * 100, 2),
                "unit": batch.get('unit', 'KGM'),
                "production_date": batch.get('production_date'),
                "quality_metrics": batch.get('quality_metrics'),
                "origin_data": batch.get('origin_data'),
                "certifications": batch.get('certifications')
            })
            
            remaining_quantity -= quantity_used
        
        return allocation
    
    def _calculate_lifo_allocation(
        self, 
        requested_quantity: float, 
        available_batches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate LIFO (Last-In-First-Out) allocation."""
        # Sort by production date (newest first)
        sorted_batches = sorted(
            available_batches, 
            key=lambda x: x.get('production_date', '1900-01-01'),
            reverse=True
        )
        
        allocation = []
        remaining_quantity = requested_quantity
        
        for batch in sorted_batches:
            if remaining_quantity <= 0:
                break
                
            batch_quantity = batch['quantity']
            quantity_used = min(remaining_quantity, batch_quantity)
            contribution_ratio = quantity_used / requested_quantity if requested_quantity > 0 else 0
            
            allocation.append({
                "batch_id": batch['id'],
                "batch_number": batch['batch_number'],
                "available_quantity": batch_quantity,
                "quantity_used": round(quantity_used, 4),
                "contribution_ratio": round(contribution_ratio, 4),
                "contribution_percentage": round(contribution_ratio * 100, 2),
                "unit": batch.get('unit', 'KGM'),
                "production_date": batch.get('production_date'),
                "quality_metrics": batch.get('quality_metrics'),
                "origin_data": batch.get('origin_data'),
                "certifications": batch.get('certifications')
            })
            
            remaining_quantity -= quantity_used
        
        return allocation
    
    def _calculate_entire_batches_first_allocation(
        self, 
        requested_quantity: float, 
        available_batches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate allocation using entire batches first, then proportional."""
        # Sort by quantity (largest first) to use entire batches efficiently
        sorted_batches = sorted(available_batches, key=lambda x: x['quantity'], reverse=True)
        
        allocation = []
        remaining_quantity = requested_quantity
        
        # First pass: use entire batches
        for batch in sorted_batches:
            if remaining_quantity <= 0:
                break
                
            batch_quantity = batch['quantity']
            if batch_quantity <= remaining_quantity:
                # Use entire batch
                contribution_ratio = batch_quantity / requested_quantity if requested_quantity > 0 else 0
                
                allocation.append({
                    "batch_id": batch['id'],
                    "batch_number": batch['batch_number'],
                    "available_quantity": batch_quantity,
                    "quantity_used": round(batch_quantity, 4),
                    "contribution_ratio": round(contribution_ratio, 4),
                    "contribution_percentage": round(contribution_ratio * 100, 2),
                    "unit": batch.get('unit', 'KGM'),
                    "production_date": batch.get('production_date'),
                    "quality_metrics": batch.get('quality_metrics'),
                    "origin_data": batch.get('origin_data'),
                    "certifications": batch.get('certifications')
                })
                
                remaining_quantity -= batch_quantity
        
        # Second pass: proportional allocation from remaining batches
        if remaining_quantity > 0:
            remaining_batches = [b for b in sorted_batches if b['id'] not in [a['batch_id'] for a in allocation]]
            if remaining_batches:
                proportional_allocation = self._calculate_proportional_allocation(
                    remaining_quantity, remaining_batches
                )
                allocation.extend(proportional_allocation)
        
        return allocation
    
    def draw_from_inventory(
        self, 
        company_id: UUID, 
        product_id: UUID, 
        quantity: float,
        method: AllocationMethod = AllocationMethod.PROPORTIONAL,
        transformation_event_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Draw quantity from inventory pool and create allocation record.
        
        Args:
            company_id: Company ID
            product_id: Product ID
            quantity: Quantity to draw
            method: Allocation method
            transformation_event_id: Associated transformation event ID
            user_id: User performing the allocation
            
        Returns:
            Dict with allocation details
        """
        try:
            # Get available inventory
            inventory = self.get_available_inventory(company_id, product_id)
            
            if quantity > inventory['total_quantity']:
                raise ValueError(f"Insufficient inventory. Available: {inventory['total_quantity']}, Requested: {quantity}")
            
            # Calculate allocation
            allocation_plan = self.calculate_proportional_allocation(
                quantity, inventory['batches'], method
            )
            
            # Create inventory allocation record
            allocation = InventoryAllocation(
                transformation_event_id=transformation_event_id,
                inventory_pool_id=None,  # Will be set when pool is created/updated
                requested_quantity=quantity,
                allocated_quantity=quantity,
                unit=inventory['unit'],
                allocation_method=method,
                allocation_details=allocation_plan,
                created_by_user_id=user_id
            )
            
            self.db.add(allocation)
            self.db.flush()  # Get the ID
            
            # Update batch quantities (reduce available quantities)
            for allocation_item in allocation_plan:
                batch_id = UUID(allocation_item['batch_id'])
                quantity_used = allocation_item['quantity_used']
                
                batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
                if batch:
                    # Reduce batch quantity
                    batch.quantity = batch.quantity - Decimal(str(quantity_used))
                    if batch.quantity <= 0:
                        batch.status = 'consumed'
            
            self.db.commit()
            
            return {
                "allocation_id": str(allocation.id),
                "requested_quantity": quantity,
                "allocated_quantity": quantity,
                "unit": inventory['unit'],
                "allocation_method": method.value,
                "allocation_details": allocation_plan,
                "total_batches_used": len(allocation_plan)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error drawing from inventory: {str(e)}")
            raise
    
    def get_or_create_inventory_pool(self, company_id: UUID, product_id: UUID, user_id: UUID) -> InventoryPool:
        """
        Get or create inventory pool for a company-product combination.
        
        Args:
            company_id: Company ID
            product_id: Product ID
            user_id: User ID for audit trail
            
        Returns:
            InventoryPool instance
        """
        try:
            # Check if pool already exists
            pool = self.db.query(InventoryPool).filter(
                and_(
                    InventoryPool.company_id == company_id,
                    InventoryPool.product_id == product_id
                )
            ).first()
            
            if pool:
                # Update existing pool
                inventory = self.get_available_inventory(company_id, product_id)
                pool.total_available_quantity = inventory['total_quantity']
                pool.unit = inventory['unit']
                pool.batch_count = inventory['batch_count']
                pool.pool_composition = inventory['pool_composition']
                pool.last_calculated_at = func.now()
                pool.updated_at = func.now()
            else:
                # Create new pool
                inventory = self.get_available_inventory(company_id, product_id)
                pool = InventoryPool(
                    company_id=company_id,
                    product_id=product_id,
                    total_available_quantity=inventory['total_quantity'],
                    unit=inventory['unit'],
                    batch_count=inventory['batch_count'],
                    pool_composition=inventory['pool_composition'],
                    created_by_user_id=user_id
                )
                self.db.add(pool)
            
            self.db.commit()
            return pool
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error getting/creating inventory pool: {str(e)}")
            raise
