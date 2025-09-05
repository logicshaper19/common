"""
Enhanced origin data capture and validation service.
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from dataclasses import dataclass
from enum import Enum

from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.schemas.confirmation import GeographicCoordinates, OriginDataCapture
from app.core.logging import get_logger

logger = get_logger(__name__)


class CertificationBody(str, Enum):
    """Recognized certification bodies for palm oil supply chain."""
    RSPO = "RSPO"  # Roundtable on Sustainable Palm Oil
    NDPE = "NDPE"  # No Deforestation, No Peat, No Exploitation
    ISPO = "ISPO"  # Indonesian Sustainable Palm Oil
    MSPO = "MSPO"  # Malaysian Sustainable Palm Oil
    RTRS = "RTRS"  # Round Table on Responsible Soy
    ISCC = "ISCC"  # International Sustainability and Carbon Certification
    SAN = "SAN"    # Sustainable Agriculture Network
    UTZ = "UTZ"    # UTZ Certified
    RAINFOREST_ALLIANCE = "Rainforest Alliance"
    ORGANIC = "Organic"
    FAIR_TRADE = "Fair Trade"
    NON_GMO = "Non-GMO"
    SUSTAINABLE = "Sustainable"
    TRACEABLE = "Traceable"


class PalmOilRegion(str, Enum):
    """Major palm oil producing regions with geographic boundaries."""
    SOUTHEAST_ASIA = "Southeast Asia"
    WEST_AFRICA = "West Africa"
    CENTRAL_AFRICA = "Central Africa"
    SOUTH_AMERICA = "South America"
    CENTRAL_AMERICA = "Central America"


@dataclass
class GeographicBoundary:
    """Geographic boundary definition for palm oil regions."""
    name: str
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    description: str


@dataclass
class CertificationRequirement:
    """Certification requirement for specific regions or products."""
    region: Optional[PalmOilRegion]
    product_category: Optional[str]
    required_certifications: List[CertificationBody]
    recommended_certifications: List[CertificationBody]
    compliance_level: str  # "mandatory", "recommended", "optional"


@dataclass
class OriginDataValidationResult:
    """Comprehensive origin data validation result."""
    is_valid: bool
    coordinate_validation: Dict[str, Any]
    certification_validation: Dict[str, Any]
    harvest_date_validation: Dict[str, Any]
    regional_compliance: Dict[str, Any]
    quality_score: float
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    compliance_status: str


class OriginDataValidationService:
    """Enhanced service for origin data capture and validation."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Define palm oil producing regions with geographic boundaries
        self.PALM_OIL_REGIONS = {
            PalmOilRegion.SOUTHEAST_ASIA: GeographicBoundary(
                name="Southeast Asia",
                min_latitude=-10.0,
                max_latitude=20.0,
                min_longitude=90.0,
                max_longitude=140.0,
                description="Indonesia, Malaysia, Thailand, Philippines"
            ),
            PalmOilRegion.WEST_AFRICA: GeographicBoundary(
                name="West Africa",
                min_latitude=-5.0,
                max_latitude=15.0,
                min_longitude=-20.0,
                max_longitude=15.0,
                description="Nigeria, Ghana, Ivory Coast, Cameroon"
            ),
            PalmOilRegion.CENTRAL_AFRICA: GeographicBoundary(
                name="Central Africa",
                min_latitude=-10.0,
                max_latitude=10.0,
                min_longitude=10.0,
                max_longitude=30.0,
                description="Democratic Republic of Congo, Central African Republic"
            ),
            PalmOilRegion.SOUTH_AMERICA: GeographicBoundary(
                name="South America",
                min_latitude=-20.0,
                max_latitude=10.0,
                min_longitude=-80.0,
                max_longitude=-35.0,
                description="Colombia, Ecuador, Brazil, Peru"
            ),
            PalmOilRegion.CENTRAL_AMERICA: GeographicBoundary(
                name="Central America",
                min_latitude=5.0,
                max_latitude=20.0,
                min_longitude=-95.0,
                max_longitude=-75.0,
                description="Guatemala, Honduras, Costa Rica"
            )
        }
        
        # Define certification requirements by region
        self.CERTIFICATION_REQUIREMENTS = {
            PalmOilRegion.SOUTHEAST_ASIA: CertificationRequirement(
                region=PalmOilRegion.SOUTHEAST_ASIA,
                product_category="raw_material",
                required_certifications=[CertificationBody.RSPO],
                recommended_certifications=[CertificationBody.NDPE, CertificationBody.ISPO, CertificationBody.MSPO],
                compliance_level="recommended"
            ),
            PalmOilRegion.WEST_AFRICA: CertificationRequirement(
                region=PalmOilRegion.WEST_AFRICA,
                product_category="raw_material",
                required_certifications=[CertificationBody.RSPO],
                recommended_certifications=[CertificationBody.RAINFOREST_ALLIANCE, CertificationBody.SUSTAINABLE],
                compliance_level="recommended"
            ),
            PalmOilRegion.CENTRAL_AFRICA: CertificationRequirement(
                region=PalmOilRegion.CENTRAL_AFRICA,
                product_category="raw_material",
                required_certifications=[],
                recommended_certifications=[CertificationBody.RSPO, CertificationBody.RAINFOREST_ALLIANCE],
                compliance_level="optional"
            ),
            PalmOilRegion.SOUTH_AMERICA: CertificationRequirement(
                region=PalmOilRegion.SOUTH_AMERICA,
                product_category="raw_material",
                required_certifications=[],
                recommended_certifications=[CertificationBody.RSPO, CertificationBody.RAINFOREST_ALLIANCE, CertificationBody.RTRS],
                compliance_level="recommended"
            ),
            PalmOilRegion.CENTRAL_AMERICA: CertificationRequirement(
                region=PalmOilRegion.CENTRAL_AMERICA,
                product_category="raw_material",
                required_certifications=[],
                recommended_certifications=[CertificationBody.RAINFOREST_ALLIANCE, CertificationBody.SUSTAINABLE],
                compliance_level="optional"
            )
        }
        
        # High-value certifications for quality scoring
        self.HIGH_VALUE_CERTIFICATIONS = {
            CertificationBody.RSPO,
            CertificationBody.NDPE,
            CertificationBody.ISPO,
            CertificationBody.MSPO,
            CertificationBody.RAINFOREST_ALLIANCE,
            CertificationBody.ORGANIC,
            CertificationBody.FAIR_TRADE
        }
    
    def validate_comprehensive_origin_data(
        self,
        origin_data: OriginDataCapture,
        product_id: UUID,
        purchase_order_id: Optional[UUID] = None
    ) -> OriginDataValidationResult:
        """
        Perform comprehensive validation of origin data.
        
        Args:
            origin_data: Origin data to validate
            product_id: Product UUID for context-specific validation
            purchase_order_id: Optional purchase order UUID for additional context
            
        Returns:
            Comprehensive validation result
        """
        logger.info(
            "Starting comprehensive origin data validation",
            product_id=str(product_id),
            po_id=str(purchase_order_id) if purchase_order_id else None
        )
        
        # Get product information
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return OriginDataValidationResult(
                is_valid=False,
                coordinate_validation={},
                certification_validation={},
                harvest_date_validation={},
                regional_compliance={},
                quality_score=0.0,
                errors=["Product not found"],
                warnings=[],
                suggestions=[],
                compliance_status="invalid"
            )
        
        # Validate geographic coordinates
        coord_validation = self._validate_geographic_coordinates(origin_data.geographic_coordinates)
        
        # Determine region from coordinates
        detected_region = self._detect_palm_oil_region(origin_data.geographic_coordinates)
        
        # Validate certifications
        cert_validation = self._validate_certifications_comprehensive(
            origin_data.certifications,
            product,
            detected_region
        )
        
        # Validate harvest date
        harvest_validation = self._validate_harvest_date_comprehensive(
            origin_data.harvest_date,
            product
        )
        
        # Validate regional compliance
        regional_compliance = self._validate_regional_compliance(
            origin_data,
            detected_region,
            product
        )
        
        # Calculate quality score
        quality_score = self._calculate_origin_data_quality_score(
            coord_validation,
            cert_validation,
            harvest_validation,
            regional_compliance
        )
        
        # Compile all errors, warnings, and suggestions
        all_errors = []
        all_warnings = []
        all_suggestions = []
        
        for validation in [coord_validation, cert_validation, harvest_validation, regional_compliance]:
            all_errors.extend(validation.get("errors", []))
            all_warnings.extend(validation.get("warnings", []))
            all_suggestions.extend(validation.get("suggestions", []))
        
        # Determine overall compliance status
        compliance_status = self._determine_overall_compliance_status(
            coord_validation,
            cert_validation,
            harvest_validation,
            regional_compliance,
            quality_score
        )
        
        is_valid = len(all_errors) == 0
        
        result = OriginDataValidationResult(
            is_valid=is_valid,
            coordinate_validation=coord_validation,
            certification_validation=cert_validation,
            harvest_date_validation=harvest_validation,
            regional_compliance=regional_compliance,
            quality_score=quality_score,
            errors=all_errors,
            warnings=all_warnings,
            suggestions=all_suggestions,
            compliance_status=compliance_status
        )
        
        logger.info(
            "Origin data validation completed",
            product_id=str(product_id),
            is_valid=is_valid,
            quality_score=quality_score,
            compliance_status=compliance_status,
            detected_region=detected_region.value if detected_region else None,
            errors_count=len(all_errors),
            warnings_count=len(all_warnings)
        )
        
        return result
    
    def _validate_geographic_coordinates(self, coords: GeographicCoordinates) -> Dict[str, Any]:
        """
        Validate geographic coordinates with enhanced boundary checking.
        
        Args:
            coords: Geographic coordinates to validate
            
        Returns:
            Validation result dictionary
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation (latitude/longitude ranges) is handled by Pydantic
        
        # Check GPS accuracy
        if coords.accuracy_meters:
            if coords.accuracy_meters > 100:
                warnings.append("GPS accuracy is low (>100m), consider improving location precision")
            elif coords.accuracy_meters > 50:
                warnings.append("GPS accuracy is moderate (>50m), better precision recommended")
            elif coords.accuracy_meters <= 5:
                suggestions.append("Excellent GPS accuracy achieved")
        else:
            suggestions.append("Consider providing GPS accuracy information for better validation")
        
        # Check if coordinates are in any palm oil producing region
        detected_region = self._detect_palm_oil_region(coords)
        
        if not detected_region:
            warnings.append(
                "Coordinates are outside known palm oil producing regions. "
                "Please verify location accuracy."
            )
            suggestions.append(
                "Major palm oil regions: Southeast Asia, West Africa, Central Africa, "
                "South America, Central America"
            )
        else:
            suggestions.append(f"Location detected in {detected_region.value} palm oil region")
        
        # Check elevation if provided
        if coords.elevation_meters is not None:
            if coords.elevation_meters > 1000:
                warnings.append("Elevation is high for palm oil cultivation (>1000m)")
            elif coords.elevation_meters < 0:
                warnings.append("Elevation below sea level is unusual for palm oil cultivation")
        
        return {
            "is_valid": len(errors) == 0,
            "detected_region": detected_region.value if detected_region else None,
            "accuracy_level": self._get_accuracy_level(coords.accuracy_meters),
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _detect_palm_oil_region(self, coords: GeographicCoordinates) -> Optional[PalmOilRegion]:
        """
        Detect which palm oil region the coordinates fall into.

        Args:
            coords: Geographic coordinates

        Returns:
            Detected palm oil region or None
        """
        for region, boundary in self.PALM_OIL_REGIONS.items():
            if (boundary.min_latitude <= coords.latitude <= boundary.max_latitude and
                boundary.min_longitude <= coords.longitude <= boundary.max_longitude):
                return region
        return None

    def _get_accuracy_level(self, accuracy_meters: Optional[float]) -> str:
        """Get accuracy level description."""
        if accuracy_meters is None:
            return "unknown"
        elif accuracy_meters <= 5:
            return "excellent"
        elif accuracy_meters <= 10:
            return "very_good"
        elif accuracy_meters <= 25:
            return "good"
        elif accuracy_meters <= 50:
            return "moderate"
        elif accuracy_meters <= 100:
            return "low"
        else:
            return "very_low"

    def _validate_certifications_comprehensive(
        self,
        certifications: List[str],
        product: Product,
        detected_region: Optional[PalmOilRegion]
    ) -> Dict[str, Any]:
        """
        Comprehensive certification validation.

        Args:
            certifications: List of claimed certifications
            product: Product information
            detected_region: Detected palm oil region

        Returns:
            Certification validation result
        """
        errors = []
        warnings = []
        suggestions = []

        # Validate against recognized certification bodies
        valid_certifications = {cert.value for cert in CertificationBody}
        recognized_certs = []
        unrecognized_certs = []

        for cert in certifications:
            if cert in valid_certifications:
                recognized_certs.append(cert)
            else:
                unrecognized_certs.append(cert)
                warnings.append(f"Unrecognized certification: {cert}")

        # Check regional certification requirements
        if detected_region and detected_region in self.CERTIFICATION_REQUIREMENTS:
            regional_req = self.CERTIFICATION_REQUIREMENTS[detected_region]

            # Check required certifications
            missing_required = []
            for req_cert in regional_req.required_certifications:
                if req_cert.value not in recognized_certs:
                    missing_required.append(req_cert.value)

            if missing_required and regional_req.compliance_level == "mandatory":
                errors.extend([f"Missing mandatory certification for {detected_region.value}: {cert}"
                              for cert in missing_required])
            elif missing_required and regional_req.compliance_level == "recommended":
                warnings.extend([f"Missing recommended certification for {detected_region.value}: {cert}"
                               for cert in missing_required])

            # Check recommended certifications
            missing_recommended = []
            for rec_cert in regional_req.recommended_certifications:
                if rec_cert.value not in recognized_certs:
                    missing_recommended.append(rec_cert.value)

            if missing_recommended:
                suggestions.extend([f"Consider adding recommended certification: {cert}"
                                 for cert in missing_recommended])

        # Check product-specific requirements
        if product.origin_data_requirements:
            product_required = product.origin_data_requirements.get("required_certifications", [])
            for req_cert in product_required:
                if req_cert not in recognized_certs:
                    errors.append(f"Missing product-required certification: {req_cert}")

        # Calculate certification quality score
        high_value_count = sum(1 for cert in recognized_certs
                              if cert in {c.value for c in self.HIGH_VALUE_CERTIFICATIONS})
        quality_score = min(high_value_count / 3.0, 1.0)  # Max score with 3+ high-value certs

        # Provide suggestions for improvement
        if not certifications:
            suggestions.append("Consider adding certifications like RSPO, NDPE, or ISPO for better traceability")
        elif quality_score < 0.5:
            suggestions.append("Consider adding more high-value certifications to improve quality score")

        return {
            "is_valid": len(errors) == 0,
            "recognized_certifications": recognized_certs,
            "unrecognized_certifications": unrecognized_certs,
            "quality_score": quality_score,
            "regional_compliance": detected_region.value if detected_region else None,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _validate_harvest_date_comprehensive(
        self,
        harvest_date: Optional[date],
        product: Product
    ) -> Dict[str, Any]:
        """
        Comprehensive harvest date validation.

        Args:
            harvest_date: Harvest date to validate
            product: Product information

        Returns:
            Harvest date validation result
        """
        errors = []
        warnings = []
        suggestions = []

        if harvest_date is None:
            if product.category == "raw_material":
                warnings.append("Harvest date is recommended for raw materials")
            return {
                "is_valid": True,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }

        today = date.today()

        # Check if harvest date is in the future
        if harvest_date > today:
            errors.append("Harvest date cannot be in the future")

        # Check if harvest date is too old
        days_old = (today - harvest_date).days

        if product.category == "raw_material":
            if days_old > 365:
                warnings.append("Harvest date is more than 1 year old")
            elif days_old > 180:
                warnings.append("Harvest date is more than 6 months old")
            elif days_old <= 30:
                suggestions.append("Fresh harvest - excellent for traceability")

        # Check seasonal patterns (palm oil can be harvested year-round in tropics)
        # This is informational rather than restrictive
        month = harvest_date.month
        if month in [12, 1, 2]:  # Dry season in some regions
            suggestions.append("Harvest during dry season - typically good quality")

        return {
            "is_valid": len(errors) == 0,
            "days_old": days_old,
            "freshness_level": self._get_freshness_level(days_old),
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _get_freshness_level(self, days_old: int) -> str:
        """Get freshness level description."""
        if days_old <= 7:
            return "very_fresh"
        elif days_old <= 30:
            return "fresh"
        elif days_old <= 90:
            return "good"
        elif days_old <= 180:
            return "acceptable"
        elif days_old <= 365:
            return "old"
        else:
            return "very_old"

    def _validate_regional_compliance(
        self,
        origin_data: OriginDataCapture,
        detected_region: Optional[PalmOilRegion],
        product: Product
    ) -> Dict[str, Any]:
        """
        Validate regional compliance requirements.

        Args:
            origin_data: Complete origin data
            detected_region: Detected palm oil region
            product: Product information

        Returns:
            Regional compliance validation result
        """
        errors = []
        warnings = []
        suggestions = []
        compliance_score = 1.0

        if not detected_region:
            warnings.append("Cannot determine regional compliance - location outside known palm oil regions")
            compliance_score = 0.5
            return {
                "is_valid": True,
                "compliance_score": compliance_score,
                "region": None,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }

        # Get regional requirements
        regional_req = self.CERTIFICATION_REQUIREMENTS.get(detected_region)
        if not regional_req:
            return {
                "is_valid": True,
                "compliance_score": 1.0,
                "region": detected_region.value,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }

        # Check certification compliance
        recognized_certs = [cert for cert in origin_data.certifications
                           if cert in {c.value for c in CertificationBody}]

        # Required certifications
        missing_required = [cert.value for cert in regional_req.required_certifications
                           if cert.value not in recognized_certs]

        if missing_required:
            if regional_req.compliance_level == "mandatory":
                errors.extend([f"Missing mandatory regional certification: {cert}"
                              for cert in missing_required])
                compliance_score -= 0.5
            elif regional_req.compliance_level == "recommended":
                warnings.extend([f"Missing recommended regional certification: {cert}"
                               for cert in missing_required])
                compliance_score -= 0.2

        # Recommended certifications
        missing_recommended = [cert.value for cert in regional_req.recommended_certifications
                              if cert.value not in recognized_certs]

        if missing_recommended:
            suggestions.extend([f"Consider adding regional certification: {cert}"
                              for cert in missing_recommended])
            compliance_score -= 0.1

        # Check data completeness for region
        if detected_region in [PalmOilRegion.SOUTHEAST_ASIA, PalmOilRegion.WEST_AFRICA]:
            # Higher standards for major producing regions
            if not origin_data.farm_information:
                warnings.append("Farm identification recommended for major producing regions")
                compliance_score -= 0.1

            if not origin_data.harvest_date:
                warnings.append("Harvest date recommended for major producing regions")
                compliance_score -= 0.1

        compliance_score = max(compliance_score, 0.0)

        return {
            "is_valid": len(errors) == 0,
            "compliance_score": compliance_score,
            "region": detected_region.value,
            "compliance_level": regional_req.compliance_level,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }

    def _calculate_origin_data_quality_score(
        self,
        coord_validation: Dict[str, Any],
        cert_validation: Dict[str, Any],
        harvest_validation: Dict[str, Any],
        regional_compliance: Dict[str, Any]
    ) -> float:
        """
        Calculate overall origin data quality score.

        Args:
            coord_validation: Coordinate validation results
            cert_validation: Certification validation results
            harvest_validation: Harvest date validation results
            regional_compliance: Regional compliance results

        Returns:
            Quality score between 0.0 and 1.0
        """
        # Base scores
        coord_score = 1.0 if coord_validation["is_valid"] else 0.0
        cert_score = cert_validation.get("quality_score", 0.0)
        harvest_score = 1.0 if harvest_validation["is_valid"] else 0.0
        compliance_score = regional_compliance.get("compliance_score", 1.0)

        # Accuracy bonus
        accuracy_level = coord_validation.get("accuracy_level", "unknown")
        accuracy_bonus = {
            "excellent": 0.2,
            "very_good": 0.15,
            "good": 0.1,
            "moderate": 0.05,
            "low": 0.0,
            "very_low": -0.1,
            "unknown": 0.0
        }.get(accuracy_level, 0.0)

        # Freshness bonus
        freshness_level = harvest_validation.get("freshness_level", "unknown")
        freshness_bonus = {
            "very_fresh": 0.1,
            "fresh": 0.05,
            "good": 0.0,
            "acceptable": -0.05,
            "old": -0.1,
            "very_old": -0.2,
            "unknown": 0.0
        }.get(freshness_level, 0.0)

        # Weighted calculation
        quality_score = (
            coord_score * 0.3 +
            cert_score * 0.4 +
            harvest_score * 0.2 +
            compliance_score * 0.1 +
            accuracy_bonus +
            freshness_bonus
        )

        return max(min(quality_score, 1.0), 0.0)

    def _determine_overall_compliance_status(
        self,
        coord_validation: Dict[str, Any],
        cert_validation: Dict[str, Any],
        harvest_validation: Dict[str, Any],
        regional_compliance: Dict[str, Any],
        quality_score: float
    ) -> str:
        """
        Determine overall compliance status.

        Args:
            coord_validation: Coordinate validation results
            cert_validation: Certification validation results
            harvest_validation: Harvest date validation results
            regional_compliance: Regional compliance results
            quality_score: Overall quality score

        Returns:
            Compliance status string
        """
        # Check for any critical errors
        all_validations = [coord_validation, cert_validation, harvest_validation, regional_compliance]
        has_errors = any(validation.get("errors", []) for validation in all_validations)

        if has_errors:
            return "non_compliant"
        elif quality_score >= 0.8:
            return "fully_compliant"
        elif quality_score >= 0.6:
            return "substantially_compliant"
        elif quality_score >= 0.4:
            return "partially_compliant"
        else:
            return "minimally_compliant"

    def get_certification_bodies(self) -> List[Dict[str, Any]]:
        """
        Get list of recognized certification bodies.

        Returns:
            List of certification body information
        """
        return [
            {
                "code": cert.value,
                "name": cert.value,
                "description": self._get_certification_description(cert),
                "is_high_value": cert in self.HIGH_VALUE_CERTIFICATIONS
            }
            for cert in CertificationBody
        ]

    def get_palm_oil_regions(self) -> List[Dict[str, Any]]:
        """
        Get list of palm oil producing regions with boundaries.

        Returns:
            List of region information
        """
        return [
            {
                "code": region.value,
                "name": boundary.name,
                "description": boundary.description,
                "boundaries": {
                    "min_latitude": boundary.min_latitude,
                    "max_latitude": boundary.max_latitude,
                    "min_longitude": boundary.min_longitude,
                    "max_longitude": boundary.max_longitude
                }
            }
            for region, boundary in self.PALM_OIL_REGIONS.items()
        ]

    def _get_certification_description(self, cert: CertificationBody) -> str:
        """Get description for certification body."""
        descriptions = {
            CertificationBody.RSPO: "Roundtable on Sustainable Palm Oil - Global standard for sustainable palm oil",
            CertificationBody.NDPE: "No Deforestation, No Peat, No Exploitation - Environmental protection standard",
            CertificationBody.ISPO: "Indonesian Sustainable Palm Oil - Indonesian national standard",
            CertificationBody.MSPO: "Malaysian Sustainable Palm Oil - Malaysian national standard",
            CertificationBody.RTRS: "Round Table on Responsible Soy - Responsible soy production standard",
            CertificationBody.ISCC: "International Sustainability and Carbon Certification - EU recognized standard",
            CertificationBody.SAN: "Sustainable Agriculture Network - Sustainable farming practices",
            CertificationBody.UTZ: "UTZ Certified - Sustainable farming and better opportunities for farmers",
            CertificationBody.RAINFOREST_ALLIANCE: "Rainforest Alliance - Environmental and social sustainability",
            CertificationBody.ORGANIC: "Organic Certification - Organic farming practices",
            CertificationBody.FAIR_TRADE: "Fair Trade Certification - Fair trade practices",
            CertificationBody.NON_GMO: "Non-GMO Certification - Non-genetically modified organisms",
            CertificationBody.SUSTAINABLE: "Sustainable Certification - General sustainability practices",
            CertificationBody.TRACEABLE: "Traceable Certification - Supply chain traceability"
        }
        return descriptions.get(cert, f"{cert.value} certification")
