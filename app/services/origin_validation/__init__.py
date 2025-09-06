"""
Origin Data Validation Service - Modular Architecture

This package provides a modular, testable, and maintainable architecture for
origin data validation, replacing the monolithic OriginDataValidationService.

The architecture follows domain-driven design principles with clear separation
of concerns:

- models/: Domain models, enums, and data structures
- validators/: Individual validation components
- services/: Business logic and orchestration
- config/: External configuration files

Usage:
    from app.services.origin_validation import create_origin_validation_service
    
    # Create service with dependency injection
    service = create_origin_validation_service(db)
    
    # Perform validation
    result = service.validate_comprehensive_origin_data(origin_data, product_id)
"""

from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional

from .services.data_provider import OriginDataProvider
from .services.orchestrator import OriginValidationOrchestrator
from .validators import (
    CoordinateValidator,
    CertificationValidator, 
    HarvestDateValidator,
    RegionalValidator
)
from .models.boundaries import GeographicBoundaryService
from .models.requirements import CertificationRequirementService


def create_origin_validation_service(
    db: Session,
    config_path: Optional[Path] = None
) -> OriginValidationOrchestrator:
    """
    Factory function to create validation service with dependencies.
    
    Args:
        db: Database session
        config_path: Optional path to configuration files
        
    Returns:
        Configured OriginValidationOrchestrator instance
    """
    
    if config_path is None:
        config_path = Path(__file__).parent / "config"
    
    # Create data provider
    data_provider = OriginDataProvider(config_path)
    
    # Create domain services
    boundary_service = GeographicBoundaryService(data_provider)
    requirement_service = CertificationRequirementService(data_provider)
    
    # Create validators
    coord_validator = CoordinateValidator(boundary_service)
    cert_validator = CertificationValidator(requirement_service)
    date_validator = HarvestDateValidator()
    regional_validator = RegionalValidator(boundary_service, requirement_service)
    
    # Create orchestrator
    return OriginValidationOrchestrator(
        db=db,
        data_provider=data_provider,
        coord_validator=coord_validator,
        cert_validator=cert_validator,
        date_validator=date_validator,
        regional_validator=regional_validator
    )


# Backward compatibility wrapper
class OriginDataValidationService:
    """
    Legacy wrapper for backward compatibility.
    
    This class maintains the same interface as the original monolithic service
    while delegating to the new modular architecture internally.
    """
    
    def __init__(self, db: Session):
        self._orchestrator = create_origin_validation_service(db)
    
    def validate_comprehensive_origin_data(self, *args, **kwargs):
        """Delegate to new orchestrator."""
        return self._orchestrator.validate_comprehensive_origin_data(*args, **kwargs)
    
    def get_certification_bodies(self):
        """Get certification bodies configuration."""
        return self._orchestrator.data_provider.certifications["certification_bodies"]
    
    def get_palm_oil_regions(self):
        """Get palm oil regions configuration."""
        return self._orchestrator.data_provider.regions
    
    def get_certification_requirements(self):
        """Get certification requirements configuration."""
        return self._orchestrator.data_provider.certifications["regional_requirements"]


__all__ = [
    "create_origin_validation_service",
    "OriginDataValidationService",  # For backward compatibility
    "OriginValidationOrchestrator",
]
