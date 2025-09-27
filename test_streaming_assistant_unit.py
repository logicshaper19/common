#!/usr/bin/env python3
"""
Unit tests for the streaming assistant functionality.
Tests critical functions and error handling.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.streaming_assistant import (
    SupplyChainStreamingAssistant,
    StreamingResponse,
    ResponseType,
    InputValidationError,
    StreamingAssistantError,
    DataRetrievalError
)


class TestStreamingResponse:
    """Test StreamingResponse dataclass."""
    
    def test_streaming_response_creation(self):
        """Test creating a StreamingResponse."""
        response = StreamingResponse(
            type=ResponseType.TEXT,
            content="Test message",
            metadata={"test": True},
            timestamp=datetime.now()
        )
        
        assert response.type == ResponseType.TEXT
        assert response.content == "Test message"
        assert response.metadata == {"test": True}
        assert response.timestamp is not None
    
    def test_streaming_response_to_dict(self):
        """Test converting StreamingResponse to dictionary."""
        timestamp = datetime.now()
        response = StreamingResponse(
            type=ResponseType.CHART,
            content={"chart_type": "line", "data": []},
            metadata={"progress": 50},
            timestamp=timestamp
        )
        
        result = response.to_dict()
        
        assert result["type"] == "chart"
        assert result["content"]["chart_type"] == "line"
        assert result["metadata"]["progress"] == 50
        assert result["timestamp"] == timestamp.isoformat()
    
    def test_streaming_response_to_dict_no_metadata(self):
        """Test converting StreamingResponse to dictionary without metadata."""
        response = StreamingResponse(
            type=ResponseType.TEXT,
            content="Test message"
        )
        
        result = response.to_dict()
        
        assert result["type"] == "text"
        assert result["content"] == "Test message"
        assert result["metadata"] == {}
        assert result["timestamp"] is None


class TestSupplyChainStreamingAssistant:
    """Test SupplyChainStreamingAssistant class."""
    
    @pytest.fixture
    def assistant(self):
        """Create a test assistant instance."""
        with patch('app.core.streaming_assistant.EnhancedSupplyChainPrompts'):
            return SupplyChainStreamingAssistant()
    
    def test_assistant_initialization(self, assistant):
        """Test assistant initialization."""
        assert assistant.max_message_length == 5000
        assert 'inventory_summary' in assistant.allowed_content_types
        assert 'transparency_analysis' in assistant.allowed_content_types
        assert assistant.cache_ttl == 300
    
    def test_validate_user_input_valid(self, assistant):
        """Test input validation with valid input."""
        valid_inputs = [
            "Show me my inventory",
            "What's our transparency score?",
            "Hello, how are you?",
            "1234567890" * 500  # 5000 characters
        ]
        
        for input_text in valid_inputs:
            result = assistant._validate_user_input(input_text)
            assert result is not None
            assert len(result) <= 5000
    
    def test_validate_user_input_invalid(self, assistant):
        """Test input validation with invalid input."""
        invalid_inputs = [
            "",  # Empty
            "   ",  # Whitespace only
            "<script>alert('xss')</script>",  # XSS attempt
            "javascript:alert('xss')",  # JavaScript protocol
            "data:text/html,<script>alert('xss')</script>",  # Data URI
            "onload=alert('xss')",  # Event handler
            "A" * 5001  # Too long
        ]
        
        for input_text in invalid_inputs:
            with pytest.raises(InputValidationError):
                assistant._validate_user_input(input_text)
    
    def test_validate_user_input_xss_patterns(self, assistant):
        """Test XSS pattern detection."""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "onload=alert('xss')",
            "onerror=alert('xss')",
            "onclick=alert('xss')"
        ]
        
        for pattern in xss_patterns:
            with pytest.raises(InputValidationError, match="Invalid input detected"):
                assistant._validate_user_input(pattern)
    
    def test_get_cache_key(self, assistant):
        """Test cache key generation."""
        key1 = assistant._get_cache_key("inventory", "user123", "param1")
        key2 = assistant._get_cache_key("inventory", "user123", "param1")
        key3 = assistant._get_cache_key("inventory", "user123", "param2")
        
        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different parameters should generate different keys
        assert len(key1) == 32  # MD5 hash length
    
    def test_cache_operations(self, assistant):
        """Test cache operations."""
        cache_key = "test_key"
        test_data = {"test": "data"}
        
        # Test setting and getting from cache
        assistant._set_cache(cache_key, test_data, ttl_seconds=60)
        cached_data = assistant._get_from_cache(cache_key)
        
        assert cached_data == test_data
        
        # Test cache expiration
        assistant._set_cache(cache_key, test_data, ttl_seconds=-1)  # Expired
        expired_data = assistant._get_from_cache(cache_key)
        
        assert expired_data is None
    
    def test_calculate_trend(self, assistant):
        """Test trend calculation."""
        # Test positive trend
        trend1 = assistant._calculate_trend(100, "batches")
        assert trend1 == "+2.1%"
        
        # Test zero trend
        trend2 = assistant._calculate_trend(0, "batches")
        assert trend2 == "→ 0%"
        
        # Test negative trend
        trend3 = assistant._calculate_trend(-10, "batches")
        assert trend3 == "-1.5%"
    
    def test_process_inventory_for_chart(self, assistant):
        """Test processing inventory data for chart."""
        mock_batches = [
            {"product": {"name": "CPO"}, "quantity": 100},
            {"product": {"name": "CPO"}, "quantity": 50},
            {"product": {"name": "RBDPO"}, "quantity": 75},
            {"product": {"name": "Palm Kernel"}, "quantity": 25}
        ]
        
        result = assistant._process_inventory_for_chart(mock_batches)
        
        assert len(result) == 3  # 3 unique products
        assert any(item["label"] == "CPO" and item["value"] == 150 for item in result)
        assert any(item["label"] == "RBDPO" and item["value"] == 75 for item in result)
        assert any(item["label"] == "Palm Kernel" and item["value"] == 25 for item in result)
        
        # Check that all items have required properties
        for item in result:
            assert "label" in item
            assert "value" in item
            assert "color" in item
    
    def test_process_inventory_for_table(self, assistant):
        """Test processing inventory data for table."""
        mock_batches = [
            {
                "batch_id": "BATCH001",
                "product": {"name": "CPO"},
                "quantity": 100.5,
                "status": "available",
                "production_date": "2024-01-01",
                "expiry_date": "2024-06-01"
            },
            {
                "batch_id": "BATCH002",
                "product": {"name": "RBDPO"},
                "quantity": 75.0,
                "status": "reserved",
                "production_date": "2024-01-02",
                "expiry_date": "2024-07-01"
            }
        ]
        
        result = assistant._process_inventory_for_table(mock_batches)
        
        assert len(result) == 2
        assert result[0] == ["BATCH001", "CPO", "100.5", "available", "2024-01-01", "2024-06-01"]
        assert result[1] == ["BATCH002", "RBDPO", "75.0", "reserved", "2024-01-02", "2024-07-01"]
    
    def test_process_inventory_for_chart_empty_data(self, assistant):
        """Test processing empty inventory data for chart."""
        result = assistant._process_inventory_for_chart([])
        assert result == []
    
    def test_process_inventory_for_table_empty_data(self, assistant):
        """Test processing empty inventory data for table."""
        result = assistant._process_inventory_for_table([])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_analyze_content_requirements(self, assistant):
        """Test content requirement analysis."""
        # Test inventory-related queries
        inventory_queries = [
            "Show me my inventory",
            "What batches do I have?",
            "How much stock is available?",
            "List my current inventory"
        ]
        
        for query in inventory_queries:
            result = await assistant.analyze_content_requirements(query, {})
            assert "inventory_summary" in result
        
        # Test transparency-related queries
        transparency_queries = [
            "What's our transparency score?",
            "Show compliance status",
            "EUDR compliance check",
            "RSPO certification status"
        ]
        
        for query in transparency_queries:
            result = await assistant.analyze_content_requirements(query, {})
            assert any(ct in result for ct in ["transparency_analysis", "compliance_status"])
        
        # Test supplier-related queries
        supplier_queries = [
            "Show supplier network",
            "Who are our suppliers?",
            "List trading partners",
            "Supply chain relationships"
        ]
        
        for query in supplier_queries:
            result = await assistant.analyze_content_requirements(query, {})
            assert "supplier_network" in result
        
        # Test yield-related queries
        yield_queries = [
            "What's our yield performance?",
            "Show OER trends",
            "Processing efficiency",
            "Mill performance"
        ]
        
        for query in yield_queries:
            result = await assistant.analyze_content_requirements(query, {})
            assert any(ct in result for ct in ["yield_performance", "processing_efficiency"])
        
        # Test default case
        result = await assistant.analyze_content_requirements("Hello", {})
        assert result == ["inventory_summary"]


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def assistant(self):
        """Create a test assistant instance."""
        with patch('app.core.streaming_assistant.EnhancedSupplyChainPrompts'):
            return SupplyChainStreamingAssistant()
    
    def test_input_validation_error_handling(self, assistant):
        """Test input validation error handling."""
        with pytest.raises(InputValidationError):
            assistant._validate_user_input("")
        
        with pytest.raises(InputValidationError):
            assistant._validate_user_input("<script>alert('xss')</script>")
    
    def test_data_retrieval_error(self):
        """Test DataRetrievalError creation."""
        error = DataRetrievalError("Failed to retrieve data")
        assert str(error) == "Failed to retrieve data"
        assert isinstance(error, StreamingAssistantError)
    
    def test_streaming_assistant_error(self):
        """Test StreamingAssistantError creation."""
        error = StreamingAssistantError("General error")
        assert str(error) == "General error"


class TestIntegration:
    """Integration tests for the streaming assistant."""
    
    @pytest.fixture
    def assistant(self):
        """Create a test assistant instance."""
        with patch('app.core.streaming_assistant.EnhancedSupplyChainPrompts'):
            return SupplyChainStreamingAssistant()
    
    @pytest.fixture
    def mock_user_context(self):
        """Create mock user context."""
        return {
            "current_user": Mock(id="user123", company_id="company456"),
            "db": Mock(),
            "company_name": "Test Company",
            "company_type": "processor",
            "user_role": "admin"
        }
    
    @pytest.mark.asyncio
    async def test_stream_response_input_validation(self, assistant, mock_user_context):
        """Test that stream_response validates input."""
        responses = []
        
        async for response in assistant.stream_response(
            "<script>alert('xss')</script>",
            mock_user_context
        ):
            responses.append(response)
        
        # Should have an error response
        assert len(responses) > 0
        assert responses[0].type == ResponseType.ALERT
        assert "Invalid input detected" in responses[0].content["message"]
    
    @pytest.mark.asyncio
    async def test_stream_response_empty_input(self, assistant, mock_user_context):
        """Test that stream_response handles empty input."""
        responses = []
        
        async for response in assistant.stream_response(
            "",
            mock_user_context
        ):
            responses.append(response)
        
        # Should have an error response
        assert len(responses) > 0
        assert responses[0].type == ResponseType.ALERT
        assert "Invalid input detected" in responses[0].content["message"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
