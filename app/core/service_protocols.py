"""
Service Protocols for Breaking Circular Dependencies.

This module defines protocols (interfaces) for all services to enable
type-safe dependency injection without circular imports.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol, Union
from uuid import UUID
from datetime import datetime

from app.core.service_container import register_service_protocol


@register_service_protocol("brand")
class BrandServiceProtocol(Protocol):
    """Protocol for brand service operations."""
    
    def create_brand(self, brand_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new brand."""
        ...
    
    def get_brand(self, brand_id: UUID) -> Optional[Dict[str, Any]]:
        """Get brand by ID."""
        ...
    
    def get_brands_by_company(self, company_id: UUID, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all brands for a company."""
        ...
    
    def update_brand(self, brand_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a brand."""
        ...
    
    def delete_brand(self, brand_id: UUID) -> bool:
        """Delete a brand."""
        ...


@register_service_protocol("admin")
class AdminServiceProtocol(Protocol):
    """Protocol for admin service operations."""
    
    def get_company_by_id(self, company_id: UUID) -> Optional[Dict[str, Any]]:
        """Get company by ID."""
        ...
    
    def log_action(self, action: str, user_id: UUID, details: Optional[Dict[str, Any]] = None) -> None:
        """Log an admin action."""
        ...
    
    def create_audit_log(self, event_type: str, user_id: UUID, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an audit log entry."""
        ...


@register_service_protocol("user")
class UserServiceProtocol(Protocol):
    """Protocol for user service operations."""
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        ...
    
    def get_user(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        ...
    
    def update_user(self, user_id: UUID, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user."""
        ...
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user."""
        ...


@register_service_protocol("notification")
class NotificationServiceProtocol(Protocol):
    """Protocol for notification service operations."""
    
    def send_notification(
        self, 
        user_id: UUID, 
        message: str, 
        notification_type: str = "info",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a notification to a user."""
        ...
    
    def send_welcome_notification(self, user_id: UUID, user_name: str) -> None:
        """Send welcome notification to new user."""
        ...
    
    def send_brand_created_notification(self, brand_name: str, company_id: UUID) -> None:
        """Send notification about new brand creation."""
        ...
    
    def get_user_notifications(
        self, 
        user_id: UUID, 
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get notifications for a user."""
        ...


@register_service_protocol("email")
class EmailServiceProtocol(Protocol):
    """Protocol for email service operations."""
    
    def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None
    ) -> bool:
        """Send an email."""
        ...
    
    def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        ...
    
    def send_brand_notification_email(self, email: str, brand_name: str) -> bool:
        """Send email notification about brand creation."""
        ...


@register_service_protocol("product")
class ProductServiceProtocol(Protocol):
    """Protocol for product service operations."""
    
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        ...
    
    def get_product(self, product_id: UUID) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        ...
    
    def get_products_by_company(self, company_id: UUID) -> List[Dict[str, Any]]:
        """Get all products for a company."""
        ...
    
    def approve_product(self, product_id: UUID, approved_by: UUID) -> Dict[str, Any]:
        """Approve a product."""
        ...


@register_service_protocol("purchase_order")
class PurchaseOrderServiceProtocol(Protocol):
    """Protocol for purchase order service operations."""
    
    def create_purchase_order(self, po_data: Dict[str, Any], user_company_id: UUID) -> Dict[str, Any]:
        """Create a new purchase order."""
        ...
    
    def get_purchase_order(self, po_id: UUID) -> Optional[Dict[str, Any]]:
        """Get purchase order by ID."""
        ...
    
    def confirm_purchase_order(self, po_id: UUID, confirmed_by: UUID) -> Dict[str, Any]:
        """Confirm a purchase order."""
        ...
    
    def generate_po_number(self) -> str:
        """Generate a unique PO number."""
        ...


@register_service_protocol("sector")
class SectorServiceProtocol(Protocol):
    """Protocol for sector service operations."""
    
    def get_all_sectors(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all sectors."""
        ...
    
    def get_sector_by_id(self, sector_id: str) -> Optional[Dict[str, Any]]:
        """Get sector by ID."""
        ...
    
    def create_sector(self, sector_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sector."""
        ...


@register_service_protocol("document")
class DocumentServiceProtocol(Protocol):
    """Protocol for document service operations."""
    
    def upload_document(
        self, 
        file_data: bytes, 
        filename: str, 
        document_type: str,
        company_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Upload a document."""
        ...
    
    def get_document(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        ...
    
    def verify_document(self, document_id: UUID, verified_by: UUID) -> Dict[str, Any]:
        """Verify a document."""
        ...


@register_service_protocol("audit")
class AuditServiceProtocol(Protocol):
    """Protocol for audit service operations."""
    
    def log_event(
        self, 
        event_type: str, 
        user_id: UUID, 
        entity_type: str,
        entity_id: UUID,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Log an audit event."""
        ...
    
    def get_audit_trail(
        self, 
        entity_type: str, 
        entity_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get audit trail for an entity."""
        ...


@register_service_protocol("transparency")
class TransparencyServiceProtocol(Protocol):
    """Protocol for transparency service operations."""
    
    def calculate_transparency_score(self, po_id: UUID) -> Dict[str, Any]:
        """Calculate transparency score for a purchase order."""
        ...
    
    def get_supply_chain_trace(self, po_id: UUID) -> Dict[str, Any]:
        """Get supply chain traceability for a purchase order."""
        ...


@register_service_protocol("batch")
class BatchServiceProtocol(Protocol):
    """Protocol for batch service operations."""
    
    def create_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new batch."""
        ...
    
    def allocate_batch(self, batch_id: UUID, allocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Allocate a batch to a purchase order."""
        ...
    
    def get_batch_history(self, batch_id: UUID) -> List[Dict[str, Any]]:
        """Get batch allocation history."""
        ...


# Service interface registry for runtime lookup
SERVICE_INTERFACES = {
    "brand": BrandServiceProtocol,
    "admin": AdminServiceProtocol,
    "user": UserServiceProtocol,
    "notification": NotificationServiceProtocol,
    "email": EmailServiceProtocol,
    "product": ProductServiceProtocol,
    "purchase_order": PurchaseOrderServiceProtocol,
    "sector": SectorServiceProtocol,
    "document": DocumentServiceProtocol,
    "audit": AuditServiceProtocol,
    "transparency": TransparencyServiceProtocol,
    "batch": BatchServiceProtocol,
}


def get_service_interface(service_name: str) -> Protocol:
    """
    Get service interface by name.
    
    Args:
        service_name: Name of the service interface
        
    Returns:
        Service protocol class
        
    Raises:
        ValueError: If service interface not found
    """
    if service_name not in SERVICE_INTERFACES:
        raise ValueError(f"Service interface '{service_name}' not found")
    
    return SERVICE_INTERFACES[service_name]


def list_service_interfaces() -> List[str]:
    """Get list of all available service interfaces."""
    return list(SERVICE_INTERFACES.keys())
