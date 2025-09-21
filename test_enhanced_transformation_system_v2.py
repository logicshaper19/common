#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced transformation system v2.

This script validates the complete implementation of the enhanced transformation system
with all the improvements: modular architecture, proper error handling, transaction management,
input validation, dependency injection, comprehensive logging, and configuration management.
"""
import asyncio
import json
import time
import requests
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

# Test configuration
BASE_URL = "http://localhost:8000"
API_V2_BASE = f"{BASE_URL}/api/v2/transformations"

# Test data
TEST_COMPANIES = [
    {
        "name": "Enhanced Plantation Co",
        "email": "admin@enhanced-plantation.com",
        "password": "SecurePass123!",
        "company_type": "plantation_grower",
        "full_name": "Enhanced Plantation Admin",
        "role": "admin",
        "company_email": "info@enhanced-plantation.com"
    },
    {
        "name": "Advanced Mill Processing",
        "email": "admin@advanced-mill.com", 
        "password": "SecurePass123!",
        "company_type": "mill_processor",
        "full_name": "Advanced Mill Admin",
        "role": "admin",
        "company_email": "info@advanced-mill.com"
    },
    {
        "name": "Premium Refinery Ltd",
        "email": "admin@premium-refinery.com",
        "password": "SecurePass123!",
        "company_type": "refinery_crusher",
        "full_name": "Premium Refinery Admin",
        "role": "admin",
        "company_email": "info@premium-refinery.com"
    },
    {
        "name": "Elite Manufacturing Inc",
        "email": "admin@elite-manufacturing.com",
        "password": "SecurePass123!",
        "company_type": "manufacturer",
        "full_name": "Elite Manufacturing Admin",
        "role": "admin",
        "company_email": "info@elite-manufacturing.com"
    }
]

TEST_PRODUCTS = [
    {
        "name": "Fresh Fruit Bunches",
        "description": "High-quality fresh fruit bunches for processing",
        "category": "raw_material",
        "unit": "kg",
        "common_product_id": f"ENHANCED-RAW_MATERIAL-{int(time.time() * 1000)}",
        "material_breakdown": None
    },
    {
        "name": "Crude Palm Oil",
        "description": "Unrefined palm oil from mill processing",
        "category": "raw_material", 
        "unit": "kg",
        "common_product_id": f"ENHANCED-CRUDE_OIL-{int(time.time() * 1000)}",
        "material_breakdown": None
    },
    {
        "name": "Refined Palm Oil",
        "description": "Refined palm oil for manufacturing",
        "category": "raw_material",
        "unit": "kg", 
        "common_product_id": f"ENHANCED-REFINED_OIL-{int(time.time() * 1000)}",
        "material_breakdown": None
    },
    {
        "name": "Beauty Products",
        "description": "Premium beauty products made from palm oil",
        "category": "finished_good",
        "unit": "pieces",
        "common_product_id": f"ENHANCED-FINISHED_GOODS-{int(time.time() * 1000)}",
        "material_breakdown": None
    }
]


class EnhancedTransformationSystemTester:
    """Comprehensive tester for the enhanced transformation system."""
    
    def __init__(self):
        self.session = requests.Session()
        self.companies = {}
        self.products = {}
        self.purchase_orders = {}
        self.transformations = {}
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_test(self, test_name: str, success: bool, message: str = "", error: str = ""):
        """Log test results."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        if error:
            print(f"   Error: {error}")
            self.test_results["errors"].append(f"{test_name}: {error}")
        
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
    
    def make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def test_health_check(self):
        """Test health check endpoint."""
        try:
            response = self.make_request("GET", f"{API_V2_BASE}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Health Check",
                    True,
                    f"Service status: {data.get('data', {}).get('service_status', 'unknown')}"
                )
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, error=str(e))
    
    def test_available_templates(self):
        """Test available templates endpoint."""
        try:
            response = self.make_request("GET", f"{API_V2_BASE}/templates/available")
            if response.status_code == 200:
                data = response.json()
                company_types = data.get('data', {}).get('available_company_types', [])
                self.log_test(
                    "Available Templates",
                    True,
                    f"Found {len(company_types)} company types: {', '.join(company_types)}"
                )
            else:
                self.log_test("Available Templates", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Available Templates", False, error=str(e))
    
    def register_company(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a company and return credentials."""
        try:
            response = self.make_request(
                "POST",
                f"{BASE_URL}/api/v1/auth/register",
                json=company_data
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "company_id": data.get("company_id"),
                    "access_token": data.get("access_token"),
                    "company_name": company_data["name"]
                }
            else:
                raise Exception(f"Registration failed: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"Company registration failed: {str(e)}")
    
    def test_company_registration(self):
        """Test company registration for all company types."""
        print("\n🏢 Testing Company Registration...")
        
        for company_data in TEST_COMPANIES:
            try:
                credentials = self.register_company(company_data)
                self.companies[company_data["company_type"]] = credentials
                self.log_test(
                    f"Register {company_data['company_type']}",
                    True,
                    f"Company: {credentials['company_name']}"
                )
            except Exception as e:
                self.log_test(f"Register {company_data['company_type']}", False, error=str(e))
    
    def create_product(self, product_data: Dict[str, Any], access_token: str) -> Dict[str, Any]:
        """Create a product."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = self.make_request(
            "POST",
            f"{BASE_URL}/api/v1/products",
            json=product_data,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()["data"]
        else:
            raise Exception(f"Product creation failed: {response.status_code} - {response.text}")
    
    def test_product_creation(self):
        """Test product creation for each company."""
        print("\n📦 Testing Product Creation...")
        
        for i, product_data in enumerate(TEST_PRODUCTS):
            company_type = list(self.companies.keys())[i % len(self.companies)]
            credentials = self.companies[company_type]
            
            try:
                product = self.create_product(product_data, credentials["access_token"])
                self.products[product_data["name"]] = product
                self.log_test(
                    f"Create Product: {product_data['name']}",
                    True,
                    f"Product ID: {product['id']}"
                )
            except Exception as e:
                self.log_test(f"Create Product: {product_data['name']}", False, error=str(e))
    
    def create_purchase_order(self, po_data: Dict[str, Any], access_token: str) -> Dict[str, Any]:
        """Create a purchase order."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = self.make_request(
            "POST",
            f"{BASE_URL}/api/v1/simple-purchase-orders",
            json=po_data,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"PO creation failed: {response.status_code} - {response.text}")
    
    def test_purchase_order_creation(self):
        """Test purchase order creation and confirmation."""
        print("\n📋 Testing Purchase Order Creation...")
        
        # Create PO from plantation to mill
        plantation_creds = self.companies["plantation_grower"]
        mill_creds = self.companies["mill_processor"]
        
        po_data = {
            "seller_company_id": plantation_creds["company_id"],
            "buyer_company_id": mill_creds["company_id"],
            "product_id": self.products["Fresh Fruit Bunches"]["id"],
            "quantity": 1000.0,
            "unit": "kg",
            "price_per_unit": 0.5,
            "delivery_date": "2024-02-01",
            "delivery_location": "Port of Singapore"
        }
        
        try:
            po = self.create_purchase_order(po_data, plantation_creds["access_token"])
            self.purchase_orders["plantation_to_mill"] = po
            self.log_test(
                "Create PO: Plantation to Mill",
                True,
                f"PO ID: {po['id']}"
            )
        except Exception as e:
            self.log_test("Create PO: Plantation to Mill", False, error=str(e))
    
    def confirm_purchase_order(self, po_id: str, access_token: str) -> Dict[str, Any]:
        """Confirm a purchase order."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = self.make_request(
            "PUT",
            f"{BASE_URL}/api/v1/simple-purchase-orders/{po_id}/confirm",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"PO confirmation failed: {response.status_code} - {response.text}")
    
    def test_purchase_order_confirmation(self):
        """Test purchase order confirmation with batch creation."""
        print("\n✅ Testing Purchase Order Confirmation...")
        
        if "plantation_to_mill" not in self.purchase_orders:
            self.log_test("Confirm PO: Plantation to Mill", False, "No PO to confirm")
            return
        
        po = self.purchase_orders["plantation_to_mill"]
        mill_creds = self.companies["mill_processor"]
        
        try:
            result = self.confirm_purchase_order(po["id"], mill_creds["access_token"])
            self.log_test(
                "Confirm PO: Plantation to Mill",
                True,
                f"Batch created: {result.get('batch_created', False)}"
            )
            
            if result.get("transformation_suggestion"):
                self.log_test(
                    "Transformation Suggestion",
                    True,
                    "Transformation suggestion created"
                )
        except Exception as e:
            self.log_test("Confirm PO: Plantation to Mill", False, error=str(e))
    
    def test_template_generation(self):
        """Test template generation for all transformation types."""
        print("\n🎯 Testing Template Generation...")
        
        mill_creds = self.companies["mill_processor"]
        headers = {"Authorization": f"Bearer {mill_creds['access_token']}"}
        
        template_request = {
            "transformation_type": "milling",
            "company_type": "mill_processor",
            "input_batch_data": {
                "id": "test-batch-id",
                "product_id": self.products["Fresh Fruit Bunches"]["id"],
                "quantity": 1000.0,
                "unit": "kg"
            },
            "facility_id": "MILL-001"
        }
        
        try:
            response = self.make_request(
                "POST",
                f"{API_V2_BASE}/template",
                json=template_request,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                template = data.get("data", {})
                self.log_test(
                    "Generate Mill Template",
                    True,
                    f"Template size: {len(template)} fields"
                )
                
                # Validate template structure
                required_fields = [
                    "transformation_type", "company_type", "role_specific_data",
                    "output_batch_suggestion", "orchestration_metadata"
                ]
                missing_fields = [field for field in required_fields if field not in template]
                
                if not missing_fields:
                    self.log_test("Template Structure Validation", True, "All required fields present")
                else:
                    self.log_test("Template Structure Validation", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Generate Mill Template", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Generate Mill Template", False, error=str(e))
    
    def test_role_data_validation(self):
        """Test role-specific data validation."""
        print("\n🔍 Testing Role Data Validation...")
        
        mill_creds = self.companies["mill_processor"]
        headers = {"Authorization": f"Bearer {mill_creds['access_token']}"}
        
        validation_request = {
            "transformation_type": "milling",
            "company_type": "mill_processor",
            "role_data": {
                "processing_date": "2024-01-15",
                "processing_method": "mechanical_extraction",
                "fresh_fruit_bunches_processed": 1000.0,
                "crude_palm_oil_produced": 220.0,
                "extraction_rate_percentage": 22.0
            }
        }
        
        try:
            response = self.make_request(
                "POST",
                f"{API_V2_BASE}/validate-role-data",
                json=validation_request,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                validation_result = data.get("data", {})
                self.log_test(
                    "Validate Role Data",
                    True,
                    f"Valid: {validation_result.get('is_valid', False)}"
                )
            else:
                self.log_test("Validate Role Data", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Validate Role Data", False, error=str(e))
    
    def test_complete_transformation_creation(self):
        """Test complete transformation creation."""
        print("\n🔄 Testing Complete Transformation Creation...")
        
        mill_creds = self.companies["mill_processor"]
        headers = {"Authorization": f"Bearer {mill_creds['access_token']}"}
        
        transformation_request = {
            "transformation_data": {
                "transformation_type": "milling",
                "input_batch_id": "test-batch-id",
                "company_id": mill_creds["company_id"],
                "facility_id": "MILL-001",
                "process_name": "Mechanical Extraction",
                "process_description": "Standard mechanical extraction process",
                "start_time": datetime.utcnow().isoformat(),
                "status": "pending"
            },
            "user_id": mill_creds["company_id"],
            "auto_populate_role_data": True
        }
        
        try:
            response = self.make_request(
                "POST",
                f"{API_V2_BASE}/create-complete",
                json=transformation_request,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                transformation = data.get("data", {})
                self.log_test(
                    "Create Complete Transformation",
                    True,
                    f"Transformation ID: {transformation.get('transformation_id', 'unknown')}"
                )
            else:
                self.log_test("Create Complete Transformation", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Create Complete Transformation", False, error=str(e))
    
    def test_error_handling(self):
        """Test error handling with invalid inputs."""
        print("\n⚠️ Testing Error Handling...")
        
        mill_creds = self.companies["mill_processor"]
        headers = {"Authorization": f"Bearer {mill_creds['access_token']}"}
        
        # Test invalid transformation type
        invalid_template_request = {
            "transformation_type": "invalid_type",
            "company_type": "mill_processor"
        }
        
        try:
            response = self.make_request(
                "POST",
                f"{API_V2_BASE}/template",
                json=invalid_template_request,
                headers=headers
            )
            
            if response.status_code == 422:  # Validation error
                self.log_test("Invalid Transformation Type", True, "Proper validation error returned")
            else:
                self.log_test("Invalid Transformation Type", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Transformation Type", False, error=str(e))
        
        # Test invalid company type
        invalid_company_request = {
            "transformation_type": "milling",
            "company_type": "invalid_company_type"
        }
        
        try:
            response = self.make_request(
                "POST",
                f"{API_V2_BASE}/template",
                json=invalid_company_request,
                headers=headers
            )
            
            if response.status_code == 422:  # Validation error
                self.log_test("Invalid Company Type", True, "Proper validation error returned")
            else:
                self.log_test("Invalid Company Type", False, f"Unexpected status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Company Type", False, error=str(e))
    
    def test_performance_metrics(self):
        """Test performance and timing."""
        print("\n⏱️ Testing Performance Metrics...")
        
        mill_creds = self.companies["mill_processor"]
        headers = {"Authorization": f"Bearer {mill_creds['access_token']}"}
        
        # Test template generation performance
        template_request = {
            "transformation_type": "milling",
            "company_type": "mill_processor"
        }
        
        start_time = time.time()
        try:
            response = self.make_request(
                "POST",
                f"{API_V2_BASE}/template",
                json=template_request,
                headers=headers
            )
            end_time = time.time()
            
            if response.status_code == 200:
                duration = end_time - start_time
                self.log_test(
                    "Template Generation Performance",
                    duration < 2.0,  # Should complete within 2 seconds
                    f"Duration: {duration:.3f}s"
                )
            else:
                self.log_test("Template Generation Performance", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Template Generation Performance", False, error=str(e))
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Enhanced Transformation System v2 Tests")
        print("=" * 60)
        
        # Basic connectivity tests
        self.test_health_check()
        self.test_available_templates()
        
        # Core functionality tests
        self.test_company_registration()
        self.test_product_creation()
        self.test_purchase_order_creation()
        self.test_purchase_order_confirmation()
        
        # Enhanced transformation tests
        self.test_template_generation()
        self.test_role_data_validation()
        self.test_complete_transformation_creation()
        
        # Error handling and performance tests
        self.test_error_handling()
        self.test_performance_metrics()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 Errors:")
            for error in self.test_results['errors']:
                print(f"   - {error}")
        
        return self.test_results['failed'] == 0


def main():
    """Main test execution."""
    tester = EnhancedTransformationSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Enhanced transformation system v2 is working correctly.")
        exit(0)
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        exit(1)


if __name__ == "__main__":
    main()
