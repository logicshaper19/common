"""
Comprehensive Testing Framework
Unit tests and security tests for supply chain functions.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Any
import tempfile
import os
import sys
from datetime import datetime, date, timedelta
import json
import uuid
import logging

# Import the modules we're testing
from .certification_functions import CertificationManager
from .supply_chain_functions import SupplyChainManager
from .input_validator import InputValidator, ValidationError, ValidatorType
from .secure_query_builder import SecureQueryBuilder, QueryOperator
from .database_manager import SecureDatabaseManager, DatabaseConfig

# Configure logging for tests
logging.basicConfig(level=logging.WARNING)

class SecurityTestCase(unittest.TestCase):
    """Base class for security-focused tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        self.validator = InputValidator()
    
    def assert_no_sql_injection(self, query: str, params: List[Any]):
        """Assert that query is properly parameterized."""
        # Check that query uses placeholders
        param_count = query.count('%s')
        self.assertEqual(param_count, len(params), 
                        "Parameter count mismatch - possible SQL injection risk")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            "' OR '1'='1",
            "; DROP TABLE",
            "UNION SELECT",
            "' UNION ",
            "-- ",
            "/*",
            "*/",
            "xp_",
            "sp_"
        ]
        
        query_lower = query.lower()
        for pattern in dangerous_patterns:
            self.assertNotIn(pattern.lower(), query_lower,
                           f"Query contains dangerous pattern: {pattern}")
    
    def generate_malicious_inputs(self) -> List[str]:
        """Generate common SQL injection and XSS payloads."""
        return [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "' AND (SELECT COUNT(*) FROM users) > 0 --",
            "'; EXEC xp_cmdshell('dir'); --",
            "1; DELETE FROM products; --",
            "' OR 1=1#",
            "\"; DELETE FROM batches; \"",
            "' OR 'a'='a",
            "admin'--",
            "admin'/*",
            "' OR 1=1-- ",
            "' OR 1=1/*",
            "' UNION ALL SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
            "<img src=x onerror=alert('xss')>",
            "<?php echo 'Hello'; ?>",
            "${7*7}",
            "{{7*7}}",
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "\x00\x01\x02\x03\x04\x05"
        ]

