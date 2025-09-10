"""
Event-Driven Architecture System.

This module provides a comprehensive event system to decouple services
and eliminate circular dependencies through publisher-subscriber patterns.
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, List, Callable, Any, Optional, Union, Type
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from functools import wraps

from app.core.logging import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """Enumeration of all system events."""
    
    # User events
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    
    # Company events
    COMPANY_CREATED = "company_created"
    COMPANY_UPDATED = "company_updated"
    COMPANY_VERIFIED = "company_verified"
    
    # Brand events
    BRAND_CREATED = "brand_created"
    BRAND_UPDATED = "brand_updated"
    BRAND_DELETED = "brand_deleted"
    
    # Purchase Order events
    PO_CREATED = "po_created"
    PO_CONFIRMED = "po_confirmed"
    PO_UPDATED = "po_updated"
    PO_CANCELLED = "po_cancelled"
    PO_COMPLETED = "po_completed"
    
    # Product events
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_APPROVED = "product_approved"
    
    # Batch events
    BATCH_CREATED = "batch_created"
    BATCH_ALLOCATED = "batch_allocated"
    BATCH_CONSUMED = "batch_consumed"
    
    # Document events
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_VERIFIED = "document_verified"
    DOCUMENT_REJECTED = "document_rejected"
    
    # Notification events
    NOTIFICATION_CREATED = "notification_created"
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_READ = "notification_read"
    
    # Audit events
    AUDIT_LOG_CREATED = "audit_log_created"
    SECURITY_VIOLATION = "security_violation"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    HEALTH_CHECK = "health_check"


@dataclass
class Event:
    """
    Base event class for all system events.
    
    Events are immutable data structures that represent something
    that has happened in the system.
    """
    
    event_type: EventType
    data: Dict[str, Any]
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[UUID] = None
    company_id: Optional[UUID] = None
    correlation_id: Optional[UUID] = None
    source_service: Optional[str] = None
    
    def __post_init__(self):
        """Ensure event is properly initialized."""
        if not isinstance(self.event_type, EventType):
            raise ValueError("event_type must be an EventType enum")
        
        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': str(self.event_id),
            'event_type': self.event_type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'user_id': str(self.user_id) if self.user_id else None,
            'company_id': str(self.company_id) if self.company_id else None,
            'correlation_id': str(self.correlation_id) if self.correlation_id else None,
            'source_service': self.source_service
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            event_id=UUID(data['event_id']),
            event_type=EventType(data['event_type']),
            data=data['data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            user_id=UUID(data['user_id']) if data.get('user_id') else None,
            company_id=UUID(data['company_id']) if data.get('company_id') else None,
            correlation_id=UUID(data['correlation_id']) if data.get('correlation_id') else None,
            source_service=data.get('source_service')
        )


class EventHandler(ABC):
    """Abstract base class for event handlers."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event."""
        pass
    
    @property
    @abstractmethod
    def event_types(self) -> List[EventType]:
        """Return list of event types this handler can process."""
        pass


