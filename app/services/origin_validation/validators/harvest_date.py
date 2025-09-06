"""
Harvest date validation component.

This module handles validation of harvest dates including freshness,
seasonal compliance, and date range validation.
"""

from typing import Dict, Any, Optional
from datetime import date, timedelta
from .base import BaseValidator, ValidationResult


class HarvestDateValidator(BaseValidator):
    """Validates harvest dates for freshness and compliance."""
    
    def validate(self, harvest_date: Optional[date], 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate harvest date comprehensively.
        
        Args:
            harvest_date: Harvest date to validate
            context: Validation context including product info
            
        Returns:
            Harvest date validation result
        """
        result = ValidationResult()
        product = context.get("product")
        
        if harvest_date is None:
            return self._handle_missing_date(product, result)
        
        # Validate date is not in future
        self._validate_not_future(harvest_date, result)
        
        # Calculate freshness score
        freshness_score = self._calculate_freshness_score(harvest_date)
        
        # Validate freshness based on product type
        self._validate_freshness(harvest_date, freshness_score, product, result)
        
        # Validate seasonal compliance
        seasonal_compliance = self._validate_seasonal_compliance(
            harvest_date, context.get("detected_region"), result
        )
        
        # Set metadata
        result.update_metadata({
            "harvest_date": harvest_date.isoformat(),
            "days_since_harvest": (date.today() - harvest_date).days,
            "freshness_score": freshness_score,
            "seasonal_compliance": seasonal_compliance,
            "date_provided": True
        })
        
        return result.to_dict()
    
    def _handle_missing_date(self, product: Any, result: ValidationResult) -> Dict[str, Any]:
        """Handle case where harvest date is not provided."""
        if hasattr(product, 'category') and product.category == "raw_material":
            result.add_warning("Harvest date is recommended for raw materials")
        else:
            result.add_suggestion("Harvest date not provided - consider including for better traceability")
        
        result.update_metadata({
            "date_provided": False,
            "freshness_score": 0.5,  # Neutral score when date not provided
            "seasonal_compliance": True  # Assume compliant if no date to check
        })
        
        return result.to_dict()
    
    def _validate_not_future(self, harvest_date: date, result: ValidationResult) -> None:
        """Validate that harvest date is not in the future."""
        today = date.today()
        
        if harvest_date > today:
            result.add_error("Harvest date cannot be in the future")
        elif harvest_date == today:
            result.add_suggestion("Harvest date is today - verify timing")
    
    def _calculate_freshness_score(self, harvest_date: date) -> float:
        """
        Calculate freshness score based on days since harvest.
        
        Args:
            harvest_date: Date of harvest
            
        Returns:
            Freshness score (0-1, higher is fresher)
        """
        days_since_harvest = (date.today() - harvest_date).days
        
        if days_since_harvest < 0:
            return 0.0  # Future date
        elif days_since_harvest <= 30:
            return 1.0  # Very fresh
        elif days_since_harvest <= 90:
            return 0.8  # Fresh
        elif days_since_harvest <= 180:
            return 0.6  # Acceptable
        elif days_since_harvest <= 365:
            return 0.4  # Older but acceptable
        elif days_since_harvest <= 730:
            return 0.2  # Old
        else:
            return 0.1  # Very old
    
    def _validate_freshness(
        self, 
        harvest_date: date, 
        freshness_score: float, 
        product: Any, 
        result: ValidationResult
    ) -> None:
        """Validate freshness based on product requirements."""
        days_since_harvest = (date.today() - harvest_date).days
        
        # Different freshness requirements based on product category
        if hasattr(product, 'category'):
            if product.category == "raw_material":
                if days_since_harvest > 365:
                    result.add_warning(f"Raw material is {days_since_harvest} days old - verify quality")
                elif days_since_harvest > 180:
                    result.add_suggestion(f"Raw material is {days_since_harvest} days old - consider freshness impact")
                elif days_since_harvest <= 30:
                    result.add_suggestion("Excellent freshness for raw material")
            
            elif product.category == "processed":
                if days_since_harvest > 730:
                    result.add_warning(f"Processed product source is {days_since_harvest} days old")
                elif days_since_harvest <= 90:
                    result.add_suggestion("Good freshness for processed product source")
        
        # General freshness feedback
        if freshness_score >= 0.8:
            result.add_suggestion("Excellent product freshness")
        elif freshness_score >= 0.6:
            result.add_suggestion("Good product freshness")
        elif freshness_score >= 0.4:
            result.add_suggestion("Acceptable product freshness")
        elif freshness_score >= 0.2:
            result.add_warning("Product freshness is declining")
        else:
            result.add_warning("Poor product freshness - verify quality")
    
    def _validate_seasonal_compliance(
        self, 
        harvest_date: date, 
        detected_region: Optional[str], 
        result: ValidationResult
    ) -> bool:
        """
        Validate seasonal compliance for the region.
        
        Args:
            harvest_date: Date of harvest
            detected_region: Detected palm oil region
            result: Result object to add messages to
            
        Returns:
            True if seasonally compliant
        """
        if not detected_region:
            result.add_suggestion("Cannot validate seasonal compliance - region not detected")
            return True
        
        # Most palm oil regions have year-round harvest, but some have seasonal patterns
        seasonal_regions = {
            "Central America": self._validate_central_america_season,
            "South America": self._validate_south_america_season
        }
        
        validator = seasonal_regions.get(detected_region)
        if validator:
            return validator(harvest_date, result)
        else:
            # Year-round harvest regions
            result.add_suggestion(f"Year-round harvest region ({detected_region}) - no seasonal restrictions")
            return True
    
    def _validate_central_america_season(self, harvest_date: date, result: ValidationResult) -> bool:
        """Validate Central America seasonal patterns."""
        # Central America typically has dry season harvest (December-April)
        month = harvest_date.month
        
        if month in [12, 1, 2, 3, 4]:
            result.add_suggestion("Harvest during optimal dry season")
            return True
        elif month in [5, 6, 11]:
            result.add_suggestion("Harvest during transition period")
            return True
        else:
            result.add_warning("Harvest during wet season - verify quality impact")
            return False
    
    def _validate_south_america_season(self, harvest_date: date, result: ValidationResult) -> bool:
        """Validate South America seasonal patterns."""
        # South America has varied patterns, but generally avoid peak wet season
        month = harvest_date.month
        
        if month in [6, 7, 8, 9]:
            result.add_suggestion("Harvest during favorable dry season")
            return True
        elif month in [12, 1, 2]:
            result.add_warning("Harvest during wet season - monitor quality")
            return False
        else:
            result.add_suggestion("Harvest during acceptable period")
            return True
    
    def get_optimal_harvest_window(self, region: Optional[str]) -> Dict[str, Any]:
        """
        Get optimal harvest window information for a region.
        
        Args:
            region: Palm oil region
            
        Returns:
            Harvest window information
        """
        if not region:
            return {
                "optimal_months": list(range(1, 13)),
                "description": "Year-round harvest possible",
                "restrictions": []
            }
        
        windows = {
            "Central America": {
                "optimal_months": [12, 1, 2, 3, 4],
                "description": "Dry season harvest preferred",
                "restrictions": ["Avoid peak wet season (July-October)"]
            },
            "South America": {
                "optimal_months": [6, 7, 8, 9],
                "description": "Dry season harvest optimal",
                "restrictions": ["Monitor quality during wet season (December-February)"]
            }
        }
        
        return windows.get(region, {
            "optimal_months": list(range(1, 13)),
            "description": "Year-round harvest typical",
            "restrictions": []
        })
