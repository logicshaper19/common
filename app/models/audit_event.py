"""
Audit Event model for the Common supply chain platform.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.models.base import JSONType


class AuditEvent(Base):
    """Audit Event model for tracking all PO modifications."""
    
    __tablename__ = "audit_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_id = Column(UUID(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    event_type = Column(String(100), nullable=False)  # 'created', 'confirmed', 'composition_updated'
    actor_company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    data = Column(JSONType, nullable=False)  # Full snapshot of changes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
