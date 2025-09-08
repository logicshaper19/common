"""
Geographic coordinates validation service.
"""
from typing import Any, List, Dict
import math

from ..domain.models import ValidationResult, GeographicCoordinates
from .base import ValidationService


class CoordinatesValidator(ValidationService):
    """Validator for geographic coordinates."""
    
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """
        Validate geographic coordinates.
        
        Args:
            data: Coordinates data (dict with latitude, longitude, etc.)
            context: Optional context (precision requirements, boundary checks)
            
        Returns:
            List of validation results
        """
        results = []
        
        if not isinstance(data, dict):
            results.append(
                self._create_error(
                    message="Coordinates must be provided as a dictionary",
                    code="INVALID_TYPE"
                )
            )
            return results
        
        # Validate required fields
        results.extend(self._validate_required_field(data, "latitude", float))
        results.extend(self._validate_required_field(data, "longitude", float))
        
        # If basic validation failed, return early
        if any(not result.is_valid for result in results):
            return results
        
        # Validate coordinate ranges
        results.extend(
            self._validate_numeric_range(
                data["latitude"], "latitude", -90.0, 90.0
            )
        )
        results.extend(
            self._validate_numeric_range(
                data["longitude"], "longitude", -180.0, 180.0
            )
        )
        
        # Validate optional fields
        if "accuracy_meters" in data and data["accuracy_meters"] is not None:
            results.extend(
                self._validate_numeric_range(
                    data["accuracy_meters"], "accuracy_meters", 0.0
                )
            )
        
        if "elevation_meters" in data and data["elevation_meters"] is not None:
            results.extend(self._validate_elevation(data["elevation_meters"]))
        
        # Perform advanced validations if basic ones passed
        if all(result.is_valid for result in results):
            results.extend(self._validate_precision(data, context))
            results.extend(self._validate_location_plausibility(data, context))
        
        return results
    
    def _validate_elevation(self, elevation: Any) -> List[ValidationResult]:
        """Validate elevation value."""
        results = []
        
        try:
            elev_value = float(elevation)
            
            # Check for reasonable elevation range (Dead Sea to Everest)
            if elev_value < -500 or elev_value > 9000:
                results.append(
                    self._create_warning(
                        message=f"Elevation {elev_value}m is outside typical range (-500m to 9000m). Please verify.",
                        field="elevation_meters",
                        suggestions=["Double-check elevation measurement", "Ensure correct units (meters)"]
                    )
                )
            
        except (ValueError, TypeError):
            results.append(
                self._create_error(
                    message="Elevation must be a valid number",
                    field="elevation_meters",
                    code="INVALID_NUMBER"
                )
            )
        
        return results
    
    def _validate_precision(
        self, 
        data: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """Validate coordinate precision."""
        results = []
        
        # Default precision requirements
        required_precision = 10.0  # meters
        if context and "required_precision_meters" in context:
            required_precision = context["required_precision_meters"]
        
        accuracy = data.get("accuracy_meters")
        
        if accuracy is None:
            results.append(
                self._create_warning(
                    message="GPS accuracy not provided. Consider including accuracy information.",
                    field="accuracy_meters",
                    suggestions=["Use GPS device that provides accuracy", "Take multiple readings"]
                )
            )
        elif accuracy > required_precision:
            results.append(
                self._create_warning(
                    message=f"GPS accuracy ({accuracy}m) is lower than recommended ({required_precision}m)",
                    field="accuracy_meters",
                    suggestions=[
                        "Use more precise GPS equipment",
                        "Take reading in open area away from buildings",
                        "Wait for better satellite signal"
                    ]
                )
            )
        else:
            results.append(
                self._create_success(
                    message=f"GPS accuracy ({accuracy}m) meets precision requirements"
                )
            )
        
        return results
    
    def _validate_location_plausibility(
        self, 
        data: Dict[str, Any], 
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """Validate that coordinates represent a plausible location."""
        results = []
        
        lat = data["latitude"]
        lon = data["longitude"]
        
        # Check if coordinates are at (0, 0) - often indicates GPS error
        if abs(lat) < 0.001 and abs(lon) < 0.001:
            results.append(
                self._create_warning(
                    message="Coordinates are very close to (0, 0). This may indicate a GPS error.",
                    suggestions=["Verify GPS is working correctly", "Take new reading"]
                )
            )
            return results
        
        # Check if coordinates are in ocean (basic check)
        if self._is_likely_ocean_location(lat, lon):
            results.append(
                self._create_warning(
                    message="Coordinates appear to be in ocean. Please verify location.",
                    suggestions=["Double-check coordinates", "Ensure correct hemisphere"]
                )
            )
        
        # Validate against expected region if provided
        if context and "expected_region" in context:
            region_results = self._validate_region(lat, lon, context["expected_region"])
            results.extend(region_results)
        
        return results
    
    def _is_likely_ocean_location(self, lat: float, lon: float) -> bool:
        """
        Basic check if coordinates are likely in ocean.
        This is a simplified check - in production, you'd use a proper land/ocean dataset.
        """
        # Very basic heuristic - check if far from major landmasses
        # This is not accurate but serves as an example
        
        # Check if in middle of Pacific
        if -30 < lat < 30 and -180 < lon < -120:
            return True
        
        # Check if in middle of Atlantic
        if -30 < lat < 30 and -60 < lon < 20:
            return True
        
        return False
    
    def _validate_region(
        self, 
        lat: float, 
        lon: float, 
        expected_region: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate coordinates are within expected region."""
        results = []
        
        if "bounds" in expected_region:
            bounds = expected_region["bounds"]
            min_lat = bounds.get("min_lat")
            max_lat = bounds.get("max_lat")
            min_lon = bounds.get("min_lon")
            max_lon = bounds.get("max_lon")
            
            if (min_lat and lat < min_lat) or (max_lat and lat > max_lat) or \
               (min_lon and lon < min_lon) or (max_lon and lon > max_lon):
                results.append(
                    self._create_warning(
                        message=f"Coordinates are outside expected region: {expected_region.get('name', 'Unknown')}",
                        suggestions=["Verify coordinates are correct", "Check if different region is intended"]
                    )
                )
        
        if "center" in expected_region and "radius_km" in expected_region:
            center = expected_region["center"]
            radius_km = expected_region["radius_km"]
            
            distance = self._calculate_distance(
                lat, lon, center["lat"], center["lon"]
            )
            
            if distance > radius_km:
                results.append(
                    self._create_warning(
                        message=f"Coordinates are {distance:.1f}km from expected center (max: {radius_km}km)",
                        suggestions=["Verify coordinates", "Check if location is correct"]
                    )
                )
        
        return results
    
    def _calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.
        Returns distance in kilometers.
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        earth_radius_km = 6371.0
        
        return earth_radius_km * c
