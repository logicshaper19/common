"""
Sector and Tier Models for Common Supply Chain Platform
Supports sector-specific tier configurations
"""
import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Sector(Base):
    """
    Represents a business sector (e.g., palm_oil, apparel, electronics)
    Each sector has its own tier structure and terminology
    """
    __tablename__ = "sectors"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    regulatory_focus = Column(JSON)  # List of regulations like EUDR, UFLPA
    
    # Relationships
    tiers = relationship("SectorTier", back_populates="sector", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="sector")
    users = relationship("User", back_populates="sector")


class SectorTier(Base):
    """
    Defines tier structure for each sector
    E.g., Palm Oil: Brand(1), Refinery(2), Trader(3), Mill(4), Cooperative(5)
    """
    __tablename__ = "sector_tiers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sector_id = Column(String(50), ForeignKey("sectors.id"), nullable=False)
    level = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_originator = Column(Boolean, default=False)  # True for entities that add origin data
    required_data_fields = Column(JSON)  # List of required fields for this tier
    permissions = Column(JSON)  # List of permissions for this tier
    
    # Relationships
    sector = relationship("Sector", back_populates="tiers")
    
    class Config:
        from_attributes = True


class SectorProduct(Base):
    """
    Products specific to each sector with tier applicability
    """
    __tablename__ = "sector_products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sector_id = Column(String(50), ForeignKey("sectors.id"), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    hs_code = Column(String(20))  # Harmonized System code
    specifications = Column(JSON)  # Product-specific data requirements
    applicable_tiers = Column(JSON)  # List of tier levels that can use this product
    
    # Relationships
    sector = relationship("Sector")
    
    class Config:
        from_attributes = True
