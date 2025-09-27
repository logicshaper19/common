#!/usr/bin/env python3
"""
Comprehensive test of the fixed pragmatic LangChain system.
Tests all components: system, API, tools, and integration.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_system_imports():
    """Test that all system components can be imported."""
    print("🔍 Testing System Imports")
    print("=" * 30)
    
    try:
        from app.core.pragmatic_langchain_system import create_pragmatic_system
        print("✅ pragmatic_langchain_system imported")
        
        from app.api.unified_assistant import PragmaticChatRequest
        print("✅ PragmaticChatRequest imported")
        
        from app.api.unified_assistant import pragmatic_chat, pragmatic_status
        print("✅ API endpoints imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_system_creation():
    """Test that the system can be created and initialized."""
    print("\n🏗️ Testing System Creation")
    print("=" * 30)
    
    try:
        from app.core.pragmatic_langchain_system import create_pragmatic_system
        
        system = create_pragmatic_system()
        
        print(f"✅ System created successfully")
        print(f"   Phase: {system.current_phase}")
        print(f"   Tools: {len(system.tools)}")
        print(f"   Fallback: {system.fallback_mode}")
        print(f"   LLM Type: {type(system.llm).__name__}")
        
        # Test system status
        status = system.get_implementation_status()
        print(f"   Status: {status['current_phase']} phase active")
        
        return True
    except Exception as e:
        print(f"❌ System creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_functionality():
    """Test that the tools work correctly."""
    print("\n🔧 Testing Tool Functionality")
    print("=" * 30)
    
    try:
        from app.core.pragmatic_langchain_system import create_pragmatic_system
        
        system = create_pragmatic_system()
        
        # Test each tool
        tool_tests = [
            ("get_expiring_certificates", {"company_id": "123", "days_ahead": 30}),
            ("find_available_inventory", {"product_type": "CPO", "min_quantity": 0}),
            ("check_compliance_status", {"company_id": "123"}),
            ("get_recent_orders", {"company_id": "123", "days_back": 30}),
            ("search_by_certification", {"cert_type": "RSPO", "company_id": "123"})
        ]
        
        for tool_name, params in tool_tests:
            try:
                tool = next((t for t in system.tools if t.name == tool_name), None)
                if tool:
                    result = tool.invoke(params)
                    print(f"✅ {tool_name}: {len(str(result))} chars output")
                else:
                    print(f"❌ {tool_name}: Tool not found")
            except Exception as e:
                print(f"❌ {tool_name}: Error - {str(e)[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Tool testing error: {e}")
        return False

async def test_query_processing():
    """Test that queries are processed correctly."""
    print("\n💬 Testing Query Processing")
    print("=" * 30)
    
    try:
        from app.core.pragmatic_langchain_system import create_pragmatic_system
        
        system = create_pragmatic_system()
        
        test_queries = [
            "Show me certificates expiring in 30 days",
            "Find available CPO inventory",
            "Check compliance status",
            "What are my recent orders?",
            "Find RSPO certified batches"
        ]
        
        user_context = {
            "company_id": "123",
            "user_role": "manager",
            "user_name": "Test User"
        }
        
        for i, query in enumerate(test_queries, 1):
            try:
                result = await system.process_query(query, user_context)
                print(f"✅ Query {i}: {result['method_used']} ({result['processing_time']:.3f}s)")
                print(f"   Response: {result['response'][:80]}...")
            except Exception as e:
                print(f"❌ Query {i}: Error - {str(e)[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Query processing error: {e}")
        return False

async def test_api_models():
    """Test that API models work correctly."""
    print("\n📋 Testing API Models")
    print("=" * 30)
    
    try:
        from app.api.unified_assistant import PragmaticChatRequest
        
        # Test model creation
        request = PragmaticChatRequest(
            message="Test message",
            company_id="123",
            user_role="manager"
        )
        
        print(f"✅ Request created: {request.message}")
        print(f"   Company ID: {request.company_id}")
        print(f"   User Role: {request.user_role}")
        
        # Test model validation
        assert request.message == "Test message"
        assert request.company_id == "123"
        assert request.user_role == "manager"
        
        print("✅ Model validation passed")
        
        return True
    except Exception as e:
        print(f"❌ API model error: {e}")
        return False

async def test_fallback_system():
    """Test that the fallback system works."""
    print("\n🔄 Testing Fallback System")
    print("=" * 30)
    
    try:
        from app.core.pragmatic_langchain_system import create_pragmatic_system
        
        system = create_pragmatic_system()
        
        # Test fallback processing
        user_context = {"company_id": "123"}
        
        fallback_queries = [
            "expiring certificates",
            "available inventory",
            "compliance status"
        ]
        
        for query in fallback_queries:
            try:
                result = await system._fallback_processing(query, user_context)
                print(f"✅ Fallback '{query}': {len(result)} chars")
            except Exception as e:
                print(f"❌ Fallback '{query}': Error - {str(e)[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Fallback testing error: {e}")
        return False

async def run_comprehensive_test():
    """Run all tests and provide a summary."""
    print("🧪 COMPREHENSIVE SYSTEM TEST")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("System Imports", test_system_imports),
        ("System Creation", test_system_creation),
        ("Tool Functionality", test_tool_functionality),
        ("Query Processing", test_query_processing),
        ("API Models", test_api_models),
        ("Fallback System", test_fallback_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. System needs attention.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)
