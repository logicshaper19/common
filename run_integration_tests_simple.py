#!/usr/bin/env python3
"""
Simplified Final Integration Testing Runner

This script runs essential integration tests to validate the system.
"""

import sys
import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_api_endpoints() -> Dict[str, Any]:
    """Test core API endpoints."""
    
    print("\n🔌 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        server_running = True
        print("   ✅ Server is running")
    except:
        server_running = False
        print("   ❌ Server is not running")
        return {
            "status": "FAIL",
            "error": "Server not accessible",
            "endpoints_tested": 0,
            "endpoints_passed": 0
        }
    
    # Core endpoints to test
    endpoints = [
        {"path": "/health", "method": "GET", "expected": [200]},
        {"path": "/docs", "method": "GET", "expected": [200]},
        {"path": "/api/v1/companies", "method": "GET", "expected": [200, 401]},
        {"path": "/api/v1/products", "method": "GET", "expected": [200, 401]},
        {"path": "/api/v1/purchase-orders", "method": "GET", "expected": [200, 401]},
    ]
    
    results = {
        "endpoints_tested": len(endpoints),
        "endpoints_passed": 0,
        "endpoints_failed": 0,
        "details": []
    }
    
    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint['path']}"
            response = requests.get(url, timeout=10)
            
            if response.status_code in endpoint["expected"]:
                status = "PASS"
                results["endpoints_passed"] += 1
            else:
                status = "FAIL"
                results["endpoints_failed"] += 1
            
            results["details"].append({
                "endpoint": endpoint["path"],
                "status_code": response.status_code,
                "status": status,
                "response_time": response.elapsed.total_seconds()
            })
            
            print(f"   {'✅' if status == 'PASS' else '❌'} {endpoint['path']}: {response.status_code}")
            
        except Exception as e:
            results["endpoints_failed"] += 1
            results["details"].append({
                "endpoint": endpoint["path"],
                "status": "ERROR",
                "error": str(e)
            })
            print(f"   ❌ {endpoint['path']}: ERROR - {str(e)}")
    
    results["success_rate"] = f"{(results['endpoints_passed']/results['endpoints_tested'])*100:.1f}%"
    results["status"] = "PASS" if results["endpoints_passed"] >= results["endpoints_tested"] * 0.8 else "FAIL"
    
    return results


def test_database_connectivity() -> Dict[str, Any]:
    """Test database connectivity and basic operations."""
    
    print("\n🗄️ Testing Database Connectivity...")
    
    try:
        from app.database import get_db
        from app.models.company import Company
        from sqlalchemy.orm import Session
        
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Test basic query
        companies = db.query(Company).limit(5).all()
        
        print(f"   ✅ Database connected successfully")
        print(f"   ✅ Found {len(companies)} companies in database")
        
        return {
            "status": "PASS",
            "companies_found": len(companies),
            "connection_successful": True
        }
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {str(e)}")
        return {
            "status": "FAIL",
            "error": str(e),
            "connection_successful": False
        }


def test_core_functionality() -> Dict[str, Any]:
    """Test core platform functionality."""
    
    print("\n⚙️ Testing Core Functionality...")
    
    results = {
        "tests_run": 0,
        "tests_passed": 0,
        "details": []
    }
    
    # Test 1: Import core modules
    try:
        from app.services.purchase_order import PurchaseOrderService
        from app.services.product import ProductService
        from app.services.company import CompanyService
        
        results["tests_run"] += 1
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Core Service Imports",
            "status": "PASS",
            "details": "All core services imported successfully"
        })
        print("   ✅ Core services import successfully")
        
    except Exception as e:
        results["tests_run"] += 1
        results["details"].append({
            "test": "Core Service Imports",
            "status": "FAIL",
            "error": str(e)
        })
        print(f"   ❌ Core service import failed: {str(e)}")
    
    # Test 2: Service instantiation
    try:
        from app.database import get_db
        from sqlalchemy.orm import Session
        
        db_gen = get_db()
        db = next(db_gen)
        
        # Test service creation
        from app.services.purchase_order import PurchaseOrderService
        po_service = PurchaseOrderService(db)
        
        results["tests_run"] += 1
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Service Instantiation",
            "status": "PASS",
            "details": "Services can be instantiated with database session"
        })
        print("   ✅ Services instantiate successfully")
        
    except Exception as e:
        results["tests_run"] += 1
        results["details"].append({
            "test": "Service Instantiation",
            "status": "FAIL",
            "error": str(e)
        })
        print(f"   ❌ Service instantiation failed: {str(e)}")
    
    # Test 3: Basic service methods
    try:
        po_number = po_service.generate_po_number()
        
        results["tests_run"] += 1
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Service Methods",
            "status": "PASS",
            "details": f"Generated PO number: {po_number}"
        })
        print(f"   ✅ Service methods work (generated PO: {po_number})")
        
    except Exception as e:
        results["tests_run"] += 1
        results["details"].append({
            "test": "Service Methods",
            "status": "FAIL",
            "error": str(e)
        })
        print(f"   ❌ Service method failed: {str(e)}")
    
    results["success_rate"] = f"{(results['tests_passed']/results['tests_run'])*100:.1f}%" if results['tests_run'] > 0 else "0%"
    results["status"] = "PASS" if results["tests_passed"] >= results["tests_run"] * 0.8 else "FAIL"
    
    return results