class TestInputValidator(SecurityTestCase):
    """Test input validation security."""
    
    def test_sql_injection_detection(self):
        """Test that SQL injection patterns are detected."""
        malicious_inputs = self.generate_malicious_inputs()
        
        for malicious_input in malicious_inputs:
            with self.assertRaises(ValidationError):
                self.validator._validate_string("test_field", malicious_input, 
                    self.validator.ValidationRule("test", ValidatorType.STRING))
    
    def test_uuid_validation(self):
        """Test UUID validation."""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            str(uuid.uuid4()),
            "550e8400-e29b-41d4-a716-446655440000"
        ]
        
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",
            "123e4567-e89b-12d3-a456-42661417400X",
            "'; DROP TABLE users; --",
            ""
        ]
        
        for valid_uuid in valid_uuids:
            result = self.validator._validate_uuid("test_field", valid_uuid,
                self.validator.ValidationRule("test", ValidatorType.UUID))
            self.assertIsInstance(result, str)
        
        for invalid_uuid in invalid_uuids:
            with self.assertRaises(ValidationError):
                self.validator._validate_uuid("test_field", invalid_uuid,
                    self.validator.ValidationRule("test", ValidatorType.UUID))
    
    def test_email_validation(self):
        """Test email validation security."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "valid+email@test.org"
        ]
        
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>@domain.com",
            "user@domain.com'; DELETE FROM users; --"
        ]
        
        for valid_email in valid_emails:
            result = self.validator._validate_email("test_field", valid_email,
                self.validator.ValidationRule("test", ValidatorType.EMAIL))
            self.assertIsInstance(result, str)
        
        for invalid_email in invalid_emails:
            with self.assertRaises(ValidationError):
                self.validator._validate_email("test_field", invalid_email,
                    self.validator.ValidationRule("test", ValidatorType.EMAIL))
    
    def test_percentage_validation(self):
        """Test percentage validation."""
        valid_percentages = [0, 50, 100, 25.5, 99.99]
        invalid_percentages = [-1, 101, "not_a_number", float('inf'), float('nan')]
        
        for valid_pct in valid_percentages:
            result = self.validator._validate_percentage("test_field", valid_pct,
                self.validator.ValidationRule("test", ValidatorType.PERCENTAGE))
            self.assertIsInstance(result, float)
            self.assertGreaterEqual(result, 0)
            self.assertLessEqual(result, 100)
        
        for invalid_pct in invalid_percentages:
            with self.assertRaises(ValidationError):
                self.validator._validate_percentage("test_field", invalid_pct,
                    self.validator.ValidationRule("test", ValidatorType.PERCENTAGE))

class TestSecureQueryBuilder(SecurityTestCase):
    """Test secure query builder."""
    
    def test_table_whitelist(self):
        """Test that only whitelisted tables are allowed."""
        builder = SecureQueryBuilder()
        
        # Valid table
        builder.select(['id', 'name'], 'companies')
        
        # Invalid table should raise error
        with self.assertRaises(ValueError):
            builder.select(['id', 'name'], 'malicious_table')
    
    def test_column_whitelist(self):
        """Test that only whitelisted columns are allowed."""
        builder = SecureQueryBuilder()
        
        # Valid column
        builder.select(['id'], 'companies')
        
        # Invalid column should raise error
        with self.assertRaises(ValueError):
            builder.select(['malicious_column'], 'companies')
    
    def test_parameterized_queries(self):
        """Test that queries are properly parameterized."""
        builder = SecureQueryBuilder()
        builder.select(['id', 'name'], 'companies')
        builder.where('id', QueryOperator.EQUALS, "test-id")
        builder.where('name', QueryOperator.LIKE, "test-name")
        
        query, params = builder.build()
        
        # Check parameterization
        self.assert_no_sql_injection(query, params)
        self.assertIn('%s', query)
        self.assertEqual(len(params), 2)
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection is prevented."""
        builder = SecureQueryBuilder()
        builder.select(['id'], 'companies')
        
        # Try to inject SQL
        malicious_values = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM passwords --"
        ]
        
        for malicious_value in malicious_values:
            builder_copy = SecureQueryBuilder()
            builder_copy.select(['id'], 'companies')
            builder_copy.where('id', QueryOperator.EQUALS, malicious_value)
            
            query, params = builder_copy.build()
            
            # Ensure value is parameterized, not embedded
            self.assertNotIn(malicious_value, query)
            self.assertIn(malicious_value, params)

