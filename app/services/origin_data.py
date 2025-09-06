"""
Enhanced origin data capture and validation service.

This module provides backward compatibility for the legacy OriginDataValidationService
while delegating to the new modular architecture internally.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from dataclasses import dataclass
from enum import Enum

from app.schemas.confirmation import OriginDataCapture
from app.core.logging import get_logger

# Import new modular service
from app.services.origin_validation import create_origin_validation_service

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
    """Major palm oil producing regions."""
    SOUTHEAST_ASIA = "Southeast Asia"
    WEST_AFRICA = "West Africa"
    CENTRAL_AFRICA = "Central Africa"
    SOUTH_AMERICA = "South America"
    CENTRAL_AMERICA = "Central America"
    OCEANIA = "Oceania"


@dataclass
class CertificationRequirement:
    """Certification requirement for specific regions or products."""
    region: Optional[PalmOilRegion]
    product_category: Optional[str]
    required_certifications: List[CertificationBody]
    recommended_certifications: List[CertificationBody]
    compliance_level: str  # "mandatory", "recommended", "optional"


@dataclass
class GeographicBoundary:
    """Geographic boundary for a palm oil region."""
    name: str
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    description: str


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
    """
    Enhanced origin data validation service with comprehensive validation capabilities.
    
    This service provides backward compatibility for the legacy interface while
    delegating to the new modular architecture internally.
    
    This service provides:
    - Geographic coordinate validation with palm oil region detection
    - Comprehensive certification body validation
    - Harvest date validation with freshness scoring
    - Regional compliance requirements checking
    - Quality scoring and compliance status determination
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Create the new modular service internally
        self._orchestrator = create_origin_validation_service(db)
        
        # Legacy attributes for backward compatibility
        self.PALM_OIL_REGIONS = {}
        self.CERTIFICATION_REQUIREMENTS = {}
        self.HIGH_VALUE_CERTIFICATIONS = set()
    
    def validate_comprehensive_origin_data(
        self,
        origin_data: OriginDataCapture,
        product_id: UUID,
        purchase_order_id: Optional[UUID] = None
    ) -> OriginDataValidationResult:
        """
        Perform comprehensive validation of origin data.
        
        This method delegates to the new modular architecture while maintaining
        backward compatibility with the legacy interface.
        
        Args:
            origin_data: Origin data to validate
            product_id: Product UUID for context-specific validation
            purchase_order_id: Optional purchase order UUID for additional context
            
        Returns:
            Comprehensive validation result
        """
        # Delegate to the new modular orchestrator
        return self._orchestrator.validate_comprehensive_origin_data(
            origin_data, product_id, purchase_order_id
        )
    
    # Legacy compatibility methods
    def get_certification_bodies(self) -> Dict[str, Any]:
        """Get certification bodies configuration."""
        return self._orchestrator.get_certification_bodies()
    
    def get_palm_oil_regions(self) -> Dict[str, Any]:
        """Get palm oil regions configuration."""
        return self._orchestrator.get_palm_oil_regions()
    
    def get_certification_requirements(self) -> Dict[str, Any]:
        """Get certification requirements configuration."""
        return self._orchestrator.get_certification_requirements()
