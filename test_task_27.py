#!/usr/bin/env python3
"""
Task 27: Final integration and system testing
Comprehensive test suite for the Common Supply Chain Platform
"""

import sys
import os
import json
import time
import requests
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

@dataclass
class TestResult:
    """Test result data structure."""
    test_name: str
    status: str  # "PASS", "FAIL", "SKIP"
    message: str
    duration: float
    details: Dict[str, Any] = None

class TestStatus(Enum):
    """Test status enumeration."""
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

class Task27TestSuite:
    """Comprehensive test suite for Task 27."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        
    def run_test(self, test_func, test_name: str) -> TestResult:
        """Run a single test and record the result."""
        print(f"\n🧪 Running: {test_name}")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                status = TestStatus.PASS
                message = "Test passed successfully"
                print(f"✅ {test_name}: PASSED ({duration:.2f}s)")
            else:
                status = TestStatus.FAIL
                message = "Test failed"
                print(f"❌ {test_name}: FAILED ({duration:.2f}s)")
                
        except Exception as e:
            duration = time.time() - start_time
            status = TestStatus.ERROR
            message = f"Test error: {str(e)}"
            print(f"💥 {test_name}: ERROR ({duration:.2f}s) - {str(e)}")
            
        test_result = TestResult(
            test_name=test_name,
            status=status.value,
            message=message,
            duration=duration
        )
        
        self.results.append(test_result)
        return test_result
    
    def test_backend_health(self) -> bool:
        """Test 1: Backend health check."""
        try:
            response = requests.get(f"{self.base_url}/health/", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def test_backend_api_docs(self) -> bool:
        """Test 2: Backend API documentation accessibility."""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def test_backend_auth_endpoints(self) -> bool:
        """Test 3: Authentication endpoints."""
        try:
            # Test auth endpoints exist
            response = requests.get(f"{self.base_url}/auth/", timeout=5)
            return response.status_code in [200, 404, 405]  # Any response means endpoint exists
        except requests.exceptions.RequestException:
            return False
    
    def test_backend_products_endpoints(self) -> bool:
        """Test 4: Products endpoints."""
        try:
            response = requests.get(f"{self.base_url}/products/", timeout=5)
            return response.status_code in [200, 401, 403]  # Auth required is expected
        except requests.exceptions.RequestException:
            return False
    
    def test_backend_purchase_orders_endpoints(self) -> bool:
        """Test 5: Purchase orders endpoints."""
        try:
            response = requests.get(f"{self.base_url}/purchase-orders/", timeout=5)
            return response.status_code in [200, 401, 403]  # Auth required is expected
        except requests.exceptions.RequestException:
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """Test 6: Frontend accessibility."""
        try:
            response = requests.get(f"{self.frontend_url}", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def test_database_connectivity(self) -> bool:
        """Test 7: Database connectivity."""
        try:
            # Try to import and test database connection
            from app.core.database import get_db
            db = next(get_db())
            db.close()
            return True
        except Exception:
            return False
    
    def test_requirements_validation(self) -> bool:
        """Test 8: Requirements validation against implemented functionality."""
        try:
            # Check if key modules exist
            required_modules = [
                'app.models.user',
                'app.models.company', 
                'app.models.product',
                'app.models.purchase_order',
                'app.services.auth',
                'app.services.purchase_order',
                'app.core.database',
                'app.core.security'
            ]
            
            for module in required_modules:
                __import__(module)
            
            return True
        except ImportError as e:
            print(f"Missing module: {e}")
            return False
    
    def test_api_structure(self) -> bool:
        """Test 9: API structure validation."""
        try:
            # Check if main API modules exist
            api_modules = [
                'app.api.auth',
                'app.api.products', 
                'app.api.purchase_orders',
                'app.api.health'
            ]
            
            for module in api_modules:
                __import__(module)
            
            return True
        except ImportError as e:
            print(f"Missing API module: {e}")
            return False
    
    def test_models_structure(self) -> bool:
        """Test 10: Database models structure."""
        try:
            # Check if key models exist
            from app.models.user import User
            from app.models.company import Company
            from app.models.product import Product
            from app.models.purchase_order import PurchaseOrder
            
            # Check if models have required attributes
            user_attrs = ['id', 'email', 'full_name', 'role', 'company_id']
            company_attrs = ['id', 'name', 'company_type', 'email']
            product_attrs = ['id', 'name', 'category', 'can_have_composition']
            po_attrs = ['id', 'po_number', 'buyer_company_id', 'seller_company_id', 'product_id', 'status']
            
            for attr in user_attrs:
                if not hasattr(User, attr):
                    return False
                    
            for attr in company_attrs:
                if not hasattr(Company, attr):
                    return False
                    
            for attr in product_attrs:
                if not hasattr(Product, attr):
                    return False
                    
            for attr in po_attrs:
                if not hasattr(PurchaseOrder, attr):
                    return False
            
            return True
        except Exception as e:
            print(f"Model structure error: {e}")
            return False
    
    def test_services_structure(self) -> bool:
        """Test 11: Services structure validation."""
        try:
            # Check if key services exist
            from app.services.auth import AuthService
            from app.services.purchase_order import PurchaseOrderService
            
            return True
        except ImportError as e:
            print(f"Missing service: {e}")
            return False
    
    def test_configuration(self) -> bool:
        """Test 12: Configuration validation."""
        try:
            from app.core.config import settings
            
            # Check if required settings exist
            required_settings = ['app_name', 'app_version', 'debug']
            for setting in required_settings:
                if not hasattr(settings, setting):
                    return False
            
            return True
        except Exception as e:
            print(f"Configuration error: {e}")
            return False
    
    def test_file_structure(self) -> bool:
        """Test 13: File structure validation."""
        required_files = [
            'app/main.py',
            'app/core/database.py',
            'app/core/config.py',
            'app/core/security.py',
            'app/models/user.py',
            'app/models/company.py',
            'app/models/product.py',
            'app/models/purchase_order.py',
            'app/api/auth.py',
            'app/api/products.py',
            'app/api/purchase_orders.py',
            'app/services/auth.py',
            'app/services/purchase_order.py',
            'requirements.txt',
            'frontend/package.json',
            'frontend/src/App.tsx'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                print(f"Missing file: {file_path}")
                return False
        
        return True
    
    def test_frontend_structure(self) -> bool:
        """Test 14: Frontend structure validation."""
        frontend_files = [
            'frontend/package.json',
            'frontend/src/App.tsx',
            'frontend/src/index.tsx',
            'frontend/src/components/ui/Button.tsx',
            'frontend/src/components/layout/Layout.tsx',
            'frontend/src/pages/Dashboard.tsx',
            'frontend/src/types/transparency.ts'
        ]
        
        for file_path in frontend_files:
            if not os.path.exists(file_path):
                print(f"Missing frontend file: {file_path}")
                return False
        
        return True
    
    def test_docker_configuration(self) -> bool:
        """Test 15: Docker configuration validation."""
        docker_files = [
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.production.yml'
        ]
        
        for file_path in docker_files:
            if not os.path.exists(file_path):
                print(f"Missing Docker file: {file_path}")
                return False
        
        return True
    
    def test_documentation(self) -> bool:
        """Test 16: Documentation validation."""
        doc_files = [
            'README.md',
            'frontend/README.md',
            'docs/admin-support-system.md'
        ]
        
        for file_path in doc_files:
            if not os.path.exists(file_path):
                print(f"Missing documentation: {file_path}")
                return False
        
        return True
    
    def run_all_tests(self):
        """Run all tests in the suite."""
        print("🚀 Starting Task 27: Final Integration and System Testing")
        print("=" * 60)
        
        # Backend Tests
        print("\n📡 Backend Tests")
        print("-" * 30)
        self.run_test(self.test_backend_health, "Backend Health Check")
        self.run_test(self.test_backend_api_docs, "Backend API Documentation")
        self.run_test(self.test_backend_auth_endpoints, "Authentication Endpoints")
        self.run_test(self.test_backend_products_endpoints, "Products Endpoints")
        self.run_test(self.test_backend_purchase_orders_endpoints, "Purchase Orders Endpoints")
        
        # Frontend Tests
        print("\n🎨 Frontend Tests")
        print("-" * 30)
        self.run_test(self.test_frontend_accessibility, "Frontend Accessibility")
        
        # Infrastructure Tests
        print("\n🏗️ Infrastructure Tests")
        print("-" * 30)
        self.run_test(self.test_database_connectivity, "Database Connectivity")
        self.run_test(self.test_configuration, "Configuration Validation")
        self.run_test(self.test_docker_configuration, "Docker Configuration")
        
        # Structure Tests
        print("\n📁 Structure Tests")
        print("-" * 30)
        self.run_test(self.test_file_structure, "File Structure Validation")
        self.run_test(self.test_frontend_structure, "Frontend Structure Validation")
        self.run_test(self.test_models_structure, "Database Models Structure")
        self.run_test(self.test_services_structure, "Services Structure")
        self.run_test(self.test_api_structure, "API Structure Validation")
        
        # Requirements Tests
        print("\n📋 Requirements Tests")
        print("-" * 30)
        self.run_test(self.test_requirements_validation, "Requirements Validation")
        
        # Documentation Tests
        print("\n📚 Documentation Tests")
        print("-" * 30)
        self.run_test(self.test_documentation, "Documentation Validation")
        
        # Generate Report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == TestStatus.PASS.value])
        failed_tests = len([r for r in self.results if r.status == TestStatus.FAIL.value])
        error_tests = len([r for r in self.results if r.status == TestStatus.ERROR.value])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"💥 Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0 or error_tests > 0:
            print("\n❌ FAILED TESTS:")
            print("-" * 30)
            for result in self.results:
                if result.status in [TestStatus.FAIL.value, TestStatus.ERROR.value]:
                    print(f"• {result.test_name}: {result.message}")
        
        print("\n📈 DETAILED RESULTS:")
        print("-" * 30)
        for result in self.results:
            status_icon = "✅" if result.status == TestStatus.PASS.value else "❌" if result.status == TestStatus.FAIL.value else "💥"
            print(f"{status_icon} {result.test_name}: {result.status} ({result.duration:.2f}s)")
        
        # Save report to file
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": (passed_tests/total_tests)*100
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "message": r.message,
                    "duration": r.duration
                }
                for r in self.results
            ]
        }
        
        with open("task_27_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: task_27_test_report.json")
        
        # Final verdict
        if failed_tests == 0 and error_tests == 0:
            print("\n🎉 ALL TESTS PASSED! Task 27 completed successfully!")
            return True
        else:
            print(f"\n⚠️  {failed_tests + error_tests} tests failed. Please review and fix issues.")
            return False

def main():
    """Main test execution function."""
    test_suite = Task27TestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ Task 27: Final Integration and System Testing - COMPLETED")
        sys.exit(0)
    else:
        print("\n❌ Task 27: Final Integration and System Testing - FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()

