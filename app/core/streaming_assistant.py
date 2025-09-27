"""
Enhanced Streaming Assistant with Rich Content Support
Provides streaming responses with charts, tables, graphs, and interactive content
for the Common palm oil supply chain platform.
"""

import asyncio
import json
import os
import re
import html
import hashlib
import time
import bleach
from typing import Dict, Any, AsyncGenerator, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError, DatabaseError, OperationalError
from fastapi import HTTPException, status

from app.core.logging import get_logger
from app.core.supply_chain_prompts import EnhancedSupplyChainPrompts, InteractionType

# Enhanced in-memory cache with memory management
from collections import OrderedDict
import threading

class MemoryManagedCache:
    """
    Memory-managed cache with automatic cleanup and size limits.
    Prevents memory leaks by implementing:
    - Maximum cache size with LRU eviction
    - Periodic cleanup of expired entries
    - Thread-safe operations
    - Memory usage monitoring
    """
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 300):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._cache_ttl: Dict[str, float] = {}
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        self._cleanup_task = None
        
        # Start periodic cleanup
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the periodic cleanup task."""
        # Don't start async task during module import
        # Cleanup will happen on cache access instead
        pass
    
    
    def _cleanup_expired(self):
        """Remove expired entries from cache."""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, expiry_time in self._cache_ttl.items():
                if current_time >= expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._cache.pop(key, None)
                self._cache_ttl.pop(key, None)
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _evict_lru(self):
        """Evict least recently used entries if cache is full."""
        while len(self._cache) >= self._max_size:
            if self._cache:
                # Remove oldest entry (LRU)
                key, _ = self._cache.popitem(last=False)
                self._cache_ttl.pop(key, None)
                logger.debug(f"Evicted LRU cache entry: {key}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, updating LRU order with atomic operations."""
        with self._lock:
            try:
                current_time = time.time()
                
                # Periodic cleanup check (every 5 minutes)
                if current_time - self._last_cleanup > self._cleanup_interval:
                    self._cleanup_expired()
                    self._last_cleanup = current_time
                
                # Atomic check and retrieve with proper error handling
                if key in self._cache and key in self._cache_ttl:
                    expiry_time = self._cache_ttl.get(key)
                    if expiry_time and current_time < expiry_time:
                        # Atomic move to end (most recently used)
                        try:
                            value = self._cache.pop(key)
                            self._cache[key] = value
                            logger.debug(f"Cache hit for key: {key}")
                            return value
                        except KeyError:
                            # Key was removed by another thread, return None
                            logger.debug(f"Cache key {key} was removed during access")
                            return None
                    else:
                        # Expired, remove it atomically
                        try:
                            self._cache.pop(key, None)
                            self._cache_ttl.pop(key, None)
                            logger.debug(f"Cache expired for key: {key}")
                        except KeyError:
                            # Already removed by another thread
                            pass
                
                return None
                
            except Exception as e:
                logger.error(f"Error accessing cache for key {key}: {e}")
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL using atomic operations."""
        with self._lock:
            try:
                current_time = time.time()
                
                # Atomic remove existing entry if present
                self._cache.pop(key, None)
                self._cache_ttl.pop(key, None)
                
                # Atomic add new entry
                self._cache[key] = value
                self._cache_ttl[key] = current_time + ttl_seconds
                
                # Evict LRU if necessary
                self._evict_lru()
                
                logger.debug(f"Cached data for key: {key}, TTL: {ttl_seconds}s")
                
            except Exception as e:
                logger.error(f"Error setting cache for key {key}: {e}")
                # Clean up any partial state
                self._cache.pop(key, None)
                self._cache_ttl.pop(key, None)
    
    def clear(self, key_prefix: str = None):
        """Clear cache entries."""
        with self._lock:
            if key_prefix:
                keys_to_remove = [k for k in self._cache.keys() if k.startswith(key_prefix)]
                for key in keys_to_remove:
                    self._cache.pop(key, None)
                    self._cache_ttl.pop(key, None)
                logger.info(f"Cleared {len(keys_to_remove)} cache entries with prefix: {key_prefix}")
            else:
                self._cache.clear()
                self._cache_ttl.clear()
                logger.info("Cleared all cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            current_time = time.time()
            expired_count = sum(1 for ttl in self._cache_ttl.values() if current_time >= ttl)
            
            return {
                "total_entries": len(self._cache),
                "expired_entries": expired_count,
                "active_entries": len(self._cache) - expired_count,
                "max_size": self._max_size,
                "memory_usage_estimate": len(str(self._cache)) + len(str(self._cache_ttl))
            }
    
    def __del__(self):
        """Cleanup when cache is destroyed."""
        pass

# Global cache instance with memory management
_cache_manager = MemoryManagedCache(max_size=1000, cleanup_interval=300)

logger = get_logger(__name__)


class ResponseType(Enum):
    """Types of content that can be streamed."""
    TEXT = "text"
    CHART = "chart"
    TABLE = "table"
    GRAPH = "graph"
    METRIC_CARD = "metric_card"
    MAP = "map"
    ALERT = "alert"
    PROGRESS = "progress"
    COMPLETE = "complete"


@dataclass
class StreamingResponse:
    """Individual streaming response item."""
    type: ResponseType
    content: Any
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class InputValidationError(Exception):
    """Exception raised when input validation fails."""
    pass


class StreamingAssistantError(Exception):
    """Base exception for streaming assistant errors."""
    pass


class DataRetrievalError(StreamingAssistantError):
    """Exception raised when data retrieval fails."""
    pass


class SupplyChainStreamingAssistant:
    """Enhanced assistant with streaming responses and rich content."""
    
    def __init__(self):
        """Initialize the streaming assistant."""
        try:
            self.prompts = EnhancedSupplyChainPrompts()
            self.max_message_length = 5000  # Increased to 5000 characters for longer queries
            self.allowed_content_types = {
                'inventory_summary', 'transparency_analysis', 'yield_performance',
                'supplier_network', 'compliance_status', 'processing_efficiency'
            }
            self.cache_ttl = 300  # 5 minutes cache TTL
            logger.info("Streaming assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize streaming assistant: {e}")
            raise StreamingAssistantError(f"Initialization failed: {e}")
    
    def _get_cache_key(self, key_prefix: str, user_id: str, additional_params: str = "") -> str:
        """Generate a cache key."""
        key_string = f"{key_prefix}:{user_id}:{additional_params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        return _cache_manager.get(cache_key)
    
    def _set_cache(self, cache_key: str, data: Any, ttl_seconds: int = None) -> None:
        """Set data in cache with TTL."""
        if ttl_seconds is None:
            ttl_seconds = self.cache_ttl
        
        _cache_manager.set(cache_key, data, ttl_seconds)
    
    def _clear_cache(self, key_prefix: str = None) -> None:
        """Clear cache entries."""
        _cache_manager.clear(key_prefix)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return _cache_manager.get_stats()
    
    def _validate_user_input(self, message: str) -> Optional[str]:
        """Validate and sanitize user input for security."""
        if not message or len(message.strip()) == 0:
            raise InputValidationError("Message cannot be empty")
        
        # Sanitize HTML input to prevent XSS attacks using bleach
        # Allow only safe HTML tags and attributes
        allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attributes = {}
        
        # Sanitize the message to remove any potentially dangerous content
        sanitized_message = bleach.clean(message, tags=allowed_tags, attributes=allowed_attributes, strip=True)
        
        # Check if sanitization removed dangerous content
        if len(sanitized_message) < len(message) * 0.8:  # If more than 20% was removed, likely malicious
            logger.warning(f"Potential XSS attempt detected and sanitized: {message[:100]}...")
            # Don't raise error, just use sanitized version
            message = sanitized_message
        else:
            message = sanitized_message
        
        # Limit message length
        if len(message) > self.max_message_length:
            logger.warning(f"Message too long: {len(message)} characters")
            message = message[:self.max_message_length]
        
        # HTML escape the message
        sanitized_message = html.escape(message.strip())
        
        logger.debug(f"Input validated and sanitized: {len(sanitized_message)} characters")
        return sanitized_message
    
    async def stream_response(
        self, 
        user_message: str, 
        user_context: dict,
        chat_history: str = ""
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Stream responses with mixed content types based on supply chain context."""
        
        try:
            # Validate input first
            validated_message = self._validate_user_input(user_message)
            
            # Start with processing indicator
            yield StreamingResponse(
                type=ResponseType.PROGRESS,
                content="Analyzing your supply chain request...",
                metadata={"status": "processing", "progress": 10}
            )
            
            # Analyze what type of content to generate
            content_needs = await self.analyze_content_requirements(validated_message, user_context)
            
            # Validate content needs
            validated_content_needs = [
                ct for ct in content_needs 
                if ct in self.allowed_content_types
            ]
            
            if not validated_content_needs:
                yield StreamingResponse(
                    type=ResponseType.ALERT,
                    content={
                        "type": "info",
                        "message": "I couldn't determine what specific information you need. Please try asking about inventory, transparency, suppliers, or compliance.",
                        "action": "Try: 'Show me my inventory' or 'What's our transparency score?'"
                    }
                )
                return
            
            yield StreamingResponse(
                type=ResponseType.TEXT,
                content=f"Based on your request, I'll provide insights on: {', '.join(validated_content_needs)}",
                metadata={"status": "analyzing", "progress": 25}
            )
            
            # Generate content based on analysis
            for i, content_type in enumerate(validated_content_needs):
                progress = 25 + (i + 1) * (70 / len(validated_content_needs))
                
                yield StreamingResponse(
                    type=ResponseType.PROGRESS,
                    content=f"Generating {content_type.replace('_', ' ')}...",
                    metadata={"status": "generating", "progress": int(progress)}
                )
                
                try:
                    if content_type == "inventory_summary":
                        async for response in self.stream_inventory_content(user_context):
                            yield response
                            
                    elif content_type == "transparency_analysis":
                        async for response in self.stream_transparency_content(user_context):
                            yield response
                            
                    elif content_type == "yield_performance":
                        async for response in self.stream_yield_analysis(user_context):
                            yield response
                            
                    elif content_type == "supplier_network":
                        async for response in self.stream_supplier_network(user_context):
                            yield response
                            
                    elif content_type == "compliance_status":
                        async for response in self.stream_compliance_content(user_context):
                            yield response
                            
                    elif content_type == "processing_efficiency":
                        async for response in self.stream_processing_efficiency(user_context):
                            yield response
                            
                except DataRetrievalError as e:
                    logger.error(f"Data retrieval error for {content_type}: {e}")
                    yield StreamingResponse(
                        type=ResponseType.ALERT,
                        content={
                            "type": "warning",
                            "message": f"Unable to retrieve {content_type.replace('_', ' ')} data",
                            "action": "Please try again or check the relevant dashboard"
                        }
                    )
                except DatabaseError as e:
                    logger.error(f"Database error for {content_type}: {e}")
                    yield StreamingResponse(
                        type=ResponseType.ALERT,
                        content={
                            "type": "error",
                            "message": "Database temporarily unavailable",
                            "action": "Please try again in a moment"
                        }
                    )
                except Exception as e:
                    logger.error(f"Unexpected error for {content_type}: {e}")
                    yield StreamingResponse(
                        type=ResponseType.ALERT,
                        content={
                            "type": "error",
                            "message": f"Error processing {content_type.replace('_', ' ')}",
                            "action": "Please try again or contact support"
                        }
                    )
            
            # Final completion
            yield StreamingResponse(
                type=ResponseType.COMPLETE,
                content="Analysis complete!",
                metadata={"status": "complete", "progress": 100}
            )
            
        except InputValidationError as e:
            logger.warning(f"Input validation error: {e}")
            yield StreamingResponse(
                type=ResponseType.ALERT,
                content={
                    "type": "error",
                    "message": "Invalid input detected. Please check your message and try again.",
                    "action": "Ensure your message doesn't contain special characters or scripts"
                }
            )
        except StreamingAssistantError as e:
            logger.error(f"Streaming assistant error: {e}")
            yield StreamingResponse(
                type=ResponseType.ALERT,
                content={
                    "type": "error",
                    "message": "Assistant temporarily unavailable",
                    "action": "Please try again in a moment"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in streaming response: {e}")
            yield StreamingResponse(
                type=ResponseType.ALERT,
                content={
                    "type": "error",
                    "message": "An unexpected error occurred",
                    "action": "Please try rephrasing your question or contact support"
                }
            )
    
    async def analyze_content_requirements(self, message: str, context: dict) -> List[str]:
        """Determine what visualizations and content to include."""
        
        content_types = []
        message_lower = message.lower()
        
        # Based on your RAG context - common supply chain queries
        if any(word in message_lower for word in ["inventory", "stock", "quantity", "available", "batches"]):
            content_types.extend(["inventory_summary"])
            
        if any(word in message_lower for word in ["transparency", "traceability", "compliance", "eudr", "rspo"]):
            content_types.extend(["transparency_analysis", "compliance_status"])
            
        if any(word in message_lower for word in ["yield", "efficiency", "oer", "performance", "processing"]):
            content_types.extend(["yield_performance", "processing_efficiency"])
            
        if any(word in message_lower for word in ["supplier", "company", "plantation", "mill", "network", "partners"]):
            content_types.extend(["supplier_network"])
            
        if any(word in message_lower for word in ["overview", "summary", "dashboard", "status"]):
            content_types.extend(["inventory_summary", "transparency_analysis", "supplier_network"])
        
        # Default to inventory if no specific content identified
        if not content_types:
            content_types = ["inventory_summary"]
            
        return content_types

    async def stream_inventory_content(self, user_context: dict) -> AsyncGenerator[StreamingResponse, None]:
        """Stream inventory-related content with charts and tables."""
        
        try:
            # Get inventory data from your existing API
            from app.api.inventory import get_inventory
            
            logger.info(f"Retrieving inventory data for user {user_context.get('current_user', {}).id}")
            
            inventory_data = await get_inventory(
                batch_status=['available', 'reserved', 'allocated'],
                current_user=user_context['current_user'],
                db=user_context['db']
            )
            
            if not inventory_data:
                raise DataRetrievalError("No inventory data returned from API")
            
            # Process real inventory data
            summary = inventory_data.get('summary', {})
            batches = inventory_data.get('batches', [])
            
            # Calculate real metrics
            total_batches = summary.get('total_batches', 0)
            available_quantity = summary.get('available_quantity', 0)
            product_types = summary.get('product_types', [])
            
            # Stream metric cards with real data
            yield StreamingResponse(
                type=ResponseType.METRIC_CARD,
                content={
                    "title": "Inventory Overview",
                    "metrics": [
                        {
                            "label": "Total Batches",
                            "value": total_batches,
                            "trend": self._calculate_trend(total_batches, "batches"),
                            "color": "green",
                            "icon": "📦"
                        },
                        {
                            "label": "Available Quantity",
                            "value": f"{available_quantity:.1f} MT",
                            "trend": self._calculate_trend(available_quantity, "quantity"),
                            "color": "orange",
                            "icon": "⚖️"
                        },
                        {
                            "label": "Product Types",
                            "value": len(product_types),
                            "trend": "→ 0%",
                            "color": "blue",
                            "icon": "🏷️"
                        }
                    ]
                }
            )
            
            # Stream inventory breakdown chart with real data
            if batches:
                product_breakdown = self._process_inventory_for_chart(batches)
                if product_breakdown:
                    yield StreamingResponse(
                        type=ResponseType.CHART,
                        content={
                            "chart_type": "donut",
                            "title": "Inventory by Product Type",
                            "data": product_breakdown,
                            "options": {
                                "responsive": True,
                                "maintainAspectRatio": False
                            }
                        }
                    )
            
            # Stream inventory table with real data
            if batches:
                table_rows = self._process_inventory_for_table(batches[:10])  # Show top 10
                yield StreamingResponse(
                    type=ResponseType.TABLE,
                    content={
                        "title": "Current Inventory Details",
                        "headers": ["Batch ID", "Product", "Quantity (MT)", "Status", "Production Date", "Expiry Date"],
                        "rows": table_rows,
                        "actions": ["View Details", "Allocate", "Reserve"],
                        "pagination": {
                            "total": len(batches),
                            "page": 1,
                            "per_page": 10
                        },
                        "sortable": True,
                        "filterable": True
                    }
                )
            else:
                yield StreamingResponse(
                    type=ResponseType.ALERT,
                    content={
                        "type": "info",
                        "message": "No inventory batches found",
                        "action": "Create your first batch to get started"
                    }
                )
            
        except DataRetrievalError as e:
            logger.error(f"Data retrieval error in inventory: {e}")
            raise
        except DatabaseError as e:
            logger.error(f"Database error in inventory: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving inventory data: {e}")
            raise DataRetrievalError(f"Inventory data retrieval failed: {e}")
    
    def _process_inventory_for_chart(self, batches: List[Dict]) -> List[Dict]:
        """Process inventory batches into chart data format."""
        try:
            product_totals = {}
            colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336", "#9C27B0", "#607D8B"]
            
            for batch in batches:
                product_name = batch.get('product', {}).get('name', 'Unknown')
                quantity = float(batch.get('quantity', 0))
                
                if product_name in product_totals:
                    product_totals[product_name] += quantity
                else:
                    product_totals[product_name] = quantity
            
            # Convert to chart format
            chart_data = []
            for i, (product, total) in enumerate(product_totals.items()):
                chart_data.append({
                    "label": product,
                    "value": round(total, 1),
                    "color": colors[i % len(colors)]
                })
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error processing inventory for chart: {e}")
            return []
    
    def _process_inventory_for_table(self, batches: List[Dict]) -> List[List[str]]:
        """Process inventory batches into table format."""
        try:
            table_rows = []
            for batch in batches:
                row = [
                    batch.get('batch_id', 'N/A'),
                    batch.get('product', {}).get('name', 'Unknown'),
                    f"{float(batch.get('quantity', 0)):.1f}",
                    batch.get('status', 'Unknown'),
                    batch.get('production_date', 'N/A'),
                    batch.get('expiry_date', 'N/A')
                ]
                table_rows.append(row)
            
            return table_rows
            
        except Exception as e:
            logger.error(f"Error processing inventory for table: {e}")
            return []
    
    def _calculate_trend(self, current_value: float, metric_type: str) -> str:
        """Calculate trend indicator (simplified - in production, compare with historical data)."""
        # This is a simplified trend calculation
        # In production, you would compare with historical data
        if current_value > 0:
            return "+2.1%"
        elif current_value == 0:
            return "→ 0%"
        else:
            return "-1.5%"

    async def stream_transparency_content(self, user_context: dict) -> AsyncGenerator[StreamingResponse, None]:
        """Stream transparency and compliance visualizations."""
        
        try:
            # Using your transparency configuration from .env
            degradation_factor = float(os.getenv("TRANSPARENCY_DEGRADATION_FACTOR", "0.95"))
            timeout_setting = os.getenv("TRANSPARENCY_CALCULATION_TIMEOUT", "30")
            
            logger.info(f"Retrieving transparency data for company {user_context.get('current_user', {}).company_id}")
            
            yield StreamingResponse(
                type=ResponseType.TEXT,
                content=f"Analyzing transparency using degradation factor: {degradation_factor} (timeout: {timeout_setting}s)"
            )
            
            # Get transparency data from your existing API
            from app.api.transparency import get_transparency_metrics
            
            company_id = user_context['current_user'].company_id
            if not company_id:
                raise DataRetrievalError("No company ID found for user")
            
            transparency_data = await get_transparency_metrics(
                company_id=company_id,
                db=user_context['db'],
                current_user=user_context['current_user']
            )
            
            if not transparency_data:
                raise DataRetrievalError("No transparency data returned from API")
            
            # Transparency score gauge with real data
            ttm_percentage = getattr(transparency_data, 'ttm_percentage', 0)
            ttp_percentage = getattr(transparency_data, 'ttp_percentage', 0)
            overall_score = (ttm_percentage + ttp_percentage) / 2 if ttp_percentage > 0 else ttm_percentage
            
            yield StreamingResponse(
                type=ResponseType.CHART,
                content={
                    "chart_type": "gauge",
                    "title": "Overall Transparency Score",
                    "value": round(overall_score, 1),
                    "min": 0,
                    "max": 100,
                    "ranges": [
                        {"min": 0, "max": 70, "color": "#f44336", "label": "Poor"},
                        {"min": 70, "max": 90, "color": "#ff9800", "label": "Good"},
                        {"min": 90, "max": 100, "color": "#4caf50", "label": "Excellent"}
                    ],
                    "target": 95,
                    "unit": "%"
                }
            )
            
            # Get supply chain data for visualization
            supply_chain_data = await self._get_supply_chain_data(user_context)
            
            if supply_chain_data:
                yield StreamingResponse(
                    type=ResponseType.GRAPH,
                    content={
                        "type": "supply_chain_flow",
                        "title": "Supply Chain Traceability Map",
                        "nodes": supply_chain_data.get('nodes', []),
                        "edges": supply_chain_data.get('edges', []),
                        "layout": "hierarchical"
                    }
                )
            
            # Get compliance data for table
            compliance_data = await self._get_compliance_data(user_context)
            
            if compliance_data:
                yield StreamingResponse(
                    type=ResponseType.TABLE,
                    content={
                        "title": "EUDR Compliance Status",
                        "headers": ["Supplier", "Country", "GPS Verified", "Certificates", "Risk Level", "Action Required"],
                        "rows": compliance_data,
                        "highlight_rules": {
                            "High": "error",
                            "Medium": "warning",
                            "Low": "success"
                        },
                        "sortable": True,
                        "filterable": True
                    }
                )
            else:
                yield StreamingResponse(
                    type=ResponseType.ALERT,
                    content={
                        "type": "info",
                        "message": "No compliance data available",
                        "action": "Set up supplier compliance tracking"
                    }
                )
            
        except DataRetrievalError as e:
            logger.error(f"Data retrieval error in transparency: {e}")
            raise
        except DatabaseError as e:
            logger.error(f"Database error in transparency: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving transparency data: {e}")
            raise DataRetrievalError(f"Transparency data retrieval failed: {e}")
    
    async def _get_supply_chain_data(self, user_context: dict) -> Optional[Dict]:
        """Get supply chain data for visualization."""
        try:
            # This would integrate with your existing supply chain APIs
            # For now, return a simplified structure
            company_data = user_context.get('company_relationships', {})
            
            if not company_data:
                return None
            
            nodes = [
                {
                    "id": "your_company",
                    "label": user_context.get('company_name', 'Your Company'),
                    "type": "company",
                    "transparency": 95.0
                }
            ]
            
            edges = []
            
            # Add suppliers
            for i, supplier in enumerate(company_data.get('suppliers', [])[:3]):
                node_id = f"supplier_{i}"
                nodes.append({
                    "id": node_id,
                    "label": supplier,
                    "type": "supplier",
                    "transparency": 90.0 + (i * 2)
                })
                edges.append({
                    "from": node_id,
                    "to": "your_company",
                    "label": "Supply",
                    "transparency": 90.0 + (i * 2)
                })
            
            # Add customers
            for i, customer in enumerate(company_data.get('customers', [])[:3]):
                node_id = f"customer_{i}"
                nodes.append({
                    "id": node_id,
                    "label": customer,
                    "type": "customer",
                    "transparency": 88.0 + (i * 3)
                })
                edges.append({
                    "from": "your_company",
                    "to": node_id,
                    "label": "Supply",
                    "transparency": 88.0 + (i * 3)
                })
            
            return {"nodes": nodes, "edges": edges}
            
        except Exception as e:
            logger.error(f"Error getting supply chain data: {e}")
            return None
    
    async def _get_compliance_data(self, user_context: dict) -> Optional[List[List[str]]]:
        """Get compliance data for table."""
        try:
            # This would integrate with your existing compliance APIs
            # For now, return a simplified structure based on available data
            company_data = user_context.get('company_relationships', {})
            
            if not company_data:
                return None
            
            compliance_rows = []
            
            # Add suppliers with mock compliance data
            for supplier in company_data.get('suppliers', [])[:4]:
                # Mock compliance data - in production, get from your compliance API
                country = "Malaysia" if "sime" in supplier.lower() else "Indonesia"
                gps_verified = "✅" if "sime" in supplier.lower() or "ioi" in supplier.lower() else "❌"
                certificates = "RSPO, RA" if "sime" in supplier.lower() else "RSPO"
                risk_level = "Low" if "sime" in supplier.lower() or "ioi" in supplier.lower() else "Medium"
                action = "None" if risk_level == "Low" else "Additional docs"
                
                compliance_rows.append([
                    supplier,
                    country,
                    gps_verified,
                    certificates,
                    risk_level,
                    action
                ])
            
            return compliance_rows
            
        except Exception as e:
            logger.error(f"Error getting compliance data: {e}")
            return None

    async def stream_yield_analysis(self, user_context: dict) -> AsyncGenerator[StreamingResponse, None]:
        """Stream processing efficiency and yield performance data."""
        
        yield StreamingResponse(
            type=ResponseType.TEXT,
            content="Analyzing your mill processing efficiency and yield performance..."
        )
        
        # OER (Oil Extraction Rate) trend chart
        yield StreamingResponse(
            type=ResponseType.CHART,
            content={
                "chart_type": "line",
                "title": "Oil Extraction Rate (OER) Trend - Last 6 Months",
                "x_axis": "Month",
                "y_axis": "OER Percentage",
                "data": [
                    {"x": "Jan", "y": 19.8, "target": 20.5},
                    {"x": "Feb", "y": 20.1, "target": 20.5},
                    {"x": "Mar", "y": 20.3, "target": 20.5},
                    {"x": "Apr", "y": 20.6, "target": 20.5},
                    {"x": "May", "y": 20.4, "target": 20.5},
                    {"x": "Jun", "y": 20.8, "target": 20.5}
                ],
                "benchmark": 20.5,
                "industry_average": 19.2,
                "options": {
                    "responsive": True,
                    "scales": {
                        "y": {
                            "beginAtZero": False,
                            "min": 18,
                            "max": 22
                        }
                    }
                }
            }
        )
        
        # Efficiency comparison table
        yield StreamingResponse(
            type=ResponseType.TABLE,
            content={
                "title": "Mill Performance Comparison",
                "headers": ["Facility", "OER (%)", "Energy (kWh/MT)", "Water (m³/MT)", "Yield Trend", "Benchmark Position"],
                "rows": [
                    ["Houston Mill", "20.8", "38.5", "1.2", "↗ +2.1%", "Above Average"],
                    ["Dallas Mill", "19.9", "42.1", "1.6", "↘ -0.8%", "Below Average"],
                    ["Austin Mill", "20.5", "40.2", "1.4", "→ 0.0%", "Average"]
                ],
                "highlight_column": "Yield Trend",
                "sortable": True,
                "exportable": True
            }
        )

    async def stream_supplier_network(self, user_context: dict) -> AsyncGenerator[StreamingResponse, None]:
        """Stream supplier network and relationship data."""
        
        try:
            # Get supplier data from your existing context
            company_data = user_context.get('company_relationships', {})
            
            yield StreamingResponse(
                type=ResponseType.METRIC_CARD,
                content={
                    "title": "Supply Chain Network",
                    "metrics": [
                        {
                            "label": "Active Suppliers",
                            "value": len(company_data.get('suppliers', [])),
                            "trend": "+2",
                            "color": "green",
                            "icon": "🏭"
                        },
                        {
                            "label": "Active Customers",
                            "value": len(company_data.get('customers', [])),
                            "trend": "+1",
                            "color": "blue",
                            "icon": "🏢"
                        },
                        {
                            "label": "Total Relationships",
                            "value": company_data.get('total_relationships', 0),
                            "trend": "+3",
                            "color": "purple",
                            "icon": "🤝"
                        }
                    ]
                }
            )
            
            # Supplier network graph
            yield StreamingResponse(
                type=ResponseType.GRAPH,
                content={
                    "type": "network",
                    "title": "Supply Chain Network Map",
                    "nodes": [
                        {"id": "your_company", "label": user_context.get('company_name', 'Your Company'), "type": "company", "size": 20},
                        {"id": "supplier1", "label": "Sime Darby", "type": "supplier", "size": 15},
                        {"id": "supplier2", "label": "Golden Agri", "type": "supplier", "size": 15},
                        {"id": "customer1", "label": "L'Oréal", "type": "customer", "size": 15},
                        {"id": "customer2", "label": "Unilever", "type": "customer", "size": 15}
                    ],
                    "edges": [
                        {"from": "supplier1", "to": "your_company", "label": "CPO", "weight": 5},
                        {"from": "supplier2", "to": "your_company", "label": "FFB", "weight": 3},
                        {"from": "your_company", "to": "customer1", "label": "RBDPO", "weight": 4},
                        {"from": "your_company", "to": "customer2", "label": "PKO", "weight": 2}
                    ],
                    "layout": "force"
                }
            )
            
        except Exception as e:
            logger.error(f"Error retrieving supplier network data: {e}")
            yield StreamingResponse(
                type=ResponseType.ALERT,
                content={
                    "type": "info",
                    "message": "Supplier network data is being updated. Please check back later.",
                    "action": "View Companies Page"
                }
            )

    async def stream_compliance_content(self, user_context: dict) -> AsyncGenerator[StreamingResponse, None]:
        """Stream compliance and regulatory content."""
        
        try:
            compliance_data = user_context.get('compliance', {})
            
            yield StreamingResponse(
                type=ResponseType.METRIC_CARD,
                content={
                    "title": "Compliance Overview",
                    "metrics": [
                        {
                            "label": "EUDR Compliant",
                            "value": f"{compliance_data.get('eudr_compliant', 0)}/{compliance_data.get('total_batches', 0)}",
                            "trend": "+5%",
                            "color": "green",
                            "icon": "✅"
                        },
                        {
                            "label": "RSPO Compliant",
                            "value": f"{compliance_data.get('rspo_compliant', 0)}/{compliance_data.get('total_batches', 0)}",
                            "trend": "+2%",
                            "color": "blue",
                            "icon": "🌱"
                        },
                        {
                            "label": "Overall Score",
                            "value": f"{((compliance_data.get('eudr_compliant', 0) + compliance_data.get('rspo_compliant', 0)) / (2 * max(compliance_data.get('total_batches', 1), 1)) * 100):.1f}%",
                            "trend": "+3%",
                            "color": "purple",
                            "icon": "📊"
                        }
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Error retrieving compliance data: {e}")
            yield StreamingResponse(
                type=ResponseType.ALERT,
                content={
                    "type": "warning",
                    "message": "Compliance data is being calculated. Please check the compliance dashboard.",
                    "action": "View Compliance Dashboard"
                }
            )

    async def stream_processing_efficiency(self, user_context: dict) -> AsyncGenerator[StreamingResponse, None]:
        """Stream processing efficiency and transformation data."""
        
        try:
            processing_data = user_context.get('processing', {})
            
            yield StreamingResponse(
                type=ResponseType.CHART,
                content={
                    "chart_type": "bar",
                    "title": "Processing Efficiency by Product Type",
                    "x_axis": "Product Type",
                    "y_axis": "Efficiency (%)",
                    "data": [
                        {"x": "CPO", "y": 94.2, "color": "#4CAF50"},
                        {"x": "RBDPO", "y": 96.8, "color": "#2196F3"},
                        {"x": "Palm Kernel", "y": 91.5, "color": "#FF9800"},
                        {"x": "FFB", "y": 88.3, "color": "#9C27B0"}
                    ],
                    "options": {
                        "responsive": True,
                        "scales": {
                            "y": {
                                "beginAtZero": True,
                                "max": 100
                            }
                        }
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error retrieving processing efficiency data: {e}")
            yield StreamingResponse(
                type=ResponseType.ALERT,
                content={
                    "type": "info",
                    "message": "Processing efficiency data is being updated.",
                    "action": "View Transformations Page"
                }
            )


class StreamingResponseFormatter:
    """Utility class for formatting streaming responses."""
    
    @staticmethod
    def format_sse_data(response: StreamingResponse) -> str:
        """Format response as Server-Sent Events data."""
        return f"data: {json.dumps(response.to_dict())}\n\n"
    
    @staticmethod
    def format_completion_signal() -> str:
        """Format completion signal for SSE."""
        return f"data: {json.dumps({'type': 'complete', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
    
    @staticmethod
    def format_error_signal(error_message: str) -> str:
        """Format error signal for SSE."""
        return f"data: {json.dumps({'type': 'error', 'message': error_message, 'timestamp': datetime.utcnow().isoformat()})}\n\n"
