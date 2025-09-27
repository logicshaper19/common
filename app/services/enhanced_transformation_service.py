"""
Enhanced Transformation Service for inventory-level transformations.
Integrates inventory pooling, provenance tracking, and mass balance validation.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.transformation import TransformationEvent, TransformationType, TransformationStatus
from app.models.inventory_transformation import (
    TransformationProvenance, 
    InventoryAllocation, 
    AllocationMethod,
    TransformationMode
)
from app.models.batch import Batch
from app.services.inventory_pool_service import InventoryPoolService
from app.services.mass_balance_service import MassBalanceService
from app.schemas.inventory_transformation import (
    InventoryTransformationCreate,
    InventoryTransformationResponse,
    InventoryAvailabilityResponse,
    AllocationPreview,
    TransformationProvenanceResponse,
    MassBalanceValidationResponse
)
from app.core.logging import get_logger
from app.core.transformation_errors import (
    InsufficientInventoryError,
    InvalidAllocationMethodError,
    MassBalanceValidationError,
    ProvenanceInheritanceError,
    TransformationNotFoundError,
    ProductNotFoundError,
    CompanyNotFoundError,
    InvalidQuantityError
)

logger = get_logger(__name__)


class EnhancedTransformationService:
    """Enhanced service for inventory-level transformations with provenance tracking."""
    
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryPoolService(db)
        self.mass_balance_service = MassBalanceService(db)
    
    async def create_inventory_level_transformation(
        self,
        transformation_data: InventoryTransformationCreate,
        user_id: UUID
    ) -> InventoryTransformationResponse:
        """
        Create an inventory-level transformation with automatic allocation and provenance tracking.
        
        Args:
            transformation_data: Transformation creation data
            user_id: User creating the transformation
            
        Returns:
            Complete transformation response with provenance and validation
        """
        try:
            # 1. Validate inventory availability
            inventory = self.inventory_service.get_available_inventory(
                transformation_data.company_id,
                transformation_data.input_product_id
            )
            
            if transformation_data.input_quantity_requested > inventory['total_quantity']:
                raise InsufficientInventoryError(
                    requested_quantity=float(transformation_data.input_quantity_requested),
                    available_quantity=inventory['total_quantity'],
                    unit=inventory['unit']
                )
            
            # 2. Calculate allocation preview
            allocation_plan = self.inventory_service.calculate_proportional_allocation(
                requested_quantity=float(transformation_data.input_quantity_requested),
                available_batches=inventory['batches'],
                method=transformation_data.inventory_drawdown_method
            )
            
            # 3. Create transformation event
            transformation_event = TransformationEvent(
                event_id=transformation_data.event_id,
                transformation_type=TransformationType(transformation_data.transformation_type),
                company_id=transformation_data.company_id,
                facility_id=transformation_data.facility_id,
                process_description=transformation_data.process_description,
                process_parameters=transformation_data.process_parameters,
                quality_metrics=transformation_data.quality_metrics,
                start_time=transformation_data.start_time,
                end_time=transformation_data.end_time,
                location_name=transformation_data.location_name,
                location_coordinates=transformation_data.location_coordinates,
                certifications=transformation_data.certifications,
                compliance_data=transformation_data.compliance_data,
                status=TransformationStatus.PLANNED,
                transformation_mode=TransformationMode.INVENTORY_LEVEL,
                input_product_id=transformation_data.input_product_id,
                input_quantity_requested=transformation_data.input_quantity_requested,
                inventory_drawdown_method=transformation_data.inventory_drawdown_method.value,
                created_by_user_id=user_id
            )
            
            self.db.add(transformation_event)
            self.db.flush()  # Get the ID
            
            # 4. Draw from inventory and create allocation
            allocation_result = self.inventory_service.draw_from_inventory(
                company_id=transformation_data.company_id,
                product_id=transformation_data.input_product_id,
                quantity=float(transformation_data.input_quantity_requested),
                method=transformation_data.inventory_drawdown_method,
                transformation_event_id=transformation_event.id,
                user_id=user_id
            )
            
            # 5. Create provenance records with eager loading
            provenance_records = []
            batch_ids = [UUID(item['batch_id']) for item in allocation_result['allocation_details']]
            
            # Eager load all source batches in one query
            source_batches = self.db.query(Batch).filter(
                Batch.id.in_(batch_ids)
            ).all()
            
            # Create a lookup dictionary for O(1) access
            batch_lookup = {batch.id: batch for batch in source_batches}
            
            for allocation_item in allocation_result['allocation_details']:
                source_batch = batch_lookup.get(UUID(allocation_item['batch_id']))
                
                if source_batch:
                    provenance = TransformationProvenance(
                        transformation_event_id=transformation_event.id,
                        source_batch_id=source_batch.id,
                        contribution_ratio=Decimal(str(allocation_item['contribution_ratio'])),
                        contribution_quantity=Decimal(str(allocation_item['quantity_used'])),
                        contribution_unit=allocation_item['unit'],
                        inherited_origin_data=source_batch.origin_data,
                        inherited_certifications=source_batch.certifications,
                        inherited_quality_metrics=source_batch.quality_metrics,
                        allocation_method=transformation_data.inventory_drawdown_method,
                        allocation_priority=len(provenance_records) + 1,
                        created_by_user_id=user_id
                    )
                    
                    self.db.add(provenance)
                    provenance_records.append(provenance)
            
            # 6. Create output batches with inherited provenance
            output_batches = await self._create_output_batches_with_provenance(
                transformation_event, allocation_result, user_id
            )
            
            # 7. Update transformation with output data
            transformation_event.input_batches = allocation_result['allocation_details']
            transformation_event.output_batches = output_batches
            transformation_event.total_input_quantity = transformation_data.input_quantity_requested
            transformation_event.total_output_quantity = sum(
                batch['quantity'] for batch in output_batches
            )
            
            # 8. Validate mass balance
            mass_balance_result = self.mass_balance_service.validate_with_expected_outputs(
                transformation_event_id=transformation_event.id,
                input_quantity=float(transformation_data.input_quantity_requested),
                actual_outputs=output_batches,
                transformation_type=transformation_data.transformation_type,
                input_product="Fresh Fruit Bunches (FFB)",  # TODO: Get from product data
                user_id=user_id
            )
            
            # 9. Update transformation status
            if mass_balance_result['is_balanced']:
                transformation_event.status = TransformationStatus.COMPLETED
            else:
                transformation_event.status = TransformationStatus.PENDING_VALIDATION
            
            self.db.commit()
            
            # 10. Return complete response
            return await self._build_transformation_response(
                transformation_event, provenance_records, mass_balance_result
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating inventory-level transformation: {str(e)}")
            raise
    
    async def get_inventory_availability(
        self,
        company_id: UUID,
        product_id: UUID
    ) -> InventoryAvailabilityResponse:
        """
        Get available inventory for transformations.
        
        Args:
            company_id: Company ID
            product_id: Product ID
            
        Returns:
            Inventory availability details
        """
        try:
            inventory = self.inventory_service.get_available_inventory(company_id, product_id)
            
            return InventoryAvailabilityResponse(
                total_quantity=Decimal(str(inventory['total_quantity'])),
                unit=inventory['unit'],
                batch_count=inventory['batch_count'],
                batches=inventory['batches'],
                pool_composition=inventory['pool_composition']
            )
            
        except Exception as e:
            logger.error(f"Error getting inventory availability: {str(e)}")
            raise
    
    async def preview_allocation(
        self,
        company_id: UUID,
        product_id: UUID,
        requested_quantity: float,
        method: AllocationMethod = AllocationMethod.PROPORTIONAL
    ) -> AllocationPreview:
        """
        Preview allocation without actually drawing from inventory.
        
        Args:
            company_id: Company ID
            product_id: Product ID
            requested_quantity: Quantity to preview
            method: Allocation method
            
        Returns:
            Allocation preview details
        """
        try:
            inventory = self.inventory_service.get_available_inventory(company_id, product_id)
            
            if requested_quantity > inventory['total_quantity']:
                return AllocationPreview(
                    requested_quantity=Decimal(str(requested_quantity)),
                    allocation_method=method,
                    allocation_details=[],
                    total_batches_used=0,
                    can_fulfill=False
                )
            
            allocation_details = self.inventory_service.calculate_proportional_allocation(
                requested_quantity=requested_quantity,
                available_batches=inventory['batches'],
                method=method
            )
            
            return AllocationPreview(
                requested_quantity=Decimal(str(requested_quantity)),
                allocation_method=method,
                allocation_details=allocation_details,
                total_batches_used=len(allocation_details),
                can_fulfill=True
            )
            
        except Exception as e:
            logger.error(f"Error previewing allocation: {str(e)}")
            raise
    
    async def get_transformation_provenance(
        self,
        transformation_event_id: UUID
    ) -> List[TransformationProvenanceResponse]:
        """
        Get provenance details for a transformation.
        
        Args:
            transformation_event_id: Transformation event ID
            
        Returns:
            List of provenance records
        """
        try:
            provenance_records = self.db.query(TransformationProvenance).filter(
                TransformationProvenance.transformation_event_id == transformation_event_id
            ).all()
            
            return [
                TransformationProvenanceResponse(
                    id=record.id,
                    source_batch_id=record.source_batch_id,
                    source_batch_number=record.source_batch.batch_id,
                    contribution_ratio=record.contribution_ratio,
                    contribution_quantity=record.contribution_quantity,
                    contribution_unit=record.contribution_unit,
                    contribution_percentage=float(record.contribution_ratio) * 100,
                    allocation_method=record.allocation_method,
                    inherited_origin_data=record.inherited_origin_data,
                    inherited_certifications=record.inherited_certifications,
                    created_at=record.created_at
                )
                for record in provenance_records
            ]
            
        except Exception as e:
            logger.error(f"Error getting transformation provenance: {str(e)}")
            raise
    
    async def _create_output_batches_with_provenance(
        self,
        transformation_event: TransformationEvent,
        allocation_result: Dict[str, Any],
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Create output batches with inherited provenance from source batches.
        
        Args:
            transformation_event: The transformation event
            allocation_result: Result from inventory allocation
            user_id: User creating the batches
            
        Returns:
            List of output batch information
        """
        try:
            # Get expected outputs for the transformation
            expected_outputs = self.mass_balance_service.calculate_expected_outputs(
                input_quantity=float(transformation_event.input_quantity_requested),
                transformation_type=transformation_event.transformation_type.value,
                input_product="Fresh Fruit Bunches (FFB)"  # TODO: Get from product data
            )
            
            # Create output batches
            output_batches = []
            for expected_output in expected_outputs:
                if expected_output.get('is_main_product', True):
                    # Create actual batch record
                    output_batch = Batch(
                        batch_id=f"OUT-{transformation_event.event_id}-{expected_output['product'].replace(' ', '-')}",
                        batch_type='transformation',
                        company_id=transformation_event.company_id,
                        product_id=transformation_event.input_product_id,  # TODO: Map to output product
                        quantity=Decimal(str(expected_output['quantity'])),
                        unit=expected_output['unit'],
                        production_date=transformation_event.start_time.date(),
                        quality_metrics=expected_output.get('quality_metrics', {}),
                        location_name=transformation_event.location_name,
                        location_coordinates=transformation_event.location_coordinates,
                        transformation_id=transformation_event.event_id,
                        parent_batch_ids=[item['batch_id'] for item in allocation_result['allocation_details']],
                        origin_data=self._merge_origin_data(allocation_result['allocation_details']),
                        certifications=self._merge_certifications(allocation_result['allocation_details']),
                        status='active',
                        created_by_user_id=user_id
                    )
                    
                    self.db.add(output_batch)
                    self.db.flush()  # Get the ID
                    
                    output_batches.append({
                        'batch_id': str(output_batch.id),
                        'batch_number': output_batch.batch_id,
                        'product': expected_output['product'],
                        'quantity': float(output_batch.quantity),
                        'unit': output_batch.unit,
                        'yield_rate': expected_output['yield_rate']
                    })
            
            return output_batches
            
        except Exception as e:
            logger.error(f"Error creating output batches: {str(e)}")
            raise
    
    def _merge_origin_data(self, allocation_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge origin data from multiple source batches proportionally.
        
        Args:
            allocation_details: List of allocation details with source batch info
            
        Returns:
            Merged origin data
        """
        try:
            merged_data = {
                'source_batches': [],
                'farms': [],
                'locations': [],
                'certifications': set(),
                'merged_at': datetime.now().isoformat()
            }
            
            for item in allocation_details:
                if 'origin_data' in item and item['origin_data']:
                    origin_data = item['origin_data']
                    contribution_ratio = item['contribution_ratio']
                    
                    # Add source batch info
                    merged_data['source_batches'].append({
                        'batch_id': item['batch_id'],
                        'batch_number': item['batch_number'],
                        'contribution_ratio': contribution_ratio,
                        'quantity_used': item['quantity_used']
                    })
                    
                    # Merge farm information
                    if 'farm_information' in origin_data:
                        farm_info = origin_data['farm_information']
                        merged_data['farms'].append({
                            'farm_name': farm_info.get('farm_name'),
                            'farm_id': farm_info.get('farm_id'),
                            'contribution_ratio': contribution_ratio
                        })
                    
                    # Merge location information
                    if 'location_details' in origin_data:
                        location_info = origin_data['location_details']
                        merged_data['locations'].append({
                            'city': location_info.get('city'),
                            'state_province': location_info.get('state_province'),
                            'country': location_info.get('country'),
                            'contribution_ratio': contribution_ratio
                        })
                    
                    # Merge certifications
                    if 'certifications' in origin_data:
                        for cert in origin_data['certifications']:
                            merged_data['certifications'].add(cert)
            
            # Convert set to list for JSON serialization
            merged_data['certifications'] = list(merged_data['certifications'])
            
            return merged_data
            
        except Exception as e:
            logger.error(f"Error merging origin data: {str(e)}")
            return {}
    
    def _merge_certifications(self, allocation_details: List[Dict[str, Any]]) -> List[str]:
        """
        Merge certifications from multiple source batches.
        
        Args:
            allocation_details: List of allocation details with source batch info
            
        Returns:
            List of unique certifications
        """
        try:
            certifications = set()
            
            for item in allocation_details:
                if 'certifications' in item and item['certifications']:
                    for cert in item['certifications']:
                        certifications.add(cert)
            
            return list(certifications)
            
        except Exception as e:
            logger.error(f"Error merging certifications: {str(e)}")
            return []
    
    async def _build_transformation_response(
        self,
        transformation_event: TransformationEvent,
        provenance_records: List[TransformationProvenance],
        mass_balance_result: Dict[str, Any]
    ) -> InventoryTransformationResponse:
        """
        Build complete transformation response with all related data.
        
        Args:
            transformation_event: The transformation event
            provenance_records: List of provenance records
            mass_balance_result: Mass balance validation result
            
        Returns:
            Complete transformation response
        """
        try:
            # Build provenance responses
            provenance_responses = [
                TransformationProvenanceResponse(
                    id=record.id,
                    source_batch_id=record.source_batch_id,
                    source_batch_number=record.source_batch.batch_id,
                    contribution_ratio=record.contribution_ratio,
                    contribution_quantity=record.contribution_quantity,
                    contribution_unit=record.contribution_unit,
                    contribution_percentage=float(record.contribution_ratio) * 100,
                    allocation_method=record.allocation_method,
                    inherited_origin_data=record.inherited_origin_data,
                    inherited_certifications=record.inherited_certifications,
                    created_at=record.created_at
                )
                for record in provenance_records
            ]
            
            # Build mass balance response
            mass_balance_response = MassBalanceValidationResponse(
                is_balanced=mass_balance_result['is_balanced'],
                input_quantity=Decimal(str(mass_balance_result['input_quantity'])),
                total_output=Decimal(str(mass_balance_result['total_output'])),
                expected_output=Decimal(str(mass_balance_result['expected_output'])),
                waste_quantity=Decimal(str(mass_balance_result['waste_quantity'])),
                balance_ratio=mass_balance_result['balance_ratio'],
                tolerance=mass_balance_result['tolerance'],
                deviation_percentage=mass_balance_result['deviation_percentage'],
                validation_notes=mass_balance_result.get('validation_notes'),
                validation_id=UUID(mass_balance_result['validation_id'])
            )
            
            return InventoryTransformationResponse(
                id=transformation_event.id,
                event_id=transformation_event.event_id,
                transformation_type=transformation_event.transformation_type.value,
                transformation_mode=TransformationMode(transformation_event.transformation_mode),
                company_id=transformation_event.company_id,
                facility_id=transformation_event.facility_id,
                input_product_id=transformation_event.input_product_id,
                input_quantity_requested=transformation_event.input_quantity_requested,
                input_quantity_used=transformation_event.total_input_quantity,
                inventory_drawdown_method=AllocationMethod(transformation_event.inventory_drawdown_method),
                output_batches=transformation_event.output_batches,
                total_output_quantity=transformation_event.total_output_quantity,
                provenance_records=provenance_responses,
                mass_balance_validation=mass_balance_response,
                process_description=transformation_event.process_description,
                start_time=transformation_event.start_time,
                end_time=transformation_event.end_time,
                status=transformation_event.status.value,
                created_at=transformation_event.created_at,
                created_by_user_id=transformation_event.created_by_user_id
            )
            
        except Exception as e:
            logger.error(f"Error building transformation response: {str(e)}")
            raise
