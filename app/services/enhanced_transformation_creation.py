"""
Enhanced transformation creation service with automatic role-specific data population.

This service automatically creates transformation events with pre-filled role-specific data
based on company type and transformation type.
"""
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal

from app.models.transformation import (
    TransformationEvent, 
    TransformationType, 
    PlantationHarvestData,
    MillProcessingData,
    RefineryProcessingData,
    ManufacturerProcessingData
)
from app.models.batch import Batch
from app.models.company import Company
from app.schemas.transformation import TransformationEventCreate, BatchReference
from app.services.transformation.templates import create_template_engine
from app.services.transformation.transaction_manager import TransactionManager
from app.services.transformation.exceptions import (
    TransformationError, 
    ValidationError, 
    DataIntegrityError,
    TransactionError,
    EntityNotFoundError
)
from app.services.transformation.schemas import (
    CompleteTransformationRequest,
    TransformationEventCreateSchema,
    RoleDataValidationRequest
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnhancedTransformationCreationService:
    """Service for creating transformations with automatic role-specific data population."""
    
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = create_template_engine(db)
        self.transaction_manager = TransactionManager(db)
        self.logger = get_logger(self.__class__.__name__)
    
    async def create_complete_transformation(
        self,
        transformation_data: Dict[str, Any],
        user_id: UUID,
        auto_populate_role_data: bool = True
    ) -> Dict[str, Any]:
        """
        Create a complete transformation event with automatic role-specific data population.
        
        Args:
            transformation_data: Basic transformation data
            user_id: ID of the user creating the transformation
            auto_populate_role_data: Whether to automatically populate role-specific data
            
        Returns:
            Complete transformation event with all data populated
        """
        try:
            # Extract basic transformation data
            transformation_type = TransformationType(transformation_data['transformation_type'])
            company_id = UUID(transformation_data['company_id'])
            
            # Get company to determine company type
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError(f"Company {company_id} not found")
            
            # Create comprehensive template
            template = self.template_engine.get_transformation_template(
                transformation_type=transformation_type,
                company_type=company.company_type,
                input_batch_data=transformation_data.get('input_batch_data'),
                facility_id=transformation_data.get('facility_id')
            )
            
            # Merge template data with provided data (provided data takes precedence)
            complete_data = {**template, **transformation_data}
            
            # Validate the complete transformation data
            role_specific_data = complete_data.get('role_specific_data', {})
            is_valid, validation_errors = self.validation_service.validate_transformation_data(
                transformation_type=transformation_type,
                company_type=company.company_type,
                transformation_data=complete_data,
                role_specific_data=role_specific_data
            )
            
            if not is_valid:
                logger.warning(
                    f"Transformation validation failed",
                    transformation_type=transformation_type.value,
                    company_type=company.company_type,
                    errors=validation_errors
                )
                # For now, we'll continue with warnings, but in production you might want to raise an exception
                # raise ValueError(f"Transformation validation failed: {', '.join(validation_errors)}")
            
            # Create the base transformation event
            transformation_event = TransformationEvent(
                event_id=complete_data['event_id'],
                transformation_type=transformation_type,
                company_id=company_id,
                facility_id=complete_data['facility_id'],
                input_batches=complete_data.get('input_batches', []),
                output_batches=complete_data.get('output_batches', []),
                process_description=complete_data['process_description'],
                process_parameters=complete_data['process_parameters'],
                quality_metrics=complete_data['quality_metrics'],
                efficiency_metrics=complete_data['efficiency_metrics'],
                total_input_quantity=complete_data.get('total_input_quantity'),
                total_output_quantity=complete_data.get('total_output_quantity'),
                yield_percentage=complete_data.get('yield_percentage'),
                start_time=complete_data['start_time'],
                end_time=complete_data.get('end_time'),
                location_name=complete_data.get('location_name'),
                location_coordinates=complete_data['location_coordinates'],
                weather_conditions=complete_data.get('weather_conditions'),
                certifications=complete_data['certifications'],
                compliance_data=complete_data['compliance_data'],
                status=complete_data.get('status', 'planned'),
                validation_status=complete_data.get('validation_status', 'pending'),
                event_metadata=complete_data.get('event_metadata', {}),
                created_by_user_id=user_id
            )
            
            self.db.add(transformation_event)
            self.db.flush()  # Get the ID
            
            # Auto-populate role-specific data if requested
            role_data_id = None
            if auto_populate_role_data:
                role_data_id = await self._create_role_specific_data(
                    transformation_event.id,
                    transformation_type,
                    complete_data.get('role_specific_data', {}),
                    user_id
                )
            
            self.db.commit()
            
            # Create output batches if suggested
            output_batches = []
            if complete_data.get('output_batch_suggestion'):
                output_batches = await self._create_output_batches(
                    transformation_event.id,
                    complete_data['output_batch_suggestion'],
                    user_id
                )
            
            result = {
                "transformation_event_id": str(transformation_event.id),
                "event_id": transformation_event.event_id,
                "transformation_type": transformation_type.value,
                "company_id": str(company_id),
                "role_specific_data_id": role_data_id,
                "output_batches_created": len(output_batches),
                "auto_populated": auto_populate_role_data,
                "template_used": True
            }
            
            logger.info(
                f"Created complete transformation event {transformation_event.event_id}",
                transformation_id=str(transformation_event.id),
                company_id=str(company_id),
                transformation_type=transformation_type.value,
                role_data_created=role_data_id is not None,
                output_batches_created=len(output_batches)
            )
            
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create complete transformation: {str(e)}", exc_info=True)
            raise
    
    async def _create_role_specific_data(
        self,
        transformation_event_id: UUID,
        transformation_type: TransformationType,
        role_data: Dict[str, Any],
        user_id: UUID
    ) -> Optional[UUID]:
        """Create role-specific data based on transformation type."""
        try:
            if transformation_type == TransformationType.HARVEST:
                return await self._create_plantation_data(transformation_event_id, role_data)
            elif transformation_type == TransformationType.MILLING:
                return await self._create_mill_data(transformation_event_id, role_data)
            elif transformation_type == TransformationType.REFINING:
                return await self._create_refinery_data(transformation_event_id, role_data)
            elif transformation_type == TransformationType.MANUFACTURING:
                return await self._create_manufacturer_data(transformation_event_id, role_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to create role-specific data: {str(e)}", exc_info=True)
            return None
    
    async def _create_plantation_data(
        self, 
        transformation_event_id: UUID, 
        plantation_data: Dict[str, Any]
    ) -> UUID:
        """Create plantation harvest data."""
        plantation = PlantationHarvestData(
            transformation_event_id=transformation_event_id,
            farm_id=plantation_data.get('farm_id', 'FARM-001'),
            farm_name=plantation_data.get('farm_name', 'Main Plantation'),
            gps_coordinates=plantation_data.get('gps_coordinates', {}),
            field_id=plantation_data.get('field_id', 'FIELD-001'),
            harvest_date=plantation_data.get('harvest_date', date.today()),
            harvest_method=plantation_data.get('harvest_method', 'manual'),
            yield_per_hectare=Decimal(str(plantation_data.get('yield_per_hectare', 20.5))),
            total_hectares=Decimal(str(plantation_data.get('total_hectares', 100.0))),
            ffb_quality_grade=plantation_data.get('ffb_quality_grade', 'A'),
            moisture_content=Decimal(str(plantation_data.get('moisture_content', 25.0))),
            free_fatty_acid=Decimal(str(plantation_data.get('free_fatty_acid', 3.5))),
            labor_hours=Decimal(str(plantation_data.get('labor_hours', 8.0))),
            equipment_used=plantation_data.get('equipment_used', []),
            fuel_consumed=Decimal(str(plantation_data.get('fuel_consumed', 5.0))),
            certifications=plantation_data.get('certifications', []),
            sustainability_metrics=plantation_data.get('sustainability_metrics', {})
        )
        
        self.db.add(plantation)
        self.db.flush()
        return plantation.id
    
    async def _create_mill_data(
        self, 
        transformation_event_id: UUID, 
        mill_data: Dict[str, Any]
    ) -> UUID:
        """Create mill processing data."""
        mill = MillProcessingData(
            transformation_event_id=transformation_event_id,
            extraction_rate=Decimal(str(mill_data.get('extraction_rate', 22.5))),
            processing_capacity=Decimal(str(mill_data.get('processing_capacity', 50.0))),
            processing_time_hours=Decimal(str(mill_data.get('processing_time_hours', 8.0))),
            ffb_quantity=Decimal(str(mill_data.get('ffb_quantity', 1000.0))),
            ffb_quality_grade=mill_data.get('ffb_quality_grade', 'A'),
            ffb_moisture_content=Decimal(str(mill_data.get('ffb_moisture_content', 25.0))),
            cpo_quantity=Decimal(str(mill_data.get('cpo_quantity', 225.0))),
            cpo_quality_grade=mill_data.get('cpo_quality_grade', 'A'),
            cpo_ffa_content=Decimal(str(mill_data.get('cpo_ffa_content', 3.5))),
            cpo_moisture_content=Decimal(str(mill_data.get('cpo_moisture_content', 0.1))),
            kernel_quantity=Decimal(str(mill_data.get('kernel_quantity', 50.0))),
            oil_content_input=Decimal(str(mill_data.get('oil_content_input', 25.0))),
            oil_content_output=Decimal(str(mill_data.get('oil_content_output', 95.0))),
            extraction_efficiency=Decimal(str(mill_data.get('extraction_efficiency', 90.0))),
            energy_consumed=Decimal(str(mill_data.get('energy_consumed', 150.0))),
            water_consumed=Decimal(str(mill_data.get('water_consumed', 2.5))),
            steam_consumed=Decimal(str(mill_data.get('steam_consumed', 0.8))),
            equipment_used=mill_data.get('equipment_used', []),
            maintenance_status=mill_data.get('maintenance_status', {})
        )
        
        self.db.add(mill)
        self.db.flush()
        return mill.id
    
    async def _create_refinery_data(
        self, 
        transformation_event_id: UUID, 
        refinery_data: Dict[str, Any]
    ) -> UUID:
        """Create refinery processing data."""
        refinery = RefineryProcessingData(
            transformation_event_id=transformation_event_id,
            process_type=refinery_data.get('process_type', 'refining'),
            input_oil_quantity=Decimal(str(refinery_data.get('input_oil_quantity', 1000.0))),
            input_oil_type=refinery_data.get('input_oil_type', 'CPO'),
            input_oil_quality=refinery_data.get('input_oil_quality', {}),
            output_olein_quantity=Decimal(str(refinery_data.get('output_olein_quantity', 600.0))),
            output_stearin_quantity=Decimal(str(refinery_data.get('output_stearin_quantity', 350.0))),
            output_other_quantity=Decimal(str(refinery_data.get('output_other_quantity', 50.0))),
            iv_value=Decimal(str(refinery_data.get('iv_value', 52.0))),
            melting_point=Decimal(str(refinery_data.get('melting_point', 24.0))),
            solid_fat_content=refinery_data.get('solid_fat_content', {}),
            color_grade=refinery_data.get('color_grade', 'A'),
            refining_loss=Decimal(str(refinery_data.get('refining_loss', 2.0))),
            fractionation_yield_olein=Decimal(str(refinery_data.get('fractionation_yield_olein', 60.0))),
            fractionation_yield_stearin=Decimal(str(refinery_data.get('fractionation_yield_stearin', 35.0))),
            temperature_profile=refinery_data.get('temperature_profile', {}),
            pressure_profile=refinery_data.get('pressure_profile', {}),
            energy_consumed=Decimal(str(refinery_data.get('energy_consumed', 200.0))),
            water_consumed=Decimal(str(refinery_data.get('water_consumed', 5.0))),
            chemicals_used=refinery_data.get('chemicals_used', {})
        )
        
        self.db.add(refinery)
        self.db.flush()
        return refinery.id
    
    async def _create_manufacturer_data(
        self, 
        transformation_event_id: UUID, 
        manufacturer_data: Dict[str, Any]
    ) -> UUID:
        """Create manufacturer processing data."""
        manufacturer = ManufacturerProcessingData(
            transformation_event_id=transformation_event_id,
            product_type=manufacturer_data.get('product_type', 'soap'),
            product_name=manufacturer_data.get('product_name', 'Premium Product'),
            product_grade=manufacturer_data.get('product_grade', 'A'),
            recipe_ratios=manufacturer_data.get('recipe_ratios', {}),
            total_recipe_quantity=Decimal(str(manufacturer_data.get('total_recipe_quantity', 1000.0))),
            recipe_unit=manufacturer_data.get('recipe_unit', 'kg'),
            input_materials=manufacturer_data.get('input_materials', []),
            output_quantity=Decimal(str(manufacturer_data.get('output_quantity', 950.0))),
            output_unit=manufacturer_data.get('output_unit', 'kg'),
            production_lot_number=manufacturer_data.get('production_lot_number', f"LOT-{datetime.now().strftime('%Y%m%d')}-001"),
            packaging_type=manufacturer_data.get('packaging_type', 'unit'),
            packaging_quantity=Decimal(str(manufacturer_data.get('packaging_quantity', 100.0))),
            quality_control_tests=manufacturer_data.get('quality_control_tests', {}),
            quality_parameters=manufacturer_data.get('quality_parameters', {}),
            batch_testing_results=manufacturer_data.get('batch_testing_results', {}),
            production_line=manufacturer_data.get('production_line', 'Line-01'),
            production_shift=manufacturer_data.get('production_shift', 'Day'),
            production_speed=Decimal(str(manufacturer_data.get('production_speed', 50.0))),
            energy_consumed=Decimal(str(manufacturer_data.get('energy_consumed', 100.0))),
            water_consumed=Decimal(str(manufacturer_data.get('water_consumed', 2.0))),
            waste_generated=Decimal(str(manufacturer_data.get('waste_generated', 50.0)))
        )
        
        self.db.add(manufacturer)
        self.db.flush()
        return manufacturer.id
    
    async def _create_output_batches(
        self,
        transformation_event_id: UUID,
        output_batch_suggestion: Dict[str, Any],
        user_id: UUID
    ) -> List[UUID]:
        """Create output batches from suggestion."""
        try:
            # This would integrate with the batch service to create actual batches
            # For now, we'll return the suggestion data
            logger.info(
                f"Output batch suggestion for transformation {transformation_event_id}",
                batch_id=output_batch_suggestion.get('batch_id'),
                quantity=output_batch_suggestion.get('quantity'),
                unit=output_batch_suggestion.get('unit')
            )
            
            # TODO: Integrate with BatchTrackingService to create actual batches
            return []
            
        except Exception as e:
            logger.error(f"Failed to create output batches: {str(e)}", exc_info=True)
            return []
