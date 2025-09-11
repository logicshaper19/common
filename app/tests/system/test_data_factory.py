"""
Test data factory for system tests
"""
import json
import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta


class SystemTestDataFactory:
    """Factory for creating consistent test data across system tests."""
    
    def __init__(self):
        self.created_data = []
    
    def create_test_user(self, role: str = "buyer") -> Dict[str, Any]:
        """Create test user data."""
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "email": f"test-{role}-{user_id[:8]}@example.com",
            "password": "TestPassword123!",
            "full_name": f"Test {role.title()} User",
            "role": role,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        self.created_data.append(("user", user_id))
        return user_data
    
    def create_test_company(self, company_type: str = "brand") -> Dict[str, Any]:
        """Create test company data."""
        company_id = str(uuid.uuid4())
        company_data = {
            "id": company_id,
            "name": f"Test {company_type.title()} Company",
            "company_type": company_type,
            "email": f"contact-{company_id[:8]}@testcompany.com",
            "description": f"Test company for {company_type} testing",
            "created_at": datetime.now().isoformat()
        }
        
        self.created_data.append(("company", company_id))
        return company_data
    
    def create_test_product(self, category: str = "raw_material") -> Dict[str, Any]:
        """Create test product data."""
        product_id = str(uuid.uuid4())
        product_data = {
            "id": product_id,
            "common_product_id": f"TEST-{category.upper()}-{product_id[:8]}",
            "name": f"Test {category.replace('_', ' ').title()} Product",
            "description": f"Test product for {category} testing",
            "category": category,
            "can_have_composition": category != "raw_material",
            "default_unit": "KGM",
            "hs_code": "1234.56.78",
            "created_at": datetime.now().isoformat()
        }
        
        self.created_data.append(("product", product_id))
        return product_data
    
    def create_test_purchase_order(self, buyer_company_id: str, seller_company_id: str, product_id: str) -> Dict[str, Any]:
        """Create test purchase order data."""
        po_id = str(uuid.uuid4())
        po_data = {
            "id": po_id,
            "po_number": f"PO-TEST-{po_id[:8]}",
            "buyer_company_id": buyer_company_id,
            "seller_company_id": seller_company_id,
            "product_id": product_id,
            "quantity": 1000.0,
            "unit": "KGM",
            "status": "pending",
            "delivery_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        self.created_data.append(("purchase_order", po_id))
        return po_data
    
    def create_complete_supply_chain(self) -> Dict[str, Any]:
        """Create a complete supply chain scenario for testing."""
        # Create companies
        plantation = self.create_test_company("originator")
        processor = self.create_test_company("processor")
        brand = self.create_test_company("brand")
        
        # Create users
        plantation_user = self.create_test_user("seller")
        processor_user = self.create_test_user("buyer")
        brand_user = self.create_test_user("buyer")
        
        # Create products
        ffb_product = self.create_test_product("raw_material")
        cpo_product = self.create_test_product("processed")
        refined_product = self.create_test_product("finished_good")
        
        # Create purchase orders
        ffb_po = self.create_test_purchase_order(
            processor["id"], plantation["id"], ffb_product["id"]
        )
        cpo_po = self.create_test_purchase_order(
            brand["id"], processor["id"], cpo_product["id"]
        )
        
        return {
            "companies": {
                "plantation": plantation,
                "processor": processor,
                "brand": brand
            },
            "users": {
                "plantation_user": plantation_user,
                "processor_user": processor_user,
                "brand_user": brand_user
            },
            "products": {
                "ffb": ffb_product,
                "cpo": cpo_product,
                "refined": refined_product
            },
            "purchase_orders": {
                "ffb_po": ffb_po,
                "cpo_po": cpo_po
            }
        }
    
    def get_security_test_payloads(self) -> Dict[str, List[str]]:
        """Get security test payloads for various attack vectors."""
        return {
            "xss_payloads": [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "';alert('XSS');//"
            ],
            "sql_injection_payloads": [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "admin'--"
            ],
            "path_traversal_payloads": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
            ],
            "command_injection_payloads": [
                "; ls -la",
                "| whoami",
                "&& cat /etc/passwd",
                "`id`"
            ]
        }
    
    def cleanup_test_data(self):
        """Clean up created test data."""
        # In a real implementation, this would make API calls to delete created resources
        self.created_data.clear()
    
    def save_test_scenario(self, scenario_name: str, data: Dict[str, Any]):
        """Save test scenario for reuse."""
        with open(f"test_scenarios/{scenario_name}.json", "w") as f:
            json.dump(data, f, indent=2)
    
    def load_test_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Load saved test scenario."""
        try:
            with open(f"test_scenarios/{scenario_name}.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}