"""
Transformation template orchestrator.

This module provides the main orchestrator that coordinates all template engines
and implements dependency injection for better testability.
"""
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.transformation import TransformationType
from .base import TemplateEngineInterface, BaseTemplateEngine
from .plantation_template import PlantationTemplateEngine
from .mill_template import MillTemplateEngine
from .refinery_template import RefineryTemplateEngine
from .manufacturer_template import ManufacturerTemplateEngine
from ..exceptions import TemplateGenerationError, ConfigurationError
from ..schemas import TransformationTemplateRequest
from app.core.logging import get_logger

logger = get_logger(__name__)


class TransformationTemplateOrchestrator(TemplateEngineInterface):
    """
    Main orchestrator for transformation template generation.
    
    This class coordinates all template engines and implements dependency injection
    for better testability and maintainability.
    """
    
    def __init__(
        self, 
        db: Session,
        plantation_engine: Optional[PlantationTemplateEngine] = None,
        mill_engine: Optional[MillTemplateEngine] = None,
        refinery_engine: Optional[RefineryTemplateEngine] = None,
        manufacturer_engine: Optional[ManufacturerTemplateEngine] = None
    ):
        self.db = db
        self.logger = get_logger(self.__class__.__name__)
        
        # Dependency injection for template engines
        self.plantation_engine = plantation_engine or PlantationTemplateEngine(db)
        self.mill_engine = mill_engine or MillTemplateEngine(db)
        self.refinery_engine = refinery_engine or RefineryTemplateEngine(db)
        self.manufacturer_engine = manufacturer_engine or ManufacturerTemplateEngine(db)
        
        # Map company types to engines
        self.engine_mapping = {
            'plantation_grower': self.plantation_engine,
            'mill_processor': self.mill_engine,
            'refinery_crusher': self.refinery_engine,
            'manufacturer': self.manufacturer_engine
        }
    
    def get_template(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict] = None,
        facility_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a transformation template by delegating to the appropriate engine.
        
        Args:
            transformation_type: The type of transformation
            company_type: The company type (plantation_grower, mill_processor, etc.)
            input_batch_data: Optional input batch data for inheritance
            facility_id: Optional facility ID for facility-specific defaults
            
        Returns:
            Complete transformation template with role-specific data
            
        Raises:
            TemplateGenerationError: If template generation fails
            ConfigurationError: If configuration is invalid
        """
        self.logger.info(
            "Orchestrating template generation",
            transformation_type=transformation_type.value,
            company_type=company_type,
            facility_id=facility_id
        )
        
        try:
            # Validate inputs using Pydantic schema
            request = TransformationTemplateRequest(
                transformation_type=transformation_type,
                company_type=company_type,
                input_batch_data=input_batch_data,
                facility_id=facility_id
            )
            
            # Get the appropriate engine
            engine = self._get_engine_for_company_type(company_type)
            
            # Generate template using the specific engine
            template = engine.get_template(
                transformation_type=transformation_type,
                company_type=company_type,
                input_batch_data=input_batch_data,
                facility_id=facility_id
            )
            
            # Add orchestration metadata
            template["orchestration_metadata"] = {
                "generated_by": engine.__class__.__name__,
                "generation_timestamp": self._get_current_timestamp(),
                "template_version": "2.0",
                "orchestrator_version": "1.0"
            }
            
            self.logger.info(
                "Template generation completed successfully",
                template_size=len(template),
                engine_used=engine.__class__.__name__
            )
            
            return template
            
        except Exception as e:
            self.logger.error(
                "Template generation failed in orchestrator",
                error=str(e),
                transformation_type=transformation_type.value,
                company_type=company_type,
                exc_info=True
            )
            raise TemplateGenerationError(
                message=f"Orchestrator failed to generate template: {str(e)}",
                transformation_type=transformation_type.value,
                company_type=company_type
            )
    
    def _get_engine_for_company_type(self, company_type: str) -> BaseTemplateEngine:
        """Get the appropriate template engine for the company type."""
        engine = self.engine_mapping.get(company_type)
        if not engine:
            raise ConfigurationError(
                message=f"No template engine found for company type: {company_type}",
                config_key="engine_mapping"
            )
        return engine
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_available_company_types(self) -> list:
        """Get list of available company types."""
        return list(self.engine_mapping.keys())
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about available engines."""
        return {
            "available_engines": {
                company_type: engine.__class__.__name__
                for company_type, engine in self.engine_mapping.items()
            },
            "total_engines": len(self.engine_mapping),
            "orchestrator_version": "1.0"
        }
    
    def validate_company_type(self, company_type: str) -> bool:
        """Validate if a company type is supported."""
        return company_type in self.engine_mapping
    
    def get_supported_transformation_types(self, company_type: str) -> list:
        """Get supported transformation types for a company type."""
        if not self.validate_company_type(company_type):
            return []
        
        # Map company types to their primary transformation types
        transformation_mapping = {
            'plantation_grower': [TransformationType.HARVEST],
            'mill_processor': [TransformationType.MILLING],
            'refinery_crusher': [TransformationType.REFINING],
            'manufacturer': [TransformationType.MANUFACTURING]
        }
        
        return transformation_mapping.get(company_type, [])
    
    def get_template_metadata(self, company_type: str) -> Dict[str, Any]:
        """Get metadata about templates for a company type."""
        if not self.validate_company_type(company_type):
            return {}
        
        engine = self.engine_mapping[company_type]
        supported_types = self.get_supported_transformation_types(company_type)
        
        return {
            "company_type": company_type,
            "engine_class": engine.__class__.__name__,
            "supported_transformation_types": [t.value for t in supported_types],
            "template_capabilities": {
                "role_specific_data": True,
                "quality_metrics": True,
                "process_parameters": True,
                "efficiency_metrics": True,
                "location_data": True,
                "weather_conditions": True,
                "certifications": True,
                "compliance_data": True,
                "output_batch_suggestions": True
            }
        }
