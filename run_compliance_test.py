#!/usr/bin/env python3
"""
Quick runner for the compliance test scenario.
Run this from the project root directory.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append('app')

from app.scripts.create_compliance_test_scenario import main

if __name__ == "__main__":
    print("🌱 Running Compliance Engine End-to-End Test Scenario")
    print("This will create a complete supply chain with compliance data for testing.")
    print()
    
    try:
        result = asyncio.run(main())
        print("\n✅ Test scenario created successfully!")
        print("You can now test the compliance engine with realistic data.")
        
    except Exception as e:
        print(f"\n❌ Failed to create test scenario: {str(e)}")
        sys.exit(1)
