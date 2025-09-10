"""
Password policy enforcement and validation.

This module implements comprehensive password security policies including
complexity requirements, breach checking, and password strength scoring.
"""

import re
import hashlib
import secrets
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class PasswordStrength(str, Enum):
    """Password strength levels."""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class PasswordPolicyConfig:
    """Password policy configuration."""
    
    # Minimum requirements
    MIN_LENGTH = 12
    MAX_LENGTH = 128
    
    # Character requirements
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Special characters allowed
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Complexity requirements
    MIN_UNIQUE_CHARS = 8
    MAX_REPEATED_CHARS = 2
    MAX_SEQUENTIAL_CHARS = 3
    
    # Common patterns to reject
    FORBIDDEN_PATTERNS = [
        r"password",
        r"123456",
        r"qwerty",
        r"admin",
        r"login",
        r"user",
        r"test",
        r"guest",
        r"demo"
    ]
    
    # Dictionary words to check (simplified list)
    COMMON_WORDS = {
        "password", "admin", "login", "user", "test", "guest", "demo",
        "welcome", "hello", "world", "company", "business", "office",
        "manager", "director", "employee", "staff", "team", "group"
    }


class PasswordValidationResult:
    """Result of password validation."""
    
    def __init__(self):
        self.is_valid = False
        self.strength = PasswordStrength.VERY_WEAK
        self.score = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def add_error(self, message: str):
        """Add a validation error."""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a validation warning."""
        self.warnings.append(message)
    
    def add_suggestion(self, message: str):
        """Add a suggestion for improvement."""
        self.suggestions.append(message)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "is_valid": self.is_valid,
            "strength": self.strength.value,
            "score": self.score,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions
        }


class PasswordPolicy:
    """
    Comprehensive password policy enforcement.
    
    Features:
    - Length and complexity requirements
    - Character diversity validation
    - Common pattern detection
    - Dictionary word checking
    - Strength scoring
    - Breach checking (placeholder)
    """
    
    def __init__(self, config: Optional[PasswordPolicyConfig] = None):
        self.config = config or PasswordPolicyConfig()
    
    def validate_password(self, password: str, user_info: Optional[Dict] = None) -> PasswordValidationResult:
        """
        Validate a password against the policy.
        
        Args:
            password: Password to validate
            user_info: Optional user information for personalized checks
            
        Returns:
            PasswordValidationResult with validation details
        """
        result = PasswordValidationResult()
        
        # Basic length check
        if not self._check_length(password, result):
            return result
        
        # Character requirements
        self._check_character_requirements(password, result)
        
        # Complexity checks
        self._check_complexity(password, result)
        
        # Pattern checks
        self._check_forbidden_patterns(password, result)
        
        # Dictionary checks
        self._check_dictionary_words(password, result)
        
        # Personal information checks
        if user_info:
            self._check_personal_info(password, user_info, result)
        
        # Calculate strength score
        result.score = self._calculate_strength_score(password)
        result.strength = self._determine_strength_level(result.score)
        
        # Determine if password is valid
        result.is_valid = len(result.errors) == 0 and result.score >= 60
        
        # Add suggestions if not valid
        if not result.is_valid:
            self._add_improvement_suggestions(result)
        
        return result
    
    def _check_length(self, password: str, result: PasswordValidationResult) -> bool:
        """Check password length requirements."""
        if len(password) < self.config.MIN_LENGTH:
            result.add_error(f"Password must be at least {self.config.MIN_LENGTH} characters long")
            return False
        
        if len(password) > self.config.MAX_LENGTH:
            result.add_error(f"Password must not exceed {self.config.MAX_LENGTH} characters")
            return False
        
        return True
    
    def _check_character_requirements(self, password: str, result: PasswordValidationResult):
        """Check character type requirements."""
        if self.config.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            result.add_error("Password must contain at least one uppercase letter")
        
        if self.config.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            result.add_error("Password must contain at least one lowercase letter")
        
        if self.config.REQUIRE_DIGITS and not re.search(r'[0-9]', password):
            result.add_error("Password must contain at least one digit")
        
        if self.config.REQUIRE_SPECIAL_CHARS and not re.search(f'[{re.escape(self.config.SPECIAL_CHARS)}]', password):
            result.add_error(f"Password must contain at least one special character ({self.config.SPECIAL_CHARS})")
    
    def _check_complexity(self, password: str, result: PasswordValidationResult):
        """Check password complexity requirements."""
        # Check unique characters
        unique_chars = len(set(password.lower()))
        if unique_chars < self.config.MIN_UNIQUE_CHARS:
            result.add_error(f"Password must contain at least {self.config.MIN_UNIQUE_CHARS} unique characters")
        
        # Check for repeated characters
        for i in range(len(password) - self.config.MAX_REPEATED_CHARS):
            if password[i] == password[i + 1] == password[i + 2]:
                result.add_error(f"Password cannot contain more than {self.config.MAX_REPEATED_CHARS} consecutive identical characters")
                break
        
        # Check for sequential characters
        self._check_sequential_patterns(password, result)
    
    def _check_sequential_patterns(self, password: str, result: PasswordValidationResult):
        """Check for sequential character patterns."""
        password_lower = password.lower()
        
        # Check for ascending sequences
        for i in range(len(password_lower) - self.config.MAX_SEQUENTIAL_CHARS + 1):
            sequence = password_lower[i:i + self.config.MAX_SEQUENTIAL_CHARS]
            if self._is_sequential(sequence):
                result.add_warning(f"Avoid sequential characters like '{sequence}'")
                break
    
    def _is_sequential(self, sequence: str) -> bool:
        """Check if a sequence is sequential (ascending or descending)."""
        if len(sequence) < 3:
            return False
        
        # Check ascending
        ascending = all(ord(sequence[i]) == ord(sequence[i-1]) + 1 for i in range(1, len(sequence)))
        
        # Check descending
        descending = all(ord(sequence[i]) == ord(sequence[i-1]) - 1 for i in range(1, len(sequence)))
        
        return ascending or descending
    
    def _check_forbidden_patterns(self, password: str, result: PasswordValidationResult):
        """Check for forbidden patterns."""
        password_lower = password.lower()
        
        for pattern in self.config.FORBIDDEN_PATTERNS:
            if re.search(pattern, password_lower):
                result.add_error(f"Password cannot contain common pattern: {pattern}")
    
    def _check_dictionary_words(self, password: str, result: PasswordValidationResult):
        """Check for dictionary words."""
        password_lower = password.lower()
        
        for word in self.config.COMMON_WORDS:
            if word in password_lower:
                result.add_warning(f"Avoid using common words like '{word}'")
    
    def _check_personal_info(self, password: str, user_info: Dict, result: PasswordValidationResult):
        """Check if password contains personal information."""
        password_lower = password.lower()
        
        # Check email
        if user_info.get("email"):
            email_parts = user_info["email"].lower().split("@")
            if email_parts[0] in password_lower:
                result.add_error("Password cannot contain your email username")
        
        # Check name
        if user_info.get("first_name"):
            if user_info["first_name"].lower() in password_lower:
                result.add_error("Password cannot contain your first name")
        
        if user_info.get("last_name"):
            if user_info["last_name"].lower() in password_lower:
                result.add_error("Password cannot contain your last name")
        
        # Check company name
        if user_info.get("company_name"):
            if user_info["company_name"].lower() in password_lower:
                result.add_error("Password cannot contain your company name")
    
    def _calculate_strength_score(self, password: str) -> int:
        """Calculate password strength score (0-100)."""
        score = 0
        
        # Length bonus
        score += min(len(password) * 2, 25)
        
        # Character diversity
        char_types = 0
        if re.search(r'[a-z]', password):
            char_types += 1
        if re.search(r'[A-Z]', password):
            char_types += 1
        if re.search(r'[0-9]', password):
            char_types += 1
        if re.search(f'[{re.escape(self.config.SPECIAL_CHARS)}]', password):
            char_types += 1
        
        score += char_types * 10
        
        # Unique characters
        unique_chars = len(set(password))
        score += min(unique_chars * 2, 20)
        
        # Entropy bonus
        if len(password) >= 16:
            score += 10
        if len(password) >= 20:
            score += 5
        
        # Penalty for common patterns
        password_lower = password.lower()
        for pattern in self.config.FORBIDDEN_PATTERNS:
            if re.search(pattern, password_lower):
                score -= 15
        
        return max(0, min(100, score))
    
    def _determine_strength_level(self, score: int) -> PasswordStrength:
        """Determine password strength level from score."""
        if score >= 90:
            return PasswordStrength.VERY_STRONG
        elif score >= 75:
            return PasswordStrength.STRONG
        elif score >= 60:
            return PasswordStrength.GOOD
        elif score >= 45:
            return PasswordStrength.FAIR
        elif score >= 25:
            return PasswordStrength.WEAK
        else:
            return PasswordStrength.VERY_WEAK
    
    def _add_improvement_suggestions(self, result: PasswordValidationResult):
        """Add suggestions for password improvement."""
        if result.score < 60:
            result.add_suggestion("Use a longer password (16+ characters recommended)")
            result.add_suggestion("Include a mix of uppercase, lowercase, numbers, and special characters")
            result.add_suggestion("Avoid common words and patterns")
            result.add_suggestion("Consider using a passphrase with random words")


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a cryptographically secure password.
    
    Args:
        length: Desired password length
        
    Returns:
        Secure random password
    """
    if length < 12:
        length = 12
    
    # Character sets
    lowercase = "abcdefghijklmnopqrstuvwxyz"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    digits = "0123456789"
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one character from each set
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]
    
    # Fill remaining length with random characters
    all_chars = lowercase + uppercase + digits + special
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def check_password_breach(password: str) -> bool:
    """
    Check if password appears in known breaches (placeholder implementation).
    
    In production, this would integrate with services like HaveIBeenPwned.
    
    Args:
        password: Password to check
        
    Returns:
        True if password is found in breaches
    """
    # Placeholder implementation
    # In production, use SHA-1 hash and check against breach databases
    password_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    
    # For demo purposes, mark some obviously weak passwords as breached
    weak_passwords = {
        "password123", "admin123", "welcome123", "qwerty123",
        "123456789", "password1", "admin1234"
    }
    
    return password.lower() in weak_passwords
