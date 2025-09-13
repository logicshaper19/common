"""
User model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.team_invitation import TeamInvitation


class User(Base):
    """User model representing platform users."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'admin', 'buyer', 'seller' (legacy)
    is_active = Column(Boolean, default=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    # Sector-specific fields
    sector_id = Column(String(50), ForeignKey("sectors.id"), nullable=True)
    tier_level = Column(Integer, nullable=True)  # Tier level within the sector
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    # company = relationship("Company", back_populates="users")
    sector = relationship("Sector", back_populates="users")
    # sent_invitations = relationship("TeamInvitation", 
    #                               foreign_keys="[TeamInvitation.invited_by_user_id]", 
    #                               back_populates="invited_by",
    #                               lazy="select")
    # accepted_invitations = relationship("TeamInvitation", 
    #                                   foreign_keys="[TeamInvitation.accepted_by_user_id]", 
    #                                   back_populates="accepted_by",
    #                                   lazy="select")

    # Performance indexes for frequently queried fields
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_company_id', 'company_id'),
        Index('idx_users_role', 'role'),
        Index('idx_users_active', 'is_active'),
        Index('idx_users_sector_id', 'sector_id'),
        Index('idx_users_tier_level', 'tier_level'),
        Index('idx_users_company_role', 'company_id', 'role'),
        Index('idx_users_company_active', 'company_id', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
    )
