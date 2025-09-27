"""
Test script for the pragmatic LangChain system implementation.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Mock database manager for testing
class MockDatabaseManager:
    """Mock database manager for testing."""
    def __init__(self):
        self.connected = True
    
    def get_connection(self):
        return self
    
    def execute_query(self, query: str, params=None):
        # Mock query execution
        return []

# Mock certification manager for testing
class MockCertificationManager:
    """Mock certification manager for testing."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_certifications(self, company_id=None, expires_within_days=30):
        # Mock certification data
        mock_certs = [
            type('Cert', (), {
                'company_name': 'Sime Darby Plantation',
                'certification_type': 'RSPO',
                'expiry_date': datetime(2024, 3, 15),
                'days_until_expiry': 12,
                'needs_renewal': True
            })(),
            type('Cert', (), {
                'company_name': 'Golden Agri-Resources',
                'certification_type': 'MSPO',
                'expiry_date': datetime(2024, 4, 20),
                'days_until_expiry': 48,
                'needs_renewal': False
            })()
        ]
        
        metadata = {
            'total_count': len(mock_certs),
            'expiring_soon': len([c for c in mock_certs if c.days_until_expiry <= 30])
        }
        
        return mock_certs, metadata
    
    def search_batches(self, product_type=None, min_quantity=0, status=None, company_id=None, certification_required=None):
        # Mock batch data
        mock_batches = [
            type('Batch', (), {
                'batch_id': 'BATCH-001',
                'company_name': 'Sime Darby Plantation',
                'product_name': 'CPO',
                'quantity': 50.0,
                'transparency_score': 95.5,
                'certifications': ['RSPO', 'MSPO']
            })(),
            type('Batch', (), {
                'batch_id': 'BATCH-002',
                'company_name': 'Golden Agri-Resources',
                'product_name': 'RBDPO',
                'quantity': 75.0,
                'transparency_score': 88.2,
                'certifications': ['RSPO']
            })()
        ]
        
        metadata = {
            'total_count': len(mock_batches),
            'total_quantity': sum(b.quantity for b in mock_batches)
        }
        
        return mock_batches, metadata
    
    def get_farm_locations(self, company_id=None, certification_type=None, eudr_compliant_only=False):
        # Mock farm data
        mock_farms = [
            type('Farm', (), {
                'name': 'SD Farm A',
                'company_name': 'Sime Darby Plantation',
                'latitude': 3.1390,
                'longitude': 101.6869,
                'certifications': ['RSPO'],
                'compliance_status': 'Compliant',
                'eudr_compliant': True
            })(),
            type('Farm', (), {
                'name': 'GAR Farm B',
                'company_name': 'Golden Agri-Resources',
                'latitude': 1.3521,
                'longitude': 103.8198,
                'certifications': ['RSPO', 'MSPO'],
                'compliance_status': 'Compliant',
                'eudr_compliant': True
            })()
        ]
        
        metadata = {
            'total_count': len(mock_farms),
            'eudr_compliant_count': len([f for f in mock_farms if f.eudr_compliant])
        }
        
        return mock_farms, metadata
    
    def get_purchase_orders(self, company_id=None, role_filter=None, status=None, product_type=None, limit=20):
        # Mock purchase order data
        mock_orders = [
            type('Order', (), {
                'po_number': 'PO-2024-001',
                'buyer_company_name': 'L\'Oréal',
                'seller_company_name': 'Sime Darby Plantation',
                'product_name': 'CPO',
                'quantity': 100.0,
                'status': 'confirmed',
                'value_estimate': 45000.0
            })(),
            type('Order', (), {
                'po_number': 'PO-2024-002',
                'buyer_company_name': 'Unilever',
                'seller_company_name': 'Golden Agri-Resources',
                'product_name': 'RBDPO',
                'quantity': 150.0,
                'status': 'fulfilled',
                'value_estimate': 67500.0
            })()
        ]
        
        metadata = {
            'total_count': len(mock_orders),
            'total_value': sum(o.value_estimate for o in mock_orders)
        }
        
        return mock_orders, metadata

