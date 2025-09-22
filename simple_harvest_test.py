#!/usr/bin/env python3
"""
Simple test to check harvest API and products.
"""

import requests
import json

def test_harvest_api():
    # Login
    login_response = requests.post("http://127.0.0.1:8000/api/v1/auth/login", json={
        "email": "manager@tanimaju.com",
        "password": "SmallholderCoop2024!"
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check products
    products_response = requests.get("http://127.0.0.1:8000/api/v1/products", headers=headers)
    print(f"Products response: {products_response.status_code}")
    print(f"Products data: {products_response.text}")
    
    # Try simple harvest declaration
    harvest_data = {
        "product_id": "9c9b1034-a4c8-4e62-a3c4-2654007fca4d",  # FFB product ID
        "batch_number": "TEST-001",
        "quantity": 1000,
        "unit": "KGM",
        "harvest_date": "2024-01-15",
        "geographic_coordinates": {
            "latitude": 3.1390, 
            "longitude": 101.6869,
            "accuracy_meters": 5
        },
        "farm_information": {
            "farm_id": "FARM-001", 
            "farm_name": "Test Farm",
            "plantation_type": "smallholder",
            "cultivation_methods": ["organic"]
        },
        "quality_parameters": {
            "oil_content": 22.5,
            "moisture_content": 25.0
        },
        "certifications": ["RSPO"]
    }
    
    harvest_response = requests.post("http://127.0.0.1:8000/api/harvest/declare", 
                                   json=harvest_data, headers=headers)
    print(f"Harvest response: {harvest_response.status_code}")
    print(f"Harvest data: {harvest_response.text}")

if __name__ == "__main__":
    test_harvest_api()