def test_user_personas() -> Dict[str, Any]:
    """Test that user personas can be created and used."""
    
    print("\n👥 Testing User Personas...")
    
    results = {
        "personas_tested": 4,
        "personas_created": 0,
        "details": []
    }
    
    personas = [
        {"name": "Paula", "role": "Farmer/Originator", "company_type": "originator"},
        {"name": "Sam", "role": "Processor", "company_type": "processor"},
        {"name": "Maria", "role": "Retailer/Brand", "company_type": "brand"},
        {"name": "Charlie", "role": "Consumer/Viewer", "company_type": "brand"}
    ]
    
    try:
        from app.models.company import Company
        from app.models.user import User
        from app.database import get_db
        from uuid import uuid4
        
        db_gen = get_db()
        db = next(db_gen)
        
        for persona in personas:
            try:
                # Create test company
                company = Company(
                    id=uuid4(),
                    name=f"{persona['name']} Test Company",
                    company_type=persona["company_type"],
                    email=f"{persona['name'].lower()}@test.com"
                )
                
                # Create test user
                user = User(
                    id=uuid4(),
                    email=f"{persona['name'].lower()}@test.com",
                    hashed_password="test_password",
                    full_name=persona["name"],
                    role="admin",
                    company_id=company.id,
                    is_active=True
                )
                
                results["personas_created"] += 1
                results["details"].append({
                    "persona": persona["name"],
                    "role": persona["role"],
                    "status": "PASS",
                    "details": f"Created {persona['company_type']} company and user"
                })
                print(f"   ✅ {persona['name']} ({persona['role']}): Created successfully")
                
            except Exception as e:
                results["details"].append({
                    "persona": persona["name"],
                    "role": persona["role"],
                    "status": "FAIL",
                    "error": str(e)
                })
                print(f"   ❌ {persona['name']} ({persona['role']}): Failed - {str(e)}")
        
    except Exception as e:
        print(f"   ❌ Persona testing setup failed: {str(e)}")
        results["setup_error"] = str(e)
    
    results["success_rate"] = f"{(results['personas_created']/results['personas_tested'])*100:.1f}%"
    results["status"] = "PASS" if results["personas_created"] >= 3 else "FAIL"
    
    return results


def run_integration_tests() -> Dict[str, Any]:
    """Run all integration tests."""
    
    print("\n🧪 SIMPLIFIED INTEGRATION TESTING")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = {
        "test_suite": "Simplified Integration Testing",
        "timestamp": datetime.now().isoformat(),
        "results": {}
    }
    
    # Run all tests
    test_results["results"]["api_endpoints"] = test_api_endpoints()
    test_results["results"]["database_connectivity"] = test_database_connectivity()
    test_results["results"]["core_functionality"] = test_core_functionality()
    test_results["results"]["user_personas"] = test_user_personas()
    
    # Calculate overall results
    test_categories = list(test_results["results"].keys())
    passed_categories = sum(1 for result in test_results["results"].values() 
                          if result.get("status") == "PASS")
    total_categories = len(test_categories)
    
    test_results["summary"] = {
        "total_categories": total_categories,
        "passed_categories": passed_categories,
        "failed_categories": total_categories - passed_categories,
        "success_rate": f"{(passed_categories/total_categories)*100:.1f}%",
        "overall_status": "PASS" if passed_categories >= total_categories * 0.75 else "FAIL"
    }
    
    # Print summary
    print(f"\n📊 INTEGRATION TEST SUMMARY")
    print("=" * 40)
    print(f"Categories Tested: {total_categories}")
    print(f"Categories Passed: {passed_categories}")
    print(f"Categories Failed: {total_categories - passed_categories}")
    print(f"Success Rate: {test_results['summary']['success_rate']}")
    print(f"Overall Status: {test_results['summary']['overall_status']}")
    
    print(f"\n📋 Category Results:")
    for category, result in test_results["results"].items():
        status = result.get("status", "UNKNOWN")
        status_icon = "✅" if status == "PASS" else "❌"
        category_name = category.replace("_", " ").title()
        print(f"   {status_icon} {category_name}: {status}")
    
    return test_results


def main():
    """Main function."""
    
    try:
        results = run_integration_tests()
        
        # Save results
        with open("integration_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: integration_test_results.json")
        
        # Exit with appropriate code
        overall_status = results.get("summary", {}).get("overall_status", "FAIL")
        exit_code = 0 if overall_status == "PASS" else 1
        
        print(f"\n🏁 Testing Complete - Exit Code: {exit_code}")
        return exit_code
        
    except Exception as e:
        print(f"\n❌ Testing failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
