#!/usr/bin/env python3
"""
Test script to debug login validation errors.
"""
import requests
import json
import sys

def test_login():
    """Test login endpoint and show detailed validation errors."""
    url = 'http://localhost:8000/api/v1/auth/login'
    
    # Test data
    test_cases = [
        {
            "name": "Valid credentials",
            "data": {"email": "elisha@common.co", "password": "password123"}
        },
        {
            "name": "Missing email",
            "data": {"password": "password123"}
        },
        {
            "name": "Missing password", 
            "data": {"email": "elisha@common.co"}
        },
        {
            "name": "Invalid email format",
            "data": {"email": "invalid-email", "password": "password123"}
        },
        {
            "name": "Short password",
            "data": {"email": "elisha@common.co", "password": "short"}
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Testing: {test_case['name']} ===")
        print(f"Request data: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            response = requests.post(
                url, 
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 422:
                try:
                    error_data = response.json()
                    print("Validation Errors:")
                    print(json.dumps(error_data, indent=2))
                except Exception as e:
                    print(f"Could not parse JSON response: {e}")
                    print(f"Raw response: {response.text}")
            elif response.status_code == 200:
                print("✅ Login successful!")
                try:
                    success_data = response.json()
                    print(f"Access token received: {success_data.get('access_token', 'N/A')[:20]}...")
                except:
                    print("Could not parse success response")
            else:
                print(f"Unexpected status code: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_login()
