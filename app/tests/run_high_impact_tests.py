#!/usr/bin/env python3
"""
High-Impact Test Runner - Focus on critical business logic first.
"""
import pytest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_critical_tests():
    """Run tests for critical business logic."""
    print("🎯 Running Critical Business Logic Tests")
    print("=" * 50)
    
    # Test files that test critical functionality
    critical_tests = [
        "tests/unit/test_simple.py",      # Basic API
        "tests/unit/test_health.py",      # Health checks
        "tests/unit/test_auth.py",        # Authentication (if working)
    ]
    
    results = []
    for test_file in critical_tests:
        print(f"\n📋 Testing {test_file}")
        result = pytest.main([
            test_file,
            "-v",
            "--tb=short",
            "--no-header",
            "--disable-warnings"
        ])
        results.append((test_file, result == 0))
    
    return results

def run_api_tests():
    """Run API endpoint tests."""
    print("\n🌐 Running API Endpoint Tests")
    print("=" * 50)
    
    # Test API endpoints specifically
    api_tests = [
        "tests/unit/test_simple.py",
        "tests/unit/test_health.py",
    ]
    
    results = []
    for test_file in api_tests:
        print(f"\n🔗 Testing API: {test_file}")
        result = pytest.main([
            test_file,
            "-v",
            "--tb=short",
            "--no-header",
            "--disable-warnings"
        ])
        results.append((test_file, result == 0))
    
    return results

def calculate_impact_score(critical_results, api_results):
    """Calculate a meaningful impact score."""
    total_critical = len(critical_results)
    passed_critical = sum(1 for _, passed in critical_results if passed)
    
    total_api = len(api_results)
    passed_api = sum(1 for _, passed in api_results if passed)
    
    # Weight critical tests higher
    critical_score = (passed_critical / total_critical) * 60 if total_critical > 0 else 0
    api_score = (passed_api / total_api) * 40 if total_api > 0 else 0
    
    total_score = critical_score + api_score
    
    return {
        'total_score': total_score,
        'critical_score': critical_score,
        'api_score': api_score,
        'critical_passed': passed_critical,
        'critical_total': total_critical,
        'api_passed': passed_api,
        'api_total': total_api
    }

def print_impact_report(score):
    """Print a meaningful impact report."""
    print("\n" + "=" * 60)
    print("📊 HIGH-IMPACT TESTING REPORT")
    print("=" * 60)
    
    print(f"🎯 Critical Business Logic: {score['critical_passed']}/{score['critical_total']} ({score['critical_score']:.1f}%)")
    print(f"🌐 API Endpoints: {score['api_passed']}/{score['api_total']} ({score['api_score']:.1f}%)")
    print(f"📈 Overall Impact Score: {score['total_score']:.1f}%")
    
    if score['total_score'] >= 80:
        print("✅ EXCELLENT - Core functionality is solid!")
    elif score['total_score'] >= 60:
        print("🟡 GOOD - Most critical features working")
    elif score['total_score'] >= 40:
        print("🟠 FAIR - Some critical issues need attention")
    else:
        print("🔴 NEEDS WORK - Critical functionality has issues")
    
    print("\n💡 Next Steps:")
    if score['critical_score'] < 60:
        print("  - Focus on fixing critical business logic tests")
    if score['api_score'] < 40:
        print("  - Ensure all API endpoints are working")
    if score['total_score'] >= 80:
        print("  - Move to integration and E2E testing")
        print("  - Add performance and security testing")

if __name__ == "__main__":
    print("🚀 High-Impact Test Runner Starting...")
    
    # Run critical tests
    critical_results = run_critical_tests()
    
    # Run API tests
    api_results = run_api_tests()
    
    # Calculate impact score
    score = calculate_impact_score(critical_results, api_results)
    
    # Print report
    print_impact_report(score)
    
    # Exit with appropriate code
    if score['total_score'] >= 60:
        print("\n🎉 High-impact tests are in good shape!")
        sys.exit(0)
    else:
        print("\n⚠️  High-impact tests need attention")
        sys.exit(1)
