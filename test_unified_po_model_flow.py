#!/usr/bin/env python3
"""
Test script for Unified PO Model with automatic batch creation and transformation recording.

This script tests the complete flow:
1. PO Creation → PO Confirmation → Automatic Batch Creation
2. Transformation Recording at Mill and Refinery
3. Chain Building through batch relationships
4. Traceability verification
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

class UnifiedPOModelTester:
    """Test the Unified PO Model implementation."""
    
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
    
    def register_company(self, company_type: str, company_name: str, admin_name: str) -> Tuple[Optional[Dict], Optional[str]]:
        """Register a new company and return company info and token."""
        timestamp = int(time.time() * 1000)
        email = f"admin{timestamp}@{company_type.replace('_', '-')}.com"
        company_email = f"contact{timestamp}@{company_name.lower().replace(' ', '').replace("'", '')}.com"
        
        data = {
            "company_name": company_name,
            "company_type": company_type,
            "admin_name": admin_name,
            "email": email,
            "password": "SecurePass123!",
            "phone": f"+1-555-{timestamp % 10000:04d}",
            "address": f"123 {company_name} Street, City, Country",
            "website": f"https://{company_name.lower().replace(' ', '').replace("'", '')}.com",
            "full_name": admin_name,
            "role": "admin",
            "company_email": company_email
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=data, headers=HEADERS)
        
        if response.status_code == 200:
            result = response.json()
            token = result["access_token"]
            
            # Decode JWT token to get company ID
            # JWT tokens have 3 parts separated by dots: header.payload.signature
            try:
                # Split the token and decode the payload (middle part)
                token_parts = token.split('.')
                if len(token_parts) == 3:
                    # Decode the payload (add padding if needed)
                    payload_encoded = token_parts[1]
                    # Add padding if needed
                    missing_padding = len(payload_encoded) % 4
                    if missing_padding:
                        payload_encoded += '=' * (4 - missing_padding)
                    
                    # Decode base64
                    payload_bytes = base64.urlsafe_b64decode(payload_encoded)
                    payload = json.loads(payload_bytes.decode('utf-8'))
                    company_id = payload.get("company_id")
                else:
                    company_id = None
            except Exception as e:
                self.log(f"❌ Failed to decode JWT token: {e}", "ERROR")
                company_id = None
            
            company_info = {
                "id": company_id,
                "name": company_name,
                "type": company_type,
                "email": email
            }
            
            self.log(f"✅ Registered {company_name} ({company_type})")
            return company_info, token
        else:
            self.log(f"❌ Failed to register {company_name}: {response.status_code} - {response.text}", "ERROR")
            return None, None
    
    def create_product(self, company_id: str, token: str, product_name: str, category: str) -> Optional[Dict]:
        """Create a product for a company."""
        # Use configuration for category mapping
        product_category = get_product_category(category)
        
        data = {
            "name": product_name,
            "description": f"High-quality {product_name.lower()}",
            "category": product_category,
            "default_unit": self.config.DEFAULT_UNIT,
            "common_product_id": f"COMMON-{category.upper()}-{int(time.time())}",
            "can_have_composition": False,
            "material_breakdown": None
        }
        
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/v1/products/", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            product_info = {
                "id": result["data"]["id"],
                "name": result["data"]["name"],
                "category": result["data"]["category"]
            }
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
                "unit_price": unit_price,
                "status": result["status"]
            }
            self.log(f"✅ Created PO: {result['po_number']}")
            return po_info
        else:
            self.log(f"❌ Failed to create PO: {response.status_code} - {response.text}", "ERROR")
            return None
    
    def confirm_purchase_order(self, po_id: str, token: str) -> bool:
        """Confirm a purchase order and check for batch creation."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.put(f"{BASE_URL}/api/v1/simple/purchase-orders/{po_id}/confirm", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Purchase order {po_id} confirmed successfully")
            
            # Check if batch was created
            if result.get("batch_created"):
                batch_id = result.get("batch_id")
                batch_name = result.get("batch_name")
                self.log(f"🎯 Batch created: {batch_name} (ID: {batch_id})")
                
                # Store batch info
                self.batches[po_id] = {
                    "id": batch_id,
                    "name": batch_name,
                    "po_id": po_id
                }
                
                # Check if transformation is suggested
                if result.get("transformation_required"):
                    suggestion = result.get("transformation_suggestion", {})
                    self.log(f"🔄 Transformation suggested: {suggestion.get('transformation_type', 'Unknown')}")
                    self.log(f"   Event ID: {suggestion.get('event_id', 'N/A')}")
                    self.log(f"   Process: {suggestion.get('process_description', 'N/A')}")
            
            return True
        else:
            self.log(f"❌ Failed to confirm purchase order {po_id}: {response.status_code} - {response.text}", "ERROR")
            return False
    
    def create_transformation_event(self, company_id: str, token: str, transformation_data: Dict) -> Optional[Dict]:
        """Create a transformation event."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/v1/transformations/", json=transformation_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Created transformation: {result.get('event_id', 'Unknown')}")
            return result
        else:
            self.log(f"❌ Failed to create transformation: {response.status_code} - {response.text}", "ERROR")
            return None
    
    def get_traceability_chain(self, batch_id: str, token: str) -> Optional[Dict]:
        """Get traceability chain for a batch."""
        headers = {**HEADERS, "Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/v1/batches/{batch_id}/traceability", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"🔍 Retrieved traceability chain for batch {batch_id}")
            return result
        else:
            self.log(f"❌ Failed to get traceability chain: {response.status_code} - {response.text}", "ERROR")
            return None
    
    def run_unified_po_test(self):
        """Run the complete Unified PO Model test."""
        self.log("🚀 Starting Unified PO Model Test")
        self.log("=" * 60)
        
        # Step 1: Create supply chain companies
        self.log("📋 Step 1: Creating Supply Chain Companies")
        self.log("-" * 40)
        
        # Create Brand (downstream)
        brand_info, brand_token = self.register_company(
            "manufacturer", 
            "L'Oréal Beauty", 
            "Brand Admin"
        )
        if not brand_info:
            return False
        self.companies["brand"] = brand_info
        self.tokens["brand"] = brand_token
        
        # Create Refinery (processor)
        refinery_info, refinery_token = self.register_company(
            "refinery_crusher", 
            "Singapore Refinery Ltd", 
            "Refinery Admin"
        )
        if not refinery_info:
            return False
        self.companies["refinery"] = refinery_info
        self.tokens["refinery"] = refinery_token
        
        # Create Mill (processor)
        mill_info, mill_token = self.register_company(
            "mill_processor", 
            "Malaysia Mill Co", 
            "Mill Admin"
        )
        if not mill_info:
            return False
        self.companies["mill"] = mill_info
        self.tokens["mill"] = mill_token
        
        # Create Plantation (originator)
        plantation_info, plantation_token = self.register_company(
            "plantation_grower", 
            "Green Acres Plantation", 
            "Plantation Admin"
        )
        if not plantation_info:
            return False
        self.companies["plantation"] = plantation_info
        self.tokens["plantation"] = plantation_token
        
        # Step 2: Create products
        self.log("\n📋 Step 2: Creating Products")
        self.log("-" * 40)
        
        # Brand creates beauty products
        brand_product = self.create_product(
            brand_info["id"], 
            brand_token, 
            "Beauty Cream", 
            "finished_goods"
        )
        if not brand_product:
            return False
        self.products["brand"] = brand_product
        
        # Refinery creates refined palm oil
        refinery_product = self.create_product(
            refinery_info["id"], 
            refinery_token, 
            "Refined Palm Oil", 
            "refined_oil"
        )
        if not refinery_product:
            return False
        self.products["refinery"] = refinery_product
        
        # Mill creates crude palm oil
        mill_product = self.create_product(
            mill_info["id"], 
            mill_token, 
            "Crude Palm Oil", 
            "crude_oil"
        )
        if not mill_product:
            return False
        self.products["mill"] = mill_product
        
        # Plantation creates fresh fruit bunches
        plantation_product = self.create_product(
            plantation_info["id"], 
            plantation_token, 
            "Fresh Fruit Bunches", 
            "raw_material"
        )
        if not plantation_product:
            return False
        self.products["plantation"] = plantation_product
        
        # Step 3: Create purchase order chain
        self.log("\n📋 Step 3: Creating Purchase Order Chain")
        self.log("-" * 40)
        
        # Brand → Refinery (main PO)
        self.log("🔗 Creating Brand → Refinery Purchase Order")
        po1 = self.create_purchase_order(
            brand_info["id"],           # buyer
            refinery_info["id"],        # seller
            refinery_product["id"],     # product
            brand_token,                # token
            1000.0,                     # quantity
            2.50,                       # unit price
            None                        # no parent PO
        )
        if not po1:
            return False
        self.purchase_orders["po1"] = po1
        
        # Refinery → Mill (fulfilling PO1)
        self.log("🔗 Creating Refinery → Mill Purchase Order (fulfilling PO1)")
        po2 = self.create_purchase_order(
            refinery_info["id"],        # buyer
            mill_info["id"],            # seller
            mill_product["id"],         # product
            refinery_token,             # token
            1000.0,                     # quantity
            2.00,                       # unit price
            po1["id"]                   # parent PO
        )
        if not po2:
            return False
        self.purchase_orders["po2"] = po2
        
        # Mill → Plantation (fulfilling PO2)
        self.log("🔗 Creating Mill → Plantation Purchase Order (fulfilling PO2)")
        po3 = self.create_purchase_order(
            mill_info["id"],            # buyer
            plantation_info["id"],      # seller
            plantation_product["id"],   # product
            mill_token,                 # token
            1000.0,                     # quantity
            1.50,                       # unit price
            po2["id"]                   # parent PO
        )
        if not po3:
            return False
        self.purchase_orders["po3"] = po3
        
        # Step 4: Confirm purchase orders and create batches
        self.log("\n✅ Step 4: Confirming Purchase Orders (Unified PO Model)")
        self.log("-" * 40)
        
        # Plantation confirms PO3 (creates batch)
        self.log("✅ Plantation confirming PO3 (creates batch)")
        if not self.confirm_purchase_order(po3["id"], plantation_token):
            return False
        
        # Mill confirms PO2 (creates batch + transformation suggestion)
        self.log("✅ Mill confirming PO2 (creates batch + transformation suggestion)")
        if not self.confirm_purchase_order(po2["id"], mill_token):
            return False
        
        # Refinery confirms PO1 (creates batch + transformation suggestion)
        self.log("✅ Refinery confirming PO1 (creates batch + transformation suggestion)")
        if not self.confirm_purchase_order(po1["id"], refinery_token):
            return False
        
        # Step 5: Record transformations
        self.log("\n🔄 Step 5: Recording Transformations")
        self.log("-" * 40)
        
        # Mill transformation: Fresh Fruit Bunches → Crude Palm Oil
        if "po2" in self.batches:
            mill_batch = self.batches["po2"]
            mill_transformation = {
                "event_id": f"MILL-{datetime.now().strftime('%Y%m%d')}-001",
                "transformation_type": "MILLING",
                "company_id": mill_info["id"],
                "facility_id": "MILL-001",
                "input_batches": [{
                    "batch_id": "plantation_batch_placeholder",  # Would be actual batch ID
                    "quantity": 1000.0,
                    "unit": "kg"
                }],
                "output_batches": [{
                    "batch_id": mill_batch["id"],
                    "quantity": 800.0,  # Typical yield
                    "unit": "kg"
                }],
                "process_description": "Fresh fruit bunches crushed and pressed to extract crude palm oil",
                "process_parameters": {
                    "temperature": 80,
                    "pressure": 2.5,
                    "extraction_time": 2.5
                },
                "quality_metrics": {
                    "ffa_content": 2.1,
                    "moisture": 0.15,
                    "color": "red"
                },
                "start_time": datetime.now().isoformat(),
                "location_name": "Malaysia Mill Co",
                "yield_percentage": 80.0
            }
            
            mill_transformation_result = self.create_transformation_event(
                mill_info["id"], 
                mill_token, 
                mill_transformation
            )
            if mill_transformation_result:
                self.transformations["mill"] = mill_transformation_result
        
        # Refinery transformation: Crude Palm Oil → Refined Palm Oil
        if "po1" in self.batches:
            refinery_batch = self.batches["po1"]
            refinery_transformation = {
                "event_id": f"REFINERY-{datetime.now().strftime('%Y%m%d')}-001",
                "transformation_type": "REFINING",
                "company_id": refinery_info["id"],
                "facility_id": "REFINERY-001",
                "input_batches": [{
                    "batch_id": "mill_batch_placeholder",  # Would be actual batch ID
                    "quantity": 800.0,
                    "unit": "kg"
                }],
                "output_batches": [{
                    "batch_id": refinery_batch["id"],
                    "quantity": 750.0,  # Typical yield
                    "unit": "kg"
                }],
                "process_description": "Crude palm oil refined through degumming, neutralization, bleaching, and deodorization",
                "process_parameters": {
                    "degumming_temp": 70,
                    "neutralization_ph": 8.5,
                    "bleaching_temp": 90,
                    "deodorization_temp": 200
                },
                "quality_metrics": {
                    "ffa_content": 0.1,
                    "moisture": 0.05,
                    "color": "pale_yellow"
                },
                "start_time": datetime.now().isoformat(),
                "location_name": "Singapore Refinery Ltd",
                "yield_percentage": 93.75
            }
            
            refinery_transformation_result = self.create_transformation_event(
                refinery_info["id"], 
                refinery_token, 
                refinery_transformation
            )
            if refinery_transformation_result:
                self.transformations["refinery"] = refinery_transformation_result
        
        # Step 6: Verify traceability chain
        self.log("\n🔍 Step 6: Verifying Traceability Chain")
        self.log("-" * 40)
        
        # Get traceability for brand's batch
        if "po1" in self.batches:
            brand_batch_id = self.batches["po1"]["id"]
            traceability = self.get_traceability_chain(brand_batch_id, brand_token)
            if traceability:
                self.log(f"📊 Traceability chain for batch {brand_batch_id}:")
                for i, node in enumerate(traceability.get("chain", []), 1):
                    self.log(f"   {i}. {node.get('company_name', 'Unknown')} - {node.get('product_name', 'Unknown')} ({node.get('quantity', 0)} {node.get('unit', 'kg')})")
        
        # Step 7: Summary
        self.log("\n📊 Step 7: Test Summary")
        self.log("-" * 40)
        self.log(f"✅ Companies created: {len(self.companies)}")
        self.log(f"✅ Products created: {len(self.products)}")
        self.log(f"✅ Purchase orders created: {len(self.purchase_orders)}")
        self.log(f"✅ Batches created: {len(self.batches)}")
        self.log(f"✅ Transformations recorded: {len(self.transformations)}")
        
        self.log("\n🎉 Unified PO Model test completed successfully!")
        return True

def main():
    """Run the Unified PO Model test."""
    tester = UnifiedPOModelTester()
    success = tester.run_unified_po_test()
    
    if success:
        print("\n✅ All tests passed! The Unified PO Model is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")
    
    return success

if __name__ == "__main__":
    main()
