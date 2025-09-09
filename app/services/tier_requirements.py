"""
Tier Requirements Service
Manages tier-based requirements for company types, document uploads, and compliance
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from app.models.sector import Sector, SectorTier
from app.models.company import Company


class CompanyType(str, Enum):
    """Company types with tier implications."""
    ORIGINATOR = "originator"  # Raw material producers (farms, plantations, mines)
    PROCESSOR = "processor"    # Manufacturing/processing facilities
    BRAND = "brand"           # Retail brands and consumer-facing companies
    TRADER = "trader"         # Trading and aggregation companies


class RequirementType(str, Enum):
    """Types of requirements for different tiers."""
    DOCUMENT = "document"
    COORDINATE = "coordinate"
    CERTIFICATION = "certification"
    DATA_FIELD = "data_field"


@dataclass
class TierRequirement:
    """Individual requirement for a specific tier."""
    type: RequirementType
    name: str
    description: str
    is_mandatory: bool
    validation_rules: Dict[str, Any]
    help_text: Optional[str] = None


@dataclass
class CompanyTypeProfile:
    """Profile defining requirements for a company type."""
    company_type: CompanyType
    tier_level: int
    sector_id: str
    transparency_weight: float
    base_requirements: List[TierRequirement]
    sector_specific_requirements: List[TierRequirement]


class TierRequirementsService:
    """Service for managing tier-based requirements."""
    
    def __init__(self, db: Session):
        self.db = db
        
        # Company type transparency weights
        self.TRANSPARENCY_WEIGHTS = {
            CompanyType.ORIGINATOR: 1.0,  # Highest transparency potential
            CompanyType.PROCESSOR: 0.8,   # Good transparency potential
            CompanyType.BRAND: 0.6,       # Lower transparency potential
            CompanyType.TRADER: 0.4       # Lowest transparency potential
        }
        
        # Base requirements for originators
        self.ORIGINATOR_BASE_REQUIREMENTS = [
            TierRequirement(
                type=RequirementType.COORDINATE,
                name="Geographic Coordinates",
                description="Precise latitude and longitude coordinates for traceability",
                is_mandatory=True,
                validation_rules={
                    "precision_threshold": 0.001,
                    "required_fields": ["latitude", "longitude"],
                    "coordinate_system": "WGS84"
                },
                help_text="Coordinates must be accurate to within 100 meters for compliance"
            ),
            TierRequirement(
                type=RequirementType.DOCUMENT,
                name="Operating License",
                description="Valid operating license for primary production",
                is_mandatory=True,
                validation_rules={
                    "file_types": ["pdf"],
                    "max_size_mb": 5,
                    "expiry_check": True
                },
                help_text="License must be current and valid for your operating region"
            ),
            TierRequirement(
                type=RequirementType.DOCUMENT,
                name="Environmental Impact Assessment",
                description="Environmental impact assessment report",
                is_mandatory=True,
                validation_rules={
                    "file_types": ["pdf"],
                    "max_size_mb": 15,
                    "validity_period_years": 3
                },
                help_text="EIA must be conducted by certified environmental consultants"
            )
        ]
        
        # Base requirements for processors
        self.PROCESSOR_BASE_REQUIREMENTS = [
            TierRequirement(
                type=RequirementType.DOCUMENT,
                name="Manufacturing License",
                description="Valid manufacturing/processing license",
                is_mandatory=True,
                validation_rules={
                    "file_types": ["pdf"],
                    "max_size_mb": 5,
                    "expiry_check": True
                }
            ),
            TierRequirement(
                type=RequirementType.DOCUMENT,
                name="Safety Compliance Certificate",
                description="Workplace safety compliance certificate",
                is_mandatory=True,
                validation_rules={
                    "file_types": ["pdf"],
                    "max_size_mb": 5,
                    "validity_period_years": 1
                }
            )
        ]
    
    def get_company_type_profile(self, company_type: str, sector_id: str) -> CompanyTypeProfile:
        """Get the complete profile for a company type in a specific sector."""
        company_type_enum = CompanyType(company_type)
        
        # Get sector information
        sector = self.db.query(Sector).filter(Sector.id == sector_id).first()
        if not sector:
            raise ValueError(f"Sector {sector_id} not found")
        
        # Determine tier level based on company type and sector
        tier_level = self._get_tier_level_for_company_type(company_type_enum, sector_id)
        
        # Get base requirements
        base_requirements = self._get_base_requirements(company_type_enum)
        
        # Get sector-specific requirements
        sector_requirements = self._get_sector_specific_requirements(
            company_type_enum, sector_id, tier_level
        )
        
        return CompanyTypeProfile(
            company_type=company_type_enum,
            tier_level=tier_level,
            sector_id=sector_id,
            transparency_weight=self.TRANSPARENCY_WEIGHTS[company_type_enum],
            base_requirements=base_requirements,
            sector_specific_requirements=sector_requirements
        )
    
    def _get_tier_level_for_company_type(self, company_type: CompanyType, sector_id: str) -> int:
        """Determine the appropriate tier level for a company type in a sector."""
        # Query sector tiers to find the appropriate level
        tier = self.db.query(SectorTier).filter(
            SectorTier.sector_id == sector_id,
            SectorTier.is_originator == (company_type == CompanyType.ORIGINATOR)
        ).first()
        
        if tier:
            return tier.level
        
        # Default tier assignments if not found in database
        tier_mappings = {
            "palm_oil": {
                CompanyType.BRAND: 1,
                CompanyType.TRADER: 2,
                CompanyType.PROCESSOR: 3,
                CompanyType.ORIGINATOR: 4
            },
            "apparel": {
                CompanyType.BRAND: 1,
                CompanyType.TRADER: 2,
                CompanyType.PROCESSOR: 4,
                CompanyType.ORIGINATOR: 6
            }
        }
        
        return tier_mappings.get(sector_id, {}).get(company_type, 1)
    
    def _get_base_requirements(self, company_type: CompanyType) -> List[TierRequirement]:
        """Get base requirements for a company type."""
        if company_type == CompanyType.ORIGINATOR:
            return self.ORIGINATOR_BASE_REQUIREMENTS.copy()
        elif company_type == CompanyType.PROCESSOR:
            return self.PROCESSOR_BASE_REQUIREMENTS.copy()
        else:
            return []
    
    def _get_sector_specific_requirements(
        self, 
        company_type: CompanyType, 
        sector_id: str, 
        tier_level: int
    ) -> List[TierRequirement]:
        """Get sector-specific requirements for a company type and tier."""
        requirements = []
        
        if sector_id == "palm_oil":
            requirements.extend(self._get_palm_oil_requirements(company_type, tier_level))
        elif sector_id == "apparel":
            requirements.extend(self._get_apparel_requirements(company_type, tier_level))
        
        return requirements
    
    def _get_palm_oil_requirements(self, company_type: CompanyType, tier_level: int) -> List[TierRequirement]:
        """Get palm oil sector-specific requirements."""
        requirements = []
        
        if company_type == CompanyType.ORIGINATOR and tier_level >= 4:
            requirements.extend([
                TierRequirement(
                    type=RequirementType.CERTIFICATION,
                    name="RSPO Certificate",
                    description="Valid RSPO certification for sustainable palm oil production",
                    is_mandatory=True,
                    validation_rules={
                        "file_types": ["pdf", "jpg", "png"],
                        "max_size_mb": 10,
                        "certification_body": "RSPO",
                        "validity_check": True
                    },
                    help_text="RSPO certification is mandatory for palm oil originators"
                ),
                TierRequirement(
                    type=RequirementType.DOCUMENT,
                    name="Catchment Area Polygon",
                    description="Geographic boundaries of the mill's catchment area",
                    is_mandatory=True,
                    validation_rules={
                        "file_types": ["kml", "shp", "geojson", "pdf"],
                        "max_size_mb": 20,
                        "geometry_validation": True
                    },
                    help_text="Catchment area must be defined with precise geographic boundaries"
                )
            ])
        
        return requirements
    
    def _get_apparel_requirements(self, company_type: CompanyType, tier_level: int) -> List[TierRequirement]:
        """Get apparel sector-specific requirements."""
        requirements = []
        
        if company_type == CompanyType.ORIGINATOR and tier_level >= 6:
            requirements.extend([
                TierRequirement(
                    type=RequirementType.CERTIFICATION,
                    name="BCI Certificate",
                    description="Better Cotton Initiative certification",
                    is_mandatory=True,
                    validation_rules={
                        "file_types": ["pdf", "jpg", "png"],
                        "max_size_mb": 10,
                        "certification_body": "BCI",
                        "validity_check": True
                    }
                )
            ])
        
        return requirements

    def validate_company_requirements(
        self,
        company_type: str,
        sector_id: str,
        provided_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that provided data meets tier requirements."""
        profile = self.get_company_type_profile(company_type, sector_id)
        all_requirements = profile.base_requirements + profile.sector_specific_requirements

        validation_result = {
            "is_valid": True,
            "missing_requirements": [],
            "validation_errors": [],
            "warnings": []
        }

        for requirement in all_requirements:
            if requirement.is_mandatory:
                if not self._check_requirement_fulfilled(requirement, provided_data):
                    validation_result["is_valid"] = False
                    validation_result["missing_requirements"].append({
                        "name": requirement.name,
                        "type": requirement.type.value,
                        "description": requirement.description,
                        "help_text": requirement.help_text
                    })

        return validation_result

    def _check_requirement_fulfilled(self, requirement: TierRequirement, data: Dict[str, Any]) -> bool:
        """Check if a specific requirement is fulfilled by the provided data."""
        if requirement.type == RequirementType.COORDINATE:
            return self._validate_coordinates(data.get("coordinates", {}), requirement.validation_rules)
        elif requirement.type == RequirementType.DOCUMENT:
            return self._validate_document(data.get("documents", {}), requirement)
        elif requirement.type == RequirementType.CERTIFICATION:
            return self._validate_certification(data.get("certifications", {}), requirement)

        return False

    def _validate_coordinates(self, coordinates: Dict[str, Any], rules: Dict[str, Any]) -> bool:
        """Validate coordinate data against rules."""
        required_fields = rules.get("required_fields", [])
        for field in required_fields:
            if field not in coordinates or coordinates[field] is None:
                return False

        # Check precision if provided
        precision_threshold = rules.get("precision_threshold", 0.001)
        if "latitude" in coordinates and "longitude" in coordinates:
            try:
                lat = float(coordinates["latitude"])
                lon = float(coordinates["longitude"])
                # Basic validation - coordinates should be within valid ranges
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    return False
            except (ValueError, TypeError):
                return False

        return True

    def _validate_document(self, documents: Dict[str, Any], requirement: TierRequirement) -> bool:
        """Validate document data against requirement."""
        # Check if document of this type exists
        doc_key = requirement.name.lower().replace(" ", "_")
        return doc_key in documents and documents[doc_key] is not None

    def _validate_certification(self, certifications: Dict[str, Any], requirement: TierRequirement) -> bool:
        """Validate certification data against requirement."""
        cert_key = requirement.name.lower().replace(" ", "_")
        return cert_key in certifications and certifications[cert_key] is not None
