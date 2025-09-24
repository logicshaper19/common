#!/usr/bin/env python3
"""
Comprehensive performance testing script with proper authentication
Tests all purchase order endpoints with real JWT authentication
"""

import sys
import os
import time
import requests
import json
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.company import Company
from app.models.user import User
from app.core.auth import create_access_token
from sqlalchemy import text

def test_endpoint_with_auth(endpoint_url: str, company_name: str) -> Dict[str, Any]:
    """Test endpoint with proper authentication"""
    
    # Get test user for company
    db = next(get_db())
    
    try:
        company = db.query(Company).filter(Company.name == company_name).first()
        if not company:
            return {'success': False, 'error': f'Company {company_name} not found'}
        
        user = db.query(User).filter(User.company_id == company.id).first()
        if not user:
            return {'success': False, 'error': f'No user found for {company_name}'}
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.email})
        
        # Make authenticated request
        headers = {"Authorization": f"Bearer {access_token}"}
        
        start_time = time.time()
        try:
            response = requests.get(f"http://localhost:8000{endpoint_url}", headers=headers, timeout=30)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'response_time': end_time - start_time,
                    'result_count': len(data) if isinstance(data, list) else 1,
                    'status_code': response.status_code,
                    'user_email': user.email,
                    'company_type': company.company_type
                }
            else:
                return {
                    'success': False,
                    'response_time': end_time - start_time,
                    'error': f'HTTP {response.status_code}: {response.text[:100]}',
                    'user_email': user.email,
                    'company_type': company.company_type
                }
                
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            return {
                'success': False,
                'response_time': end_time - start_time,
                'error': f'Request failed: {str(e)}',
                'user_email': user.email,
                'company_type': company.company_type
            }
            
    except Exception as e:
        return {
            'success': False,
            'response_time': 0,
            'error': f'Database error: {str(e)}'
        }
    finally:
        db.close()

def test_database_performance():
    """Test database query performance directly"""
    db = next(get_db())
    
    try:
        # Test optimized query performance
        start_time = time.time()
        
        # Test the optimized query
        query = text("""
        SELECT 
            po.id,
            po.po_number,
            po.status,
            po.total_amount,
            po.created_at,
            buyer.name as buyer_name,
            seller.name as seller_name,
            p.name as product_name
        FROM purchase_orders po
        LEFT JOIN companies buyer ON po.buyer_company_id = buyer.id
        LEFT JOIN companies seller ON po.seller_company_id = seller.id  
        LEFT JOIN products p ON po.product_id = p.id
        WHERE po.status = 'pending'
        ORDER BY po.created_at DESC
        LIMIT 100;
        """)
        
        result = db.execute(query).fetchall()
        end_time = time.time()
        
        return {
            'success': True,
            'response_time': end_time - start_time,
            'result_count': len(result),
            'query_type': 'optimized_with_relations'
        }
        
    except Exception as e:
        return {
            'success': False,
            'response_time': 0,
            'error': f'Database query failed: {str(e)}'
        }
    finally:
        db.close()

def comprehensive_performance_test():
    """Test all endpoints with real authentication"""
    
    # Test companies from your palm oil supply chain
    test_scenarios = [
        ("Plantation Estate Sdn Bhd", "/api/v1/purchase-orders/with-relations"),
        ("Plantation Estate Sdn Bhd", "/api/v1/purchase-orders/incoming"),
        ("Golden Harvest Mill Sdn Bhd", "/api/v1/purchase-orders/with-relations?status=confirmed"),
        ("Palm Oil Refinery Corp", "/api/v1/purchase-orders/outgoing"),
    ]
    
    results = []
    
    print("🚀 Starting comprehensive performance test...\n")
    
    # Test database performance first
    print("Testing database query performance...")
    db_result = test_database_performance()
    if db_result['success']:
        print(f"  ✅ Database query: {db_result['response_time']:.3f}s ({db_result['result_count']} records)")
    else:
        print(f"  ❌ Database query failed: {db_result['error']}")
    results.append({**db_result, 'test_type': 'database_query'})
    
    print("\nTesting API endpoints with authentication...")
    
    for company_name, endpoint in test_scenarios:
        print(f"Testing {endpoint} for {company_name}...")
        result = test_endpoint_with_auth(endpoint, company_name)
        result['company'] = company_name
        result['endpoint'] = endpoint
        result['test_type'] = 'api_endpoint'
        results.append(result)
        
        if result['success']:
            print(f"  ✅ {result['response_time']:.3f}s ({result['result_count']} records) - {result['user_email']}")
        else:
            print(f"  ❌ {result['error']}")
    
    return results

