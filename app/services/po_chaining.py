"""
PO Chaining Service for commercial traceability
Handles automatic creation of child POs when confirming parent POs
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.purchase_order import PurchaseOrder
from app.models.company import Company
from app.models.product import Product
from app.models.batch import Batch
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
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        
        print(f"🔗 POChainingService.confirm_po_and_create_children called with po_id: {po_id}, confirming_user_id: {confirming_user_id}")
        print(f"🔗 Confirmation data: {confirmation_data}")
        logger.info(f"POChainingService.confirm_po_and_create_children called with po_id: {po_id}, confirming_user_id: {confirming_user_id}")
        logger.info(f"Confirmation data: {confirmation_data}")
        
        # Get the PO being confirmed
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            print(f"❌ PO {po_id} not found in database")
            logger.error(f"PO {po_id} not found in database")
            raise ValueError(f"PO {po_id} not found")
        
        print(f"📦 PO found: {po.po_number} with status: {po.status}")
        logger.info(f"Found PO: {po.po_number} with status: {po.status}")
        
        # Confirm the PO
        logger.info("Calling _confirm_po method")
        confirmation_result = self._confirm_po(po, confirmation_data, confirming_user_id)
        logger.info("_confirm_po method completed successfully")
        
        # Check fulfillment method
        fulfillment_method = confirmation_data.get('fulfillment_method', 'create_child_pos')
        child_pos = []
        
        if fulfillment_method == 'create_child_pos' and self._should_create_child_pos(po):
            # Create child POs to suppliers
            child_pos = self._create_child_pos(po, confirming_user_id)
        elif fulfillment_method == 'fulfill_from_stock':
            # Fulfill from existing inventory - requires batch linking
            child_pos = []
            
            # Get stock batches to fulfill from
            stock_batches = confirmation_data.get('stock_batches', [])
            if not stock_batches:
                raise ValueError("Stock fulfillment requires batch information for traceability")
            
            # Link PO to existing batches for traceability
            self._link_po_to_stock_batches(po, stock_batches)
            
            # Mark as fulfilled from stock
            po.fulfillment_status = 'fulfilled'
            po.fulfillment_percentage = 100
            po.fulfillment_notes = f"Fulfilled from existing stock: {len(stock_batches)} batches"
            self.db.commit()
        elif fulfillment_method == 'partial_stock_partial_po':
            # Partial fulfillment from stock + partial child POs
            stock_quantity = confirmation_data.get('stock_quantity', 0)
            po_quantity = confirmation_data.get('po_quantity', 0)
            stock_batches = confirmation_data.get('stock_batches', [])
            
            # Link stock batches for traceability
            if stock_batches:
                self._link_po_to_stock_batches(po, stock_batches)
            
            if po_quantity > 0:
                # Create child POs for the portion that needs to be purchased
                child_pos = self._create_child_pos(po, confirming_user_id, po_quantity)
            
            # Update fulfillment status
            po.fulfillment_status = 'partial'
            po.fulfillment_percentage = int((stock_quantity / po.quantity) * 100)
            po.fulfillment_notes = f"Partial fulfillment: {stock_quantity} from stock ({len(stock_batches)} batches), {po_quantity} from new POs"
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
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        
        logger.info(f"_confirm_po called for PO: {po.po_number} (ID: {po.id})")
        logger.info(f"Current PO status: {po.status}")
        logger.info(f"Confirmation data: {confirmation_data}")
        
        try:
            # Update PO with confirmation data
            logger.info("Updating PO with confirmation data")
            po.status = 'confirmed'
            po.confirmed_at = confirmation_data.get('confirmed_at')
            po.confirmed_quantity = confirmation_data.get('confirmed_quantity', po.quantity)
            po.confirmed_unit_price = confirmation_data.get('confirmed_unit_price', po.unit_price)
            po.confirmed_delivery_date = confirmation_data.get('confirmed_delivery_date', po.delivery_date)
            po.confirmed_delivery_location = confirmation_data.get('confirmed_delivery_location', po.delivery_location)
            po.seller_notes = confirmation_data.get('seller_notes', '')
            
            # Inherit origin data from linked harvest batches
            print("DEBUG: About to call _inherit_origin_data_from_batches")
            self._inherit_origin_data_from_batches(po, confirmation_data)
            print("DEBUG: Finished calling _inherit_origin_data_from_batches")
            
            logger.info("Committing PO confirmation to database")
            self.db.commit()
            logger.info("PO confirmation committed successfully")
        except Exception as e:
            logger.error(f"Error in _confirm_po: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            self.db.rollback()
            raise
        
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
    
    def _link_po_to_stock_batches(self, po: PurchaseOrder, stock_batches: List[Dict[str, Any]]) -> None:
        """
        Link a PO to existing stock batches for traceability compliance
        
        Args:
            po: The purchase order being fulfilled
            stock_batches: List of batch information for stock fulfillment
        """
        from app.models.batch import Batch
        from app.models.po_batch_linkage import POBatchLinkage
        
        total_quantity = 0
        
        for batch_info in stock_batches:
            batch_id = batch_info.get('batch_id')
            quantity_used = batch_info.get('quantity_used', 0)
            allocation_reason = batch_info.get('allocation_reason', 'stock_fulfillment')
            compliance_notes = batch_info.get('compliance_notes', '')
            
            if not batch_id or quantity_used <= 0:
                continue
                
            # Get the batch
            batch = self.db.query(Batch).filter(Batch.id == batch_id).first()
            if not batch:
                raise ValueError(f"Batch {batch_id} not found")
            
            # Verify the batch belongs to the confirming company
            if batch.company_id != po.seller_company_id:
                raise ValueError(f"Batch {batch_id} does not belong to company {po.seller_company_id}")
            
            # Verify batch has sufficient quantity available
            # This would check against allocated quantities in a real system
            if quantity_used > batch.quantity:
                raise ValueError(f"Batch {batch.batch_id} has insufficient quantity. Available: {batch.quantity}, Requested: {quantity_used}")
            
            # Create PO-Batch linkage for traceability
            linkage = POBatchLinkage(
                purchase_order_id=po.id,
                batch_id=batch.id,
                quantity_allocated=quantity_used,
                unit=po.unit,
                allocation_reason=allocation_reason,
                compliance_notes=compliance_notes
            )
            
            self.db.add(linkage)
            total_quantity += quantity_used
        
        # Verify total quantity matches PO quantity
        if abs(total_quantity - po.quantity) > 0.001:  # Allow small floating point differences
            raise ValueError(f"Total batch quantity ({total_quantity}) does not match PO quantity ({po.quantity})")
        
        self.db.commit()
    
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
    
    def _inherit_origin_data_from_batches(self, po: PurchaseOrder, confirmation_data: Dict[str, Any]) -> None:
        """
        Inherit origin data from linked harvest batches during PO confirmation.
        
        Args:
            po: The purchase order being confirmed
            confirmation_data: Confirmation data containing stock_batches
        """
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        
        print(f"🌾 _inherit_origin_data_from_batches called for PO: {po.id}")
        stock_batches = confirmation_data.get('stock_batches', [])
        print(f"🌾 Stock batches in confirmation data: {stock_batches}")
        logger.info(f"Stock batches in confirmation data: {stock_batches}")
        if not stock_batches:
            print("❌ No stock batches provided, skipping origin data inheritance")
            logger.info("No stock batches provided, skipping origin data inheritance")
            return
        
        logger.info(f"Inheriting origin data from {len(stock_batches)} linked batches")
        
        try:
            # Collect all batch IDs and convert to UUID objects
            batch_ids = []
            for batch in stock_batches:
                batch_id = batch.get('batch_id')
                if batch_id:
                    try:
                        # Convert string UUID to UUID object
                        from uuid import UUID
                        batch_ids.append(UUID(batch_id))
                    except ValueError:
                        logger.warning(f"Invalid UUID format for batch_id: {batch_id}")
                        continue
            
            if not batch_ids:
                print("❌ No valid batch IDs found in stock_batches")
                logger.warning("No valid batch IDs found in stock_batches")
                return
            
            print(f"🌾 Retrieving harvest batches for IDs: {batch_ids}")
            logger.info(f"Retrieving harvest batches for IDs: {batch_ids}")
            
            # Retrieve harvest batches from database
            print(f"🌾 Querying database for batches with IDs: {batch_ids}")
            logger.info(f"Querying database for batches with IDs: {batch_ids}")
            harvest_batches = self.db.query(Batch).filter(
                Batch.id.in_(batch_ids),
                Batch.batch_type == 'harvest'  # Only harvest batches have origin data
            ).all()
            
            print(f"🌾 Found {len(harvest_batches)} harvest batches in database")
            logger.info(f"Found {len(harvest_batches)} harvest batches in database")
            for batch in harvest_batches:
                print(f"🌾 Batch {batch.batch_id} (ID: {batch.id}) has origin_data: {bool(batch.origin_data)}")
                logger.info(f"Batch {batch.batch_id} (ID: {batch.id}) has origin_data: {bool(batch.origin_data)}")
            
            if not harvest_batches:
                logger.warning("No harvest batches found for the provided batch IDs")
                return
            
            logger.info(f"Found {len(harvest_batches)} harvest batches with origin data")
            
            # Collect and merge origin data from all harvest batches
            print(f"🌾 Merging origin data from {len(harvest_batches)} harvest batches")
            inherited_origin_data = self._merge_origin_data_from_batches(harvest_batches)
            print(f"🌾 Merged origin data: {inherited_origin_data}")
            
            if inherited_origin_data:
                # Update PO with inherited origin data
                print(f"🌾 Setting origin data on PO: {inherited_origin_data}")
                logger.info(f"Setting origin data on PO: {inherited_origin_data}")
                if po.origin_data:
                    # Merge with existing origin data
                    existing_origin_data = po.origin_data if isinstance(po.origin_data, dict) else {}
                    po.origin_data = {**existing_origin_data, **inherited_origin_data}
                    print(f"🌾 Merged origin data: {po.origin_data}")
                    logger.info(f"Merged origin data: {po.origin_data}")
                else:
                    # Set new origin data
                    po.origin_data = inherited_origin_data
                    print(f"🌾 Set new origin data: {po.origin_data}")
                    logger.info(f"Set new origin data: {po.origin_data}")
                
                print("✅ Successfully inherited origin data from harvest batches")
                logger.info("Successfully inherited origin data from harvest batches")
                logger.info(f"Inherited origin data keys: {list(inherited_origin_data.keys())}")
                
                # Update transparency score based on inherited origin data
                print("🌾 Updating transparency score based on inherited origin data")
                print("🌾 *** CALLING _update_transparency_score METHOD ***")
                self._update_transparency_score(po, inherited_origin_data)
                print("🌾 *** FINISHED _update_transparency_score METHOD ***")
                
                # ✅ FIX: Transfer batch ownership (3 lines)
                print("🔄 Transferring batch ownership to buyer company")
                for batch in harvest_batches:
                    batch.company_id = po.buyer_company_id
                    batch.status = 'transferred'
                    batch.updated_at = datetime.utcnow()
                    print(f"🔄 Transferred batch {batch.batch_id} to buyer company {po.buyer_company_id}")
                    logger.info(f"Transferred batch {batch.batch_id} to buyer company {po.buyer_company_id}")
            else:
                print("❌ No origin data to inherit from harvest batches")
                logger.warning("No origin data to inherit from harvest batches")
                
        except Exception as e:
            logger.error(f"Error inheriting origin data from batches: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            # Don't raise the exception - origin data inheritance is not critical for PO confirmation
    
    def _merge_origin_data_from_batches(self, harvest_batches: List[Batch]) -> Dict[str, Any]:
        """
        Merge origin data from multiple harvest batches.
        
        Args:
            harvest_batches: List of harvest batch objects
            
        Returns:
            Merged origin data dictionary
        """
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        
        merged_origin_data = {}
        
        for batch in harvest_batches:
            if not batch.origin_data:
                continue
                
            origin_data = batch.origin_data if isinstance(batch.origin_data, dict) else {}
            
            # Merge farm information
            if 'farm_information' in origin_data:
                if 'farm_information' not in merged_origin_data:
                    merged_origin_data['farm_information'] = []
                
                # Add farm info if not already present
                farm_info = origin_data['farm_information']
                if isinstance(farm_info, dict):
                    # Single farm
                    if farm_info not in merged_origin_data['farm_information']:
                        merged_origin_data['farm_information'].append(farm_info)
                elif isinstance(farm_info, list):
                    # Multiple farms
                    for farm in farm_info:
                        if farm not in merged_origin_data['farm_information']:
                            merged_origin_data['farm_information'].append(farm)
            
            # Merge geographic coordinates
            if 'geographic_coordinates' in origin_data:
                if 'geographic_coordinates' not in merged_origin_data:
                    merged_origin_data['geographic_coordinates'] = []
                
                coords = origin_data['geographic_coordinates']
                if isinstance(coords, dict):
                    # Single coordinate set
                    if coords not in merged_origin_data['geographic_coordinates']:
                        merged_origin_data['geographic_coordinates'].append(coords)
                elif isinstance(coords, list):
                    # Multiple coordinate sets
                    for coord in coords:
                        if coord not in merged_origin_data['geographic_coordinates']:
                            merged_origin_data['geographic_coordinates'].append(coord)
            
            # Merge harvest date (use the earliest date)
            if 'harvest_date' in origin_data:
                harvest_date = origin_data['harvest_date']
                if 'harvest_date' not in merged_origin_data:
                    merged_origin_data['harvest_date'] = harvest_date
                else:
                    # Keep the earliest harvest date
                    try:
                        from datetime import datetime
                        existing_date = datetime.fromisoformat(merged_origin_data['harvest_date'].replace('Z', '+00:00'))
                        new_date = datetime.fromisoformat(harvest_date.replace('Z', '+00:00'))
                        if new_date < existing_date:
                            merged_origin_data['harvest_date'] = harvest_date
                    except (ValueError, AttributeError):
                        # If date parsing fails, keep the existing date
                        pass
            
            # Merge certifications
            if 'certifications' in origin_data:
                if 'certifications' not in merged_origin_data:
                    merged_origin_data['certifications'] = []
                
                certs = origin_data['certifications']
                if isinstance(certs, list):
                    for cert in certs:
                        if cert not in merged_origin_data['certifications']:
                            merged_origin_data['certifications'].append(cert)
                elif isinstance(certs, str) and certs not in merged_origin_data['certifications']:
                    merged_origin_data['certifications'].append(certs)
            
            # Add batch reference for traceability
            if 'source_batches' not in merged_origin_data:
                merged_origin_data['source_batches'] = []
            
            batch_reference = {
                'batch_id': str(batch.id),
                'batch_number': batch.batch_id,
                'quantity': float(batch.quantity),
                'unit': batch.unit,
                'production_date': batch.production_date.isoformat() if batch.production_date else None
            }
            
            if batch_reference not in merged_origin_data['source_batches']:
                merged_origin_data['source_batches'].append(batch_reference)
        
        logger.info(f"Merged origin data from {len(harvest_batches)} batches")
        return merged_origin_data
    
    def _update_transparency_score(self, po: PurchaseOrder, origin_data: Dict[str, Any]) -> None:
        """
        Update transparency score based on inherited origin data.
        
        NOTE: This method is deprecated in favor of deterministic transparency.
        The deterministic transparency system calculates transparency in real-time
        from the supply_chain_traceability materialized view based on explicit
        user-created links, not algorithmic scoring.
        
        Args:
            po: The purchase order
            origin_data: The inherited origin data
        """
        # No-op: Deterministic transparency handles this via materialized views
        logger.info("Transparency score update skipped - using deterministic transparency system")
