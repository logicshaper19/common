"""
Amendment number generation logic.
"""
from sqlalchemy.orm import Session
from app.models.amendment import Amendment
from app.core.logging import get_logger

logger = get_logger(__name__)


class AmendmentNumberGenerator:
    """Generates unique amendment numbers."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate(self, po_number: str) -> str:
        """
        Generate a unique amendment number for a purchase order.
        
        Args:
            po_number: Purchase order number (e.g., 'PO-202409-0001')
            
        Returns:
            Unique amendment number (e.g., 'AMD-PO-202409-0001-001')
        """
        # Count existing amendments for this PO
        existing_count = self.db.query(Amendment).filter(
            Amendment.amendment_number.like(f"AMD-{po_number}-%")
        ).count()
        
        # Generate next amendment number
        amendment_sequence = existing_count + 1
        amendment_number = f"AMD-{po_number}-{amendment_sequence:03d}"
        
        logger.info(
            "Generated amendment number",
            po_number=po_number,
            amendment_number=amendment_number,
            sequence=amendment_sequence
        )
        
        return amendment_number
