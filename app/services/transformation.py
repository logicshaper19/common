"""
Transformation service for comprehensive supply chain transformation tracking.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from fastapi import HTTPException, status

from app.models.transformation import (
    TransformationEvent,
    PlantationHarvestData,
    MillProcessingData,
    RefineryProcessingData,
    ManufacturerProcessingData,
    TransformationBatchMapping
)
from app.models.batch import Batch
from app.models.company import Company
from app.models.user import User
from app.schemas.transformation import (
    TransformationEventCreate,
    TransformationEventUpdate,
    TransformationEventResponse,
    TransformationEventWithData,
    TransformationChainNode,
    TransformationChainResponse,
    TransformationSummaryResponse,
    TransformationEfficiencyMetrics,
    PlantationHarvestData as PlantationHarvestDataSchema,
    MillProcessingData as MillProcessingDataSchema,
    RefineryProcessingData as RefineryProcessingDataSchema,
    ManufacturerProcessingData as ManufacturerProcessingDataSchema,
    TransformationType,
    TransformationStatus,
    ValidationStatus
)


class TransformationService:
    """Service for managing transformation events and data."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_transformation_event(
        self, 
        transformation_data: TransformationEventCreate, 
        user_id: UUID
    ) -> TransformationEventResponse:
        """Create a new transformation event."""
        try:
            # Create the transformation event
            transformation_event = TransformationEvent(
                event_id=transformation_data.event_id,
                transformation_type=transformation_data.transformation_type,
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
                event_metadata=transformation_data.event_metadata,
                created_by_user_id=user_id
            )
            
            # Calculate input/output quantities
            total_input = sum(batch.quantity for batch in transformation_data.input_batches)
            total_output = sum(batch.quantity for batch in transformation_data.output_batches)
            yield_percentage = (total_output / total_input * 100) if total_input > 0 else 0
            
            transformation_event.total_input_quantity = total_input
            transformation_event.total_output_quantity = total_output
            transformation_event.yield_percentage = yield_percentage
            
            self.db.add(transformation_event)
            self.db.flush()  # Get the ID
            
            # Create batch mappings
            await self._create_batch_mappings(
                transformation_event.id, 
                transformation_data.input_batches, 
                transformation_data.output_batches, 
                user_id
            )
            
            self.db.commit()
            
            # Return the response
            return await self._get_transformation_response(transformation_event.id)
            
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create transformation event: {str(e)}"
            )
    
    async def list_transformation_events(
        self,
        company_id: Optional[UUID] = None,
        transformation_type: Optional[TransformationType] = None,
        status: Optional[TransformationStatus] = None,
        facility_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        per_page: int = 20,
        current_user: User = None
    ) -> List[TransformationSummaryResponse]:
        """List transformation events with filtering and pagination."""
        try:
            query = self.db.query(TransformationEvent).join(Company)
            
            # Apply filters
            if company_id:
                query = query.filter(TransformationEvent.company_id == company_id)
            
            if transformation_type:
                query = query.filter(TransformationEvent.transformation_type == transformation_type)
            
            if status:
                query = query.filter(TransformationEvent.status == status)
            
            if facility_id:
                query = query.filter(TransformationEvent.facility_id == facility_id)
            
            if start_date:
                query = query.filter(TransformationEvent.start_time >= start_date)
            
            if end_date:
                query = query.filter(TransformationEvent.start_time <= end_date)
            
            # Apply pagination
            offset = (page - 1) * per_page
            transformations = query.offset(offset).limit(per_page).all()
            
            # Convert to response format
            return [
                TransformationSummaryResponse(
                    id=t.id,
                    event_id=t.event_id,
                    transformation_type=t.transformation_type,
                    company_name=t.company.company_name,
                    facility_id=t.facility_id,
                    status=t.status,
                    start_time=t.start_time,
                    end_time=t.end_time,
                    total_input_quantity=t.total_input_quantity,
                    total_output_quantity=t.total_output_quantity,
                    yield_percentage=t.yield_percentage,
                    location_name=t.location_name
                )
                for t in transformations
            ]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list transformation events: {str(e)}"
            )
    
    async def get_transformation_event(
        self, 
        transformation_id: UUID, 
        current_user: User
    ) -> TransformationEventWithData:
        """Get a specific transformation event with role-specific data."""
        try:
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            # Get role-specific data
            plantation_data = None
            mill_data = None
            refinery_data = None
            manufacturer_data = None
            
            if transformation.transformation_type == TransformationType.HARVEST:
                plantation_data = self.db.query(PlantationHarvestData).filter(
                    PlantationHarvestData.transformation_event_id == transformation_id
                ).first()
            
            elif transformation.transformation_type == TransformationType.MILLING:
                mill_data = self.db.query(MillProcessingData).filter(
                    MillProcessingData.transformation_event_id == transformation_id
                ).first()
            
            elif transformation.transformation_type in [TransformationType.REFINING, TransformationType.FRACTIONATION]:
                refinery_data = self.db.query(RefineryProcessingData).filter(
                    RefineryProcessingData.transformation_event_id == transformation_id
                ).first()
            
            elif transformation.transformation_type in [TransformationType.BLENDING, TransformationType.MANUFACTURING]:
                manufacturer_data = self.db.query(ManufacturerProcessingData).filter(
                    ManufacturerProcessingData.transformation_event_id == transformation_id
                ).first()
            
            return TransformationEventWithData(
                id=transformation.id,
                event_id=transformation.event_id,
                transformation_type=transformation.transformation_type,
                company_id=transformation.company_id,
                company_name=transformation.company.company_name,
                facility_id=transformation.facility_id,
                process_description=transformation.process_description,
                process_parameters=transformation.process_parameters,
                quality_metrics=transformation.quality_metrics,
                start_time=transformation.start_time,
                end_time=transformation.end_time,
                location_name=transformation.location_name,
                location_coordinates=transformation.location_coordinates,
                certifications=transformation.certifications,
                compliance_data=transformation.compliance_data,
                event_metadata=transformation.event_metadata,
                total_input_quantity=transformation.total_input_quantity,
                total_output_quantity=transformation.total_output_quantity,
                yield_percentage=transformation.yield_percentage,
                efficiency_metrics=transformation.efficiency_metrics,
                status=transformation.status,
                validation_status=transformation.validation_status,
                validated_by_user_id=transformation.validated_by_user_id,
                validated_at=transformation.validated_at,
                created_at=transformation.created_at,
                updated_at=transformation.updated_at,
                created_by_user_id=transformation.created_by_user_id,
                plantation_data=plantation_data,
                mill_data=mill_data,
                refinery_data=refinery_data,
                manufacturer_data=manufacturer_data
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get transformation event: {str(e)}"
            )
    
    async def update_transformation_event(
        self, 
        transformation_id: UUID, 
        transformation_data: TransformationEventUpdate, 
        user_id: UUID
    ) -> TransformationEventResponse:
        """Update a transformation event."""
        try:
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            # Update fields
            update_data = transformation_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(transformation, field, value)
            
            transformation.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return await self._get_transformation_response(transformation_id)
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update transformation event: {str(e)}"
            )
    
    async def delete_transformation_event(
        self, 
        transformation_id: UUID, 
        user_id: UUID
    ) -> None:
        """Delete a transformation event."""
        try:
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            # Delete related data first
            self.db.query(TransformationBatchMapping).filter(
                TransformationBatchMapping.transformation_event_id == transformation_id
            ).delete()
            
            self.db.query(PlantationHarvestData).filter(
                PlantationHarvestData.transformation_event_id == transformation_id
            ).delete()
            
            self.db.query(MillProcessingData).filter(
                MillProcessingData.transformation_event_id == transformation_id
            ).delete()
            
            self.db.query(RefineryProcessingData).filter(
                RefineryProcessingData.transformation_event_id == transformation_id
            ).delete()
            
            self.db.query(ManufacturerProcessingData).filter(
                ManufacturerProcessingData.transformation_event_id == transformation_id
            ).delete()
            
            # Delete the transformation event
            self.db.delete(transformation)
            self.db.commit()
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete transformation event: {str(e)}"
            )
    
    async def validate_transformation_event(
        self, 
        transformation_id: UUID, 
        validation_status: ValidationStatus, 
        validation_notes: Optional[str], 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Validate or reject a transformation event."""
        try:
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            transformation.validation_status = validation_status
            transformation.validated_by_user_id = user_id
            transformation.validated_at = datetime.utcnow()
            
            if validation_notes:
                if not transformation.event_metadata:
                    transformation.event_metadata = {}
                transformation.event_metadata["validation_notes"] = validation_notes
            
            self.db.commit()
            
            return {
                "message": f"Transformation event {validation_status.value} successfully",
                "transformation_id": transformation_id,
                "validation_status": validation_status.value,
                "validated_at": transformation.validated_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to validate transformation event: {str(e)}"
            )
    
    async def get_transformation_chain(
        self, 
        transformation_id: UUID, 
        max_depth: int, 
        current_user: User
    ) -> TransformationChainResponse:
        """Get the transformation chain for a specific transformation event."""
        try:
            # Use the database function to get the chain
            result = self.db.execute(
                text("SELECT * FROM get_transformation_chain(:batch_id, :max_depth)"),
                {"batch_id": transformation_id, "max_depth": max_depth}
            ).fetchall()
            
            nodes = [
                TransformationChainNode(
                    batch_id=row.batch_id,
                    batch_identifier=row.batch_identifier,
                    transformation_type=row.transformation_type,
                    company_name=row.company_name,
                    depth=row.depth,
                    chain_path=row.chain_path
                )
                for row in result
            ]
            
            total_depth = max([node.depth for node in nodes]) if nodes else 0
            chain_completeness = (len(nodes) / (total_depth + 1)) * 100 if total_depth > 0 else 0
            
            return TransformationChainResponse(
                nodes=nodes,
                total_depth=total_depth,
                chain_completeness=chain_completeness
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get transformation chain: {str(e)}"
            )
    
    async def get_batch_transformation_chain(
        self, 
        batch_id: UUID, 
        max_depth: int, 
        current_user: User
    ) -> TransformationChainResponse:
        """Get the transformation chain for a specific batch."""
        try:
            # Use the database function to get the chain
            result = self.db.execute(
                text("SELECT * FROM get_transformation_chain(:batch_id, :max_depth)"),
                {"batch_id": batch_id, "max_depth": max_depth}
            ).fetchall()
            
            nodes = [
                TransformationChainNode(
                    batch_id=row.batch_id,
                    batch_identifier=row.batch_identifier,
                    transformation_type=row.transformation_type,
                    company_name=row.company_name,
                    depth=row.depth,
                    chain_path=row.chain_path
                )
                for row in result
            ]
            
            total_depth = max([node.depth for node in nodes]) if nodes else 0
            chain_completeness = (len(nodes) / (total_depth + 1)) * 100 if total_depth > 0 else 0
            
            return TransformationChainResponse(
                nodes=nodes,
                total_depth=total_depth,
                chain_completeness=chain_completeness
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get batch transformation chain: {str(e)}"
            )
    
    async def get_transformation_efficiency(
        self, 
        transformation_id: UUID, 
        current_user: User
    ) -> TransformationEfficiencyMetrics:
        """Get efficiency metrics for a transformation event."""
        try:
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            # Calculate efficiency metrics
            input_quantity = transformation.total_input_quantity or 0
            output_quantity = transformation.total_output_quantity or 0
            yield_percentage = transformation.yield_percentage or 0
            
            # Extract efficiency metrics from the event
            efficiency_metrics = transformation.efficiency_metrics or {}
            energy_efficiency = efficiency_metrics.get("energy_efficiency")
            water_efficiency = efficiency_metrics.get("water_efficiency")
            waste_percentage = efficiency_metrics.get("waste_percentage")
            quality_improvement = efficiency_metrics.get("quality_improvement")
            
            return TransformationEfficiencyMetrics(
                transformation_event_id=transformation_id,
                input_quantity=input_quantity,
                output_quantity=output_quantity,
                yield_percentage=yield_percentage,
                energy_efficiency=energy_efficiency,
                water_efficiency=water_efficiency,
                waste_percentage=waste_percentage,
                quality_improvement=quality_improvement
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get transformation efficiency: {str(e)}"
            )
    
    async def get_transformation_analytics(
        self,
        company_id: Optional[UUID] = None,
        transformation_type: Optional[TransformationType] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        current_user: User = None
    ) -> Dict[str, Any]:
        """Get transformation analytics and summary statistics."""
        try:
            query = self.db.query(TransformationEvent)
            
            # Apply filters
            if company_id:
                query = query.filter(TransformationEvent.company_id == company_id)
            
            if transformation_type:
                query = query.filter(TransformationEvent.transformation_type == transformation_type)
            
            if start_date:
                query = query.filter(TransformationEvent.start_time >= start_date)
            
            if end_date:
                query = query.filter(TransformationEvent.start_time <= end_date)
            
            # Get summary statistics
            total_events = query.count()
            
            # Get transformation type distribution
            type_distribution = self.db.query(
                TransformationEvent.transformation_type,
                func.count(TransformationEvent.id).label('count')
            ).group_by(TransformationEvent.transformation_type).all()
            
            # Get average yield by transformation type
            yield_stats = self.db.query(
                TransformationEvent.transformation_type,
                func.avg(TransformationEvent.yield_percentage).label('avg_yield'),
                func.max(TransformationEvent.yield_percentage).label('max_yield'),
                func.min(TransformationEvent.yield_percentage).label('min_yield')
            ).group_by(TransformationEvent.transformation_type).all()
            
            # Get validation status distribution
            validation_stats = self.db.query(
                TransformationEvent.validation_status,
                func.count(TransformationEvent.id).label('count')
            ).group_by(TransformationEvent.validation_status).all()
            
            return {
                "total_events": total_events,
                "type_distribution": {t.transformation_type: t.count for t in type_distribution},
                "yield_statistics": {
                    t.transformation_type: {
                        "average_yield": float(t.avg_yield) if t.avg_yield else 0,
                        "max_yield": float(t.max_yield) if t.max_yield else 0,
                        "min_yield": float(t.min_yield) if t.min_yield else 0
                    }
                    for t in yield_stats
                },
                "validation_status": {v.validation_status: v.count for v in validation_stats},
                "date_range": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get transformation analytics: {str(e)}"
            )
    
    # Role-specific data methods
    async def add_plantation_data(
        self, 
        transformation_id: UUID, 
        plantation_data: PlantationHarvestDataSchema, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Add plantation harvest data to a transformation event."""
        try:
            # Check if transformation exists and is harvest type
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            if transformation.transformation_type != TransformationType.HARVEST:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transformation event is not a harvest event"
                )
            
            # Create plantation data
            plantation = PlantationHarvestData(
                transformation_event_id=transformation_id,
                **plantation_data.dict()
            )
            
            self.db.add(plantation)
            self.db.commit()
            
            return {"message": "Plantation data added successfully", "id": plantation.id}
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add plantation data: {str(e)}"
            )
    
    async def add_mill_data(
        self, 
        transformation_id: UUID, 
        mill_data: MillProcessingDataSchema, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Add mill processing data to a transformation event."""
        try:
            # Check if transformation exists and is milling type
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            if transformation.transformation_type != TransformationType.MILLING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transformation event is not a milling event"
                )
            
            # Create mill data
            mill = MillProcessingData(
                transformation_event_id=transformation_id,
                **mill_data.dict()
            )
            
            self.db.add(mill)
            self.db.commit()
            
            return {"message": "Mill data added successfully", "id": mill.id}
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add mill data: {str(e)}"
            )
    
    async def add_refinery_data(
        self, 
        transformation_id: UUID, 
        refinery_data: RefineryProcessingDataSchema, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Add refinery processing data to a transformation event."""
        try:
            # Check if transformation exists and is refining/fractionation type
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            if transformation.transformation_type not in [TransformationType.REFINING, TransformationType.FRACTIONATION]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transformation event is not a refining/fractionation event"
                )
            
            # Create refinery data
            refinery = RefineryProcessingData(
                transformation_event_id=transformation_id,
                **refinery_data.dict()
            )
            
            self.db.add(refinery)
            self.db.commit()
            
            return {"message": "Refinery data added successfully", "id": refinery.id}
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add refinery data: {str(e)}"
            )
    
    async def add_manufacturer_data(
        self, 
        transformation_id: UUID, 
        manufacturer_data: ManufacturerProcessingDataSchema, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Add manufacturer processing data to a transformation event."""
        try:
            # Check if transformation exists and is blending/manufacturing type
            transformation = self.db.query(TransformationEvent).filter(
                TransformationEvent.id == transformation_id
            ).first()
            
            if not transformation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Transformation event not found"
                )
            
            if transformation.transformation_type not in [TransformationType.BLENDING, TransformationType.MANUFACTURING]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transformation event is not a blending/manufacturing event"
                )
            
            # Create manufacturer data
            manufacturer = ManufacturerProcessingData(
                transformation_event_id=transformation_id,
                **manufacturer_data.dict()
            )
            
            self.db.add(manufacturer)
            self.db.commit()
            
            return {"message": "Manufacturer data added successfully", "id": manufacturer.id}
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add manufacturer data: {str(e)}"
            )
    
    # Helper methods
    async def _create_batch_mappings(
        self, 
        transformation_event_id: UUID, 
        input_batches: List, 
        output_batches: List, 
        user_id: UUID
    ) -> None:
        """Create batch mappings for input and output batches."""
        # Create input batch mappings
        for i, batch in enumerate(input_batches):
            mapping = TransformationBatchMapping(
                transformation_event_id=transformation_event_id,
                batch_id=batch.batch_id,
                role="input",
                sequence_order=i + 1,
                quantity_used=batch.quantity,
                quantity_unit=batch.unit,
                quality_grade=batch.quality_grade,
                created_by_user_id=user_id
            )
            self.db.add(mapping)
        
        # Create output batch mappings
        for i, batch in enumerate(output_batches):
            mapping = TransformationBatchMapping(
                transformation_event_id=transformation_event_id,
                batch_id=batch.batch_id,
                role="output",
                sequence_order=i + 1,
                quantity_used=batch.quantity,
                quantity_unit=batch.unit,
                quality_grade=batch.quality_grade,
                created_by_user_id=user_id
            )
            self.db.add(mapping)
    
    async def _get_transformation_response(self, transformation_id: UUID) -> TransformationEventResponse:
        """Get transformation event response."""
        transformation = self.db.query(TransformationEvent).filter(
            TransformationEvent.id == transformation_id
        ).first()
        
        return TransformationEventResponse(
            id=transformation.id,
            event_id=transformation.event_id,
            transformation_type=transformation.transformation_type,
            company_id=transformation.company_id,
            company_name=transformation.company.company_name,
            facility_id=transformation.facility_id,
            process_description=transformation.process_description,
            process_parameters=transformation.process_parameters,
            quality_metrics=transformation.quality_metrics,
            start_time=transformation.start_time,
            end_time=transformation.end_time,
            location_name=transformation.location_name,
            location_coordinates=transformation.location_coordinates,
            certifications=transformation.certifications,
            compliance_data=transformation.compliance_data,
            event_metadata=transformation.event_metadata,
            total_input_quantity=transformation.total_input_quantity,
            total_output_quantity=transformation.total_output_quantity,
            yield_percentage=transformation.yield_percentage,
            efficiency_metrics=transformation.efficiency_metrics,
            status=transformation.status,
            validation_status=transformation.validation_status,
            validated_by_user_id=transformation.validated_by_user_id,
            validated_at=transformation.validated_at,
            created_at=transformation.created_at,
            updated_at=transformation.updated_at,
            created_by_user_id=transformation.created_by_user_id
        )