def generate_performance_report(results: List[Dict[str, Any]]):
    """Generate a comprehensive performance report"""
    
    print("\n" + "="*60)
    print("📊 PERFORMANCE TEST REPORT")
    print("="*60)
    
    # Separate results by type
    api_results = [r for r in results if r.get('test_type') == 'api_endpoint']
    db_results = [r for r in results if r.get('test_type') == 'database_query']
    
    # Database performance
    if db_results:
        db_result = db_results[0]
        print(f"\n🗄️  Database Performance:")
        if db_result['success']:
            print(f"   Query Time: {db_result['response_time']:.3f}s")
            print(f"   Records Returned: {db_result['result_count']}")
            print(f"   Status: ✅ EXCELLENT" if db_result['response_time'] < 0.1 else "⚠️  NEEDS OPTIMIZATION")
        else:
            print(f"   Status: ❌ FAILED - {db_result['error']}")
    
    # API performance summary
    if api_results:
        successful_tests = [r for r in api_results if r['success']]
        failed_tests = [r for r in api_results if not r['success']]
        
        print(f"\n🌐 API Performance Summary:")
        print(f"   Total Tests: {len(api_results)}")
        print(f"   Successful: {len(successful_tests)}")
        print(f"   Failed: {len(failed_tests)}")
        
        if successful_tests:
            avg_response_time = sum(r['response_time'] for r in successful_tests) / len(successful_tests)
            print(f"   Average Response Time: {avg_response_time:.3f}s")
            
            # Performance recommendations
            if avg_response_time < 0.5:
                print(f"   Status: ✅ EXCELLENT PERFORMANCE")
            elif avg_response_time < 1.0:
                print(f"   Status: ✅ GOOD PERFORMANCE")
            elif avg_response_time < 2.0:
                print(f"   Status: ⚠️  ACCEPTABLE PERFORMANCE")
            else:
                print(f"   Status: ❌ NEEDS OPTIMIZATION")
        
        # Detailed results
        print(f"\n📋 Detailed Results:")
        for result in api_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['endpoint']} ({result['company']})")
            if result['success']:
                print(f"      Time: {result['response_time']:.3f}s, Records: {result['result_count']}")
            else:
                print(f"      Error: {result['error']}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if db_results and db_results[0]['success'] and db_results[0]['response_time'] > 0.1:
        print("   - Consider adding more database indexes")
        print("   - Review query optimization")
    
    if api_results:
        slow_tests = [r for r in api_results if r['success'] and r['response_time'] > 1.0]
        if slow_tests:
            print("   - Enable caching for slow endpoints")
            print("   - Consider query result pagination")
        
        failed_tests = [r for r in api_results if not r['success']]
        if failed_tests:
            print("   - Fix authentication issues")
            print("   - Check endpoint availability")
    
    print("\n" + "="*60)

def main():
    """Main test execution"""
    try:
        results = comprehensive_performance_test()
        generate_performance_report(results)
        
        # Return exit code based on results
        failed_tests = [r for r in results if not r['success']]
        if failed_tests:
            print(f"\n❌ {len(failed_tests)} tests failed")
            return 1
        else:
            print(f"\n🎉 All tests passed!")
            return 0
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
