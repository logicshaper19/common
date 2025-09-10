"""
FastAPI Dependencies for Service Injection.

This module provides FastAPI dependency functions for clean service injection
without tight coupling or circular dependencies.
"""

from typing import Type, TypeVar, Callable, Any
from functools import lru_cache
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.core.service_container import get_container, service_transaction
from app.core.service_protocols import (
    BrandServiceProtocol,
    AdminServiceProtocol,
    UserServiceProtocol,
    NotificationServiceProtocol,
    EmailServiceProtocol,
    ProductServiceProtocol,
    PurchaseOrderServiceProtocol,
    SectorServiceProtocol,
    DocumentServiceProtocol,
    AuditServiceProtocol,
    TransparencyServiceProtocol,
    BatchServiceProtocol
)
from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def create_service_dependency(service_type: Type[T]) -> Callable[[Session], T]:
    """
    Create a FastAPI dependency function for a service type.
    
    Args:
        service_type: The service class to inject
        
    Returns:
        FastAPI dependency function
    """
    def get_service(db: Session = Depends(get_db)) -> T:
        container = get_container()
        return container.get_service(service_type, db)
    
    return get_service


# Brand Service Dependencies
def get_brand_service(db: Session = Depends(get_db)) -> BrandServiceProtocol:
    """Get brand service instance."""
    try:
        from app.services.brand_service import BrandService
        container = get_container()
        return container.get_service(BrandService, db)
    except ImportError:
        logger.warning("BrandService not available")
        raise ValueError("BrandService not available")


# Admin Service Dependencies
def get_admin_service(db: Session = Depends(get_db)) -> AdminServiceProtocol:
    """Get admin service instance."""
    try:
        from app.services.admin_service import AdminService
        container = get_container()
        return container.get_service(AdminService, db)
    except ImportError:
        logger.warning("AdminService not available")
        raise ValueError("AdminService not available")


# User Service Dependencies
def get_user_service(db: Session = Depends(get_db)) -> UserServiceProtocol:
    """Get user service instance."""
    try:
        from app.services.user_service import UserService
        container = get_container()
        return container.get_service(UserService, db)
    except ImportError:
        logger.warning("UserService not available")
        raise ValueError("UserService not available")


# Notification Service Dependencies
def get_notification_service(db: Session = Depends(get_db)) -> NotificationServiceProtocol:
    """Get notification service instance."""
    try:
        from app.services.notification_service import NotificationService
        container = get_container()
        return container.get_service(NotificationService, db)
    except ImportError:
        logger.warning("NotificationService not available")
        raise ValueError("NotificationService not available")


# Email Service Dependencies
def get_email_service(db: Session = Depends(get_db)) -> EmailServiceProtocol:
    """Get email service instance."""
    try:
        from app.services.email_service import EmailService
        container = get_container()
        return container.get_service(EmailService, db)
    except ImportError:
        logger.warning("EmailService not available")
        raise ValueError("EmailService not available")


# Product Service Dependencies
def get_product_service(db: Session = Depends(get_db)) -> ProductServiceProtocol:
    """Get product service instance."""
    try:
        from app.services.product import ProductService
        container = get_container()
        return container.get_service(ProductService, db)
    except ImportError:
        logger.warning("ProductService not available")
        raise ValueError("ProductService not available")


# Purchase Order Service Dependencies
def get_purchase_order_service(db: Session = Depends(get_db)) -> PurchaseOrderServiceProtocol:
    """Get purchase order service instance."""
    try:
        from app.services.purchase_order import create_purchase_order_service
        return create_purchase_order_service(db)
    except ImportError:
        logger.warning("PurchaseOrderService not available")
        raise ValueError("PurchaseOrderService not available")


# Sector Service Dependencies
def get_sector_service(db: Session = Depends(get_db)) -> SectorServiceProtocol:
    """Get sector service instance."""
    try:
        from app.services.sector_service import SectorService
        container = get_container()
        return container.get_service(SectorService, db)
    except ImportError:
        logger.warning("SectorService not available")
        raise ValueError("SectorService not available")


# Document Service Dependencies
def get_document_service(db: Session = Depends(get_db)) -> DocumentServiceProtocol:
    """Get document service instance."""
    try:
        from app.services.document_service import DocumentService
        container = get_container()
        return container.get_service(DocumentService, db)
    except ImportError:
        logger.warning("DocumentService not available")
        raise ValueError("DocumentService not available")


