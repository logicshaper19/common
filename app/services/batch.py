"""
Batch tracking service for harvest, processing, and transformation batches.
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.batch import Batch, BatchTransaction, BatchRelationship
from app.models.company import Company
from app.models.product import Product
from app.models.user import User
from app.schemas.batch import (
    BatchCreate,
    BatchUpdate,
    BatchTransactionCreate,
    BatchRelationshipCreate,
    BatchType,
    BatchStatus,
    TransactionType,
    RelationshipType as BatchRelationshipType
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BatchTrackingService:
    """Service for managing batch tracking and traceability."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_batch(
        self,
        batch_data: BatchCreate,
        company_id: UUID,
        user_id: UUID
    ) -> Batch:
        """
        Create a new batch.
        
        Args:
            batch_data: Batch creation data
            company_id: Company creating the batch
            user_id: User creating the batch
            
        Returns:
            Created batch
        """
        logger.info(
            "Creating new batch",
            batch_id=batch_data.batch_id,
            batch_type=batch_data.batch_type,
            company_id=str(company_id)
        )
        
        try:
            # Check if batch ID already exists
            existing_batch = self.db.query(Batch).filter(
                Batch.batch_id == batch_data.batch_id
            ).first()
            
            if existing_batch:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Batch with ID {batch_data.batch_id} already exists"
                )
            
            # Validate product exists
            product = self.db.query(Product).filter(
                Product.id == batch_data.product_id
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Convert coordinates if provided
            location_coordinates = None
            if batch_data.location_coordinates:
                location_coordinates = {
                    "latitude": batch_data.location_coordinates.latitude,
                    "longitude": batch_data.location_coordinates.longitude,
                    "accuracy_meters": batch_data.location_coordinates.accuracy_meters
                }
            
            # Convert quality metrics if provided
            quality_metrics = None
            if batch_data.quality_metrics:
                quality_metrics = batch_data.quality_metrics.model_dump(exclude_none=True)

            # Convert parent batch IDs to strings for JSON serialization
            parent_batch_ids = None
            if batch_data.parent_batch_ids:
                parent_batch_ids = [str(batch_id) for batch_id in batch_data.parent_batch_ids]
            
            # Create batch
            batch = Batch(
                id=uuid4(),
                batch_id=batch_data.batch_id,
                batch_type=batch_data.batch_type.value,
                company_id=company_id,
                product_id=batch_data.product_id,
                quantity=batch_data.quantity,
                unit=batch_data.unit,
                production_date=batch_data.production_date,
                expiry_date=batch_data.expiry_date,
                location_name=batch_data.location_name,
                location_coordinates=location_coordinates,
                facility_code=batch_data.facility_code,
                quality_metrics=quality_metrics,
                processing_method=batch_data.processing_method,
                storage_conditions=batch_data.storage_conditions,
                transportation_method=batch_data.transportation_method,
                transformation_id=batch_data.transformation_id,
                parent_batch_ids=parent_batch_ids,
                origin_data=batch_data.origin_data,
                certifications=batch_data.certifications,
                status=BatchStatus.ACTIVE.value,
                created_by_user_id=user_id,
                batch_metadata=batch_data.batch_metadata
            )
            
            self.db.add(batch)
            self.db.commit()
            self.db.refresh(batch)
            
            # Create batch creation transaction
            self._create_batch_transaction(
                TransactionType.CREATION,
                None,
                batch.id,
                batch_data.quantity,
                batch_data.unit,
                company_id,
                user_id,
                datetime.utcnow(),
                f"Batch {batch_data.batch_id} created"
            )
            
            logger.info(
                "Batch created successfully",
                batch_id=batch_data.batch_id,
                batch_uuid=str(batch.id),
                company_id=str(company_id)
            )
            
            return batch
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to create batch",
                batch_id=batch_data.batch_id,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create batch"
            )
    
    def update_batch(
        self,
        batch_id: UUID,
        update_data: BatchUpdate,
        company_id: UUID,
        user_id: UUID
    ) -> Batch:
        """
        Update an existing batch.
        
        Args:
            batch_id: Batch UUID
            update_data: Update data
            company_id: Company updating the batch
            user_id: User updating the batch
            
        Returns:
            Updated batch
        """
        logger.info(
            "Updating batch",
            batch_id=str(batch_id),
            company_id=str(company_id)
        )
        
        try:
            # Get batch
            batch = self.db.query(Batch).filter(
                Batch.id == batch_id
            ).first()
            
            if not batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Batch not found"
                )
            
            # Check permissions
            if batch.company_id != company_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update batches belonging to your company"
                )
            
            # Update fields
            if update_data.quantity is not None:
                batch.quantity = update_data.quantity
            
            if update_data.status is not None:
                batch.status = update_data.status.value
            
            if update_data.expiry_date is not None:
                batch.expiry_date = update_data.expiry_date
            
            if update_data.quality_metrics is not None:
                batch.quality_metrics = update_data.quality_metrics.model_dump(exclude_none=True)
            
            if update_data.storage_conditions is not None:
                batch.storage_conditions = update_data.storage_conditions
            
            if update_data.transportation_method is not None:
                batch.transportation_method = update_data.transportation_method
            
            if update_data.certifications is not None:
                batch.certifications = update_data.certifications
            
            if update_data.batch_metadata is not None:
                batch.batch_metadata = update_data.batch_metadata
            
            self.db.commit()
            self.db.refresh(batch)
            
            logger.info(
                "Batch updated successfully",
                batch_id=str(batch_id),
                batch_identifier=batch.batch_id
            )
            
            return batch
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to update batch",
                batch_id=str(batch_id),
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update batch"
            )
    
    def get_batch_by_id(self, batch_id: UUID, company_id: UUID) -> Optional[Batch]:
        """
        Get batch by ID with company access control.
        
        Args:
            batch_id: Batch UUID
            company_id: Requesting company ID
            
        Returns:
            Batch if found and accessible
        """
        batch = self.db.query(Batch).filter(
            and_(
                Batch.id == batch_id,
                Batch.company_id == company_id
            )
        ).first()
        
        return batch
    
    def get_batch_by_identifier(self, batch_identifier: str, company_id: UUID) -> Optional[Batch]:
        """
        Get batch by identifier with company access control.
        
        Args:
            batch_identifier: Batch identifier string
            company_id: Requesting company ID
            
        Returns:
            Batch if found and accessible
        """
        batch = self.db.query(Batch).filter(
            and_(
                Batch.batch_id == batch_identifier,
                Batch.company_id == company_id
            )
        ).first()
        
        return batch
    
    def get_company_batches(
        self,
        company_id: UUID,
        batch_type: Optional[BatchType] = None,
        status: Optional[BatchStatus] = None,
        product_id: Optional[UUID] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Tuple[List[Batch], int]:
        """
        Get batches for a company with filtering.
        
        Args:
            company_id: Company UUID
            batch_type: Optional filter by batch type
            status: Optional filter by status
            product_id: Optional filter by product
            page: Page number
            per_page: Items per page
            
        Returns:
            Tuple of (batches, total_count)
        """
        query = self.db.query(Batch).filter(
            Batch.company_id == company_id
        )
        
        if batch_type:
            query = query.filter(Batch.batch_type == batch_type.value)
        
        if status:
            query = query.filter(Batch.status == status.value)
        
        if product_id:
            query = query.filter(Batch.product_id == product_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        batches = query.order_by(desc(Batch.production_date)).offset(offset).limit(per_page).all()
        
        return batches, total_count

    def create_batch_transaction(
        self,
        transaction_data: BatchTransactionCreate,
        company_id: UUID,
        user_id: UUID
    ) -> BatchTransaction:
        """
        Create a batch transaction.

        Args:
            transaction_data: Transaction creation data
            company_id: Company creating the transaction
            user_id: User creating the transaction

        Returns:
            Created batch transaction
        """
        logger.info(
            "Creating batch transaction",
            transaction_type=transaction_data.transaction_type,
            company_id=str(company_id)
        )

        try:
            # Validate batches exist and belong to company
            if transaction_data.source_batch_id:
                source_batch = self.db.query(Batch).filter(
                    and_(
                        Batch.id == transaction_data.source_batch_id,
                        Batch.company_id == company_id
                    )
                ).first()

                if not source_batch:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Source batch not found or not accessible"
                    )

            if transaction_data.destination_batch_id:
                dest_batch = self.db.query(Batch).filter(
                    and_(
                        Batch.id == transaction_data.destination_batch_id,
                        Batch.company_id == company_id
                    )
                ).first()

                if not dest_batch:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Destination batch not found or not accessible"
                    )

            # Create transaction
            transaction = self._create_batch_transaction(
                transaction_data.transaction_type,
                transaction_data.source_batch_id,
                transaction_data.destination_batch_id,
                transaction_data.quantity_moved,
                transaction_data.unit,
                company_id,
                user_id,
                transaction_data.transaction_date,
                transaction_data.notes,
                transaction_data.reference_number,
                transaction_data.purchase_order_id,
                transaction_data.transaction_data
            )

            return transaction

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to create batch transaction",
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create batch transaction"
            )

    def _create_batch_transaction(
        self,
        transaction_type: TransactionType,
        source_batch_id: Optional[UUID],
        destination_batch_id: Optional[UUID],
        quantity_moved: Decimal,
        unit: str,
        company_id: UUID,
        user_id: UUID,
        transaction_date: datetime,
        notes: Optional[str] = None,
        reference_number: Optional[str] = None,
        purchase_order_id: Optional[UUID] = None,
        transaction_data: Optional[Dict[str, Any]] = None
    ) -> BatchTransaction:
        """Internal method to create batch transaction."""

        transaction = BatchTransaction(
            id=uuid4(),
            transaction_type=transaction_type.value,
            source_batch_id=source_batch_id,
            destination_batch_id=destination_batch_id,
            quantity_moved=quantity_moved,
            unit=unit,
            company_id=company_id,
            transaction_date=transaction_date,
            reference_number=reference_number,
            notes=notes,
            purchase_order_id=purchase_order_id,
            created_by_user_id=user_id,
            transaction_data=transaction_data
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        logger.info(
            "Batch transaction created",
            transaction_id=str(transaction.id),
            transaction_type=transaction_type.value
        )

        return transaction

    def create_batch_relationship(
        self,
        relationship_data: BatchRelationshipCreate,
        company_id: UUID,
        user_id: UUID
    ) -> BatchRelationship:
        """
        Create a batch relationship for traceability.

        Args:
            relationship_data: Relationship creation data
            company_id: Company creating the relationship
            user_id: User creating the relationship

        Returns:
            Created batch relationship
        """
        logger.info(
            "Creating batch relationship",
            parent_batch_id=str(relationship_data.parent_batch_id),
            child_batch_id=str(relationship_data.child_batch_id),
            relationship_type=relationship_data.relationship_type
        )

        try:
            # Validate batches exist and belong to company
            parent_batch = self.db.query(Batch).filter(
                and_(
                    Batch.id == relationship_data.parent_batch_id,
                    Batch.company_id == company_id
                )
            ).first()

            child_batch = self.db.query(Batch).filter(
                and_(
                    Batch.id == relationship_data.child_batch_id,
                    Batch.company_id == company_id
                )
            ).first()

            if not parent_batch or not child_batch:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or both batches not found or not accessible"
                )

            # Check if relationship already exists
            existing_relationship = self.db.query(BatchRelationship).filter(
                and_(
                    BatchRelationship.parent_batch_id == relationship_data.parent_batch_id,
                    BatchRelationship.child_batch_id == relationship_data.child_batch_id
                )
            ).first()

            if existing_relationship:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Batch relationship already exists"
                )

            # Create relationship
            relationship = BatchRelationship(
                id=uuid4(),
                parent_batch_id=relationship_data.parent_batch_id,
                child_batch_id=relationship_data.child_batch_id,
                relationship_type=relationship_data.relationship_type.value,
                quantity_contribution=relationship_data.quantity_contribution,
                percentage_contribution=relationship_data.percentage_contribution,
                transformation_process=relationship_data.transformation_process,
                transformation_date=relationship_data.transformation_date,
                yield_percentage=relationship_data.yield_percentage,
                quality_impact=relationship_data.quality_impact,
                created_by_user_id=user_id
            )

            self.db.add(relationship)
            self.db.commit()
            self.db.refresh(relationship)

            logger.info(
                "Batch relationship created successfully",
                relationship_id=str(relationship.id),
                parent_batch=parent_batch.batch_id,
                child_batch=child_batch.batch_id
            )

            return relationship

        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to create batch relationship",
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create batch relationship"
            )
