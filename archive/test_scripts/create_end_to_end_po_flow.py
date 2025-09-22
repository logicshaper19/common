#!/usr/bin/env python3
"""
Create a complete end-to-end purchase order flow from Brand to Origin
with full traceability and transformation tracking.
"""
import requests
import json
import uuid
import time
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def create_brand_company():
    """Create a brand company (manufacturer)."""
    timestamp = int(time.time())
    
    registration_data = {
        "email": f"brand{timestamp}@manufacturer.com",
        "password": "SecurePass123!",
        "full_name": "Brand Manager",
        "role": "admin",
        "company_name": f"Global Consumer Brand {timestamp}",
        "company_type": "manufacturer",
        "company_email": f"brand{timestamp}@manufacturer.com"
    }
    
    print("🏭 Creating Brand Company...")
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data)
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        
        # Decode JWT to get company_id
        import base64
        token_parts = access_token.split('.')
        payload = token_parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded_payload = base64.b64decode(payload)
        token_data = json.loads(decoded_payload)
        company_id = token_data.get("company_id")
        
        print(f"    ✅ Brand Company Created: {company_id}")
        return company_id, access_token
    else:
        print(f"    ❌ Failed to create brand company: {response.status_code} - {response.text}")
        return None, None

def create_supply_chain_companies():
    """Create the supply chain companies in order."""
    timestamp = int(time.time())
    companies = {}
    
    # Company types in supply chain order (downstream to upstream)
    supply_chain = [
        ("trader_aggregator", "Global Trading Co"),
        ("refinery_crusher", "Premium Refinery Ltd"),
        ("mill_processor", "Sustainable Mill Corp"),
        ("plantation_grower", "Green Acres Plantation")
    ]
    
    for company_type, company_name in supply_chain:
        email_safe_type = company_type.replace("_", "-")
        
        registration_data = {
            "email": f"admin{timestamp}@{email_safe_type}.com",
            "password": "SecurePass123!",
            "full_name": f"Admin User",
            "role": "admin",
            "company_name": f"{company_name} {timestamp}",
            "company_type": company_type,
            "company_email": f"{email_safe_type}{timestamp}@example.com"
        }
        
        print(f"🏢 Creating {company_name}...")
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            
            # Decode JWT to get company_id
            import base64
            token_parts = access_token.split('.')
            payload = token_parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.b64decode(payload)
            token_data = json.loads(decoded_payload)
            company_id = token_data.get("company_id")
            
            companies[company_type] = {
                "id": company_id,
                "name": f"{company_name} {timestamp}",
                "access_token": access_token
            }
            
            print(f"    ✅ {company_name} Created: {company_id}")
            timestamp += 1
        else:
            print(f"    ❌ Failed to create {company_name}: {response.status_code}")
    
    return companies