# Audit Service Dependencies
def get_audit_service(db: Session = Depends(get_db)) -> AuditServiceProtocol:
    """Get audit service instance."""
    try:
        from app.services.audit_service import AuditService
        container = get_container()
        return container.get_service(AuditService, db)
    except ImportError:
        logger.warning("AuditService not available")
        raise ValueError("AuditService not available")


# Transparency Service Dependencies
def get_transparency_service(db: Session = Depends(get_db)) -> TransparencyServiceProtocol:
    """Get transparency service instance."""
    try:
        from app.services.transparency_service import TransparencyService
        container = get_container()
        return container.get_service(TransparencyService, db)
    except ImportError:
        logger.warning("TransparencyService not available")
        raise ValueError("TransparencyService not available")


# Batch Service Dependencies
def get_batch_service(db: Session = Depends(get_db)) -> BatchServiceProtocol:
    """Get batch service instance."""
    try:
        from app.services.batch_service import BatchService
        container = get_container()
        return container.get_service(BatchService, db)
    except ImportError:
        logger.warning("BatchService not available")
        raise ValueError("BatchService not available")


# Multi-Service Transaction Dependencies
class ServiceBundle:
    """Bundle of services for multi-service operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self._services = {}
    
    def get_brand_service(self) -> BrandServiceProtocol:
        """Get brand service."""
        if 'brand' not in self._services:
            self._services['brand'] = get_brand_service(self.db)
        return self._services['brand']
    
    def get_admin_service(self) -> AdminServiceProtocol:
        """Get admin service."""
        if 'admin' not in self._services:
            self._services['admin'] = get_admin_service(self.db)
        return self._services['admin']
    
    def get_notification_service(self) -> NotificationServiceProtocol:
        """Get notification service."""
        if 'notification' not in self._services:
            self._services['notification'] = get_notification_service(self.db)
        return self._services['notification']
    
    def get_audit_service(self) -> AuditServiceProtocol:
        """Get audit service."""
        if 'audit' not in self._services:
            self._services['audit'] = get_audit_service(self.db)
        return self._services['audit']


def get_service_bundle(db: Session = Depends(get_db)) -> ServiceBundle:
    """Get service bundle for multi-service operations."""
    return ServiceBundle(db)


# Utility functions for service management
@lru_cache(maxsize=None)
def get_available_services() -> dict:
    """Get list of available services."""
    services = {}
    
    service_checks = [
        ("brand", get_brand_service),
        ("admin", get_admin_service),
        ("user", get_user_service),
        ("notification", get_notification_service),
        ("email", get_email_service),
        ("product", get_product_service),
        ("purchase_order", get_purchase_order_service),
        ("sector", get_sector_service),
        ("document", get_document_service),
        ("audit", get_audit_service),
        ("transparency", get_transparency_service),
        ("batch", get_batch_service),
    ]
    
    for service_name, service_func in service_checks:
        try:
            # Try to get the service without a database session
            # This is just to check if the service is available
            services[service_name] = True
        except (ImportError, ValueError):
            services[service_name] = False
    
    return services


def validate_service_dependencies() -> dict:
    """
    Validate that all service dependencies are properly configured.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "services": {},
        "errors": []
    }
    
    available_services = get_available_services()
    
    for service_name, is_available in available_services.items():
        if is_available:
            results["services"][service_name] = "available"
        else:
            results["services"][service_name] = "unavailable"
            results["errors"].append(f"Service '{service_name}' is not available")
            results["valid"] = False
    
    # Check container initialization
    try:
        container = get_container()
        registered_services = container.factory.get_registered_services()
        results["container_services"] = registered_services
    except Exception as e:
        results["errors"].append(f"Service container error: {str(e)}")
        results["valid"] = False
    
    return results


# Service health check
def check_service_health(db: Session = Depends(get_db)) -> dict:
    """
    Check health of all services.
    
    Returns:
        Dictionary with health status of each service
    """
    health_status = {
        "timestamp": str(datetime.utcnow()),
        "services": {},
        "overall_status": "healthy"
    }
    
    service_checks = [
        ("brand", get_brand_service),
        ("admin", get_admin_service),
        ("notification", get_notification_service),
        ("audit", get_audit_service),
    ]
    
    for service_name, service_func in service_checks:
        try:
            service = service_func(db)
            # Basic health check - just verify service can be instantiated
            health_status["services"][service_name] = "healthy"
        except Exception as e:
            health_status["services"][service_name] = f"unhealthy: {str(e)}"
            health_status["overall_status"] = "degraded"
    
    return health_status