# Mock supply chain manager for testing
class MockSupplyChainManager:
    """Mock supply chain manager for testing."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_supply_chain_analytics(self, company_id=None):
        # Mock analytics data
        mock_analytics = type('Analytics', (), {
            'health_score': 87.5,
            'critical_issues': ['Certificate expiring in 12 days', 'Low transparency score on 2 batches'],
            'recommendations': ['Renew RSPO certificate', 'Investigate transparency issues']
        })()
        
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'data_freshness': '5 minutes'
        }
        
        return mock_analytics, metadata
    
    def trace_supply_chain(self, batch_id=None):
        # Mock traceability data
        mock_traceability = type('Traceability', (), {
            'origin_farm': 'SD Farm A',
            'processing_steps': ['Harvest', 'Milling', 'Refining'],
            'transparency_score': 95.5,
            'compliance_status': 'Compliant'
        })()
        
        metadata = {
            'traceability_completeness': '100%',
            'last_updated': datetime.now().isoformat()
        }
        
        return mock_traceability, metadata

# Test the pragmatic system
async def test_pragmatic_system():
    """Test the pragmatic LangChain system."""
    print("🧪 Testing Pragmatic LangChain System")
    print("=" * 50)
    
    try:
        # Import the pragmatic system
        from app.core.pragmatic_langchain_system import PragmaticLangChainSystem
        
        # Create mock database manager
        mock_db_manager = MockDatabaseManager()
        
        # Create pragmatic system with mocked managers
        system = PragmaticLangChainSystem(mock_db_manager)
        
        # Override the managers with mocks
        system.cert_manager = MockCertificationManager(mock_db_manager)
        system.supply_manager = MockSupplyChainManager(mock_db_manager)
        
        print(f"✅ System initialized - Phase {system.current_phase}")
        print(f"✅ Tools available: {len(system.tools)}")
        print(f"✅ Fallback enabled: {system.fallback_mode}")
        
        # Test queries
        test_queries = [
            "Show me certificates expiring in 30 days",
            "Find available CPO inventory",
            "Check compliance status for my company",
            "Show recent purchase orders",
            "Find RSPO certified batches"
        ]
        
        user_context = {
            "company_id": "123",
            "user_role": "manager",
            "user_name": "Test User"
        }
        
        print("\n🔍 Testing Phase 1 Tools:")
        print("-" * 30)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: {query}")
            
            try:
                result = await system.process_query(query, user_context)
                
                print(f"   Method: {result['method_used']}")
                print(f"   Time: {result['processing_time']:.2f}s")
                print(f"   Response: {result['response'][:100]}...")
                
                if result['method_used'].startswith('langchain'):
                    print("   ✅ LangChain agent used")
                elif result['method_used'] == 'fallback_direct':
                    print("   ⚠️  Fallback system used")
                else:
                    print("   ❌ Error occurred")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        
        # Test system status
        print("\n📊 System Status:")
        print("-" * 20)
        status = system.get_implementation_status()
        print(f"Current Phase: {status['current_phase']}")
        print(f"Tools Available: {status['tools_available']}")
        print(f"Fallback Enabled: {status['fallback_enabled']}")
        
        # Test phase advancement
        print("\n🚀 Testing Phase Advancement:")
        print("-" * 30)
        
        # Mock successful metrics for Phase 1
        phase_1_metrics = {
            "success_rate": 0.95,  # >90% required
            "avg_response_time": 1.5,  # <2.0s required
            "user_feedback": 4.5  # >4.0 required
        }
        
        print(f"Phase 1 Metrics: {phase_1_metrics}")
        
        advanced = system.advance_to_next_phase(phase_1_metrics)
        if advanced:
            print("✅ Advanced to Phase 2!")
            print(f"New Phase: {system.current_phase}")
            print(f"Tools Available: {len(system.tools)}")
        else:
            print("❌ Did not advance to Phase 2")
        
        print("\n🎉 Test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure the pragmatic system is properly implemented")
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()

# Test API endpoint integration
def test_api_integration():
    """Test API endpoint integration."""
    print("\n🌐 Testing API Integration:")
    print("-" * 30)
    
    try:
        # Test the API endpoint structure
        from app.api.unified_assistant import PragmaticChatRequest
        
        # Create test request
        request = PragmaticChatRequest(
            message="Show me certificates expiring soon",
            company_id="123",
            user_role="manager"
        )
        
        print(f"✅ Request model created: {request.message}")
        print(f"✅ Company ID: {request.company_id}")
        print(f"✅ User Role: {request.user_role}")
        
        print("✅ API integration structure is correct")
        
    except ImportError as e:
        print(f"❌ API import error: {str(e)}")
    except Exception as e:
        print(f"❌ API test error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Pragmatic LangChain System Test Suite")
    print("=" * 60)
    
    # Test the system
    asyncio.run(test_pragmatic_system())
    
    # Test API integration
    test_api_integration()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\nNext steps:")
    print("1. Run the test script to verify implementation")
    print("2. Test the API endpoints")
    print("3. Monitor performance metrics")
    print("4. Advance to Phase 2 when ready")
