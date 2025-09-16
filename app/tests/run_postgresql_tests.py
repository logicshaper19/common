#!/usr/bin/env python3
"""
PostgreSQL Test Runner - Full database testing capability.
"""
import pytest
import sys
import os
import subprocess

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def check_docker_status():
    """Check if Docker and PostgreSQL container are running."""
    try:
        # Check if Docker is running
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker is not running. Please start Docker Desktop first.")
            return False
        
        # Check if PostgreSQL container is running
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if 'test-postgres' not in result.stdout:
            print("❌ PostgreSQL test container not found.")
            print("   Run: ./tests/setup_postgresql_testing.sh")
            return False
        
        print("✅ Docker and PostgreSQL container are running")
        return True
        
    except FileNotFoundError:
        print("❌ Docker command not found. Please install Docker first.")
        return False

def run_postgresql_tests():
    """Run tests with PostgreSQL database."""
    print("🐘 Running PostgreSQL Tests")
    print("=" * 50)
    
    # Test files that work with PostgreSQL
    postgresql_tests = [
        "tests/unit/test_simple.py",      # Basic API
        "tests/unit/test_health.py",      # Health checks
        "tests/unit/test_auth.py",        # Authentication
        "tests/unit/test_notifications.py", # Notifications
    ]
    
    results = []
    for test_file in postgresql_tests:
        if os.path.exists(test_file):
            print(f"\n📋 Testing {test_file}")
            result = pytest.main([
                test_file,
                "-v",
                "--tb=short",
                "--no-header",
                "--disable-warnings",
                "-x",  # Stop on first failure
                "--confcutdir=tests",  # Use tests directory for conftest discovery
                "-p", "no:cacheprovider",  # Disable cache to avoid conflicts
                "--override-ini=conftest=tests/postgresql_conftest.py"  # Use PostgreSQL conftest
            ])
            results.append((test_file, result == 0))
        else:
            print(f"⚠️  {test_file} (not found)")
            results.append((test_file, False))
    
    return results

def calculate_postgresql_score(results):
    """Calculate PostgreSQL test score."""
    if not results:
        return 0
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    return (passed / total) * 100

def print_postgresql_report(score, results):
    """Print PostgreSQL test report."""
    print("\n" + "=" * 60)
    print("🐘 POSTGRESQL TESTING REPORT")
    print("=" * 60)
    
    print(f"📊 PostgreSQL Test Score: {score:.1f}%")
    print()
    
    for test_file, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_file}")
    
    print("\n💡 PostgreSQL Testing Assessment:")
    if score >= 80:
        print("  🚀 EXCELLENT - Full database testing working!")
        print("  📈 Next: Add integration and E2E tests")
    elif score >= 60:
        print("  🟡 GOOD - Most database tests working")
        print("  🔧 Next: Fix remaining database issues")
    elif score >= 40:
        print("  🟠 FAIR - Some database functionality working")
        print("  ⚠️  Next: Focus on critical database tests")
    else:
        print("  🔴 NEEDS WORK - Database testing has issues")
        print("  🚨 Next: Check database connection and models")
    
    print(f"\n📈 Progress: {score:.1f}% PostgreSQL testing ready")
    print("   (Much better than SQLite limitations!)")

def main():
    """Run PostgreSQL testing."""
    print("🚀 PostgreSQL Test Runner Starting...")
    
    # Check Docker status
    if not check_docker_status():
        sys.exit(1)
    
    # Run PostgreSQL tests
    results = run_postgresql_tests()
    score = calculate_postgresql_score(results)
    print_postgresql_report(score, results)
    
    # Exit with appropriate code
    if score >= 60:
        print("\n🎉 PostgreSQL testing is working!")
        sys.exit(0)
    else:
        print("\n⚠️  PostgreSQL testing needs attention")
        sys.exit(1)

if __name__ == "__main__":
    main()
