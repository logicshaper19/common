#!/usr/bin/env python3
"""
Comprehensive test script for enhanced API response format standardization.
"""

import sys
import json
from datetime import datetime
from typing import List, Dict, Any
sys.path.append('.')

from app.core.response_models import (
    StandardResponse,
    PaginatedResponse,
    ErrorResponse,
    ResponseStatus,
    ResponseMeta,
    PaginationMeta,
    success_response,
    error_response,
    paginated_response,
    warning_response,
    partial_success_response
)
from app.core.response_wrapper import ResponseBuilder


def test_enhanced_response_structure():
    """Test the enhanced response structure."""
    print("🔧 Testing Enhanced Response Structure...")
    
    # Test success response
    response = success_response(
        data={"id": 1, "name": "Test Item"},
        message="Item retrieved successfully",
        api_version="v1"
    )
    
    # Check structure
    assert hasattr(response, 'status')
    assert hasattr(response, 'message')
    assert hasattr(response, 'data')
    assert hasattr(response, 'meta')
    assert hasattr(response, 'success')  # Property
    
    # Check values
    assert response.status == ResponseStatus.SUCCESS
    assert response.success == True  # Derived from status
    assert response.message == "Item retrieved successfully"
    assert response.data == {"id": 1, "name": "Test Item"}
    assert response.meta.api_version == "v1"
    assert isinstance(response.meta.request_id, str)
    assert isinstance(response.meta.timestamp, datetime)
    
    print("  ✅ Success response structure correct")
    
    # Test error response
    error_resp = error_response(
        message="Something went wrong",
        errors=["Field validation failed", "Missing required field"],
        error_code="VALIDATION_ERROR",
        api_version="v1"
    )
    
    assert error_resp.status == ResponseStatus.ERROR
    assert error_resp.success == False  # Property
    assert error_resp.message == "Something went wrong"
    assert len(error_resp.errors) == 2
    assert error_resp.error_code == "VALIDATION_ERROR"
    assert error_resp.meta.api_version == "v1"
    
    print("  ✅ Error response structure correct")
    
    print("✅ Enhanced response structure tests passed!\n")


def test_new_status_types():
    """Test new status types (warning, partial_success)."""
    print("⚠️  Testing New Status Types...")
    
    # Test warning response
    warning_resp = warning_response(
        data={"processed": 10, "skipped": 2},
        message="Processing completed with warnings",
        warnings=["2 items were skipped due to validation errors"],
        api_version="v1"
    )
    
    assert warning_resp.status == ResponseStatus.WARNING
    assert warning_resp.success == False  # Warning is not success
    assert warning_resp.message == "Processing completed with warnings"
    assert len(warning_resp.warnings) == 1
    assert warning_resp.data["processed"] == 10
    
    print("  ✅ Warning response created correctly")
    
    # Test partial success response
    partial_resp = partial_success_response(
        data={"successful": 8, "failed": 2},
        message="Batch operation partially completed",
        warnings=["Some items could not be processed"],
        errors=["Item 5 failed validation", "Item 9 network timeout"],
        api_version="v1"
    )
    
    assert partial_resp.status == ResponseStatus.PARTIAL_SUCCESS
    assert partial_resp.success == False  # Partial success is not full success
    assert partial_resp.message == "Batch operation partially completed"
    assert len(partial_resp.warnings) == 1
    assert len(partial_resp.errors) == 2
    assert partial_resp.data["successful"] == 8
    
    print("  ✅ Partial success response created correctly")
    
    print("✅ New status types tests passed!\n")


def test_paginated_response_with_metadata():
    """Test paginated response with enhanced metadata."""
    print("📄 Testing Paginated Response with Metadata...")
    
    # Sample data
    items = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"}
    ]
    
    # Create paginated response
    paginated_resp = paginated_response(
        data=items,
        page=2,
        per_page=3,
        total=10,
        message="Items retrieved successfully",
        api_version="v1"
    )
    
    # Check structure
    assert paginated_resp.status == ResponseStatus.SUCCESS
    assert paginated_resp.success == True
    assert len(paginated_resp.data) == 3
    assert paginated_resp.meta.api_version == "v1"
    
    # Check pagination metadata
    pagination = paginated_resp.meta.pagination
    assert pagination is not None
    assert pagination.page == 2
    assert pagination.per_page == 3
    assert pagination.total == 10
    assert pagination.total_pages == 4  # ceil(10/3)
    assert pagination.has_next == True
    assert pagination.has_prev == True
    
    # Test backward compatibility property
    assert paginated_resp.pagination == pagination
    
    print("  ✅ Paginated response with metadata correct")
    
    print("✅ Paginated response tests passed!\n")


