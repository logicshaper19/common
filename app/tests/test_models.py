"""
Test-specific model definitions that work with SQLite.
This provides compatibility for testing without requiring PostgreSQL.
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4

from app.core.database import Base

# Create a separate metadata for test models to avoid conflicts
from sqlalchemy import MetaData
test_metadata = MetaData()

class TestTransformationProcessTemplate(Base):
    """Test-compatible version of TransformationProcessTemplate for SQLite."""
    __tablename__ = "test_transformation_process_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    template_name = Column(String(255), nullable=False)
    transformation_type = Column(String(50), nullable=False)
    company_type = Column(String(50), nullable=False)
    sector_id = Column(String(50), nullable=True)
    template_config = Column(JSONB, nullable=False)  # Using JSONB for PostgreSQL
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by_user_id = Column(String, ForeignKey('users.id'))
    updated_by_user_id = Column(String, ForeignKey('users.id'))
    
    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user = relationship("User", foreign_keys=[updated_by_user_id])


class TestNotificationTemplate(Base):
    """Test-compatible version of NotificationTemplate for SQLite."""
    __tablename__ = "test_notification_templates"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    event_type = Column(String(100), nullable=False)
    channel = Column(String(50), nullable=False)
    subject_template = Column(Text, nullable=True)
    body_template = Column(Text, nullable=False)
    variables = Column(JSONB, nullable=True)  # Using JSONB for PostgreSQL
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    preferences = relationship("TestUserNotificationPreferences", back_populates="template")


class TestUserNotificationPreferences(Base):
    """Test-compatible version of UserNotificationPreferences for SQLite."""
    __tablename__ = "test_user_notification_preferences"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    template_id = Column(String, ForeignKey('notification_templates.id'), nullable=False)
    is_enabled = Column(Boolean, default=True)
    delivery_method = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    template = relationship("TestNotificationTemplate", back_populates="preferences")


class TestWebhookEndpoint(Base):
    """Test-compatible version of WebhookEndpoint for SQLite."""
    __tablename__ = "test_webhook_endpoints"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    company_id = Column(String, ForeignKey('companies.id'), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSONB, nullable=False)  # Using JSONB for PostgreSQL
    secret_key = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    company = relationship("Company")


class TestNotification(Base):
    """Test-compatible version of Notification for SQLite."""
    __tablename__ = "test_notifications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String, nullable=True)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")
