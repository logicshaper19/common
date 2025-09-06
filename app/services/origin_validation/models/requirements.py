"""
Certification requirements and domain models.

This module contains data structures for certification requirements
and related domain models.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from .enums import CertificationBody, PalmOilRegion


@dataclass
class CertificationRequirement:
    """Certification requirement for specific regions or products."""
    region: Optional[PalmOilRegion]
    product_category: Optional[str]
    required_certifications: List[CertificationBody]
    recommended_certifications: List[CertificationBody]
    compliance_level: str  # "mandatory", "recommended", "optional"

    def __post_init__(self):
        """Validate requirement data after initialization."""
        valid_levels = ["mandatory", "recommended", "optional"]
        if self.compliance_level not in valid_levels:
            raise ValueError(f"Invalid compliance level: {self.compliance_level}")

    @property
    def all_certifications(self) -> List[CertificationBody]:
        """Get all certifications (required + recommended)."""
        return self.required_certifications + self.recommended_certifications

    @property
    def is_mandatory(self) -> bool:
        """Check if this requirement is mandatory."""
        return self.compliance_level == "mandatory"

    @property
    def is_recommended(self) -> bool:
        """Check if this requirement is recommended."""
        return self.compliance_level == "recommended"

    @property
    def is_optional(self) -> bool:
        """Check if this requirement is optional."""
        return self.compliance_level == "optional"

    def check_compliance(self, certifications: List[str]) -> Dict[str, Any]:
        """
        Check compliance against this requirement.
        
        Args:
            certifications: List of certification strings to check
            
        Returns:
            Compliance result dictionary
        """
        cert_values = [cert.value for cert in self.all_certifications]
        provided_certs = [cert for cert in certifications if cert in cert_values]
        
        # Check required certifications
        required_values = [cert.value for cert in self.required_certifications]
        missing_required = [cert for cert in required_values if cert not in certifications]
        
        # Check recommended certifications
        recommended_values = [cert.value for cert in self.recommended_certifications]
        missing_recommended = [cert for cert in recommended_values if cert not in certifications]
        
        # Calculate compliance score
        if self.is_mandatory:
            # Must have all required certifications
            compliance_score = 1.0 if len(missing_required) == 0 else 0.0
        elif self.is_recommended:
            # Score based on percentage of required + recommended met
            total_possible = len(required_values) + len(recommended_values)
            if total_possible == 0:
                compliance_score = 1.0
            else:
                met_count = len(provided_certs)
                compliance_score = min(met_count / total_possible, 1.0)
        else:  # optional
            # Any certification is good
            compliance_score = 1.0 if len(provided_certs) > 0 else 0.8
        
        return {
            "is_compliant": len(missing_required) == 0,
            "compliance_score": compliance_score,
            "provided_certifications": provided_certs,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "compliance_level": self.compliance_level
        }


@dataclass
class GeographicBoundary:
    """Geographic boundary definition for a palm oil region."""
    region: PalmOilRegion
    name: str
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    description: str
    major_producers: List[str]
    harvest_seasons: List[str]
    quality_standards: List[str]

    def __post_init__(self):
        """Validate boundary data after initialization."""
        if not -90 <= self.min_latitude <= 90:
            raise ValueError("Invalid min_latitude")
        if not -90 <= self.max_latitude <= 90:
            raise ValueError("Invalid max_latitude")
        if not -180 <= self.min_longitude <= 180:
            raise ValueError("Invalid min_longitude")
        if not -180 <= self.max_longitude <= 180:
            raise ValueError("Invalid max_longitude")
        if self.min_latitude >= self.max_latitude:
            raise ValueError("min_latitude must be less than max_latitude")
        if self.min_longitude >= self.max_longitude:
            raise ValueError("min_longitude must be less than max_longitude")

    def contains_point(self, latitude: float, longitude: float) -> bool:
        """
        Check if a point is within this geographic boundary.
        
        Args:
            latitude: Point latitude
            longitude: Point longitude
            
        Returns:
            True if point is within boundary
        """
        return (
            self.min_latitude <= latitude <= self.max_latitude and
            self.min_longitude <= longitude <= self.max_longitude
        )

    def get_center_point(self) -> tuple[float, float]:
        """Get the center point of this boundary."""
        center_lat = (self.min_latitude + self.max_latitude) / 2
        center_lon = (self.min_longitude + self.max_longitude) / 2
        return center_lat, center_lon

    def get_area_km2(self) -> float:
        """
        Approximate area in square kilometers.
        
        Note: This is a rough approximation using rectangular projection.
        For precise calculations, use proper geographic libraries.
        """
        import math
        
        lat_diff = self.max_latitude - self.min_latitude
        lon_diff = self.max_longitude - self.min_longitude
        
        # Convert degrees to kilometers (approximate)
        lat_km = lat_diff * 111.32  # 1 degree latitude ≈ 111.32 km
        
        # Longitude distance varies by latitude
        avg_lat = (self.min_latitude + self.max_latitude) / 2
        lon_km = lon_diff * 111.32 * math.cos(math.radians(avg_lat))
        
        return abs(lat_km * lon_km)


@dataclass
class ProductCategoryRequirement:
    """Certification requirements for a specific product category."""
    category: str
    description: str
    base_requirements: List[CertificationBody]
    premium_requirements: List[CertificationBody]
    regional_overrides: Dict[PalmOilRegion, List[CertificationBody]]

    def get_requirements_for_region(self, region: Optional[PalmOilRegion]) -> List[CertificationBody]:
        """Get certification requirements for a specific region."""
        if region and region in self.regional_overrides:
            return self.regional_overrides[region]
        return self.base_requirements

    def get_premium_requirements_for_region(self, region: Optional[PalmOilRegion]) -> List[CertificationBody]:
        """Get premium certification requirements for a specific region."""
        base = self.get_requirements_for_region(region)
        return base + self.premium_requirements


class CertificationRequirementService:
    """Service for managing certification requirements."""

    def __init__(self, data_provider):
        self.data_provider = data_provider
        self._requirements_cache = {}

    def get_requirements_for_region(
        self,
        region: PalmOilRegion,
        category: str
    ) -> Optional[CertificationRequirement]:
        """
        Get certification requirements for a region and category.

        Args:
            region: Palm oil region
            category: Product category

        Returns:
            Certification requirement or None if not found
        """
        cache_key = f"{region.value}_{category}"

        if cache_key not in self._requirements_cache:
            req_data = self.data_provider.get_regional_requirements(region.value, category)

            if req_data:
                # Convert string certification names to enums
                required_certs = []
                recommended_certs = []

                for cert_name in req_data.get("required", []):
                    try:
                        required_certs.append(CertificationBody(cert_name))
                    except ValueError:
                        continue

                for cert_name in req_data.get("recommended", []):
                    try:
                        recommended_certs.append(CertificationBody(cert_name))
                    except ValueError:
                        continue

                requirement = CertificationRequirement(
                    region=region,
                    product_category=category,
                    required_certifications=required_certs,
                    recommended_certifications=recommended_certs,
                    compliance_level=req_data.get("compliance_level", "optional")
                )
                self._requirements_cache[cache_key] = requirement
            else:
                self._requirements_cache[cache_key] = None

        return self._requirements_cache[cache_key]
