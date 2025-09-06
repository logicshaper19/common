"""
Coordinate validation component.

This module handles validation of geographic coordinates including
GPS accuracy, elevation, and regional detection.
"""

from typing import Dict, Any, Optional
from ..models.boundaries import GeographicBoundaryService
from ..models.enums import PalmOilRegion, AccuracyLevel
from .base import BaseValidator, ValidationResult
from app.schemas.confirmation import GeographicCoordinates


class CoordinateValidator(BaseValidator):
    """Validates geographic coordinates."""
    
    def __init__(self, boundary_service: GeographicBoundaryService):
        self.boundary_service = boundary_service
    
    def validate(self, coords: GeographicCoordinates, 
                context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate coordinates with enhanced boundary checking.
        
        Args:
            coords: Geographic coordinates to validate
            context: Validation context
            
        Returns:
            Coordinate validation result
        """
        result = ValidationResult()
        
        # GPS accuracy validation
        accuracy_level = self._validate_accuracy(coords.accuracy_meters, result)
        
        # Regional detection
        detected_region = self.boundary_service.detect_region(coords)
        if detected_region:
            result.add_suggestion(f"Coordinates detected in {detected_region.value} region")
        else:
            result.add_warning("Coordinates outside known palm oil regions")
        
        # Elevation validation
        self._validate_elevation(coords.elevation_meters, result)
        
        # Coordinate precision validation
        self._validate_precision(coords, result)
        
        # Set metadata
        result.update_metadata({
            "detected_region": detected_region.value if detected_region else None,
            "accuracy_level": accuracy_level.value,
            "latitude": coords.latitude,
            "longitude": coords.longitude,
            "accuracy_meters": coords.accuracy_meters,
            "elevation_meters": coords.elevation_meters
        })
        
        return result.to_dict()
    
    def _validate_accuracy(self, accuracy_meters: Optional[float], 
                          result: ValidationResult) -> AccuracyLevel:
        """
        Validate GPS accuracy.
        
        Args:
            accuracy_meters: GPS accuracy in meters
            result: Result object to add messages to
            
        Returns:
            Accuracy level enum
        """
        if accuracy_meters is None:
            result.add_suggestion("Consider providing GPS accuracy information for better validation")
            return AccuracyLevel.MODERATE
        
        accuracy_level = AccuracyLevel.from_accuracy_meters(accuracy_meters)
        
        if accuracy_level == AccuracyLevel.POOR:
            result.add_warning(f"GPS accuracy is poor ({accuracy_meters}m), consider improving location precision")
        elif accuracy_level == AccuracyLevel.LOW:
            result.add_warning(f"GPS accuracy is low ({accuracy_meters}m), better precision recommended")
        elif accuracy_level == AccuracyLevel.MODERATE:
            result.add_suggestion(f"GPS accuracy is moderate ({accuracy_meters}m)")
        elif accuracy_level == AccuracyLevel.GOOD:
            result.add_suggestion(f"Good GPS accuracy ({accuracy_meters}m)")
        elif accuracy_level == AccuracyLevel.EXCELLENT:
            result.add_suggestion(f"Excellent GPS accuracy achieved ({accuracy_meters}m)")
        
        return accuracy_level
    
    def _validate_elevation(self, elevation_meters: Optional[float], 
                           result: ValidationResult) -> None:
        """
        Validate elevation data.
        
        Args:
            elevation_meters: Elevation in meters
            result: Result object to add messages to
        """
        if elevation_meters is None:
            result.add_suggestion("Elevation data not provided - consider including for better validation")
            return
        
        # Check for reasonable elevation ranges for palm oil cultivation
        if elevation_meters < 0:
            result.add_warning("Elevation below sea level - verify coordinate accuracy")
        elif elevation_meters > 1000:
            result.add_warning("High elevation (>1000m) - palm oil cultivation typically occurs at lower elevations")
        elif elevation_meters > 500:
            result.add_suggestion("Moderate elevation - verify suitability for palm oil cultivation")
        else:
            result.add_suggestion("Elevation within typical palm oil cultivation range")
    
    def _validate_precision(self, coords: GeographicCoordinates, 
                           result: ValidationResult) -> None:
        """
        Validate coordinate precision.
        
        Args:
            coords: Geographic coordinates
            result: Result object to add messages to
        """
        # Check decimal precision
        lat_str = str(coords.latitude)
        lon_str = str(coords.longitude)
        
        lat_decimals = len(lat_str.split('.')[-1]) if '.' in lat_str else 0
        lon_decimals = len(lon_str.split('.')[-1]) if '.' in lon_str else 0
        
        min_decimals = min(lat_decimals, lon_decimals)
        
        if min_decimals < 4:
            result.add_warning("Low coordinate precision - consider providing more decimal places")
        elif min_decimals >= 6:
            result.add_suggestion("High coordinate precision provided")
        
        # Check for obviously rounded coordinates (ending in multiple zeros)
        if lat_str.endswith('00') or lon_str.endswith('00'):
            result.add_warning("Coordinates appear to be rounded - verify precision")
