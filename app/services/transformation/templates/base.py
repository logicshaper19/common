"""
Base classes for transformation template engines.

This module provides abstract base classes and common functionality
for all transformation template engines.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.transformation import TransformationType
from app.services.transformation.config.industry_standards import get_standards_for_company_type, RegionType
from app.services.transformation.exceptions import TemplateGenerationError, ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class TemplateEngineInterface(ABC):
    """Interface for transformation template engines."""
    
    @abstractmethod
    def get_template(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict] = None,
        facility_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a transformation template for the given parameters."""
        pass


class BaseTemplateEngine(TemplateEngineInterface):
    """Base implementation for transformation template engines."""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(self.__class__.__name__)
    
    def get_template(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict] = None,
        facility_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a transformation template with common validation and logging."""
        self.logger.info(
            "Generating transformation template",
            transformation_type=transformation_type.value,
            company_type=company_type,
            facility_id=facility_id
        )
        
        try:
            # Validate inputs
            self._validate_inputs(transformation_type, company_type, facility_id)
            
            # Get base template
            template = self._get_base_template(transformation_type, company_type, facility_id)
            
            # Add role-specific data
            role_data = self._get_role_specific_data(transformation_type, company_type, input_batch_data)
            template.update(role_data)
            
            # Add industry standards
            standards = self._get_industry_standards(company_type)
            template["industry_standards"] = standards
            
            self.logger.info(
                "Template generated successfully",
                template_size=len(template),
                has_role_specific_data=bool(template.get('role_specific_data'))
            )
            
            return template
            
        except Exception as e:
            self.logger.error(
                "Template generation failed",
                error=str(e),
                transformation_type=transformation_type.value,
                company_type=company_type,
                exc_info=True
            )
            raise TemplateGenerationError(
                message=f"Failed to generate template: {str(e)}",
                transformation_type=transformation_type.value,
                company_type=company_type
            )
    
    def _validate_inputs(
        self, 
        transformation_type: TransformationType, 
        company_type: str, 
        facility_id: Optional[str]
    ) -> None:
        """Validate input parameters."""
        if not transformation_type:
            raise TemplateGenerationError("Transformation type is required")
        
        if not company_type:
            raise TemplateGenerationError("Company type is required")
        
        valid_company_types = [
            'plantation_grower', 
            'mill_processor', 
            'refinery_crusher', 
            'manufacturer'
        ]
        if company_type not in valid_company_types:
            raise TemplateGenerationError(f"Invalid company type: {company_type}")
        
        if facility_id and not self._is_valid_facility_id(facility_id):
            raise TemplateGenerationError(f"Invalid facility ID format: {facility_id}")
    
    def _is_valid_facility_id(self, facility_id: str) -> bool:
        """Validate facility ID format."""
        import re
        return bool(re.match(r'^[A-Z]+-\d+$', facility_id))
    
    def _get_base_template(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        facility_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get base template structure."""
        return {
            "transformation_type": transformation_type.value,
            "company_type": company_type,
            "facility_id": facility_id or self._generate_facility_id(company_type),
            "created_at": datetime.utcnow().isoformat(),
            "template_version": "1.0",
            "role_specific_data": {}
        }
    
    def _generate_facility_id(self, company_type: str) -> str:
        """Generate a facility ID based on company type."""
        type_mapping = {
            'plantation_grower': 'PLANTATION',
            'mill_processor': 'MILL',
            'refinery_crusher': 'REFINERY',
            'manufacturer': 'MANUFACTURER'
        }
        prefix = type_mapping.get(company_type, 'FACILITY')
        return f"{prefix}-001"
    
    def _get_industry_standards(self, company_type: str) -> Dict[str, Any]:
        """Get industry standards for the company type."""
        try:
            return get_standards_for_company_type(company_type, RegionType.SOUTHEAST_ASIA)
        except Exception as e:
            self.logger.warning(f"Failed to load industry standards: {e}")
            return {}
    
    @abstractmethod
    def _get_role_specific_data(
        self, 
        transformation_type: TransformationType, 
        company_type: str,
        input_batch_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Get role-specific data for the transformation type."""
        pass
    
    def _get_default_quality_metrics(self, transformation_type: TransformationType) -> Dict[str, Any]:
        """Get default quality metrics for the transformation type."""
        if transformation_type == TransformationType.HARVEST:
            return {
                "moisture_content": Decimal("12.0"),
                "ffa_content": Decimal("3.5"),
                "color_grade": "A1",
                "purity_percentage": Decimal("95.0")
            }
        elif transformation_type == TransformationType.MILLING:
            return {
                "moisture_content": Decimal("0.1"),
                "ffa_content": Decimal("4.0"),
                "iodine_value": Decimal("52.0"),
                "color_grade": "A2",
                "purity_percentage": Decimal("98.0")
            }
        elif transformation_type == TransformationType.REFINING:
            return {
                "moisture_content": Decimal("0.05"),
                "ffa_content": Decimal("0.1"),
                "iodine_value": Decimal("53.0"),
                "peroxide_value": Decimal("1.0"),
                "color_grade": "A1",
                "purity_percentage": Decimal("99.5")
            }
        elif transformation_type == TransformationType.MANUFACTURING:
            return {
                "moisture_content": Decimal("0.02"),
                "ffa_content": Decimal("0.05"),
                "iodine_value": Decimal("53.0"),
                "peroxide_value": Decimal("0.5"),
                "color_grade": "A1",
                "purity_percentage": Decimal("99.8")
            }
        return {}
    
    def _get_default_process_parameters(self, transformation_type: TransformationType) -> Dict[str, Any]:
        """Get default process parameters for the transformation type."""
        if transformation_type == TransformationType.HARVEST:
            return {
                "temperature": Decimal("30.0"),
                "humidity": Decimal("75.0"),
                "duration_hours": Decimal("4.0"),
                "energy_consumed": Decimal("10.0")
            }
        elif transformation_type == TransformationType.MILLING:
            return {
                "temperature": Decimal("90.0"),
                "pressure": Decimal("2.0"),
                "duration_hours": Decimal("6.0"),
                "energy_consumed": Decimal("150.0"),
                "water_used": Decimal("500.0")
            }
        elif transformation_type == TransformationType.REFINING:
            return {
                "temperature": Decimal("220.0"),
                "pressure": Decimal("0.3"),
                "duration_hours": Decimal("8.0"),
                "energy_consumed": Decimal("300.0"),
                "chemical_additives": ["Phosphoric Acid", "Bleaching Earth"]
            }
        elif transformation_type == TransformationType.MANUFACTURING:
            return {
                "temperature": Decimal("180.0"),
                "pressure": Decimal("1.0"),
                "duration_hours": Decimal("4.0"),
                "energy_consumed": Decimal("200.0"),
                "chemical_additives": ["Antioxidants", "Preservatives"]
            }
        return {}
    
    def _get_default_efficiency_metrics(self, transformation_type: TransformationType) -> Dict[str, Any]:
        """Get default efficiency metrics for the transformation type."""
        if transformation_type == TransformationType.HARVEST:
            return {
                "yield_percentage": Decimal("20.0"),
                "waste_percentage": Decimal("3.0"),
                "energy_efficiency": Decimal("85.0"),
                "processing_time_hours": Decimal("4.0")
            }
        elif transformation_type == TransformationType.MILLING:
            return {
                "yield_percentage": Decimal("22.0"),
                "waste_percentage": Decimal("8.0"),
                "energy_efficiency": Decimal("80.0"),
                "processing_time_hours": Decimal("6.0")
            }
        elif transformation_type == TransformationType.REFINING:
            return {
                "yield_percentage": Decimal("96.0"),
                "waste_percentage": Decimal("2.0"),
                "energy_efficiency": Decimal("75.0"),
                "processing_time_hours": Decimal("8.0")
            }
        elif transformation_type == TransformationType.MANUFACTURING:
            return {
                "yield_percentage": Decimal("95.0"),
                "waste_percentage": Decimal("1.0"),
                "energy_efficiency": Decimal("90.0"),
                "processing_time_hours": Decimal("4.0")
            }
        return {}
    
    def _get_default_certifications(self, transformation_type: TransformationType) -> List[Dict[str, Any]]:
        """Get default certifications for the transformation type."""
        base_certifications = [
            {
                "certification_type": "RSPO Mass Balance",
                "certification_body": "RSPO",
                "certificate_number": "RSPO-MB-2024-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True
            }
        ]
        
        if transformation_type in [TransformationType.REFINING, TransformationType.MANUFACTURING]:
            base_certifications.append({
                "certification_type": "ISCC EU",
                "certification_body": "ISCC",
                "certificate_number": "ISCC-EU-2024-001",
                "issue_date": date.today().isoformat(),
                "expiry_date": date.today().replace(year=date.today().year + 1).isoformat(),
                "is_valid": True
            })
        
        return base_certifications
    
    def _get_default_location_data(self, company_type: str) -> Dict[str, Any]:
        """Get default location data based on company type."""
        location_templates = {
            'plantation_grower': {
                "facility_name": "Harvest Facility",
                "address": "Plantation Road, Estate Area",
                "city": "Kuala Lumpur",
                "state_province": "Selangor",
                "country": "MY",
                "latitude": Decimal("3.1390"),
                "longitude": Decimal("101.6869")
            },
            'mill_processor': {
                "facility_name": "Processing Mill",
                "address": "Industrial Zone, Mill Complex",
                "city": "Port Klang",
                "state_province": "Selangor", 
                "country": "MY",
                "latitude": Decimal("3.0000"),
                "longitude": Decimal("101.4000")
            },
            'refinery_crusher': {
                "facility_name": "Refinery Plant",
                "address": "Refinery Complex, Industrial Area",
                "city": "Johor Bahru",
                "state_province": "Johor",
                "country": "MY",
                "latitude": Decimal("1.4927"),
                "longitude": Decimal("103.7414")
            },
            'manufacturer': {
                "facility_name": "Manufacturing Plant",
                "address": "Manufacturing Complex, Industrial Park",
                "city": "Shah Alam",
                "state_province": "Selangor",
                "country": "MY",
                "latitude": Decimal("3.0733"),
                "longitude": Decimal("101.5185")
            }
        }
        
        return location_templates.get(company_type, {
            "facility_name": "Processing Facility",
            "address": "Industrial Area",
            "city": "Kuala Lumpur",
            "state_province": "Selangor",
            "country": "MY"
        })
    
    def _get_default_weather_conditions(self) -> Dict[str, Any]:
        """Get default weather conditions for Southeast Asia."""
        return {
            "temperature_celsius": Decimal("28.0"),
            "humidity_percentage": Decimal("80.0"),
            "rainfall_mm": Decimal("150.0"),
            "wind_speed_kmh": Decimal("15.0"),
            "weather_condition": "partly_cloudy"
        }
    
    def create_output_batch_suggestion(
        self, 
        transformation_type: TransformationType,
        input_batch_data: Optional[Dict],
        company_type: str
    ) -> Dict[str, Any]:
        """Create output batch suggestion based on transformation type."""
        if not input_batch_data:
            return {}
        
        input_quantity = input_batch_data.get('quantity', Decimal('0'))
        input_unit = input_batch_data.get('unit', 'kg')
        
        # Get yield percentage based on transformation type
        yield_percentages = {
            TransformationType.HARVEST: Decimal('20.0'),
            TransformationType.MILLING: Decimal('22.0'),
            TransformationType.REFINING: Decimal('96.0'),
            TransformationType.MANUFACTURING: Decimal('95.0')
        }
        
        yield_percentage = yield_percentages.get(transformation_type, Decimal('90.0'))
        output_quantity = (input_quantity * yield_percentage / 100).quantize(Decimal('0.01'))
        
        return {
            "suggested_output_quantity": float(output_quantity),
            "suggested_output_unit": input_unit,
            "yield_percentage": float(yield_percentage),
            "waste_quantity": float(input_quantity - output_quantity),
            "waste_unit": input_unit,
            "processing_efficiency": float(yield_percentage)
        }
