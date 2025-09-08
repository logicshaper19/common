"""
Purchase Order Service - Modular Architecture

This package provides a modular, testable, and maintainable architecture for
purchase order management, replacing the monolithic PurchaseOrderService.

The architecture follows domain-driven design principles with clear separation
of concerns:

- service.py: Main orchestrator coordinating all operations
- validators.py: All validation logic and business rules
- repository.py: Database operations and data access
- audit_manager.py: Audit logging and compliance tracking
- notification_manager.py: Event notifications and messaging
- traceability_service.py: Supply chain tracing and lineage
- po_number_generator.py: PO number generation logic
- exceptions.py: Custom exception hierarchy

Usage:
    from app.services.purchase_order import create_purchase_order_service
    
    # Create service with dependency injection
    service = create_purchase_order_service(db)
    
    # Create purchase order
    po = service.create_purchase_order(po_data, user_company_id)
    
    # Get traceability
    trace = service.trace_supply_chain(trace_request)
"""

from sqlalchemy.orm import Session
from typing import Optional

from .service import PurchaseOrderOrchestrator
from .validators import PurchaseOrderValidator
from .repository import PurchaseOrderRepository
from .audit_manager import PurchaseOrderAuditManager
from .notification_manager import NotificationManager
from .traceability_service import TraceabilityService
from .po_number_generator import PONumberGenerator
from .exceptions import (
    PurchaseOrderError,
    PurchaseOrderValidationError,
    PurchaseOrderNotFoundError,
    PurchaseOrderPermissionError
)


def create_purchase_order_service(db: Session) -> PurchaseOrderOrchestrator:
    """
    Factory function to create purchase order service with dependencies.
    
    Args:
        db: Database session
        
    Returns:
        Configured PurchaseOrderOrchestrator instance
    """
    
    # Create specialized services
    repository = PurchaseOrderRepository(db)
    validator = PurchaseOrderValidator(db)
    audit_manager = PurchaseOrderAuditManager(db)
    notification_manager = NotificationManager(db)
    po_generator = PONumberGenerator(db)
    traceability_service = TraceabilityService(db)
    
    # Create main orchestrator
    return PurchaseOrderOrchestrator(
        db=db,
        repository=repository,
        validator=validator,
        audit_manager=audit_manager,
        notification_manager=notification_manager,
        po_generator=po_generator,
        traceability_service=traceability_service
    )


# Backward compatibility wrapper
class PurchaseOrderService:
    """
    Legacy wrapper for backward compatibility.
    
    This class maintains the same interface as the original monolithic service
    while delegating to the new modular architecture internally.
    """
    
    def __init__(self, db: Session):
        self._orchestrator = create_purchase_order_service(db)
        self.db = db  # Keep for any legacy code that accesses db directly
        
        # Legacy compatibility - expose product service
        from app.services.product import ProductService
        self.product_service = ProductService(db)
    
    def generate_po_number(self) -> str:
        """Delegate to new orchestrator."""
        return self._orchestrator.generate_po_number()
    
    def create_purchase_order(self, po_data, current_user_company_id):
        """Delegate to new orchestrator."""
        return self._orchestrator.create_purchase_order(po_data, current_user_company_id)
    
    def get_purchase_order_by_id(self, po_id: str):
        """Delegate to new orchestrator."""
        return self._orchestrator.get_purchase_order_by_id(po_id)
    
    def get_purchase_order_with_details(self, po_id: str):
        """Delegate to new orchestrator."""
        return self._orchestrator.get_purchase_order_with_details(po_id)
    
    def update_purchase_order(self, po_id: str, po_data, current_user_company_id):
        """Delegate to new orchestrator."""
        return self._orchestrator.update_purchase_order(po_id, po_data, current_user_company_id)
    
    def delete_purchase_order(self, po_id: str, current_user_company_id):
        """Delegate to new orchestrator."""
        return self._orchestrator.delete_purchase_order(po_id, current_user_company_id)
    
    def list_purchase_orders(self, filters, current_user_company_id):
        """Delegate to new orchestrator."""
        return self._orchestrator.list_purchase_orders(filters, current_user_company_id)

    def list_purchase_orders_with_details(self, filters, current_user_company_id):
        """Delegate to new orchestrator for detailed purchase orders."""
        return self._orchestrator.list_purchase_orders_with_details(filters, current_user_company_id)

    def trace_supply_chain(self, request):
        """Delegate to new orchestrator."""
        return self._orchestrator.trace_supply_chain(request)
    
    def get_traceability_data(self, po_id: str, max_depth: int = 5):
        """Delegate to new orchestrator."""
        return self._orchestrator.get_traceability_data(po_id, max_depth)

    # Phase 1 MVP Amendment Methods
    def propose_changes(self, po_id: str, proposal, current_user):
        """Delegate to new orchestrator."""
        return self._orchestrator.propose_changes(po_id, proposal, current_user)

    def approve_changes(self, po_id: str, approval, current_user):
        """Delegate to new orchestrator."""
        return self._orchestrator.approve_changes(po_id, approval, current_user)

    def get_purchase_order(self, po_id: str):
        """Get purchase order by ID (for amendment validation)."""
        return self._orchestrator.get_purchase_order_by_id(po_id)

    # Admin-only methods
    def list_purchase_orders_admin(self, filters):
        """
        List all purchase orders for admin (no company filtering).
        Admin can see all purchase orders across all companies.
        """
        return self._orchestrator.list_purchase_orders_admin(filters)

    def delete_purchase_order_admin(self, po_id: str) -> bool:
        """
        Delete purchase order as admin (no company permission check).
        Admin can delete any purchase order for administrative purposes.
        """
        return self._orchestrator.delete_purchase_order_admin(po_id)


__all__ = [
    "create_purchase_order_service",
    "PurchaseOrderService",  # For backward compatibility
    "PurchaseOrderOrchestrator",
    "PurchaseOrderError",
    "PurchaseOrderValidationError",
    "PurchaseOrderNotFoundError",
    "PurchaseOrderPermissionError",
]
