"""
Service for detecting and handling discrepancies between original PO and seller confirmation.
"""
import json
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import date

from app.models.purchase_order import PurchaseOrder
from app.schemas.purchase_order import SellerConfirmation, DiscrepancyDetail
from app.core.logging import get_logger

logger = get_logger(__name__)


class DiscrepancyDetectionService:
    """Service for detecting discrepancies between original PO and seller confirmation."""
    
    def __init__(self):
        """Initialize the discrepancy detection service."""
        self.tolerance_percentage = 0.001  # 0.1% tolerance for quantity/price differences
    
    def detect_discrepancies(
        self, 
        original_po: PurchaseOrder, 
        confirmation: SellerConfirmation
    ) -> List[DiscrepancyDetail]:
        """
        Detect discrepancies between original PO and seller confirmation.
        
        Args:
            original_po: The original purchase order
            confirmation: The seller's confirmation data
            
        Returns:
            List of discrepancy details
        """
        discrepancies = []
        
        # Check quantity discrepancy
        if self._has_quantity_discrepancy(original_po.quantity, confirmation.confirmed_quantity):
            discrepancies.append(DiscrepancyDetail(
                field_name="quantity",
                original_value=float(original_po.quantity),
                confirmed_value=float(confirmation.confirmed_quantity),
                difference=self._calculate_quantity_difference(
                    original_po.quantity, 
                    confirmation.confirmed_quantity,
                    original_po.unit
                )
            ))
        
        # Check unit price discrepancy
        if (confirmation.confirmed_unit_price is not None and 
            self._has_price_discrepancy(original_po.unit_price, confirmation.confirmed_unit_price)):
            discrepancies.append(DiscrepancyDetail(
                field_name="unit_price",
                original_value=float(original_po.unit_price),
                confirmed_value=float(confirmation.confirmed_unit_price),
                difference=self._calculate_price_difference(
                    original_po.unit_price, 
                    confirmation.confirmed_unit_price
                )
            ))
        
        # Check delivery date discrepancy
        if (confirmation.confirmed_delivery_date is not None and 
            confirmation.confirmed_delivery_date != original_po.delivery_date):
            discrepancies.append(DiscrepancyDetail(
                field_name="delivery_date",
                original_value=original_po.delivery_date.isoformat(),
                confirmed_value=confirmation.confirmed_delivery_date.isoformat(),
                difference=self._calculate_date_difference(
                    original_po.delivery_date,
                    confirmation.confirmed_delivery_date
                )
            ))
        
        # Check delivery location discrepancy
        if (confirmation.confirmed_delivery_location is not None and 
            confirmation.confirmed_delivery_location.strip() != original_po.delivery_location.strip()):
            discrepancies.append(DiscrepancyDetail(
                field_name="delivery_location",
                original_value=original_po.delivery_location,
                confirmed_value=confirmation.confirmed_delivery_location,
                difference="Location changed"
            ))
        
        logger.info(
            "Discrepancy detection completed",
            po_id=str(original_po.id),
            discrepancies_found=len(discrepancies),
            discrepancy_types=[d.field_name for d in discrepancies]
        )
        
        return discrepancies
    
    def _has_quantity_discrepancy(self, original: Decimal, confirmed: Decimal) -> bool:
        """Check if there's a significant quantity discrepancy."""
        if original == confirmed:
            return False
        
        # Calculate percentage difference
        percentage_diff = abs(float(confirmed - original)) / float(original)
        return percentage_diff > self.tolerance_percentage
    
    def _has_price_discrepancy(self, original: Decimal, confirmed: Decimal) -> bool:
        """Check if there's a significant price discrepancy."""
        if original == confirmed:
            return False
        
        # Calculate percentage difference
        percentage_diff = abs(float(confirmed - original)) / float(original)
        return percentage_diff > self.tolerance_percentage
    
    def _calculate_quantity_difference(self, original: Decimal, confirmed: Decimal, unit: str) -> str:
        """Calculate human-readable quantity difference."""
        diff = confirmed - original
        percentage = (float(diff) / float(original)) * 100
        
        if diff > 0:
            return f"+{diff:.3f} {unit} (+{percentage:.1f}%)"
        else:
            return f"{diff:.3f} {unit} ({percentage:.1f}%)"
    
    def _calculate_price_difference(self, original: Decimal, confirmed: Decimal) -> str:
        """Calculate human-readable price difference."""
        diff = confirmed - original
        percentage = (float(diff) / float(original)) * 100
        
        if diff > 0:
            return f"+${diff:.2f} (+{percentage:.1f}%)"
        else:
            return f"-${abs(diff):.2f} ({percentage:.1f}%)"
    
    def _calculate_date_difference(self, original: date, confirmed: date) -> str:
        """Calculate human-readable date difference."""
        diff = (confirmed - original).days
        
        if diff > 0:
            return f"{diff} days later"
        elif diff < 0:
            return f"{abs(diff)} days earlier"
        else:
            return "Same date"
    
    def create_discrepancy_reason(self, discrepancies: List[DiscrepancyDetail]) -> str:
        """Create a JSON string describing the discrepancies."""
        discrepancy_data = {
            "total_discrepancies": len(discrepancies),
            "discrepancies": [
                {
                    "field": d.field_name,
                    "original": d.original_value,
                    "confirmed": d.confirmed_value,
                    "difference": d.difference
                }
                for d in discrepancies
            ]
        }
        return json.dumps(discrepancy_data)
    
    def requires_buyer_approval(self, discrepancies: List[DiscrepancyDetail]) -> bool:
        """Determine if the discrepancies require buyer approval."""
        # For now, any discrepancy requires approval
        # In the future, we could have rules for auto-approval of minor changes
        return len(discrepancies) > 0
