#!/usr/bin/env python3
"""
Script to test the transparency API endpoints.
"""
import requests
import json

def test_transparency_api():
    """Test the transparency API endpoints."""
    
    base_url = "http://localhost:8000"
    
    # First, login as the admin user (we know this works)
    login_data = {
        "email": "elisha@common.co",
        "password": "password123"  # Default test password
    }

    print("Logging in as admin user...")
    login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token_data = login_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        print("No access token received")
        return
    
    print(f"Login successful! Token: {access_token[:20]}...")
    
    # Set up headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get user info and use L'Oreal company ID for testing
    user_response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
    if user_response.status_code == 200:
        user_data = user_response.json()
        print(f"Logged in as: {user_data.get('email')} (company: {user_data.get('company_id')})")
        # Use L'Oreal company ID for testing transparency (from PostgreSQL)
        company_id = "9ab08879-3f9b-487f-97ca-f89309c5e665"  # L'Oreal Group company ID
        print(f"Testing transparency for L'Oreal company ID: {company_id}")
    else:
        print("Failed to get user info")
        return
    
    # Test transparency metrics endpoint
    print("\n--- Testing Transparency Metrics ---")
    metrics_response = requests.get(f"{base_url}/api/v1/transparency/{company_id}", headers=headers)
    
    if metrics_response.status_code == 200:
        metrics = metrics_response.json()
        print("Transparency metrics:")
        print(json.dumps(metrics, indent=2))
    else:
        print(f"Failed to get transparency metrics: {metrics_response.status_code}")
        print(metrics_response.text)
    
    # Test supply chain visualization endpoint
    print("\n--- Testing Supply Chain Visualization ---")
    viz_response = requests.get(f"{base_url}/api/v1/transparency/po/po-001", headers=headers)
    
    if viz_response.status_code == 200:
        viz_data = viz_response.json()
        print("Supply chain visualization:")
        print(json.dumps(viz_data, indent=2))
    else:
        print(f"Failed to get supply chain visualization: {viz_response.status_code}")
        print(viz_response.text)
    
    # Test gap analysis endpoint
    print("\n--- Testing Gap Analysis ---")
    gaps_response = requests.get(f"{base_url}/api/v1/transparency/{company_id}/gaps", headers=headers)
    
    if gaps_response.status_code == 200:
        gaps = gaps_response.json()
        print("Gap analysis:")
        print(json.dumps(gaps, indent=2))
    else:
        print(f"Failed to get gap analysis: {gaps_response.status_code}")
        print(gaps_response.text)
    
    # Test recalculate endpoint
    print("\n--- Testing Recalculate Transparency ---")
    recalc_data = {"company_id": company_id}
    recalc_response = requests.post(f"{base_url}/api/v1/transparency/recalculate", 
                                   headers=headers, json=recalc_data)
    
    if recalc_response.status_code == 200:
        recalc_result = recalc_response.json()
        print("Recalculation result:")
        print(json.dumps(recalc_result, indent=2))
    else:
        print(f"Failed to recalculate transparency: {recalc_response.status_code}")
        print(recalc_response.text)

if __name__ == "__main__":
    test_transparency_api()