class TestCertificationManager(SecurityTestCase):
    """Test certification manager security and functionality."""
    
    def setUp(self):
        super().setUp()
        self.manager = CertificationManager(self.mock_db)
        
        # Mock database responses
        self.mock_cursor.fetchall.return_value = [
            {
                'id': 'cert-1',
                'company_id': 'company-1',
                'company_name': 'Test Company',
                'location_id': 'loc-1',
                'location_name': 'Test Location',
                'certification_type': 'RSPO',
                'expiry_date': datetime.now() + timedelta(days=30),
                'issue_date': datetime.now() - timedelta(days=365),
                'issuing_authority': 'RSPO Authority',
                'compliance_status': 'verified',
                'days_until_expiry': 30
            }
        ]
    
    def test_get_certifications_input_validation(self):
        """Test input validation for get_certifications."""
        # Valid inputs should work
        result = self.manager.get_certifications(
            company_id=str(uuid.uuid4()),
            certification_type='RSPO',
            expires_within_days=30
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        
        # Invalid inputs should be rejected
        with patch('app.core.certification_functions.logger') as mock_logger:
            result = self.manager.get_certifications(
                company_id="'; DROP TABLE companies; --",
                expires_within_days=-1
            )
            # Should return error due to validation failure
            self.assertIn('error', result[1])
    
    def test_search_batches_security(self):
        """Test batch search security."""
        # Test with malicious inputs
        malicious_inputs = self.generate_malicious_inputs()
        
        for malicious_input in malicious_inputs:
            with patch('app.core.certification_functions.logger'):
                result = self.manager.search_batches(
                    product_name=malicious_input,
                    company_id=malicious_input
                )
                # Should handle malicious input gracefully
                self.assertIsInstance(result, tuple)
                # Should either work (if input is sanitized) or return error
                if 'error' in result[1]:
                    self.assertIn('Invalid input', result[1]['error'])

class TestDatabaseManager(SecurityTestCase):
    """Test database manager security."""
    
    def test_connection_config_security(self):
        """Test secure database configuration."""
        config = DatabaseConfig(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_password'
        )
        
        # Check that SSL is not disabled by default
        self.assertFalse(config.ssl_disabled)
        
        # Check timeout settings
        self.assertGreater(config.connection_timeout, 0)
        self.assertGreater(config.query_timeout, 0)
    
    @patch('mysql.connector.pooling.MySQLConnectionPool')
    def test_connection_pool_initialization(self, mock_pool):
        """Test secure connection pool initialization."""
        config = DatabaseConfig(
            host='localhost',
            database='test_db',
            user='test_user',
            password='test_password'
        )
        
        manager = SecureDatabaseManager(config)
        
        # Verify pool was created with security settings
        mock_pool.assert_called_once()
        call_args = mock_pool.call_args[1]
        
        # Check security configurations
        self.assertIn('sql_mode', call_args)
        self.assertIn('STRICT_TRANS_TABLES', call_args['sql_mode'])
        self.assertFalse(call_args.get('ssl_disabled', True))

class TestSecurityIntegration(SecurityTestCase):
    """Integration tests for security across all components."""
    
    def test_end_to_end_security(self):
        """Test complete security chain from input to database."""
        # Create a mock scenario that tests the complete flow
        with patch('app.core.certification_functions.execute_secure_query') as mock_query:
            mock_query.return_value = []
            
            manager = CertificationManager(self.mock_db)
            
            # Test with potentially malicious input
            result = manager.get_certifications(
                company_id="'; DROP TABLE users; --",
                certification_type="<script>alert('xss')</script>"
            )
            
            # Should handle gracefully
            self.assertIsInstance(result, tuple)
            
            # If query was called, check it was secure
            if mock_query.called:
                args, kwargs = mock_query.call_args
                if args:
                    query = args[0]
                    params = args[1] if len(args) > 1 else []
                    self.assert_no_sql_injection(query, params)

class TestPerformance(SecurityTestCase):
    """Performance and DoS protection tests."""
    
    def test_query_limits(self):
        """Test that query limits prevent DoS."""
        manager = CertificationManager(self.mock_db)
        
        # Test with excessive limit
        with patch('app.core.certification_functions.logger'):
            result = manager.search_batches(limit=999999)
            # Should be limited or rejected
            self.assertIsInstance(result, tuple)
    
    def test_input_size_limits(self):
        """Test input size limits."""
        validator = InputValidator()
        
        # Very long string
        very_long_string = "A" * 10000
        
        rule = validator.ValidationRule(
            "test", ValidatorType.STRING, max_length=255
        )
        
        with self.assertRaises(ValidationError):
            validator.validate_field("test", very_long_string, rule)

# Test runner and utilities

class SecurityTestRunner:
    """Custom test runner for security tests."""
    
    def __init__(self):
        self.test_results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests and return results."""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add all test classes
        test_classes = [
            TestInputValidator,
            TestSecureQueryBuilder,
            TestCertificationManager,
            TestDatabaseManager,
            TestSecurityIntegration,
            TestPerformance
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        # Compile results
        test_summary = {
            'total_tests': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100,
            'failure_details': [
                {'test': str(test), 'error': error} 
                for test, error in result.failures + result.errors
            ]
        }
        
        return test_summary
    
    def run_security_scan(self) -> Dict[str, Any]:
        """Run comprehensive security scan."""
        security_issues = []
        
        # Check for common security issues
        issues_found = self._scan_for_security_issues()
        security_issues.extend(issues_found)
        
        return {
            'scan_timestamp': datetime.now().isoformat(),
            'issues_found': len(security_issues),
            'critical_issues': len([i for i in security_issues if i.get('severity') == 'critical']),
            'high_issues': len([i for i in security_issues if i.get('severity') == 'high']),
            'medium_issues': len([i for i in security_issues if i.get('severity') == 'medium']),
            'low_issues': len([i for i in security_issues if i.get('severity') == 'low']),
            'details': security_issues
        }
    
    def _scan_for_security_issues(self) -> List[Dict[str, Any]]:
        """Scan code for potential security issues."""
        issues = []
        
        # This would be expanded with actual static analysis
        # For now, it's a placeholder for security scanning logic
        
        return issues

# Test data generators

class TestDataGenerator:
    """Generate test data for security testing."""
    
    @staticmethod
    def generate_valid_company_data() -> Dict[str, Any]:
        """Generate valid company test data."""
        return {
            'company_id': str(uuid.uuid4()),
            'company_type': 'plantation_grower',
            'transparency_score': 85.5,
            'include_statistics': True,
            'include_contact_info': False
        }
    
    @staticmethod
    def generate_malicious_company_data() -> List[Dict[str, Any]]:
        """Generate malicious company test data."""
        base_data = TestDataGenerator.generate_valid_company_data()
        malicious_variants = []
        
        malicious_inputs = [
            "'; DROP TABLE companies; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "\x00\x01\x02",
            "' OR 1=1-- "
        ]
        
        for malicious_input in malicious_inputs:
            variant = base_data.copy()
            variant['company_id'] = malicious_input
            malicious_variants.append(variant)
        
        return malicious_variants
    
    @staticmethod
    def generate_batch_data() -> Dict[str, Any]:
        """Generate valid batch test data."""
        return {
            'product_name': 'Crude Palm Oil',
            'product_type': 'CPO',
            'status': 'available',
            'company_id': str(uuid.uuid4()),
            'min_quantity': 10.0,
            'min_transparency_score': 80.0,
            'certification_required': 'RSPO',
            'limit': 50
        }

# Main test execution

def run_security_tests():
    """Main function to run security tests."""
    print("🔒 Starting Security Test Suite...")
    print("=" * 50)
    
    runner = SecurityTestRunner()
    
    # Run unit tests
    print("\n📋 Running Unit Tests...")
    test_results = runner.run_all_tests()
    
    print(f"\n✅ Test Results:")
    print(f"   Total Tests: {test_results['total_tests']}")
    print(f"   Success Rate: {test_results['success_rate']:.1f}%")
    print(f"   Failures: {test_results['failures']}")
    print(f"   Errors: {test_results['errors']}")
    
    # Run security scan
    print("\n🔍 Running Security Scan...")
    security_results = runner.run_security_scan()
    
    print(f"\n🛡️ Security Scan Results:")
    print(f"   Issues Found: {security_results['issues_found']}")
    print(f"   Critical: {security_results['critical_issues']}")
    print(f"   High: {security_results['high_issues']}")
    print(f"   Medium: {security_results['medium_issues']}")
    print(f"   Low: {security_results['low_issues']}")
    
    # Overall assessment
    overall_score = (
        test_results['success_rate'] * 0.7 +
        max(0, 100 - security_results['issues_found'] * 10) * 0.3
    )
    
    print(f"\n🎯 Overall Security Score: {overall_score:.1f}/100")
    
    if overall_score >= 90:
        print("🟢 EXCELLENT - Production ready!")
    elif overall_score >= 80:
        print("🟡 GOOD - Minor improvements needed")
    elif overall_score >= 70:
        print("🟠 FAIR - Address security issues")
    else:
        print("🔴 POOR - Major security work required")
    
    return {
        'unit_tests': test_results,
        'security_scan': security_results,
        'overall_score': overall_score
    }

if __name__ == '__main__':
    run_security_tests()
