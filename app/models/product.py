"""
Product model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.base import JSONType


class Product(Base):
    """Product model representing standardized products in the catalog."""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    common_product_id = Column(String(100), unique=True, nullable=False)  # e.g., 'palm_refined_edible'
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False)  # 'raw_material', 'processed', 'finished_good'
    can_have_composition = Column(Boolean, default=False)
    material_breakdown = Column(JSONType)  # Composition rules
    default_unit = Column(String(20), nullable=False)  # 'KGM', 'MT'
    hs_code = Column(String(50))  # For trade compliance
    origin_data_requirements = Column(JSONType)  # Required origin data fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Performance indexes for frequently queried fields
    __table_args__ = (
        Index('idx_products_common_id', 'common_product_id'),
        Index('idx_products_category', 'category'),
        Index('idx_products_hs_code', 'hs_code'),
        Index('idx_products_name', 'name'),
        Index('idx_products_composition', 'can_have_composition'),
        Index('idx_products_category_composition', 'category', 'can_have_composition'),
        Index('idx_products_created_at', 'created_at'),
    )
