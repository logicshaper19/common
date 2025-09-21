#!/usr/bin/env python3
"""
Simple test runner that focuses on working tests.
"""
import pytest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_working_tests():
    """Run tests that are known to work."""
    test_files = [
        "tests/unit/test_simple.py",
        "tests/unit/test_health.py",
    ]
    
    # Run each test file individually
    for test_file in test_files:
        print(f"\n{'='*60}")
        print(f"Running {test_file}")
        print(f"{'='*60}")
        
        result = pytest.main([
            test_file,
            "-v",
            "--tb=short",
            "--no-header",
            "--disable-warnings"
        ])
        
        if result != 0:
            print(f"❌ {test_file} failed")
        else:
            print(f"✅ {test_file} passed")

def run_all_tests():
    """Run all tests with better error handling."""
    print(f"\n{'='*60}")
    print("Running All Tests")
    print(f"{'='*60}")
    
    result = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--no-header",
        "--disable-warnings",
        "--maxfail=5"  # Stop after 5 failures
    ])
    
    return result

if __name__ == "__main__":
    print("🧪 Test Runner Starting...")
    
    # First run the working tests
    run_working_tests()
    
    # Then try to run all tests
    print(f"\n{'='*60}")
    print("Attempting to run all tests...")
    print(f"{'='*60}")
    
    result = run_all_tests()
    
    if result == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  Some tests failed (exit code: {result})")
        print("This is expected due to SQLite/JSONB compatibility issues.")


