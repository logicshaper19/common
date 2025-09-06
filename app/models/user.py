"""
User model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class User(Base):
    """User model representing platform users."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'admin', 'buyer', 'seller'
    is_active = Column(Boolean, default=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    # company = relationship("Company", back_populates="users")

    # Performance indexes for frequently queried fields
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_company_id', 'company_id'),
        Index('idx_users_role', 'role'),
        Index('idx_users_active', 'is_active'),
        Index('idx_users_company_role', 'company_id', 'role'),
        Index('idx_users_company_active', 'company_id', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
    )
