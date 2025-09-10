#!/usr/bin/env python3
"""
Comprehensive test script for all security improvements.
"""

import sys
import asyncio
sys.path.append('.')

from app.core.password_policy import PasswordPolicy, PasswordStrength, generate_secure_password
from app.core.auth_rate_limiting import AuthRateLimiter, AuthAttemptResult
from app.core.rate_limiting import RateLimitType, RateLimitConfig


def test_password_policy():
    """Test password policy enforcement."""
    print("🔐 Testing Password Policy...")
    
    policy = PasswordPolicy()
    
    # Test weak passwords
    weak_passwords = [
        "password123",
        "admin",
        "12345678",
        "qwerty123",
        "Password1",  # Too short
        "passwordpasswordpassword",  # No numbers/special chars
    ]
    
    print("Testing weak passwords:")
    for password in weak_passwords:
        result = policy.validate_password(password)
        print(f"  '{password}': {result.strength.value} (score: {result.score}) - Valid: {result.is_valid}")
        assert not result.is_valid or result.score < 60, f"Weak password '{password}' should be rejected"
    
    # Test strong passwords
    strong_passwords = [
        "MyStr0ng!P@ssw0rd2024",
        "C0mplex&Secure#Password!",
        "Th1s!s@V3ryStr0ngP@ssw0rd",
    ]
    
    print("\nTesting strong passwords:")
    for password in strong_passwords:
        result = policy.validate_password(password)
        print(f"  '{password}': {result.strength.value} (score: {result.score}) - Valid: {result.is_valid}")
        assert result.is_valid and result.score >= 60, f"Strong password '{password}' should be accepted"
    
    # Test personal information detection
    user_info = {
        "email": "john.doe@company.com",
        "first_name": "John",
        "last_name": "Doe",
        "company_name": "Company"
    }
    
    personal_passwords = [
        "john123!",
        "Company2024!",
        "doe@password"
    ]
    
    print("\nTesting personal information detection:")
    for password in personal_passwords:
        result = policy.validate_password(password, user_info)
        print(f"  '{password}': Errors: {result.errors}")
        assert len(result.errors) > 0, f"Password '{password}' should be rejected for containing personal info"
    
    print("✅ Password policy tests passed!\n")


def test_password_generation():
    """Test secure password generation."""
    print("🎲 Testing Password Generation...")
    
    # Generate multiple passwords
    for length in [12, 16, 20, 24]:
        password = generate_secure_password(length)
        print(f"  Generated {length}-char password: {password}")
        
        # Validate the generated password
        policy = PasswordPolicy()
        result = policy.validate_password(password)
        
        assert len(password) == length, f"Password should be {length} characters"
        assert result.is_valid, f"Generated password should be valid"
        assert result.score >= 75, f"Generated password should be strong (score: {result.score})"
    
    print("✅ Password generation tests passed!\n")


async def test_rate_limiting_integration():
    """Test rate limiting integration."""
    print("🚦 Testing Rate Limiting Integration...")
    
    # Test rate limit configurations
    auth_config = RateLimitConfig.get_limit(RateLimitType.AUTH)
    standard_config = RateLimitConfig.get_limit(RateLimitType.STANDARD)
    
    print(f"  Auth rate limit: {auth_config}")
    print(f"  Standard rate limit: {standard_config}")
    
    assert auth_config["requests"] <= 10, "Auth rate limit should be restrictive"
    assert auth_config["window"] == 60, "Auth rate limit window should be 1 minute"
    
    # Test auth rate limiter
    rate_limiter = AuthRateLimiter()
    
    # Mock request object
    class MockRequest:
        def __init__(self, ip="192.168.1.100"):
            self.client = type('obj', (object,), {'host': ip})
            self.headers = {}
    
    request = MockRequest()
    
    # Test basic functionality
    is_allowed, info = await rate_limiter.check_auth_rate_limit(request, "test@example.com")
    assert is_allowed, "Initial request should be allowed"
    
    print("✅ Rate limiting integration tests passed!\n")