def test_response_builder_enhancements():
    """Test enhanced ResponseBuilder methods."""
    print("🏗️  Testing Enhanced ResponseBuilder...")
    
    # Test success builder
    success_resp = ResponseBuilder.success(
        data={"result": "success"},
        message="Operation completed",
        api_version="v2"
    )
    
    assert success_resp.status == ResponseStatus.SUCCESS
    assert success_resp.data["result"] == "success"
    assert success_resp.meta.api_version == "v2"
    
    print("  ✅ Success builder enhanced")
    
    # Test warning builder
    warning_resp = ResponseBuilder.warning(
        data={"warnings": 3},
        message="Completed with warnings",
        warnings=["Warning 1", "Warning 2", "Warning 3"],
        api_version="v2"
    )
    
    assert warning_resp.status == ResponseStatus.WARNING
    assert len(warning_resp.warnings) == 3
    assert warning_resp.meta.api_version == "v2"
    
    print("  ✅ Warning builder working")
    
    # Test partial success builder
    partial_resp = ResponseBuilder.partial_success(
        data={"partial": True},
        message="Partially completed",
        warnings=["Some warnings"],
        errors=["Some errors"],
        api_version="v2"
    )
    
    assert partial_resp.status == ResponseStatus.PARTIAL_SUCCESS
    assert len(partial_resp.warnings) == 1
    assert len(partial_resp.errors) == 1
    assert partial_resp.meta.api_version == "v2"
    
    print("  ✅ Partial success builder working")
    
    # Test paginated builder
    paginated_resp = ResponseBuilder.paginated(
        data=[{"id": 1}, {"id": 2}],
        page=1,
        per_page=2,
        total=5,
        message="Data retrieved",
        api_version="v2"
    )
    
    assert paginated_resp.status == ResponseStatus.SUCCESS
    assert len(paginated_resp.data) == 2
    assert paginated_resp.meta.api_version == "v2"
    assert paginated_resp.meta.pagination.total == 5
    
    print("  ✅ Paginated builder enhanced")
    
    print("✅ ResponseBuilder enhancement tests passed!\n")


def test_json_serialization():
    """Test JSON serialization of enhanced responses."""
    print("📝 Testing JSON Serialization...")
    
    # Create a complex response
    response = partial_success_response(
        data={
            "processed_items": 15,
            "failed_items": 3,
            "details": {
                "start_time": "2024-01-01T10:00:00Z",
                "end_time": "2024-01-01T10:05:00Z"
            }
        },
        message="Batch processing completed with some failures",
        warnings=["3 items failed processing"],
        errors=["Item 5: Invalid format", "Item 12: Network timeout", "Item 18: Permission denied"],
        api_version="v1"
    )
    
    # Serialize to JSON
    try:
        json_str = response.json()
        parsed = json.loads(json_str)
        
        # Check structure in JSON
        assert "status" in parsed
        assert "message" in parsed
        assert "data" in parsed
        assert "errors" in parsed
        assert "warnings" in parsed
        assert "meta" in parsed
        
        # Check meta structure
        meta = parsed["meta"]
        assert "request_id" in meta
        assert "timestamp" in meta
        assert "api_version" in meta
        assert meta["api_version"] == "v1"
        
        # Check derived success property is included
        assert "success" in parsed
        assert parsed["success"] == False  # Partial success
        
        print("  ✅ JSON serialization successful")
        print(f"  📊 JSON size: {len(json_str)} characters")
        
    except Exception as e:
        print(f"  ❌ JSON serialization failed: {e}")
        raise
    
    print("✅ JSON serialization tests passed!\n")


