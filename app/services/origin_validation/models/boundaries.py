"""
Geographic boundary services for origin validation.

This module provides services for detecting palm oil regions from coordinates
and managing geographic boundaries.
"""

from typing import Optional, List, Dict, Any
from ..services.data_provider import OriginDataProvider
from .enums import PalmOilRegion
from .requirements import GeographicBoundary
from app.schemas.confirmation import GeographicCoordinates


class GeographicBoundaryService:
    """Service for managing geographic boundaries and region detection."""
    
    def __init__(self, data_provider: OriginDataProvider):
        self.data_provider = data_provider
        self._boundaries_cache: Optional[Dict[PalmOilRegion, GeographicBoundary]] = None
    
    @property
    def boundaries(self) -> Dict[PalmOilRegion, GeographicBoundary]:
        """Get cached geographic boundaries."""
        if self._boundaries_cache is None:
            self._boundaries_cache = self._load_boundaries()
        return self._boundaries_cache
    
    def detect_region(self, coords: GeographicCoordinates) -> Optional[PalmOilRegion]:
        """
        Detect palm oil region from coordinates.
        
        Args:
            coords: Geographic coordinates to check
            
        Returns:
            Detected palm oil region or None if outside known regions
        """
        for region, boundary in self.boundaries.items():
            if boundary.contains_point(coords.latitude, coords.longitude):
                return region
        return None
    
    def get_boundary(self, region: PalmOilRegion) -> Optional[GeographicBoundary]:
        """
        Get geographic boundary for a specific region.
        
        Args:
            region: Palm oil region
            
        Returns:
            Geographic boundary or None if not found
        """
        return self.boundaries.get(region)
    
    def get_regions_near_point(
        self, 
        coords: GeographicCoordinates, 
        tolerance_degrees: float = 1.0
    ) -> List[PalmOilRegion]:
        """
        Get regions near a point within tolerance.
        
        Args:
            coords: Geographic coordinates
            tolerance_degrees: Tolerance in degrees
            
        Returns:
            List of nearby regions
        """
        nearby_regions = []
        
        for region, boundary in self.boundaries.items():
            # Check if point is within expanded boundary
            expanded_boundary = GeographicBoundary(
                region=region,
                name=boundary.name,
                min_latitude=boundary.min_latitude - tolerance_degrees,
                max_latitude=boundary.max_latitude + tolerance_degrees,
                min_longitude=boundary.min_longitude - tolerance_degrees,
                max_longitude=boundary.max_longitude + tolerance_degrees,
                description=boundary.description,
                major_producers=boundary.major_producers,
                harvest_seasons=boundary.harvest_seasons,
                quality_standards=boundary.quality_standards
            )
            
            if expanded_boundary.contains_point(coords.latitude, coords.longitude):
                nearby_regions.append(region)
        
        return nearby_regions
    
    def calculate_distance_to_region(
        self, 
        coords: GeographicCoordinates, 
        region: PalmOilRegion
    ) -> Optional[float]:
        """
        Calculate approximate distance to region boundary.
        
        Args:
            coords: Geographic coordinates
            region: Target region
            
        Returns:
            Approximate distance in kilometers or None if region not found
        """
        boundary = self.get_boundary(region)
        if not boundary:
            return None
        
        # Simple distance calculation to nearest boundary edge
        lat_dist = 0.0
        lon_dist = 0.0
        
        if coords.latitude < boundary.min_latitude:
            lat_dist = boundary.min_latitude - coords.latitude
        elif coords.latitude > boundary.max_latitude:
            lat_dist = coords.latitude - boundary.max_latitude
        
        if coords.longitude < boundary.min_longitude:
            lon_dist = boundary.min_longitude - coords.longitude
        elif coords.longitude > boundary.max_longitude:
            lon_dist = coords.longitude - boundary.max_longitude
        
        # Convert degrees to approximate kilometers
        lat_km = lat_dist * 111.32  # 1 degree latitude ≈ 111.32 km
        lon_km = lon_dist * 111.32 * abs(coords.latitude) / 90  # Longitude varies by latitude
        
        return (lat_km ** 2 + lon_km ** 2) ** 0.5
    
    def get_region_info(self, region: PalmOilRegion) -> Dict[str, Any]:
        """
        Get comprehensive information about a region.
        
        Args:
            region: Palm oil region
            
        Returns:
            Region information dictionary
        """
        boundary = self.get_boundary(region)
        if not boundary:
            return {}
        
        return {
            "region": region.value,
            "name": boundary.name,
            "description": boundary.description,
            "major_producers": boundary.major_producers,
            "harvest_seasons": boundary.harvest_seasons,
            "quality_standards": boundary.quality_standards,
            "area_km2": boundary.get_area_km2(),
            "center_point": boundary.get_center_point(),
            "boundaries": {
                "min_latitude": boundary.min_latitude,
                "max_latitude": boundary.max_latitude,
                "min_longitude": boundary.min_longitude,
                "max_longitude": boundary.max_longitude
            }
        }
    
    def _load_boundaries(self) -> Dict[PalmOilRegion, GeographicBoundary]:
        """Load geographic boundaries from configuration."""
        boundaries = {}
        regions_config = self.data_provider.regions
        
        for region_key, config in regions_config.items():
            try:
                region = PalmOilRegion(region_key)
                boundary = GeographicBoundary(
                    region=region,
                    name=config["name"],
                    min_latitude=config["min_latitude"],
                    max_latitude=config["max_latitude"],
                    min_longitude=config["min_longitude"],
                    max_longitude=config["max_longitude"],
                    description=config["description"],
                    major_producers=config["major_producers"],
                    harvest_seasons=config["harvest_seasons"],
                    quality_standards=config["quality_standards"]
                )
                boundaries[region] = boundary
            except (ValueError, KeyError) as e:
                # Log error but continue loading other boundaries
                print(f"Error loading boundary for {region_key}: {e}")
                continue
        
        return boundaries
    
    def validate_boundary_coverage(self) -> Dict[str, Any]:
        """
        Validate that all regions have proper boundary coverage.
        
        Returns:
            Validation report
        """
        report = {
            "total_regions": len(PalmOilRegion),
            "configured_regions": len(self.boundaries),
            "missing_regions": [],
            "invalid_boundaries": [],
            "coverage_percentage": 0.0
        }
        
        # Check for missing regions
        configured_regions = set(self.boundaries.keys())
        all_regions = set(PalmOilRegion)
        missing = all_regions - configured_regions
        report["missing_regions"] = [r.value for r in missing]
        
        # Check for invalid boundaries
        for region, boundary in self.boundaries.items():
            try:
                # Test boundary validity
                boundary.get_area_km2()
                boundary.get_center_point()
            except Exception as e:
                report["invalid_boundaries"].append({
                    "region": region.value,
                    "error": str(e)
                })
        
        # Calculate coverage
        report["coverage_percentage"] = (len(self.boundaries) / len(PalmOilRegion)) * 100
        
        return report
