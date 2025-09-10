"""
Service Container and Dependency Injection System.

This module provides a comprehensive dependency injection container to eliminate
tight coupling between services and ensure proper session management.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Dict, Type, TypeVar, Generic, Callable, Any, Optional, Protocol
from functools import lru_cache, wraps
from contextlib import contextmanager
from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ServiceProtocol(Protocol):
    """Base protocol for all services."""
    pass


class BaseService(ABC):
    """
    Base service class with proper session management.
    
    All services should inherit from this class to ensure:
    - Proper database session handling
    - Transaction management
    - Resource cleanup
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._transaction_active = False
    
    def __enter__(self):
        """Enter transaction context."""
        self._transaction_active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context with proper cleanup."""
        if self._transaction_active:
            try:
                if exc_type is not None:
                    logger.warning(
                        "Rolling back transaction due to exception",
                        service=self.__class__.__name__,
                        exception=str(exc_val)
                    )
                    self.db.rollback()
                else:
                    self.db.commit()
                    logger.debug(
                        "Transaction committed successfully",
                        service=self.__class__.__name__
                    )
            except Exception as e:
                logger.error(
                    "Failed to commit transaction",
                    service=self.__class__.__name__,
                    error=str(e)
                )
                self.db.rollback()
                raise
            finally:
                self._transaction_active = False


class ServiceFactory:
    """
    Factory for creating service instances with proper dependency injection.
    """
    
    def __init__(self):
        self._service_factories: Dict[Type, Callable] = {}
        self._singleton_instances: Dict[Type, Any] = {}
    
    def register(
        self, 
        service_type: Type[T], 
        factory_func: Callable[[Session], T],
        singleton: bool = False
    ) -> None:
        """
        Register a service factory function.
        
        Args:
            service_type: The service class/interface type
            factory_func: Function that creates the service instance
            singleton: Whether to create singleton instances
        """
        self._service_factories[service_type] = factory_func
        if singleton:
            self._singleton_instances[service_type] = None
        
        logger.debug(
            "Service registered",
            service_type=service_type.__name__,
            singleton=singleton
        )
    
    def create(self, service_type: Type[T], db: Session) -> T:
        """
        Create a service instance.
        
        Args:
            service_type: The service type to create
            db: Database session
            
        Returns:
            Service instance
        """
        if service_type not in self._service_factories:
            raise ValueError(f"Service {service_type.__name__} not registered")
        
        # Check for singleton
        if service_type in self._singleton_instances:
            if self._singleton_instances[service_type] is None:
                self._singleton_instances[service_type] = self._service_factories[service_type](db)
            return self._singleton_instances[service_type]
        
        # Create new instance
        return self._service_factories[service_type](db)
    
    def get_registered_services(self) -> Dict[str, bool]:
        """Get list of registered services."""
        return {
            service_type.__name__: service_type in self._singleton_instances
            for service_type in self._service_factories.keys()
        }


class ServiceContainer:
    """
    Main service container for dependency injection.
    
    This container manages service creation, dependency resolution,
    and lifecycle management.
    """
    
    def __init__(self):
        self.factory = ServiceFactory()
        self._initialized = False
    
    def register_service(
        self, 
        service_type: Type[T], 
        factory_func: Callable[[Session], T],
        singleton: bool = False
    ) -> None:
        """Register a service with the container."""
        self.factory.register(service_type, factory_func, singleton)
    
    def get_service(self, service_type: Type[T], db: Session) -> T:
        """Get a service instance."""
        return self.factory.create(service_type, db)
    
    def initialize_services(self) -> None:
        """Initialize all registered services."""
        if self._initialized:
            return
        
        # Import and register all services
        self._register_core_services()
        self._register_business_services()
        self._register_utility_services()
        
        self._initialized = True
        logger.info(
            "Service container initialized",
            registered_services=list(self.factory.get_registered_services().keys())
        )
    
    def _register_core_services(self) -> None:
        """Register core services."""
        # These imports are safe as they don't create circular dependencies
        from app.services.purchase_order import create_purchase_order_service
        from app.services.origin_validation import create_origin_validation_service
        from app.services.viral_analytics import create_viral_analytics_service
        from app.services.erp_sync import create_erp_sync_manager
        
        # Register with factory functions
        self.factory.register(
            type(create_purchase_order_service(None)),  # Get type from factory
            create_purchase_order_service
        )
    
    def _register_business_services(self) -> None:
        """Register business domain services."""
        # Import services that don't have circular dependencies
        try:
            from app.services.brand_service import BrandService
            self.factory.register(BrandService, lambda db: BrandService(db))
        except ImportError:
            logger.warning("BrandService not available")
        
        try:
            from app.services.sector_service import SectorService
            self.factory.register(SectorService, lambda db: SectorService(db))
        except ImportError:
            logger.warning("SectorService not available")
    
    def _register_utility_services(self) -> None:
        """Register utility services."""
        try:
            from app.services.data_access_control.service import DataAccessControlService
            self.factory.register(
                DataAccessControlService, 
                lambda db: DataAccessControlService(db)
            )
        except ImportError:
            logger.warning("DataAccessControlService not available")


# Global container instance
_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
        _container.initialize_services()
    return _container


@contextmanager
def service_transaction(db: Session, *service_types: Type):
    """
    Context manager for multiple services in a single transaction.
    
    Args:
        db: Database session
        *service_types: Service types to create
        
    Yields:
        Tuple of service instances
    """
    container = get_container()
    services = [container.get_service(service_type, db) for service_type in service_types]
    
    try:
        # Enter all service contexts
        for service in services:
            if hasattr(service, '__enter__'):
                service.__enter__()
        
        yield tuple(services)
        
        # Commit transaction
        db.commit()
        logger.debug("Multi-service transaction committed successfully")
        
    except Exception as e:
        logger.error("Multi-service transaction failed", error=str(e))
        db.rollback()
        raise
    finally:
        # Exit all service contexts
        for service in services:
            if hasattr(service, '__exit__'):
                try:
                    service.__exit__(None, None, None)
                except Exception as exit_error:
                    logger.warning(
                        "Error during service context exit",
                        service=service.__class__.__name__,
                        error=str(exit_error)
                    )


def service_dependency(service_type: Type[T]):
    """
    Decorator to inject services as dependencies.
    
    Usage:
        @service_dependency(BrandService)
        def my_function(brand_service: BrandService, db: Session):
            # brand_service is automatically injected
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get database session from kwargs or args
            db = kwargs.get('db')
            if not db:
                # Try to find db in args
                for arg in args:
                    if hasattr(arg, 'query'):  # Duck typing for Session
                        db = arg
                        break
            
            if not db:
                raise ValueError("Database session not found in function arguments")
            
            # Inject service
            container = get_container()
            service_instance = container.get_service(service_type, db)
            
            # Add service to kwargs
            service_param_name = service_type.__name__.lower().replace('service', '_service')
            kwargs[service_param_name] = service_instance
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class ServiceRegistry:
    """
    Registry for service protocols and implementations.
    
    This helps break circular dependencies by defining interfaces
    that services can depend on without importing concrete implementations.
    """
    
    def __init__(self):
        self._protocols: Dict[str, Type] = {}
        self._implementations: Dict[str, Type] = {}
    
    def register_protocol(self, name: str, protocol_type: Type) -> None:
        """Register a service protocol."""
        self._protocols[name] = protocol_type
        logger.debug("Protocol registered", name=name, type=protocol_type.__name__)
    
    def register_implementation(self, protocol_name: str, implementation_type: Type) -> None:
        """Register an implementation for a protocol."""
        if protocol_name not in self._protocols:
            raise ValueError(f"Protocol {protocol_name} not registered")
        
        self._implementations[protocol_name] = implementation_type
        logger.debug(
            "Implementation registered",
            protocol=protocol_name,
            implementation=implementation_type.__name__
        )
    
    def get_protocol(self, name: str) -> Type:
        """Get a protocol by name."""
        if name not in self._protocols:
            raise ValueError(f"Protocol {name} not found")
        return self._protocols[name]
    
    def get_implementation(self, protocol_name: str) -> Type:
        """Get an implementation for a protocol."""
        if protocol_name not in self._implementations:
            raise ValueError(f"Implementation for protocol {protocol_name} not found")
        return self._implementations[protocol_name]


# Global registry instance
service_registry = ServiceRegistry()


def register_service_protocol(name: str):
    """Decorator to register a service protocol."""
    def decorator(protocol_class: Type) -> Type:
        service_registry.register_protocol(name, protocol_class)
        return protocol_class
    return decorator


def register_service_implementation(protocol_name: str):
    """Decorator to register a service implementation."""
    def decorator(implementation_class: Type) -> Type:
        service_registry.register_implementation(protocol_name, implementation_class)
        return implementation_class
    return decorator
