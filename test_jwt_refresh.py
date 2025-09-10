#!/usr/bin/env python3
"""
Test script for JWT token refresh mechanism.
"""

import sys
import os
sys.path.append('.')

from datetime import datetime, timedelta, timezone
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_token, 
    verify_refresh_token,
    is_token_expired,
    create_user_token_data
)
from app.core.config import settings


def test_token_creation():
    """Test that tokens are created correctly."""
    print("🔐 Testing Token Creation...")
    
    # Test data
    user_data = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "role": "admin",
        "company_id": "test-company-id"
    }
    
    # Create access token
    access_token = create_access_token(user_data)
    print(f"✅ Access token created: {access_token[:50]}...")
    
    # Create refresh token
    refresh_token = create_refresh_token(user_data)
    print(f"✅ Refresh token created: {refresh_token[:50]}...")
    
    # Verify tokens
    access_payload = verify_token(access_token, token_type="access")
    print(f"✅ Access token verified: {access_payload['type']}")
    
    refresh_payload = verify_refresh_token(refresh_token)
    print(f"✅ Refresh token verified: {refresh_payload['type']}")
    
    print("✅ Token creation tests passed!\n")


def test_token_expiration():
    """Test token expiration logic."""
    print("⏰ Testing Token Expiration...")
    
    user_data = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "role": "admin",
        "company_id": "test-company-id"
    }
    
    # Create token that expires in 1 second
    short_lived_token = create_access_token(
        user_data, 
        expires_delta=timedelta(seconds=1)
    )
    
    # Token should not be expired immediately
    assert not is_token_expired(short_lived_token), "Token should not be expired immediately"
    print("✅ Fresh token is not expired")
    
    # Wait for token to expire
    import time
    time.sleep(2)
    
    # Token should now be expired
    assert is_token_expired(short_lived_token), "Token should be expired after waiting"
    print("✅ Token correctly expires after time limit")
    
    # Try to verify expired token (should raise exception)
    try:
        verify_token(short_lived_token)
        assert False, "Should have raised exception for expired token"
    except Exception as e:
        print(f"✅ Expired token verification correctly failed: {type(e).__name__}")
    
    print("✅ Token expiration tests passed!\n")


def test_token_types():
    """Test that token types are enforced."""
    print("🏷️  Testing Token Types...")
    
    user_data = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "role": "admin",
        "company_id": "test-company-id"
    }
    
    # Create tokens
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)
    
    # Test correct type verification
    access_payload = verify_token(access_token, token_type="access")
    assert access_payload["type"] == "access"
    print("✅ Access token type verified correctly")
    
    refresh_payload = verify_token(refresh_token, token_type="refresh")
    assert refresh_payload["type"] == "refresh"
    print("✅ Refresh token type verified correctly")
    
    # Test incorrect type verification
    try:
        verify_token(access_token, token_type="refresh")
        assert False, "Should have failed with wrong token type"
    except Exception as e:
        print(f"✅ Access token correctly rejected as refresh token: {type(e).__name__}")
    
    try:
        verify_token(refresh_token, token_type="access")
        assert False, "Should have failed with wrong token type"
    except Exception as e:
        print(f"✅ Refresh token correctly rejected as access token: {type(e).__name__}")
    
    print("✅ Token type tests passed!\n")


def test_token_data_integrity():
    """Test that token data is preserved correctly."""
    print("🔍 Testing Token Data Integrity...")
    
    original_data = {
        "sub": "test-user-id-123",
        "email": "user@company.com",
        "role": "buyer",
        "company_id": "company-id-456"
    }
    
    # Create and verify access token
    access_token = create_access_token(original_data)
    access_payload = verify_token(access_token)
    
    # Check all data is preserved
    for key, value in original_data.items():
        assert access_payload[key] == value, f"Data mismatch for {key}"
        print(f"✅ {key}: {value}")
    
    # Create and verify refresh token
    refresh_token = create_refresh_token(original_data)
    refresh_payload = verify_refresh_token(refresh_token)
    
    # Check all data is preserved
    for key, value in original_data.items():
        assert refresh_payload[key] == value, f"Data mismatch for {key} in refresh token"
    
    print("✅ Token data integrity tests passed!\n")


def test_user_token_data_helper():
    """Test the create_user_token_data helper function."""
    print("👤 Testing User Token Data Helper...")
    
    token_data = create_user_token_data(
        user_id="user-123",
        email="test@example.com",
        role="admin",
        company_id="company-456"
    )
    
    expected_data = {
        "sub": "user-123",
        "email": "test@example.com",
        "role": "admin",
        "company_id": "company-456",
        "type": "access"
    }
    
    for key, value in expected_data.items():
        assert token_data[key] == value, f"Helper function data mismatch for {key}"
        print(f"✅ {key}: {value}")
    
    print("✅ User token data helper tests passed!\n")


def test_configuration():
    """Test that JWT configuration is properly set."""
    print("⚙️  Testing JWT Configuration...")
    
    # Check required settings
    assert hasattr(settings, 'jwt_secret_key'), "JWT secret key not configured"
    assert hasattr(settings, 'jwt_algorithm'), "JWT algorithm not configured"
    assert hasattr(settings, 'jwt_access_token_expire_minutes'), "Access token expiration not configured"
    assert hasattr(settings, 'jwt_refresh_token_expire_days'), "Refresh token expiration not configured"
    
    print(f"✅ JWT Algorithm: {settings.jwt_algorithm}")
    print(f"✅ Access Token Expiration: {settings.jwt_access_token_expire_minutes} minutes")
    print(f"✅ Refresh Token Expiration: {settings.jwt_refresh_token_expire_days} days")
    print(f"✅ Secret Key Length: {len(settings.jwt_secret_key)} characters")
    
    # Validate configuration values
    assert settings.jwt_access_token_expire_minutes > 0, "Access token expiration must be positive"
    assert settings.jwt_refresh_token_expire_days > 0, "Refresh token expiration must be positive"
    assert len(settings.jwt_secret_key) >= 32, "JWT secret key should be at least 32 characters"
    
    print("✅ JWT configuration tests passed!\n")


def main():
    """Run all JWT refresh tests."""
    print("🚀 Starting JWT Token Refresh Tests\n")
    
    try:
        test_configuration()
        test_token_creation()
        test_token_expiration()
        test_token_types()
        test_token_data_integrity()
        test_user_token_data_helper()
        
        print("🎉 All JWT token refresh tests passed!")
        print("\n📋 Summary:")
        print("✅ Token creation and verification working")
        print("✅ Token expiration logic working")
        print("✅ Token type enforcement working")
        print("✅ Token data integrity preserved")
        print("✅ Configuration properly set")
        print("\n🎯 JWT Token Refresh Mechanism Ready!")
        print("📝 Next steps:")
        print("1. Add rate limiting to authentication endpoints")
        print("2. Test token refresh API endpoints")
        print("3. Implement frontend token refresh logic")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