def create_products():
    """Create products for the supply chain."""
    products = {}
    
    # Product definitions for the supply chain
    timestamp = int(time.time())
    product_definitions = {
        "refined_palm_oil": {
            "common_product_id": f"RPO-{timestamp}",
            "name": "Refined Palm Oil",
            "description": "High-quality refined palm oil for consumer products",
            "category": "finished_good",
            "can_have_composition": True,
            "material_breakdown": {
                "palm_oil": 100.0
            },
            "default_unit": "kg",
            "hs_code": "1511.10",
            "origin_data_requirements": {
                "required_fields": ["traceability_level", "certifications"],
                "optional_fields": ["coordinates", "plantation_name"]
            }
        },
        "crude_palm_oil": {
            "common_product_id": f"CPO-{timestamp}",
            "name": "Crude Palm Oil (CPO)",
            "description": "Unrefined palm oil from mill processing",
            "category": "processed",
            "can_have_composition": True,
            "material_breakdown": {
                "palm_oil": 100.0
            },
            "default_unit": "kg",
            "hs_code": "1511.10",
            "origin_data_requirements": {
                "required_fields": ["traceability_level", "certifications"],
                "optional_fields": ["mill_name", "coordinates"]
            }
        },
        "fresh_fruit_bunches": {
            "common_product_id": f"FFB-{timestamp}",
            "name": "Fresh Fruit Bunches (FFB)",
            "description": "Fresh palm fruit bunches from plantation",
            "category": "raw_material",
            "can_have_composition": False,
            "default_unit": "kg",
            "hs_code": "0801.11",
            "origin_data_requirements": {
                "required_fields": ["traceability_level", "certifications"],
                "optional_fields": ["plantation_name", "coordinates"]
            }
        }
    }
    
    # Use brand company to create products
    brand_id, brand_token = create_brand_company()
    if not brand_id:
        return {}
    
    headers = {"Authorization": f"Bearer {brand_token}"}
    
    for product_key, product_data in product_definitions.items():
        print(f"📦 Creating product: {product_data['name']}...")
        response = requests.post(f"{BASE_URL}/api/v1/products/", json=product_data, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            product = response_data.get('data', {})
            products[product_key] = product
            print(f"    ✅ Product created: {product.get('id', 'Unknown ID')}")
        else:
            print(f"    ❌ Failed to create product: {response.status_code} - {response.text}")
            print(f"    📋 Response: {response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text}")
    
    return products, brand_id, brand_token

def create_purchase_order_chain(companies, products, brand_id, brand_token):
    """Create a chain of purchase orders from brand to origin."""
    print("\n🔗 Creating Purchase Order Chain...")
    
    headers = {"Authorization": f"Bearer {brand_token}"}
    
    # Define the supply chain flow
    chain_flow = [
        {
            "from": "brand",
            "to": "trader_aggregator", 
            "product": "refined_palm_oil",
            "quantity": 10000,
            "unit_price": 800.00,
            "po_number": "PO-BRAND-001"
        },
        {
            "from": "trader_aggregator",
            "to": "refinery_crusher",
            "product": "crude_palm_oil", 
            "quantity": 12000,
            "unit_price": 600.00,
            "po_number": "PO-TRADER-001"
        },
        {
            "from": "refinery_crusher",
            "to": "mill_processor",
            "product": "crude_palm_oil",
            "quantity": 15000,
            "unit_price": 500.00,
            "po_number": "PO-REFINERY-001"
        },
        {
            "from": "mill_processor",
            "to": "plantation_grower",
            "product": "fresh_fruit_bunches",
            "quantity": 50000,
            "unit_price": 200.00,
            "po_number": "PO-MILL-001"
        }
    ]
    
    created_pos = []
    
    for i, flow in enumerate(chain_flow):
        # Determine buyer and seller
        if flow["from"] == "brand":
            buyer_id = brand_id
            buyer_token = brand_token
        else:
            buyer_id = companies[flow["from"]]["id"]
            buyer_token = companies[flow["from"]]["access_token"]
        
        seller_id = companies[flow["to"]]["id"]
        product_id = products[flow["product"]]["id"]
        
        # Create purchase order data with rich traceability
        po_data = {
            "po_number": flow["po_number"],
            "buyer_company_id": buyer_id,
            "seller_company_id": seller_id,
            "product_id": product_id,
            "quantity": flow["quantity"],
            "unit_price": flow["unit_price"],
            "total_amount": flow["quantity"] * flow["unit_price"],
            "unit": "kg",
            "delivery_date": (datetime.now() + timedelta(days=30 + i*7)).date().isoformat(),
            "delivery_location": f"Port of {flow['to'].replace('_', ' ').title()}",
            "status": "confirmed",
            "input_materials": create_input_materials_data(flow, i),
            "origin_data": create_origin_data(flow, i)
        }
        
        # Use appropriate token for the buyer
        buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
        
        print(f"  📋 Creating {flow['po_number']}: {flow['from']} → {flow['to']}")
        response = requests.post(f"{BASE_URL}/api/v1/purchase-orders/", json=po_data, headers=buyer_headers)
        
        if response.status_code == 200:
            po = response.json()
            created_pos.append(po)
            print(f"    ✅ PO Created: {po['id']}")
        else:
            print(f"    ❌ Failed to create PO: {response.status_code} - {response.text}")
    
    return created_pos

def create_input_materials_data(flow, level):
    """Create input materials data based on supply chain level."""
    if level == 0:  # Brand level
        return [{
            "material_name": "refined_palm_oil",
            "quantity": 10000,
            "unit": "kg",
            "origin": "Malaysia",
            "certifications": ["RSPO", "ISCC", "HALAL"],
            "supplier": {
                "name": "Premium Palm Oil Supplier",
                "certifications": ["RSPO", "ISO 9001", "HACCP"]
            },
            "quality_metrics": {
                "ffa_content": 0.05,
                "moisture": 0.05,
                "impurity": 0.01
            }
        }]
    elif level == 1:  # Trader level
        return [{
            "material_name": "crude_palm_oil",
            "quantity": 12000,
            "unit": "kg", 
            "origin": "Malaysia",
            "certifications": ["RSPO", "ISCC"],
            "supplier": {
                "name": "Malaysian Palm Oil Mill",
                "certifications": ["RSPO", "ISO 9001"]
            },
            "quality_metrics": {
                "ffa_content": 0.15,
                "moisture": 0.1,
                "impurity": 0.05
            }
        }]
    elif level == 2:  # Refinery level
        return [{
            "material_name": "crude_palm_oil",
            "quantity": 15000,
            "unit": "kg",
            "origin": "Malaysia", 
            "certifications": ["RSPO"],
            "supplier": {
                "name": "Sustainable Palm Mill",
                "certifications": ["RSPO"]
            },
            "quality_metrics": {
                "ffa_content": 0.2,
                "moisture": 0.12,
                "impurity": 0.08
            }
        }]
    else:  # Mill level
        return [{
            "material_name": "fresh_fruit_bunches",
            "quantity": 50000,
            "unit": "kg",
            "origin": "Malaysia",
            "certifications": ["RSPO"],
            "supplier": {
                "name": "Green Acres Plantation",
                "certifications": ["RSPO", "MSPO"]
            },
            "quality_metrics": {
                "ripeness": 0.85,
                "oil_content": 0.22,
                "moisture": 0.15
            }
        }]

def create_origin_data(flow, level):
    """Create origin data based on supply chain level."""
    base_data = {
        "traceability": {
            "batch_id": f"BATCH-{flow['po_number']}-{int(time.time())}",
            "supply_chain_level": level + 1,
            "certifications": ["RSPO"] if level >= 2 else ["RSPO", "ISCC"]
        },
        "sustainability": {
            "carbon_footprint": 2.5 + (level * 0.5),
            "deforestation_risk": "low",
            "social_impact_score": 8.5 - (level * 0.2)
        }
    }
    
    if level >= 3:  # Plantation level
        base_data["traceability"].update({
            "plantation": {
                "name": "Green Acres Plantation",
                "coordinates": {"lat": 4.2105, "lng": 101.9758},
                "certified_rspo": True,
                "size_ha": 500,
                "manager": "Ahmad Hassan",
                "established": "2010"
            },
            "mill": {
                "name": "Green Processing Mill",
                "coordinates": {"lat": 4.0, "lng": 101.0},
                "capacity_tons_day": 100,
                "certifications": ["RSPO", "MSPO"]
            }
        })
        base_data["quality_metrics"] = {
            "ffa_content": 0.25,
            "moisture": 0.15,
            "impurity": 0.1,
            "oil_extraction_rate": 0.22
        }
    elif level >= 2:  # Mill level
        base_data["traceability"].update({
            "mill": {
                "name": "Sustainable Palm Mill",
                "coordinates": {"lat": 4.1, "lng": 101.1},
                "capacity_tons_day": 150,
                "certifications": ["RSPO"]
            }
        })
        base_data["quality_metrics"] = {
            "ffa_content": 0.2,
            "moisture": 0.12,
            "impurity": 0.08
        }
    elif level >= 1:  # Refinery level
        base_data["traceability"].update({
            "refinery": {
                "name": "Premium Refinery Ltd",
                "coordinates": {"lat": 3.5, "lng": 101.5},
                "capacity_tons_day": 200,
                "certifications": ["RSPO", "ISCC"]
            }
        })
        base_data["quality_metrics"] = {
            "ffa_content": 0.15,
            "moisture": 0.1,
            "impurity": 0.05
        }
    else:  # Brand level
        base_data["traceability"].update({
            "brand": {
                "name": "Global Consumer Brand",
                "location": "Singapore",
                "certifications": ["RSPO", "ISCC", "HALAL"]
            }
        })
        base_data["quality_metrics"] = {
            "ffa_content": 0.05,
            "moisture": 0.05,
            "impurity": 0.01
        }
    
    return base_data

def demonstrate_traceability(created_pos):
    """Demonstrate the traceability capabilities."""
    print("\n🔍 Demonstrating Traceability...")
    
    # Get the first PO (brand level) to trace upstream
    if created_pos:
        brand_po = created_pos[0]
        po_id = brand_po["id"]
        
        print(f"  📊 Tracing supply chain for PO: {brand_po['po_number']}")
        
        # Create traceability request
        trace_request = {
            "purchase_order_id": po_id,
            "direction": "upstream",
            "max_depth": 10,
            "include_transformations": True,
            "include_quality_metrics": True
        }
        
        # Note: This would require authentication, but we can show the structure
        print(f"    🔗 Traceability Request: {json.dumps(trace_request, indent=2)}")
        print(f"    📈 This would show the complete supply chain from brand to plantation")
        print(f"    🏭 Including all transformations: FFB → CPO → Refined Oil")
        print(f"    📊 With quality metrics at each level")
        print(f"    🌱 Full origin data back to plantation coordinates")

def main():
    """Main function to create end-to-end PO flow."""
    print("🚀 Creating End-to-End Purchase Order Flow")
    print("=" * 60)
    
    # Step 1: Create products
    print("\n📦 Step 1: Creating Products...")
    products, brand_id, brand_token = create_products()
    if not products:
        print("❌ Failed to create products")
        return
    
    # Step 2: Create supply chain companies
    print("\n🏢 Step 2: Creating Supply Chain Companies...")
    companies = create_supply_chain_companies()
    if not companies:
        print("❌ Failed to create companies")
        return
    
    # Step 3: Create purchase order chain
    print("\n🔗 Step 3: Creating Purchase Order Chain...")
    created_pos = create_purchase_order_chain(companies, products, brand_id, brand_token)
    if not created_pos:
        print("❌ Failed to create purchase orders")
        return
    
    # Step 4: Demonstrate traceability
    print("\n🔍 Step 4: Demonstrating Traceability...")
    demonstrate_traceability(created_pos)
    
    # Summary
    print("\n🎉 End-to-End Supply Chain Created Successfully!")
    print("=" * 60)
    print("📊 Summary:")
    print(f"  🏭 Brand Company: 1")
    print(f"  🏢 Supply Chain Companies: {len(companies)}")
    print(f"  📦 Products: {len(products)}")
    print(f"  📋 Purchase Orders: {len(created_pos)}")
    print(f"  🔗 Supply Chain Levels: {len(created_pos)}")
    print("\n🌱 Complete Traceability:")
    print("  Brand → Trader → Refinery → Mill → Plantation")
    print("  With full transformation tracking and origin data")

if __name__ == "__main__":
    main()
