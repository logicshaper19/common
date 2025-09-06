"""
Purchase order number generator.

This module handles the generation of unique purchase order numbers
with configurable formats and sequence management.
"""

from typing import Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.purchase_order import PurchaseOrder
from app.core.logging import get_logger

logger = get_logger(__name__)


class PONumberGenerator:
    """Generates unique purchase order numbers."""
    
    def __init__(self, db: Session):
        self.db = db
        self.default_format = "PO-{year}{month:02d}-{sequence:04d}"
    
    def generate(
        self, 
        format_template: Optional[str] = None,
        target_date: Optional[datetime] = None
    ) -> str:
        """
        Generate a unique purchase order number.
        
        Args:
            format_template: Optional custom format template
            target_date: Optional date for the PO (defaults to today)
            
        Returns:
            Unique PO number string
        """
        if not target_date:
            target_date = datetime.now()
        
        if not format_template:
            format_template = self.default_format
        
        # Get the next sequence number for the date
        sequence = self.get_next_sequence_number(target_date)
        
        # Generate the PO number
        po_number = format_template.format(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day,
            sequence=sequence,
            date=target_date.strftime("%Y%m%d"),
            short_year=target_date.year % 100
        )
        
        logger.info(
            "Generated PO number",
            po_number=po_number,
            sequence=sequence,
            date=target_date.date().isoformat()
        )
        
        return po_number
    
    def get_next_sequence_number(self, target_date: datetime) -> int:
        """
        Get the next sequence number for a given date.
        
        Args:
            target_date: Date to get sequence for
            
        Returns:
            Next sequence number
        """
        # Get the count of POs created on the target date
        start_of_day = datetime.combine(target_date.date(), datetime.min.time())
        end_of_day = datetime.combine(target_date.date(), datetime.max.time())
        
        count = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.created_at >= start_of_day,
                PurchaseOrder.created_at <= end_of_day
            )
        ).count()
        
        # Return next sequence number
        return count + 1
    
    def validate_po_number_format(self, format_template: str) -> Dict[str, Any]:
        """
        Validate a PO number format template.
        
        Args:
            format_template: Format template to validate
            
        Returns:
            Validation result with is_valid flag and details
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "sample": None
        }
        
        try:
            # Test the format with sample data
            sample_date = datetime(2024, 1, 15)
            sample_sequence = 42
            
            sample_po_number = format_template.format(
                year=sample_date.year,
                month=sample_date.month,
                day=sample_date.day,
                sequence=sample_sequence,
                date=sample_date.strftime("%Y%m%d"),
                short_year=sample_date.year % 100
            )
            
            validation_result["sample"] = sample_po_number
            
            # Check for reasonable length
            if len(sample_po_number) > 50:
                validation_result["warnings"].append("PO number may be too long")
            
            if len(sample_po_number) < 5:
                validation_result["warnings"].append("PO number may be too short")
            
            # Check for required components
            if "{sequence" not in format_template:
                validation_result["errors"].append("Format must include sequence number")
                validation_result["is_valid"] = False
            
        except KeyError as e:
            validation_result["errors"].append(f"Invalid format placeholder: {e}")
            validation_result["is_valid"] = False
        except Exception as e:
            validation_result["errors"].append(f"Format validation error: {str(e)}")
            validation_result["is_valid"] = False
        
        return validation_result
    
    def generate_with_prefix(
        self, 
        prefix: str, 
        target_date: Optional[datetime] = None
    ) -> str:
        """
        Generate PO number with custom prefix.
        
        Args:
            prefix: Custom prefix for the PO number
            target_date: Optional date for the PO
            
        Returns:
            PO number with custom prefix
        """
        if not target_date:
            target_date = datetime.now()
        
        sequence = self.get_next_sequence_number(target_date)
        
        po_number = f"{prefix}-{target_date.year}{target_date.month:02d}-{sequence:04d}"
        
        logger.info(
            "Generated PO number with custom prefix",
            po_number=po_number,
            prefix=prefix,
            sequence=sequence
        )
        
        return po_number
    
    def generate_sequential(self, prefix: str = "PO") -> str:
        """
        Generate simple sequential PO number without date.
        
        Args:
            prefix: Prefix for the PO number
            
        Returns:
            Sequential PO number
        """
        # Get total count of all POs
        total_count = self.db.query(PurchaseOrder).count()
        next_number = total_count + 1
        
        po_number = f"{prefix}-{next_number:06d}"
        
        logger.info(
            "Generated sequential PO number",
            po_number=po_number,
            sequence=next_number
        )
        
        return po_number
    
    def check_po_number_exists(self, po_number: str) -> bool:
        """
        Check if a PO number already exists.
        
        Args:
            po_number: PO number to check
            
        Returns:
            True if exists, False otherwise
        """
        existing = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.po_number == po_number
        ).first()
        
        return existing is not None
    
    def generate_unique(
        self, 
        format_template: Optional[str] = None,
        target_date: Optional[datetime] = None,
        max_attempts: int = 10
    ) -> str:
        """
        Generate a guaranteed unique PO number.
        
        Args:
            format_template: Optional custom format template
            target_date: Optional date for the PO
            max_attempts: Maximum attempts to generate unique number
            
        Returns:
            Unique PO number
            
        Raises:
            RuntimeError: If unable to generate unique number after max attempts
        """
        for attempt in range(max_attempts):
            po_number = self.generate(format_template, target_date)
            
            if not self.check_po_number_exists(po_number):
                return po_number
            
            logger.warning(
                "Generated PO number already exists, retrying",
                po_number=po_number,
                attempt=attempt + 1
            )
            
            # For retry, add a small offset to the target date
            if target_date:
                target_date = target_date.replace(second=target_date.second + 1)
        
        raise RuntimeError(f"Unable to generate unique PO number after {max_attempts} attempts")
    
    def get_format_options(self) -> Dict[str, str]:
        """
        Get available format options for PO numbers.
        
        Returns:
            Dictionary of format names and templates
        """
        return {
            "default": "PO-{year}{month:02d}-{sequence:04d}",
            "simple": "PO-{sequence:06d}",
            "date_based": "PO-{date}-{sequence:03d}",
            "year_based": "PO-{year}-{sequence:05d}",
            "short": "{short_year}{month:02d}{sequence:04d}",
            "verbose": "PO-{year}-{month:02d}-{day:02d}-{sequence:04d}"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get PO number generation statistics.
        
        Returns:
            Statistics about PO number generation
        """
        today = datetime.now().date()
        
        # Count POs created today
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        today_count = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.created_at >= start_of_day,
                PurchaseOrder.created_at <= end_of_day
            )
        ).count()
        
        # Count POs created this month
        start_of_month = datetime(today.year, today.month, 1)
        month_count = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.created_at >= start_of_month
        ).count()
        
        # Total count
        total_count = self.db.query(PurchaseOrder).count()
        
        # Next sequence numbers
        next_daily_sequence = self.get_next_sequence_number(datetime.now())
        
        return {
            "total_pos_created": total_count,
            "pos_created_today": today_count,
            "pos_created_this_month": month_count,
            "next_daily_sequence": next_daily_sequence,
            "current_date": today.isoformat()
        }
