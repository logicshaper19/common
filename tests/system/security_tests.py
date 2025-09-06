"""
Security testing module for system tests
"""
import requests
import time
from typing import Dict, List, Any
from urllib.parse import urljoin
from tests.system.config import TestConfig
from tests.system.test_data_factory import SystemTestDataFactory


class SecurityTestSuite:
    """Security testing suite for web application vulnerabilities."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.data_factory = SystemTestDataFactory()
        self.results = {
            "vulnerabilities_found": [],
            "tests_passed": 0,
            "tests_failed": 0,
            "total_tests": 0
        }
    
    def test_xss_vulnerabilities(self) -> Dict[str, Any]:
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        print("   🔍 Testing XSS vulnerabilities...")
        
        xss_results = {
            "test_type": "XSS",
            "vulnerabilities": [],
            "endpoints_tested": 0
        }
        
        payloads = self.data_factory.get_security_test_payloads()["xss_payloads"]
        
        # Test endpoints that accept user input
        test_endpoints = [
            {"path": "/auth/login", "method": "POST", "params": ["email", "password"]},
            {"path": "/companies", "method": "POST", "params": ["name", "description"]},
            {"path": "/products", "method": "POST", "params": ["name", "description"]},
        ]
        
        for endpoint in test_endpoints:
            for payload in payloads:
                try:
                    url = urljoin(self.config.api_base_url, endpoint["path"])
                    
                    # Create test data with XSS payload
                    test_data = {}
                    for param in endpoint["params"]:
                        test_data[param] = payload
                    
                    if endpoint["method"] == "POST":
                        response = requests.post(url, json=test_data, timeout=self.config.api_timeout)
                    else:
                        response = requests.get(url, params=test_data, timeout=self.config.api_timeout)
                    
                    # Check if payload is reflected in response
                    if payload in response.text and response.status_code == 200:
                        xss_results["vulnerabilities"].append({
                            "endpoint": endpoint["path"],
                            "method": endpoint["method"],
                            "payload": payload,
                            "severity": "HIGH",
                            "description": "XSS payload reflected in response"
                        })
                        self.results["tests_failed"] += 1
                    else:
                        self.results["tests_passed"] += 1
                    
                    self.results["total_tests"] += 1
                    xss_results["endpoints_tested"] += 1
                    
                except Exception as e:
                    print(f"     ⚠️ XSS test error for {endpoint['path']}: {str(e)}")
        
        return xss_results
    
    def test_sql_injection(self) -> Dict[str, Any]:
        """Test for SQL injection vulnerabilities."""
        print("   🔍 Testing SQL injection vulnerabilities...")
        
        sqli_results = {
            "test_type": "SQL_INJECTION",
            "vulnerabilities": [],
            "endpoints_tested": 0
        }
        
        payloads = self.data_factory.get_security_test_payloads()["sql_injection_payloads"]
        
        # Test endpoints with database queries
        test_endpoints = [
            {"path": "/auth/login", "method": "POST", "params": ["email", "password"]},
            {"path": "/companies", "method": "GET", "params": ["search"]},
            {"path": "/products", "method": "GET", "params": ["category", "search"]},
            {"path": "/purchase-orders", "method": "GET", "params": ["status", "company_id"]},
        ]
        
        for endpoint in test_endpoints:
            for payload in payloads:
                try:
                    url = urljoin(self.config.api_base_url, endpoint["path"])
                    
                    # Create test data with SQL injection payload
                    test_data = {}
                    for param in endpoint["params"]:
                        test_data[param] = payload
                    
                    start_time = time.time()
                    
                    if endpoint["method"] == "POST":
                        response = requests.post(url, json=test_data, timeout=self.config.api_timeout)
                    else:
                        response = requests.get(url, params=test_data, timeout=self.config.api_timeout)
                    
                    response_time = time.time() - start_time
                    
                    # Check for SQL injection indicators
                    sql_error_indicators = [
                        "sql syntax",
                        "mysql_fetch",
                        "postgresql",
                        "ora-",
                        "sqlite",
                        "syntax error"
                    ]
                    
                    response_text = response.text.lower()
                    has_sql_error = any(indicator in response_text for indicator in sql_error_indicators)
                    
                    # Check for time-based SQL injection (response takes unusually long)
                    time_based_sqli = response_time > 5.0 and "sleep" in payload.lower()
                    
                    if has_sql_error or time_based_sqli:
                        sqli_results["vulnerabilities"].append({
                            "endpoint": endpoint["path"],
                            "method": endpoint["method"],
                            "payload": payload,
                            "severity": "CRITICAL",
                            "description": "Potential SQL injection vulnerability detected",
                            "response_time": response_time,
                            "has_sql_error": has_sql_error
                        })
                        self.results["tests_failed"] += 1
                    else:
                        self.results["tests_passed"] += 1
                    
                    self.results["total_tests"] += 1
                    sqli_results["endpoints_tested"] += 1
                    
                except Exception as e:
                    print(f"     ⚠️ SQL injection test error for {endpoint['path']}: {str(e)}")
        
        return sqli_results
    
    def test_authentication_bypass(self) -> Dict[str, Any]:
        """Test for authentication bypass vulnerabilities."""
        print("   🔍 Testing authentication bypass...")
        
        auth_results = {
            "test_type": "AUTHENTICATION_BYPASS",
            "vulnerabilities": [],
            "endpoints_tested": 0
        }
        
        # Test protected endpoints without authentication
        protected_endpoints = [
            "/companies",
            "/products",
            "/purchase-orders",
            "/users/me",
            "/transparency/companies"
        ]
        
        for endpoint in protected_endpoints:
            try:
                url = urljoin(self.config.api_base_url, endpoint)
                
                # Test without any authentication
                response = requests.get(url, timeout=self.config.api_timeout)
                
                # Should return 401 Unauthorized
                if response.status_code != 401:
                    auth_results["vulnerabilities"].append({
                        "endpoint": endpoint,
                        "method": "GET",
                        "severity": "HIGH",
                        "description": f"Endpoint accessible without authentication (returned {response.status_code})",
                        "expected_status": 401,
                        "actual_status": response.status_code
                    })
                    self.results["tests_failed"] += 1
                else:
                    self.results["tests_passed"] += 1
                
                # Test with invalid token
                invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
                response = requests.get(url, headers=invalid_headers, timeout=self.config.api_timeout)
                
                if response.status_code not in [401, 403]:
                    auth_results["vulnerabilities"].append({
                        "endpoint": endpoint,
                        "method": "GET",
                        "severity": "HIGH",
                        "description": f"Endpoint accessible with invalid token (returned {response.status_code})",
                        "expected_status": [401, 403],
                        "actual_status": response.status_code
                    })
                    self.results["tests_failed"] += 1
                else:
                    self.results["tests_passed"] += 1
                
                self.results["total_tests"] += 2
                auth_results["endpoints_tested"] += 1
                
            except Exception as e:
                print(f"     ⚠️ Auth bypass test error for {endpoint}: {str(e)}")
        
        return auth_results
    
    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test for rate limiting implementation."""
        print("   🔍 Testing rate limiting...")
        
        rate_limit_results = {
            "test_type": "RATE_LIMITING",
            "vulnerabilities": [],
            "endpoints_tested": 0
        }
        
        # Test endpoints that should have rate limiting
        test_endpoints = [
            "/auth/login",
            "/auth/register",
            "/companies",
            "/products"
        ]
        
        for endpoint in test_endpoints:
            try:
                url = urljoin(self.config.api_base_url, endpoint)
                
                # Make rapid requests to test rate limiting
                responses = []
                for i in range(20):  # Make 20 rapid requests
                    response = requests.get(url, timeout=self.config.api_timeout)
                    responses.append(response.status_code)
                    time.sleep(0.1)  # Small delay between requests
                
                # Check if any requests were rate limited (429 status)
                rate_limited = any(status == 429 for status in responses)
                
                if not rate_limited and endpoint in ["/auth/login", "/auth/register"]:
                    # Critical endpoints should have rate limiting
                    rate_limit_results["vulnerabilities"].append({
                        "endpoint": endpoint,
                        "severity": "MEDIUM",
                        "description": "No rate limiting detected on sensitive endpoint",
                        "requests_made": len(responses),
                        "rate_limited": False
                    })
                    self.results["tests_failed"] += 1
                else:
                    self.results["tests_passed"] += 1
                
                self.results["total_tests"] += 1
                rate_limit_results["endpoints_tested"] += 1
                
            except Exception as e:
                print(f"     ⚠️ Rate limiting test error for {endpoint}: {str(e)}")
        
        return rate_limit_results
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run all security tests."""
        print("\n🔒 Running Security Tests...")
        
        security_results = {
            "timestamp": time.time(),
            "test_results": {},
            "summary": {}
        }
        
        # Run individual security test suites
        security_results["test_results"]["xss"] = self.test_xss_vulnerabilities()
        security_results["test_results"]["sql_injection"] = self.test_sql_injection()
        security_results["test_results"]["authentication"] = self.test_authentication_bypass()
        security_results["test_results"]["rate_limiting"] = self.test_rate_limiting()
        
        # Compile all vulnerabilities
        all_vulnerabilities = []
        for test_type, results in security_results["test_results"].items():
            all_vulnerabilities.extend(results.get("vulnerabilities", []))
        
        # Calculate summary
        security_results["summary"] = {
            "total_vulnerabilities": len(all_vulnerabilities),
            "critical_vulnerabilities": len([v for v in all_vulnerabilities if v.get("severity") == "CRITICAL"]),
            "high_vulnerabilities": len([v for v in all_vulnerabilities if v.get("severity") == "HIGH"]),
            "medium_vulnerabilities": len([v for v in all_vulnerabilities if v.get("severity") == "MEDIUM"]),
            "tests_passed": self.results["tests_passed"],
            "tests_failed": self.results["tests_failed"],
            "total_tests": self.results["total_tests"],
            "security_score": f"{(self.results['tests_passed'] / max(self.results['total_tests'], 1)) * 100:.1f}%"
        }
        
        # Print summary
        print(f"   📊 Security Tests: {self.results['tests_passed']}/{self.results['total_tests']} passed")
        print(f"   🚨 Vulnerabilities Found: {len(all_vulnerabilities)}")
        if all_vulnerabilities:
            print(f"      Critical: {security_results['summary']['critical_vulnerabilities']}")
            print(f"      High: {security_results['summary']['high_vulnerabilities']}")
            print(f"      Medium: {security_results['summary']['medium_vulnerabilities']}")
        
        return security_results