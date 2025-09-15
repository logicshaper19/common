#!/usr/bin/env python3
"""
Simple WebSocket test script to verify connection works.
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection to dashboard endpoint."""
    uri = "ws://127.0.0.1:8000/ws/dashboard"

    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")

            # Wait for welcome message
            message = await websocket.recv()
            print(f"Received: {message}")

            # Send a ping
            ping_message = {"type": "ping", "timestamp": "2024-01-01T00:00:00Z"}
            await websocket.send(json.dumps(ping_message))
            print(f"Sent: {ping_message}")

            # Wait for pong
            response = await websocket.recv()
            print(f"Received: {response}")

    except Exception as e:
        print(f"✗ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())