class EventBus:
    """
    Event bus for publishing and subscribing to events.
    
    This implements the publisher-subscriber pattern to decouple
    services and eliminate circular dependencies.
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._async_handlers: Dict[EventType, List[Callable]] = {}
        self._middleware: List[Callable] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type with a synchronous handler.
        
        Args:
            event_type: The event type to subscribe to
            handler: Function to call when event is published
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.debug(
            "Handler subscribed to event",
            event_type=event_type.value,
            handler=handler.__name__
        )
    
    def subscribe_async(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to an event type with an asynchronous handler.
        
        Args:
            event_type: The event type to subscribe to
            handler: Async function to call when event is published
        """
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        
        self._async_handlers[event_type].append(handler)
        logger.debug(
            "Async handler subscribed to event",
            event_type=event_type.value,
            handler=handler.__name__
        )
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
        
        if event_type in self._async_handlers and handler in self._async_handlers[event_type]:
            self._async_handlers[event_type].remove(handler)
        
        logger.debug(
            "Handler unsubscribed from event",
            event_type=event_type.value,
            handler=handler.__name__
        )
    
    def add_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Add middleware to process events before handlers."""
        self._middleware.append(middleware)
        logger.debug("Event middleware added", middleware=middleware.__name__)
    
    def publish(self, event: Event) -> None:
        """
        Publish an event synchronously.
        
        Args:
            event: The event to publish
        """
        try:
            # Apply middleware
            processed_event = event
            for middleware in self._middleware:
                processed_event = middleware(processed_event)
            
            # Add to history
            self._add_to_history(processed_event)
            
            # Call synchronous handlers
            if processed_event.event_type in self._handlers:
                for handler in self._handlers[processed_event.event_type]:
                    try:
                        handler(processed_event)
                    except Exception as e:
                        logger.error(
                            "Event handler failed",
                            event_type=processed_event.event_type.value,
                            handler=handler.__name__,
                            error=str(e)
                        )
            
            logger.debug(
                "Event published",
                event_type=processed_event.event_type.value,
                event_id=str(processed_event.event_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to publish event",
                event_type=event.event_type.value,
                error=str(e)
            )
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: The event to publish
        """
        try:
            # Apply middleware
            processed_event = event
            for middleware in self._middleware:
                processed_event = middleware(processed_event)
            
            # Add to history
            self._add_to_history(processed_event)
            
            # Call synchronous handlers first
            self.publish(processed_event)
            
            # Call asynchronous handlers
            if processed_event.event_type in self._async_handlers:
                tasks = []
                for handler in self._async_handlers[processed_event.event_type]:
                    tasks.append(self._safe_async_handler(handler, processed_event))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.debug(
                "Async event published",
                event_type=processed_event.event_type.value,
                event_id=str(processed_event.event_id)
            )
            
        except Exception as e:
            logger.error(
                "Failed to publish async event",
                event_type=event.event_type.value,
                error=str(e)
            )
    
    async def _safe_async_handler(self, handler: Callable, event: Event) -> None:
        """Safely execute an async event handler."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                "Async event handler failed",
                event_type=event.event_type.value,
                handler=handler.__name__,
                error=str(e)
            )
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history with size limit."""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def get_event_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """Get event history, optionally filtered by type."""
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type]
        return self._event_history.copy()
    
    def get_subscription_info(self) -> Dict[str, int]:
        """Get information about current subscriptions."""
        info = {}
        for event_type in EventType:
            sync_count = len(self._handlers.get(event_type, []))
            async_count = len(self._async_handlers.get(event_type, []))
            if sync_count > 0 or async_count > 0:
                info[event_type.value] = {
                    'sync_handlers': sync_count,
                    'async_handlers': async_count
                }
        return info


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


def event_handler(event_types: Union[EventType, List[EventType]]):
    """
    Decorator to register a function as an event handler.
    
    Usage:
        @event_handler(EventType.USER_CREATED)
        def handle_user_created(event: Event):
            # Handle user created event
            pass
    """
    if isinstance(event_types, EventType):
        event_types = [event_types]
    
    def decorator(func: Callable[[Event], None]) -> Callable:
        event_bus = get_event_bus()
        
        for event_type in event_types:
            if asyncio.iscoroutinefunction(func):
                event_bus.subscribe_async(event_type, func)
            else:
                event_bus.subscribe(event_type, func)
        
        return func
    
    return decorator


def publish_event(
    event_type: EventType,
    data: Dict[str, Any],
    user_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    correlation_id: Optional[UUID] = None,
    source_service: Optional[str] = None
) -> None:
    """
    Convenience function to publish an event.
    
    Args:
        event_type: Type of event to publish
        data: Event data
        user_id: Optional user ID
        company_id: Optional company ID
        correlation_id: Optional correlation ID for tracking
        source_service: Optional source service name
    """
    event = Event(
        event_type=event_type,
        data=data,
        user_id=user_id,
        company_id=company_id,
        correlation_id=correlation_id,
        source_service=source_service
    )
    
    event_bus = get_event_bus()
    event_bus.publish(event)


async def publish_event_async(
    event_type: EventType,
    data: Dict[str, Any],
    user_id: Optional[UUID] = None,
    company_id: Optional[UUID] = None,
    correlation_id: Optional[UUID] = None,
    source_service: Optional[str] = None
) -> None:
    """
    Convenience function to publish an event asynchronously.
    """
    event = Event(
        event_type=event_type,
        data=data,
        user_id=user_id,
        company_id=company_id,
        correlation_id=correlation_id,
        source_service=source_service
    )
    
    event_bus = get_event_bus()
    await event_bus.publish_async(event)
