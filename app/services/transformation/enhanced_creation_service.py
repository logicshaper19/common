"""
Enhanced transformation creation service with proper error handling and transaction management.

This service provides robust transformation creation with:
- Automatic role-specific data population
- Comprehensive input validation
- Atomic transaction management
- Proper error handling and logging
- Data integrity guarantees
"""
from typing import Dict, Any, Optional, List, Tuple
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
from .templates import create_template_engine
from .transaction_manager import TransactionManager
from .exceptions import (
    TransformationError, 
    ValidationError, 
    DataIntegrityError,
    TransactionError,
    EntityNotFoundError,
    TemplateGenerationError
)
from .schemas import (
    CompleteTransformationRequest,
    TransformationEventCreateSchema,
    RoleDataValidationRequest
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class EnhancedTransformationCreationService:
    """
    Service for creating transformations with automatic role-specific data population.
    
    This service provides:
    - Automatic role-specific data population based on templates
    - Comprehensive input validation using Pydantic schemas
    - Atomic transaction management with rollback on errors
    - Proper error handling with custom exception hierarchy
    - Data integrity validation and guarantees
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.template_engine = create_template_engine(db)
        self.transaction_manager = TransactionManager(db)
        self.logger = get_logger(self.__class__.__name__)
    
    def create_complete_transformation(
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
            Dictionary containing the created transformation and metadata
            
        Raises:
            ValidationError: If input validation fails
            TemplateGenerationError: If template generation fails
            TransactionError: If database transaction fails
            DataIntegrityError: If data integrity is compromised
        """
        self.logger.info(
            "Creating complete transformation",
            user_id=str(user_id),
            auto_populate_role_data=auto_populate_role_data
        )
        
        try:
            # Validate input data
            validated_data = self._validate_transformation_data(transformation_data)
            
            # Create transformation with transaction management
            result = self.transaction_manager.execute_with_retry(
                lambda db: self._create_transformation_with_validation(
                    db, validated_data, user_id, auto_populate_role_data
                ),
                "create_complete_transformation"
            )
            
            self.logger.info(
                "Transformation created successfully",
                transformation_id=str(result["transformation_id"]),
                user_id=str(user_id)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to create complete transformation",
                error=str(e),
                user_id=str(user_id),
                exc_info=True
            )
            raise
    
    def _validate_transformation_data(self, transformation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate transformation data using Pydantic schema."""
        try:
            # Create validation request
            request = CompleteTransformationRequest(
                transformation_data=transformation_data,
                user_id=transformation_data.get('user_id'),
                auto_populate_role_data=transformation_data.get('auto_populate_role_data', True)
            )
            
            # Validate transformation event data
            event_data = TransformationEventCreateSchema(**transformation_data)
            
            return {
                "validated_event_data": event_data.dict(),
                "user_id": request.user_id,
                "auto_populate_role_data": request.auto_populate_role_data
            }
            
        except Exception as e:
            self.logger.error(f"Transformation data validation failed: {str(e)}")
            raise ValidationError(
                message=f"Transformation data validation failed: {str(e)}",
                validation_errors=[str(e)],
                details={"transformation_data": transformation_data}
            )
    
    def _create_transformation_with_validation(
        self, 
        db: Session, 
        validated_data: Dict[str, Any], 
        user_id: UUID, 
        auto_populate_role_data: bool
    ) -> Dict[str, Any]:
        """Create transformation with validation in a single transaction."""
        
        def create_entity(db: Session) -> TransformationEvent:
            # Create transformation event
            transformation_event = self._create_transformation_event(db, validated_data, user_id)
            db.flush()  # Flush to get ID
            
            # Auto-populate role-specific data if requested
            role_data_id = None
            if auto_populate_role_data:
                role_data_id = self._create_role_specific_data(
                    db, transformation_event, validated_data
                )
            
            return transformation_event, role_data_id
        
        def validate_entity(db: Session, result: Tuple[TransformationEvent, Optional[UUID]]) -> bool:
            transformation_event, role_data_id = result
            
            # Validate transformation event exists
            if not transformation_event or not transformation_event.id:
                return False
            
            # Validate input batch exists
            if not self._validate_input_batch(db, transformation_event.input_batch_id):
                return False
            
            # Validate company exists
            if not self._validate_company(db, transformation_event.company_id):
                return False
            
            return True
        
        # Create entity with validation
        transformation_event, role_data_id = self.transaction_manager.create_entity_with_validation(
            create_entity,
            [validate_entity],
            "create_transformation_with_validation"
        )
        
        return {
            "transformation_id": str(transformation_event.id),
            "transformation_type": transformation_event.transformation_type.value,
            "status": transformation_event.status,
            "created_at": transformation_event.created_at.isoformat(),
            "role_data_id": str(role_data_id) if role_data_id else None,
            "message": "Transformation created successfully with role-specific data"
        }
    
    def _create_transformation_event(
        self, 
        db: Session, 
        validated_data: Dict[str, Any], 
        user_id: UUID
    ) -> TransformationEvent:
        """Create the transformation event entity."""
        event_data = validated_data["validated_event_data"]
        
        transformation_event = TransformationEvent(
            transformation_type=event_data["transformation_type"],
            input_batch_id=event_data["input_batch_id"],
            company_id=event_data["company_id"],
            facility_id=event_data.get("facility_id"),
            process_name=event_data["process_name"],
            process_description=event_data.get("process_description"),
            start_time=event_data["start_time"],
            end_time=event_data.get("end_time"),
            status=event_data["status"],
            created_by=user_id
        )
        
        db.add(transformation_event)
        return transformation_event
    
    def _create_role_specific_data(
        self, 
        db: Session, 
        transformation_event: TransformationEvent, 
        validated_data: Dict[str, Any]
    ) -> UUID:
        """Create role-specific data based on transformation type and company type."""
        try:
            # Get company type
            company = db.query(Company).filter(Company.id == transformation_event.company_id).first()
            if not company:
                raise EntityNotFoundError(
                    message=f"Company not found: {transformation_event.company_id}",
                    entity_type="company",
                    entity_id=str(transformation_event.company_id)
                )
            
            # Get template for role-specific data
            template = self.template_engine.get_template(
                transformation_type=transformation_event.transformation_type,
                company_type=company.company_type,
                input_batch_data=self._get_input_batch_data(db, transformation_event.input_batch_id),
                facility_id=transformation_event.facility_id
            )
            
            # Create role-specific data based on transformation type
            role_data_id = self._create_specific_role_data(
                db, transformation_event, template, company.company_type
            )
            
            return role_data_id
            
        except Exception as e:
            self.logger.error(f"Failed to create role-specific data: {str(e)}")
            raise TemplateGenerationError(
                message=f"Failed to create role-specific data: {str(e)}",
                transformation_type=transformation_event.transformation_type.value,
                company_type=company.company_type if company else "unknown"
            )
    
    def _create_specific_role_data(
        self, 
        db: Session, 
        transformation_event: TransformationEvent, 
        template: Dict[str, Any], 
        company_type: str
    ) -> UUID:
        """Create specific role data based on company type."""
        role_data = template.get("role_specific_data", {})
        
        if transformation_event.transformation_type == TransformationType.HARVEST:
            return self._create_plantation_data(db, transformation_event, role_data)
        elif transformation_event.transformation_type == TransformationType.MILLING:
            return self._create_mill_data(db, transformation_event, role_data)
        elif transformation_event.transformation_type == TransformationType.REFINING:
            return self._create_refinery_data(db, transformation_event, role_data)
        elif transformation_event.transformation_type == TransformationType.MANUFACTURING:
            return self._create_manufacturer_data(db, transformation_event, role_data)
        else:
            raise ValidationError(
                message=f"Unsupported transformation type: {transformation_event.transformation_type}",
                validation_errors=[f"Unsupported transformation type: {transformation_event.transformation_type}"]
            )
    
    def _create_plantation_data(
        self, 
        db: Session, 
        transformation_event: TransformationEvent, 
        role_data: Dict[str, Any]
    ) -> UUID:
        """Create plantation harvest data."""
        plantation_data = role_data.get("plantation_data", {})
        
        plantation_harvest_data = PlantationHarvestData(
            transformation_event_id=transformation_event.id,
            harvest_date=datetime.fromisoformat(plantation_data.get("harvest_date", date.today().isoformat())),
            harvest_method=plantation_data.get("harvest_method", "manual_harvesting"),
            fruit_bunches_harvested=Decimal(str(plantation_data.get("fruit_bunches_harvested", 0))),
            estimated_oil_yield=Decimal(str(plantation_data.get("estimated_oil_yield", 0))),
            harvest_team_size=plantation_data.get("harvest_team_size", 1),
            harvest_duration_hours=Decimal(str(plantation_data.get("harvest_duration_hours", 0))),
            fruit_ripeness_percentage=Decimal(str(plantation_data.get("fruit_ripeness_percentage", 0))),
            harvest_efficiency=Decimal(str(plantation_data.get("harvest_efficiency", 0))),
            equipment_used=plantation_data.get("equipment_used", []),
            harvest_notes=plantation_data.get("harvest_notes", ""),
            quality_grade=plantation_data.get("quality_grade", ""),
            sustainability_practices=plantation_data.get("sustainability_practices", [])
        )
        
        db.add(plantation_harvest_data)
        db.flush()
        return plantation_harvest_data.id
    
    def _create_mill_data(
        self, 
        db: Session, 
        transformation_event: TransformationEvent, 
        role_data: Dict[str, Any]
    ) -> UUID:
        """Create mill processing data."""
        mill_data = role_data.get("mill_data", {})
        
        mill_processing_data = MillProcessingData(
            transformation_event_id=transformation_event.id,
            processing_date=datetime.fromisoformat(mill_data.get("processing_date", date.today().isoformat())),
            processing_method=mill_data.get("processing_method", "mechanical_extraction"),
            fresh_fruit_bunches_processed=Decimal(str(mill_data.get("fresh_fruit_bunches_processed", 0))),
            crude_palm_oil_produced=Decimal(str(mill_data.get("crude_palm_oil_produced", 0))),
            palm_kernel_produced=Decimal(str(mill_data.get("palm_kernel_produced", 0))),
            processing_capacity_tonnes_per_hour=Decimal(str(mill_data.get("processing_capacity_tonnes_per_hour", 0))),
            extraction_rate_percentage=Decimal(str(mill_data.get("extraction_rate_percentage", 0))),
            sterilization_time_minutes=mill_data.get("sterilization_time_minutes", 0),
            threshing_efficiency_percentage=Decimal(str(mill_data.get("threshing_efficiency_percentage", 0))),
            pressing_pressure_bar=Decimal(str(mill_data.get("pressing_pressure_bar", 0))),
            oil_clarification_method=mill_data.get("oil_clarification_method", ""),
            equipment_used=mill_data.get("equipment_used", []),
            processing_notes=mill_data.get("processing_notes", ""),
            quality_grade=mill_data.get("quality_grade", ""),
            sustainability_practices=mill_data.get("sustainability_practices", [])
        )
        
        db.add(mill_processing_data)
        db.flush()
        return mill_processing_data.id
    
    def _create_refinery_data(
        self, 
        db: Session, 
        transformation_event: TransformationEvent, 
        role_data: Dict[str, Any]
    ) -> UUID:
        """Create refinery processing data."""
        refinery_data = role_data.get("refinery_data", {})
        
        refinery_processing_data = RefineryProcessingData(
            transformation_event_id=transformation_event.id,
            processing_date=datetime.fromisoformat(refinery_data.get("processing_date", date.today().isoformat())),
            processing_method=refinery_data.get("processing_method", "physical_chemical_refining"),
            crude_palm_oil_input=Decimal(str(refinery_data.get("crude_palm_oil_input", 0))),
            refined_palm_oil_output=Decimal(str(refinery_data.get("refined_palm_oil_output", 0))),
            refining_loss_percentage=Decimal(str(refinery_data.get("refining_loss_percentage", 0))),
            processing_capacity_tonnes_per_day=Decimal(str(refinery_data.get("processing_capacity_tonnes_per_day", 0))),
            refining_efficiency_percentage=Decimal(str(refinery_data.get("refining_efficiency_percentage", 0))),
            degumming_method=refinery_data.get("degumming_method", ""),
            neutralization_method=refinery_data.get("neutralization_method", ""),
            bleaching_method=refinery_data.get("bleaching_method", ""),
            deodorization_method=refinery_data.get("deodorization_method", ""),
            fractionation_method=refinery_data.get("fractionation_method", ""),
            equipment_used=refinery_data.get("equipment_used", []),
            processing_notes=refinery_data.get("processing_notes", ""),
            quality_grade=refinery_data.get("quality_grade", ""),
            sustainability_practices=refinery_data.get("sustainability_practices", [])
        )
        
        db.add(refinery_processing_data)
        db.flush()
        return refinery_processing_data.id
    
    def _create_manufacturer_data(
        self, 
        db: Session, 
        transformation_event: TransformationEvent, 
        role_data: Dict[str, Any]
    ) -> UUID:
        """Create manufacturer processing data."""
        manufacturer_data = role_data.get("manufacturer_data", {})
        
        manufacturer_processing_data = ManufacturerProcessingData(
            transformation_event_id=transformation_event.id,
            processing_date=datetime.fromisoformat(manufacturer_data.get("processing_date", date.today().isoformat())),
            processing_method=manufacturer_data.get("processing_method", "formulation_and_packaging"),
            refined_oil_input=Decimal(str(manufacturer_data.get("refined_oil_input", 0))),
            finished_products_output=Decimal(str(manufacturer_data.get("finished_products_output", 0))),
            processing_loss_percentage=Decimal(str(manufacturer_data.get("processing_loss_percentage", 0))),
            processing_capacity_tonnes_per_day=Decimal(str(manufacturer_data.get("processing_capacity_tonnes_per_day", 0))),
            manufacturing_efficiency_percentage=Decimal(str(manufacturer_data.get("manufacturing_efficiency_percentage", 0))),
            formulation_method=manufacturer_data.get("formulation_method", ""),
            mixing_method=manufacturer_data.get("mixing_method", ""),
            packaging_method=manufacturer_data.get("packaging_method", ""),
            quality_control_method=manufacturer_data.get("quality_control_method", ""),
            equipment_used=manufacturer_data.get("equipment_used", []),
            processing_notes=manufacturer_data.get("processing_notes", ""),
            product_grade=manufacturer_data.get("product_grade", ""),
            sustainability_practices=manufacturer_data.get("sustainability_practices", [])
        )
        
        db.add(manufacturer_processing_data)
        db.flush()
        return manufacturer_processing_data.id
    
    def _get_input_batch_data(self, db: Session, batch_id: UUID) -> Optional[Dict[str, Any]]:
        """Get input batch data for template generation."""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            return None
        
        return {
            "id": str(batch.id),
            "product_id": str(batch.product_id),
            "quantity": float(batch.quantity),
            "unit": batch.unit,
            "quality_grade": batch.quality_grade,
            "certification_status": batch.certification_status
        }
    
    def _validate_input_batch(self, db: Session, batch_id: UUID) -> bool:
        """Validate that input batch exists and is valid."""
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        return batch is not None
    
    def _validate_company(self, db: Session, company_id: UUID) -> bool:
        """Validate that company exists and is valid."""
        company = db.query(Company).filter(Company.id == company_id).first()
        return company is not None
    
    def get_transformation_template(
        self,
        transformation_type: TransformationType,
        company_type: str,
        input_batch_data: Optional[Dict] = None,
        facility_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a transformation template for the given parameters.
        
        Args:
            transformation_type: The type of transformation
            company_type: The company type
            input_batch_data: Optional input batch data
            facility_id: Optional facility ID
            
        Returns:
            Transformation template with role-specific data
            
        Raises:
            TemplateGenerationError: If template generation fails
            ValidationError: If input validation fails
        """
        try:
            return self.template_engine.get_template(
                transformation_type=transformation_type,
                company_type=company_type,
                input_batch_data=input_batch_data,
                facility_id=facility_id
            )
        except Exception as e:
            self.logger.error(f"Template generation failed: {str(e)}")
            raise TemplateGenerationError(
                message=f"Template generation failed: {str(e)}",
                transformation_type=transformation_type.value,
                company_type=company_type
            )
    
    def validate_role_data(
        self,
        transformation_type: TransformationType,
        company_type: str,
        role_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate role-specific data.
        
        Args:
            transformation_type: The type of transformation
            company_type: The company type
            role_data: The role-specific data to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        try:
            # Basic validation - can be extended with more sophisticated rules
            validation_errors = []
            
            # Check required fields based on transformation type
            if transformation_type == TransformationType.HARVEST:
                required_fields = ["harvest_date", "harvest_method", "fruit_bunches_harvested"]
                for field in required_fields:
                    if field not in role_data:
                        validation_errors.append(f"Missing required field: {field}")
            
            elif transformation_type == TransformationType.MILLING:
                required_fields = ["processing_date", "processing_method", "fresh_fruit_bunches_processed"]
                for field in required_fields:
                    if field not in role_data:
                        validation_errors.append(f"Missing required field: {field}")
            
            elif transformation_type == TransformationType.REFINING:
                required_fields = ["processing_date", "processing_method", "crude_palm_oil_input"]
                for field in required_fields:
                    if field not in role_data:
                        validation_errors.append(f"Missing required field: {field}")
            
            elif transformation_type == TransformationType.MANUFACTURING:
                required_fields = ["processing_date", "processing_method", "refined_oil_input"]
                for field in required_fields:
                    if field not in role_data:
                        validation_errors.append(f"Missing required field: {field}")
            
            return len(validation_errors) == 0, validation_errors
            
        except Exception as e:
            self.logger.error(f"Role data validation failed: {str(e)}")
            return False, [f"Validation error: {str(e)}"]