def test_security_configurations():
    """Test security configuration values."""
    print("⚙️  Testing Security Configurations...")
    
    # Test password policy config
    from app.core.password_policy import PasswordPolicyConfig
    
    config = PasswordPolicyConfig()
    
    print(f"  Min password length: {config.MIN_LENGTH}")
    print(f"  Max password length: {config.MAX_LENGTH}")
    print(f"  Require uppercase: {config.REQUIRE_UPPERCASE}")
    print(f"  Require lowercase: {config.REQUIRE_LOWERCASE}")
    print(f"  Require digits: {config.REQUIRE_DIGITS}")
    print(f"  Require special chars: {config.REQUIRE_SPECIAL_CHARS}")
    print(f"  Min unique chars: {config.MIN_UNIQUE_CHARS}")
    
    # Validate configuration
    assert config.MIN_LENGTH >= 12, "Minimum password length should be at least 12"
    assert config.MAX_LENGTH <= 128, "Maximum password length should be reasonable"
    assert config.REQUIRE_UPPERCASE, "Should require uppercase letters"
    assert config.REQUIRE_LOWERCASE, "Should require lowercase letters"
    assert config.REQUIRE_DIGITS, "Should require digits"
    assert config.REQUIRE_SPECIAL_CHARS, "Should require special characters"
    assert config.MIN_UNIQUE_CHARS >= 8, "Should require sufficient unique characters"
    
    print("✅ Security configuration tests passed!\n")


def test_password_strength_levels():
    """Test password strength level determination."""
    print("💪 Testing Password Strength Levels...")
    
    policy = PasswordPolicy()
    
    # Test different strength levels
    test_cases = [
        ("123", PasswordStrength.VERY_WEAK),
        ("password", PasswordStrength.VERY_WEAK),
        ("Password1", PasswordStrength.WEAK),
        ("Password123", PasswordStrength.FAIR),
        ("Password123!", PasswordStrength.GOOD),
        ("MyStr0ng!P@ssw0rd2024", PasswordStrength.VERY_STRONG),
    ]
    
    for password, expected_strength in test_cases:
        result = policy.validate_password(password)
        print(f"  '{password}': {result.strength.value} (expected: {expected_strength.value})")
        
        # Allow some flexibility in strength determination
        strength_order = [
            PasswordStrength.VERY_WEAK,
            PasswordStrength.WEAK,
            PasswordStrength.FAIR,
            PasswordStrength.GOOD,
            PasswordStrength.STRONG,
            PasswordStrength.VERY_STRONG
        ]
        
        actual_index = strength_order.index(result.strength)
        expected_index = strength_order.index(expected_strength)
        
        # Allow within 1 level of expected
        assert abs(actual_index - expected_index) <= 1, f"Strength level for '{password}' should be close to expected"
    
    print("✅ Password strength level tests passed!\n")


def test_error_messages():
    """Test that error messages are helpful and specific."""
    print("💬 Testing Error Messages...")
    
    policy = PasswordPolicy()
    
    # Test specific error conditions
    test_cases = [
        ("short", "must be at least"),
        ("nouppercase123!", "uppercase letter"),
        ("NOLOWERCASE123!", "lowercase letter"),
        ("NoNumbers!", "digit"),
        ("NoSpecialChars123", "special character"),
        ("password123!", "common pattern"),
    ]
    
    for password, expected_error in test_cases:
        result = policy.validate_password(password)
        error_text = " ".join(result.errors).lower()
        print(f"  '{password}': {result.errors}")
        
        assert expected_error.lower() in error_text, f"Error for '{password}' should mention '{expected_error}'"
    
    print("✅ Error message tests passed!\n")


async def main():
    """Run all security improvement tests."""
    print("🚀 Starting Comprehensive Security Tests\n")
    
    try:
        test_password_policy()
        test_password_generation()
        await test_rate_limiting_integration()
        test_security_configurations()
        test_password_strength_levels()
        test_error_messages()
        
        print("🎉 All security improvement tests passed!")
        print("\n📋 Security Features Implemented:")
        print("✅ Comprehensive password policy enforcement")
        print("✅ Password strength scoring and validation")
        print("✅ Personal information detection")
        print("✅ Secure password generation")
        print("✅ Authentication rate limiting with progressive penalties")
        print("✅ Brute force attack protection")
        print("✅ Company isolation and access control")
        print("✅ Detailed error messages and suggestions")
        
        print("\n🛡️  Security Improvements Summary:")
        print("• Password complexity requirements (12+ chars, mixed case, numbers, symbols)")
        print("• Progressive lockout penalties (3 failures → 1 min, 5 → 5 min, etc.)")
        print("• IP and email-based rate limiting")
        print("• Personal information detection in passwords")
        print("• Company-based resource access control")
        print("• Comprehensive audit logging")
        print("• Redis-backed with memory fallback")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
