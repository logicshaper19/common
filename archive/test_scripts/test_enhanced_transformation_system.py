#!/usr/bin/env python3
"""
Test script for the enhanced transformation system.

This script tests the complete enhanced transformation system including:
1. Enhanced transformation suggestions with role-specific data
2. Automatic data population during transformation creation
3. Quality metrics and process parameter templates
4. Output batch creation
5. Validation rules for role-specific data
"""

import requests
import json
import time
import base64
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, Tuple
from app.core.unified_po_config import get_config, get_product_category

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

class EnhancedTransformationTester:
    """Test the enhanced transformation system."""
    
    def __init__(self):
        self.companies = {}
        self.tokens = {}
        self.products = {}
        self.purchase_orders = {}
        self.batches = {}
        self.transformations = {}
        self.config = get_config()
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def get_company_id_from_token(self, token: str) -> Optional[str]:
        """Extract company ID from JWT token."""
        try:
            # Decode JWT token to get company_id
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (base64url)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            return data.get('company_id')
        except Exception as e:
            self.log(f"Error decoding token: {str(e)}", "ERROR")
            return None

    def register_company(self, company_type: str, company_name: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Register a new company."""
        timestamp = int(time.time() * 1000)
        email = f"admin{timestamp}@{company_type.replace('_', '-')}.com"
        
        data = {
            "company_name": company_name,
            "company_type": company_type,
            "email": email,
            "password": "SecurePass123!",
            "first_name": "Admin",
            "last_name": "User",
            "full_name": "Admin User",
            "role": "admin",
            "company_email": email
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=data, headers=HEADERS)
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            company_id = self.get_company_id_from_token(token)
            
            if company_id:
                company_info = {
                    "id": company_id,
                    "name": company_name,
                    "type": company_type,
                    "email": email
                }
                self.companies[company_name] = company_info
                self.tokens[company_name] = token
                self.log(f"✅ Registered {company_name} ({company_type})")
                return company_info, token
            else:
                self.log(f"❌ Failed to extract company ID from token", "ERROR")
                return None, None
        else:
            self.log(f"❌ Failed to register {company_name}: {response.status_code} - {response.text}", "ERROR")
            return None, None

    def create_product(self, company_id: str, token: str, product_name: str, category: str) -> Optional[Dict]:
        """Create a product for a company."""
        product_category = get_product_category(category)
        
        data = {
            "name": product_name,
            "description": f"High-quality {product_name.lower()}",
            "category": product_category,
            "default_unit": self.config.DEFAULT_UNIT,
            "common_product_id": f"COMMON-{category.upper()}-{int(time.time() * 1000)}",
            "can_have_composition": False,
            "material_breakdown": None
        }
        
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/v1/products/", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            # Handle different response structures
            if "data" in result:
                product_data = result["data"]
            elif "product" in result:
                product_data = result["product"]
            else:
                product_data = result
            
            # Check if the required fields exist
            if "id" not in product_data:
                self.log(f"❌ Product response missing 'id' field: {product_data}", "ERROR")
                return None
            
            product_info = {
                "id": product_data["id"],
                "name": product_data["name"],
                "category": product_data["category"]
            }
            self.products[product_name] = product_info
            self.log(f"✅ Created product: {product_name}")
            return product_info
        else:
            self.log(f"❌ Failed to create product {product_name}: {response.status_code} - {response.text}", "ERROR")
            return None

    def create_purchase_order(self, buyer_id: str, seller_id: str, product_id: str, token: str, 
                            quantity: float, unit_price: float, parent_po_id: Optional[str] = None) -> Optional[Dict]:
        """Create a purchase order."""
        delivery_date = (date.today() + timedelta(days=self.config.DEFAULT_DELIVERY_DAYS)).isoformat()
        
        data = {
            "buyer_company_id": buyer_id,
            "seller_company_id": seller_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "unit": self.config.DEFAULT_UNIT,
            "delivery_date": delivery_date,
            "delivery_location": self.config.DEFAULT_DELIVERY_LOCATION,
            "parent_po_id": parent_po_id
        }
        
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/v1/simple/purchase-orders/", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            po_info = {
                "id": result["id"],
                "po_number": result["po_number"],
                "buyer_id": buyer_id,
                "seller_id": seller_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price
            }
            self.purchase_orders[result["po_number"]] = po_info
            self.log(f"✅ Created PO: {result['po_number']}")
            return po_info
        else:
            self.log(f"❌ Failed to create PO: {response.status_code} - {response.text}", "ERROR")
            return None

    def confirm_purchase_order(self, po_id: str, token: str) -> Optional[Dict]:
        """Confirm a purchase order and get transformation suggestion."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.put(f"{BASE_URL}/api/v1/simple/purchase-orders/{po_id}/confirm", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Purchase order {po_id} confirmed successfully")
            
            if result.get("batch_created"):
                self.log(f"🎯 Batch created: {result.get('batch_name')} (ID: {result.get('batch_id')})")
                
                if result.get("transformation_required"):
                    suggestion = result.get("transformation_suggestion", {})
                    self.log(f"🔄 Transformation suggestion created for {suggestion.get('transformation_type', 'unknown')}")
                    
                    # Log role-specific data
                    role_data = suggestion.get("role_specific_data", {})
                    if role_data:
                        self.log(f"📊 Role-specific data pre-filled: {len(role_data)} fields")
                    
                    # Log output batch suggestion
                    output_batch = suggestion.get("output_batch_suggestion", {})
                    if output_batch:
                        self.log(f"📦 Output batch suggested: {output_batch.get('batch_id')} ({output_batch.get('quantity')} {output_batch.get('unit')})")
            
            return result
        else:
            self.log(f"❌ Failed to confirm PO {po_id}: {response.status_code} - {response.text}", "ERROR")
            return None

    def create_transformation_from_suggestion(self, suggestion: Dict[str, Any], token: str) -> Optional[Dict]:
        """Create a transformation from a suggestion using the enhanced API."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/api/v1/transformations-enhanced/create-from-suggestion",
            json=suggestion,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Transformation created from suggestion: {result.get('data', {}).get('transformation_event_id')}")
            return result
        else:
            self.log(f"❌ Failed to create transformation from suggestion: {response.status_code} - {response.text}", "ERROR")
            return None

    def get_transformation_templates(self, company_type: str, token: str) -> Optional[Dict]:
        """Get transformation templates for a company type."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/v1/transformations-enhanced/templates/{company_type}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Retrieved transformation templates for {company_type}")
            return result
        else:
            self.log(f"❌ Failed to get templates for {company_type}: {response.status_code} - {response.text}", "ERROR")
            return None

    def validate_role_data(self, transformation_type: str, role_data: Dict[str, Any], token: str) -> Optional[Dict]:
        """Validate role-specific data."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/api/v1/transformations-enhanced/validate-role-data",
            params={
                "transformation_type": transformation_type
            },
            json=role_data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            is_valid = result.get("is_valid", False)
            errors = result.get("validation_errors", [])
            
            if is_valid:
                self.log(f"✅ Role data validation passed for {transformation_type}")
            else:
                self.log(f"❌ Role data validation failed for {transformation_type}: {errors}", "WARNING")
            
            return result
        else:
            self.log(f"❌ Failed to validate role data: {response.status_code} - {response.text}", "ERROR")
            return None

    def run_enhanced_transformation_test(self):
        """Run the complete enhanced transformation system test."""
        self.log("🚀 Starting Enhanced Transformation System Test")
        self.log("=" * 60)
        
        # Step 1: Create supply chain companies
        self.log("📋 Step 1: Creating Supply Chain Companies")
        self.log("-" * 40)
        
        # Create companies
        plantation, plantation_token = self.register_company("plantation_grower", "Green Acres Plantation")
        mill, mill_token = self.register_company("mill_processor", "Malaysia Mill Co")
        refinery, refinery_token = self.register_company("refinery_crusher", "Singapore Refinery Ltd")
        manufacturer, manufacturer_token = self.register_company("manufacturer", "L'Oréal Beauty")
        
        if not all([plantation, mill, refinery, manufacturer]):
            self.log("❌ Failed to create all companies", "ERROR")
            return False
        
        # Step 2: Create products
        self.log("\n📋 Step 2: Creating Products")
        self.log("-" * 40)
        
        plantation_product = self.create_product(plantation["id"], plantation_token, "Fresh Fruit Bunches", "raw_material")
        mill_product = self.create_product(mill["id"], mill_token, "Crude Palm Oil", "raw_material")
        refinery_product = self.create_product(refinery["id"], refinery_token, "Refined Palm Oil", "raw_material")
        manufacturer_product = self.create_product(manufacturer["id"], manufacturer_token, "Beauty Cream", "finished_good")
        
        if not all([plantation_product, mill_product, refinery_product, manufacturer_product]):
            self.log("❌ Failed to create all products", "ERROR")
            return False
        
        # Step 3: Create purchase order chain
        self.log("\n📋 Step 3: Creating Purchase Order Chain")
        self.log("-" * 40)
        
        # Create PO chain: Manufacturer → Refinery → Mill → Plantation
        po1 = self.create_purchase_order(
            manufacturer["id"], refinery["id"], refinery_product["id"], 
            manufacturer_token, 1000, 850.0
        )
        po2 = self.create_purchase_order(
            refinery["id"], mill["id"], mill_product["id"], 
            refinery_token, 1000, 750.0, po1["id"]
        )
        po3 = self.create_purchase_order(
            mill["id"], plantation["id"], plantation_product["id"], 
            mill_token, 1000, 650.0, po2["id"]
        )
        
        if not all([po1, po2, po3]):
            self.log("❌ Failed to create all purchase orders", "ERROR")
            return False
        
        # Step 4: Test enhanced transformation suggestions
        self.log("\n📋 Step 4: Testing Enhanced Transformation Suggestions")
        self.log("-" * 40)
        
        # Confirm POs to trigger transformation suggestions
        plantation_confirmation = self.confirm_purchase_order(po3["id"], plantation_token)
        mill_confirmation = self.confirm_purchase_order(po2["id"], mill_token)
        refinery_confirmation = self.confirm_purchase_order(po1["id"], refinery_token)
        
        # Step 5: Test transformation templates
        self.log("\n📋 Step 5: Testing Transformation Templates")
        self.log("-" * 40)
        
        # Get templates for each company type
        plantation_templates = self.get_transformation_templates("plantation_grower", plantation_token)
        mill_templates = self.get_transformation_templates("mill_processor", mill_token)
        refinery_templates = self.get_transformation_templates("refinery_crusher", refinery_token)
        manufacturer_templates = self.get_transformation_templates("manufacturer", manufacturer_token)
        
        # Step 6: Test role-specific data validation
        self.log("\n📋 Step 6: Testing Role-Specific Data Validation")
        self.log("-" * 40)
        
        # Test plantation data validation
        plantation_data = {
            "farm_id": "FARM-001",
            "harvest_date": "2024-01-15",
            "yield_per_hectare": 20.5,
            "total_hectares": 100.0,
            "ffb_quality_grade": "A",
            "moisture_content": 25.0,
            "free_fatty_acid": 3.5
        }
        plantation_validation = self.validate_role_data("HARVEST", plantation_data, plantation_token)
        
        # Test mill data validation
        mill_data = {
            "extraction_rate": 22.5,
            "ffb_quantity": 1000.0,
            "cpo_quantity": 225.0,
            "cpo_ffa_content": 3.5,
            "cpo_moisture_content": 0.1
        }
        mill_validation = self.validate_role_data("MILLING", mill_data, mill_token)
        
        # Test refinery data validation
        refinery_data = {
            "process_type": "refining",
            "input_oil_quantity": 1000.0,
            "iv_value": 52.0,
            "melting_point": 24.0,
            "refining_loss": 2.0
        }
        refinery_validation = self.validate_role_data("REFINING", refinery_data, refinery_token)
        
        # Test manufacturer data validation
        manufacturer_data = {
            "product_type": "soap",
            "recipe_ratios": {"palm_oil": 0.6, "coconut_oil": 0.3, "other": 0.1},
            "output_quantity": 950.0,
            "production_lot_number": "LOT-20240115-001"
        }
        manufacturer_validation = self.validate_role_data("MANUFACTURING", manufacturer_data, manufacturer_token)
        
        # Step 7: Test complete transformation creation
        self.log("\n📋 Step 7: Testing Complete Transformation Creation")
        self.log("-" * 40)
        
        # Create a complete transformation for plantation
        plantation_transformation_data = {
            "event_id": f"HARVEST-{int(time.time())}",
            "transformation_type": "HARVEST",
            "company_id": plantation["id"],
            "facility_id": "PLANTATION-001",
            "input_batches": [],
            "output_batches": [{
                "batch_id": f"FFB-{int(time.time())}",
                "quantity": 1000.0,
                "unit": "kg"
            }],
            "start_time": datetime.utcnow().isoformat(),
            "role_specific_data": plantation_data
        }
        
        plantation_transformation = self.create_transformation_from_suggestion(
            plantation_transformation_data, plantation_token
        )
        
        # Step 8: Test summary
        self.log("\n📊 Step 8: Test Summary")
        self.log("-" * 40)
        
        success_count = 0
        total_tests = 0
        
        # Count successful operations
        tests = [
            ("Company Registration", len(self.companies) == 4),
            ("Product Creation", len(self.products) == 4),
            ("Purchase Order Creation", len(self.purchase_orders) == 3),
            ("PO Confirmations", all([plantation_confirmation, mill_confirmation, refinery_confirmation])),
            ("Transformation Templates", all([plantation_templates, mill_templates, refinery_templates, manufacturer_templates])),
            ("Role Data Validation", all([
                plantation_validation and plantation_validation.get("is_valid"),
                mill_validation and mill_validation.get("is_valid"),
                refinery_validation and refinery_validation.get("is_valid"),
                manufacturer_validation and manufacturer_validation.get("is_valid")
            ])),
            ("Complete Transformation Creation", plantation_transformation is not None)
        ]
        
        for test_name, success in tests:
            total_tests += 1
            if success:
                success_count += 1
                self.log(f"✅ {test_name}")
            else:
                self.log(f"❌ {test_name}")
        
        success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
        
        self.log(f"\n🎉 Enhanced Transformation System Test Results:")
        self.log(f"✅ Successful tests: {success_count}/{total_tests}")
        self.log(f"📊 Success rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            self.log("🎉 Enhanced Transformation System test completed successfully!")
            return True
        else:
            self.log("❌ Enhanced Transformation System test failed!", "ERROR")
            return False


def main():
    """Main test function."""
    tester = EnhancedTransformationTester()
    success = tester.run_enhanced_transformation_test()
    
    if success:
        print("\n✅ All enhanced transformation system tests passed!")
        exit(0)
    else:
        print("\n❌ Some enhanced transformation system tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
