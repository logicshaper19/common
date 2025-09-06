#!/usr/bin/env python3
"""
Test admin login credentials.
"""
import requests
import json

def test_admin_login():
    """Test the admin login credentials."""
    
    # API endpoint (adjust if your backend runs on a different port)
    login_url = "http://localhost:8000/auth/login"
    
    # Admin credentials
    credentials = {
        "email": "admin@example.com",
        "password": "adminpassword123"
    }
    
    print("🔐 Testing admin login credentials...")
    print(f"📧 Email: {credentials['email']}")
    print(f"🌐 API URL: {login_url}")
    
    try:
        # Make login request
        response = requests.post(
            login_url,
            json=credentials,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"🎫 Access token received: {data.get('access_token', 'N/A')[:50]}...")
            print(f"👤 User info: {data.get('user', {})}")
            return True
            
        elif response.status_code == 401:
            print("❌ Login failed: Invalid credentials")
            print("💡 Make sure the backend is running and the admin user exists")
            return False
            
        elif response.status_code == 422:
            print("❌ Login failed: Invalid request format")
            print(f"📝 Response: {response.text}")
            return False
            
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"📝 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed: Backend server is not running")
        print("💡 Start the backend with: uvicorn app.main:app --reload")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timeout: Backend server is not responding")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_admin_login()
    
    if success:
        print("\n🎉 Admin credentials are working!")
        print("🚀 You can now log in to the frontend with these credentials.")
    else:
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure the backend server is running: uvicorn app.main:app --reload")
        print("2. Check if the database exists and has the admin user")
        print("3. Verify the API endpoint URL is correct")
        print("4. Check the backend logs for any errors")