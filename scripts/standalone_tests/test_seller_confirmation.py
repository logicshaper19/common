#!/usr/bin/env python3
"""
Test script for seller confirmation functionality.
"""
import asyncio
import requests
import json
from datetime import datetime, date

# API base URL
BASE_URL = "http://localhost:8000"

def login_user(email: str, password: str = "testpassword123"):
    """Login and get access token."""
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": email,
        "password": password
    })
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed for {email}: {response.text}")
        return None

def get_purchase_orders(token: str):
    """Get purchase orders for the logged-in user."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/purchase-orders", headers=headers)
    
    if response.status_code == 200:
        return response.json()["purchase_orders"]
    else:
        print(f"Failed to get purchase orders: {response.text}")
        return []

def seller_confirm_po(token: str, po_id: str, confirmation_data: dict):
    """Confirm a purchase order as seller."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/purchase-orders/{po_id}/seller-confirm",
        headers=headers,
        json=confirmation_data
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to confirm PO: {response.status_code} - {response.text}")
        return None

def main():
    print("🧪 Testing Seller Confirmation Functionality")
    print("=" * 50)
    
    # Test with our created test users
    test_users = [
        "maria.santos-20250907214322@greenvalley.com",  # Plantation (Tier 5)
        "ahmad.rahman-20250907214322@sustainablemill.com",  # Mill (Tier 4)
        "priya.sharma-20250907214322@searefinery.com",  # Refinery (Tier 3)
        "michael.chen-20250907214322@palmtrading.com",  # Trader (Tier 2)
    ]
    
    for user_email in test_users:
        print(f"\n👤 Testing with user: {user_email}")
        
        # Login
        token = login_user(user_email)
        if not token:
            continue
            
        # Get purchase orders
        pos = get_purchase_orders(token)
        print(f"   Found {len(pos)} purchase orders")
        
        # Find POs where this user's company is the seller
        seller_pos = [po for po in pos if po.get('status') in ['pending', 'confirmed']]
        
        if seller_pos:
            po = seller_pos[0]  # Take the first one
            print(f"   📋 Testing confirmation for PO: {po['po_number']}")
            print(f"      Original quantity: {po['quantity']} {po.get('unit', 'units')}")
            print(f"      Original price: ${po['unit_price']}")
            
            # Create confirmation data (seller confirms 95% of quantity)
            confirmed_quantity = float(po['quantity']) * 0.95
            confirmation_data = {
                "confirmed_quantity": confirmed_quantity,
                "confirmed_unit_price": float(po['unit_price']) + 5.00,  # Slight price increase
                "confirmed_delivery_date": "2025-10-15",  # Later delivery
                "confirmed_delivery_location": po['delivery_location'] + " - Warehouse B",
                "seller_notes": f"Can confirm {confirmed_quantity:.1f} units. Delivery delayed by 1 week due to quality checks. Price adjusted for premium quality."
            }
            
            # Attempt confirmation
            result = seller_confirm_po(token, po['id'], confirmation_data)
            
            if result:
                print(f"   ✅ Successfully confirmed PO!")
                print(f"      Confirmed quantity: {result.get('confirmed_quantity')} {result.get('unit', 'units')}")
                print(f"      Confirmed price: ${result.get('confirmed_unit_price')}")
                print(f"      Status: {result.get('status')}")
                print(f"      Seller notes: {result.get('seller_notes', 'None')[:100]}...")
            else:
                print(f"   ❌ Failed to confirm PO")
        else:
            print(f"   ℹ️  No pending POs found for this seller")
    
    print(f"\n🎯 Seller confirmation testing complete!")

if __name__ == "__main__":
    main()