def test_backward_compatibility():
    """Test backward compatibility with old response format."""
    print("🔄 Testing Backward Compatibility...")
    
    # Create responses and check backward compatibility properties
    standard_resp = success_response(data={"test": "data"})
    
    # Check that success property works
    assert standard_resp.success == True
    assert hasattr(standard_resp, 'meta')
    
    # Create paginated response
    paginated_resp = paginated_response(
        data=[{"id": 1}],
        page=1,
        per_page=10,
        total=1
    )
    
    # Check backward compatibility properties
    assert paginated_resp.success == True
    assert paginated_resp.pagination is not None
    assert paginated_resp.pagination.page == 1
    
    print("  ✅ Backward compatibility maintained")
    
    # Test that old code patterns still work
    if paginated_resp.success:
        items = paginated_resp.data
        pagination_info = paginated_resp.pagination
        assert len(items) == 1
        assert pagination_info.total == 1
    
    print("  ✅ Old code patterns still work")
    
    print("✅ Backward compatibility tests passed!\n")


def test_response_format_examples():
    """Test and display example response formats."""
    print("📋 Testing Response Format Examples...")
    
    # Example 1: Simple success
    simple_success = ResponseBuilder.success(
        data={"user_id": 123, "username": "john_doe"},
        message="User retrieved successfully"
    )
    
    print("  📄 Simple Success Response:")
    print(f"     Status: {simple_success.status}")
    print(f"     Success: {simple_success.success}")
    print(f"     Message: {simple_success.message}")
    print(f"     Request ID: {simple_success.meta.request_id[:8]}...")
    
    # Example 2: Paginated list
    paginated_list = ResponseBuilder.paginated(
        data=[
            {"id": 1, "name": "Product A"},
            {"id": 2, "name": "Product B"}
        ],
        page=1,
        per_page=2,
        total=10,
        message="Products retrieved successfully"
    )
    
    print("  📄 Paginated List Response:")
    print(f"     Status: {paginated_list.status}")
    print(f"     Items: {len(paginated_list.data)}")
    print(f"     Page: {paginated_list.pagination.page}/{paginated_list.pagination.total_pages}")
    print(f"     Total: {paginated_list.pagination.total}")
    
    # Example 3: Partial success with warnings and errors
    batch_result = ResponseBuilder.partial_success(
        data={
            "total_processed": 100,
            "successful": 85,
            "failed": 15,
            "summary": "Batch import completed with some failures"
        },
        message="Batch import partially completed",
        warnings=["15 records failed validation"],
        errors=["Row 23: Missing required field 'email'", "Row 45: Invalid date format"]
    )
    
    print("  📄 Partial Success Response:")
    print(f"     Status: {batch_result.status}")
    print(f"     Success: {batch_result.success}")
    print(f"     Warnings: {len(batch_result.warnings)}")
    print(f"     Errors: {len(batch_result.errors)}")
    
    print("✅ Response format examples generated!\n")


def main():
    """Run all enhanced API response tests."""
    print("🚀 Starting Enhanced API Response Format Tests\n")
    
    try:
        test_enhanced_response_structure()
        test_new_status_types()
        test_paginated_response_with_metadata()
        test_response_builder_enhancements()
        test_json_serialization()
        test_backward_compatibility()
        test_response_format_examples()
        
        print("🎉 All enhanced API response tests passed!")
        print("\n📋 API Response Improvements Implemented:")
        print("✅ Eliminated Status Field Redundancy")
        print("✅ Added Comprehensive Metadata Section")
        print("✅ Implemented Additional Status Types (warning, partial_success)")
        print("✅ Enhanced ResponseBuilder with New Methods")
        print("✅ Maintained Backward Compatibility")
        print("✅ Improved JSON Structure Organization")
        print("✅ Added API Version Tracking")
        print("✅ Enhanced Pagination Metadata")
        
        print("\n🎯 API Response Quality Summary:")
        print("• Consistent response structure across all endpoints")
        print("• Rich metadata for debugging and monitoring")
        print("• Support for complex operation results (partial success)")
        print("• Backward compatibility with existing code")
        print("• Clean separation of data and metadata")
        print("• Comprehensive error and warning handling")
        print("• Request traceability with unique IDs")
        print("• API versioning support for future changes")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
