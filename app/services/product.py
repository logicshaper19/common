"""
Product service layer for business logic and validation.
"""
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4, UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from fastapi import HTTPException, status

from app.models.product import Product
from app.schemas.product import (
    ProductCreate, 
    ProductUpdate, 
    ProductFilter,
    CompositionValidation,
    CompositionValidationResponse,
    ProductCategory
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProductService:
    """Service for product management and validation."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product.
        
        Args:
            product_data: Product creation data
            
        Returns:
            Created product
            
        Raises:
            HTTPException: If product ID already exists
        """
        # Check if common_product_id already exists
        existing_product = self.db.query(Product).filter(
            Product.common_product_id == product_data.common_product_id
        ).first()
        
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with ID '{product_data.common_product_id}' already exists"
            )
        
        try:
            product = Product(
                id=uuid4(),
                common_product_id=product_data.common_product_id,
                name=product_data.name,
                description=product_data.description,
                category=product_data.category.value,
                can_have_composition=product_data.can_have_composition,
                material_breakdown=product_data.material_breakdown,
                default_unit=product_data.default_unit,
                hs_code=product_data.hs_code,
                origin_data_requirements=product_data.origin_data_requirements
            )
            
            self.db.add(product)
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(
                "Product created successfully",
                product_id=str(product.id),
                common_product_id=product.common_product_id,
                name=product.name
            )
            
            return product
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create product", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product"
            )
    
    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """
        Get product by ID.

        Args:
            product_id: Product UUID

        Returns:
            Product or None
        """
        try:
            uuid_obj = UUID(product_id)
            return self.db.query(Product).filter(Product.id == uuid_obj).first()
        except ValueError:
            return None
    
    def get_product_by_common_id(self, common_product_id: str) -> Optional[Product]:
        """
        Get product by common product ID.
        
        Args:
            common_product_id: Common product identifier
            
        Returns:
            Product or None
        """
        return self.db.query(Product).filter(
            Product.common_product_id == common_product_id
        ).first()
    
    def update_product(self, product_id: str, product_data: ProductUpdate) -> Product:
        """
        Update a product.

        Args:
            product_id: Product UUID
            product_data: Product update data

        Returns:
            Updated product

        Raises:
            HTTPException: If product not found
        """
        try:
            uuid_obj = UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format"
            )

        product = self.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        try:
            # Update only provided fields
            update_data = product_data.dict(exclude_unset=True)
            
            # Convert enum to string if category is being updated
            if 'category' in update_data:
                update_data['category'] = update_data['category'].value
            
            for field, value in update_data.items():
                setattr(product, field, value)
            
            self.db.commit()
            self.db.refresh(product)
            
            logger.info(
                "Product updated successfully",
                product_id=str(product.id),
                updated_fields=list(update_data.keys())
            )
            
            return product
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update product", product_id=product_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product"
            )
    
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product.

        Args:
            product_id: Product UUID

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If product not found
        """
        try:
            uuid_obj = UUID(product_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format"
            )

        product = self.get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        try:
            self.db.delete(product)
            self.db.commit()
            
            logger.info("Product deleted successfully", product_id=product_id)
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete product", product_id=product_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product"
            )
    
    def list_products(self, filters: ProductFilter) -> Tuple[List[Product], int]:
        """
        List products with filtering and pagination.
        
        Args:
            filters: Product filtering criteria
            
        Returns:
            Tuple of (products, total_count)
        """
        query = self.db.query(Product)
        
        # Apply filters
        if filters.category:
            query = query.filter(Product.category == filters.category.value)
        
        if filters.can_have_composition is not None:
            query = query.filter(Product.can_have_composition == filters.can_have_composition)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.common_product_id.ilike(search_term)
                )
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        products = query.offset(offset).limit(filters.per_page).all()
        
        return products, total_count
    
    def validate_composition(self, validation_data: CompositionValidation) -> CompositionValidationResponse:
        """
        Validate product composition against defined rules.
        
        Args:
            validation_data: Composition validation request
            
        Returns:
            Validation response with errors and warnings
        """
        product = self.get_product_by_id(str(validation_data.product_id))
        if not product:
            return CompositionValidationResponse(
                is_valid=False,
                errors=["Product not found"]
            )
        
        errors = []
        warnings = []
        
        # Check if product can have composition
        if not product.can_have_composition:
            errors.append("This product type does not support composition")
        
        # Validate against material breakdown rules
        if product.material_breakdown and product.can_have_composition:
            allowed_materials = set(product.material_breakdown.keys())
            provided_materials = set(validation_data.composition.keys())
            
            # Check for unknown materials
            unknown_materials = provided_materials - allowed_materials
            if unknown_materials:
                errors.append(f"Unknown materials: {', '.join(unknown_materials)}")
            
            # Check for missing required materials (if any are defined as required)
            # For now, we'll treat all materials in breakdown as optional
            # This could be enhanced with required/optional material specifications
            
            # Validate percentage ranges if defined in material breakdown
            for material, percentage in validation_data.composition.items():
                if material in product.material_breakdown:
                    expected_percentage = product.material_breakdown[material]
                    # Allow some tolerance (±5%) for practical purposes
                    tolerance = 5.0
                    if abs(percentage - expected_percentage) > tolerance:
                        warnings.append(
                            f"Material '{material}': {percentage}% differs from expected {expected_percentage}% "
                            f"(tolerance: ±{tolerance}%)"
                        )
        
        # Additional validation based on product category
        if product.category == "raw_material":
            if validation_data.composition:
                warnings.append("Raw materials typically don't have composition breakdown")
        
        is_valid = len(errors) == 0
        
        logger.info(
            "Composition validation completed",
            product_id=str(validation_data.product_id),
            is_valid=is_valid,
            error_count=len(errors),
            warning_count=len(warnings)
        )
        
        return CompositionValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
