#!/usr/bin/env python3
"""
Test script for the streaming assistant functionality.
Tests the streaming chat endpoint with various supply chain queries.
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_streaming_endpoint():
    """Test the streaming chat endpoint."""
    
    base_url = "http://localhost:8000"  # Adjust if your server runs on a different port
    endpoint = f"{base_url}/api/v1/assistant/stream-chat"
    
    # Test messages for different types of content
    test_messages = [
        "Show me my current inventory",
        "What's our transparency score?",
        "Show me the supplier network",
        "What's our yield performance?",
        "Show compliance status",
        "Give me an overview of everything"
    ]
    
    print("🚀 Testing Streaming Assistant Endpoint")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📝 Test {i}: {message}")
        print("-" * 30)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json={
                        "message": message,
                        "include_visualizations": True,
                        "max_response_time": 30
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer test-token"  # You'll need a real token
                    }
                ) as response:
                    
                    if response.status != 200:
                        print(f"❌ HTTP Error: {response.status}")
                        continue
                    
                    print("✅ Connected to streaming endpoint")
                    print("📊 Streaming responses:")
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                
                                if data.get('type') == 'complete':
                                    print("✅ Stream completed")
                                    break
                                elif data.get('type') == 'error':
                                    print(f"❌ Error: {data.get('message')}")
                                    break
                                else:
                                    # Print response type and content preview
                                    content_preview = str(data.get('content', ''))[:100]
                                    if len(str(data.get('content', ''))) > 100:
                                        content_preview += "..."
                                    
                                    print(f"  📦 {data.get('type', 'unknown')}: {content_preview}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"⚠️  JSON decode error: {e}")
                                continue
                    
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    print("\n" + "=" * 50)
    print("🏁 Streaming tests completed!")


async def test_health_endpoint():
    """Test the health check endpoint."""
    
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/assistant/stream-chat/health"
    
    print("\n🏥 Testing Health Endpoint")
    print("-" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Health check passed")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Service: {data.get('service')}")
                    print(f"   Features: {data.get('features')}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    
    except Exception as e:
        print(f"❌ Health check error: {e}")


async def test_features_endpoint():
    """Test the features endpoint."""
    
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/assistant/stream-chat/features"
    
    print("\n🔧 Testing Features Endpoint")
    print("-" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Features endpoint working")
                    print(f"   Streaming types: {len(data.get('streaming_types', []))}")
                    print(f"   Chart types: {len(data.get('chart_types', []))}")
                    print(f"   Graph types: {len(data.get('graph_types', []))}")
                    print(f"   Supported queries: {len(data.get('supported_queries', []))}")
                else:
                    print(f"❌ Features endpoint failed: {response.status}")
                    
    except Exception as e:
        print(f"❌ Features endpoint error: {e}")


async def test_sync_endpoint():
    """Test the synchronous streaming endpoint."""
    
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/assistant/stream-chat-sync"
    
    print("\n🔄 Testing Sync Endpoint")
    print("-" * 30)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint,
                json={
                    "message": "Show me my inventory",
                    "include_visualizations": True
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer test-token"
                }
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Sync endpoint working")
                    print(f"   Success: {data.get('success')}")
                    print(f"   Message: {data.get('message')}")
                    print(f"   Session ID: {data.get('session_id')}")
                else:
                    print(f"❌ Sync endpoint failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ Sync endpoint error: {e}")


async def main():
    """Run all tests."""
    
    print("🧪 Streaming Assistant Test Suite")
    print("=" * 50)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test health endpoint first
    await test_health_endpoint()
    
    # Test features endpoint
    await test_features_endpoint()
    
    # Test sync endpoint
    await test_sync_endpoint()
    
    # Test streaming endpoint
    await test_streaming_endpoint()
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 All tests completed!")


if __name__ == "__main__":
    # Check if server is running
    print("🔍 Checking if server is running...")
    print("   Make sure your FastAPI server is running on http://localhost:8000")
    print("   You can start it with: uvicorn app.main:app --reload")
    print()
    
    # Run the tests
    asyncio.run(main())
