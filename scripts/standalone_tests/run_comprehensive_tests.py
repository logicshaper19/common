#!/usr/bin/env python3
"""
Comprehensive test runner for the Common Supply Chain Platform.

This script runs all test suites with proper configuration and reporting.
"""
import os
import sys
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path


def run_command(command, capture_output=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {command}")
        return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def setup_test_environment():
    """Set up the test environment."""
    print("Setting up test environment...")
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///./test_comprehensive.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    
    # Create test directories
    test_dirs = ["test_reports", "test_coverage", "test_logs"]
    for dir_name in test_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    print("Test environment setup complete.")


def run_unit_tests():
    """Run unit tests."""
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    unit_test_files = [
        "app/tests/test_auth.py",
        "app/tests/test_products.py",
        "app/tests/test_purchase_orders.py",
        "app/tests/test_business_relationships.py",
        "app/tests/test_compliance_service.py",
        "app/tests/test_data_access_control.py"
    ]
    
    results = []
    for test_file in unit_test_files:
        if os.path.exists(test_file):
            print(f"\nRunning {test_file}...")
            command = f"python -m pytest {test_file} -v --tb=short --cov=app --cov-report=term-missing"
            result = run_command(command)
            if result:
                results.append({
                    "file": test_file,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                else:
                    print(f"❌ {test_file} - FAILED")
            else:
                print(f"⚠️  {test_file} - ERROR")
                results.append({
                    "file": test_file,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "Command timed out or failed"
                })
    
    return results


def run_integration_tests():
    """Run integration tests."""
    print("\n" + "="*60)
    print("RUNNING INTEGRATION TESTS")
    print("="*60)
    
    integration_test_files = [
        "app/tests/test_purchase_orders_comprehensive.py",
        "app/tests/test_company_management.py",
        "app/tests/test_products_catalog.py",
        "app/tests/test_integration_workflows.py"
    ]
    
    results = []
    for test_file in integration_test_files:
        if os.path.exists(test_file):
            print(f"\nRunning {test_file}...")
            command = f"python -m pytest {test_file} -v --tb=short --cov=app --cov-report=term-missing"
            result = run_command(command)
            if result:
                results.append({
                    "file": test_file,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                else:
                    print(f"❌ {test_file} - FAILED")
            else:
                print(f"⚠️  {test_file} - ERROR")
                results.append({
                    "file": test_file,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "Command timed out or failed"
                })
    
    return results


def run_security_tests():
    """Run security tests."""
    print("\n" + "="*60)
    print("RUNNING SECURITY TESTS")
    print("="*60)
    
    security_test_files = [
        "app/tests/test_security_comprehensive.py",
        "app/tests/test_auth.py"  # Auth tests include security
    ]
    
    results = []
    for test_file in security_test_files:
        if os.path.exists(test_file):
            print(f"\nRunning {test_file}...")
            command = f"python -m pytest {test_file} -v --tb=short --cov=app --cov-report=term-missing"
            result = run_command(command)
            if result:
                results.append({
                    "file": test_file,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                else:
                    print(f"❌ {test_file} - FAILED")
            else:
                print(f"⚠️  {test_file} - ERROR")
                results.append({
                    "file": test_file,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "Command timed out or failed"
                })
    
    return results


def run_performance_tests():
    """Run performance tests."""
    print("\n" + "="*60)
    print("RUNNING PERFORMANCE TESTS")
    print("="*60)
    
    performance_test_files = [
        "app/tests/test_performance.py",
        "app/tests/test_load_testing.py"
    ]
    
    results = []
    for test_file in performance_test_files:
        if os.path.exists(test_file):
            print(f"\nRunning {test_file}...")
            command = f"python -m pytest {test_file} -v --tb=short -m slow"
            result = run_command(command)
            if result:
                results.append({
                    "file": test_file,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                else:
                    print(f"❌ {test_file} - FAILED")
            else:
                print(f"⚠️  {test_file} - ERROR")
                results.append({
                    "file": test_file,
                    "returncode": -1,
                    "stdout": "",
                    "stderr": "Command timed out or failed"
                })
    
    return results


def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*60)
    print("RUNNING ALL TESTS")
    print("="*60)
    
    command = "python -m pytest app/tests/ -v --tb=short --cov=app --cov-report=html --cov-report=term-missing"
    result = run_command(command)
    
    if result:
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    else:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "Command timed out or failed"
        }


def generate_test_report(all_results):
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("GENERATING TEST REPORT")
    print("="*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_suites": {},
        "summary": {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0
        }
    }
    
    for suite_name, results in all_results.items():
        if isinstance(results, list):
            suite_summary = {
                "total_files": len(results),
                "passed_files": 0,
                "failed_files": 0,
                "error_files": 0
            }
            
            for result in results:
                if result["returncode"] == 0:
                    suite_summary["passed_files"] += 1
                elif result["returncode"] == -1:
                    suite_summary["error_files"] += 1
                else:
                    suite_summary["failed_files"] += 1
            
            report["test_suites"][suite_name] = {
                "summary": suite_summary,
                "details": results
            }
            
            report["summary"]["total_tests"] += suite_summary["total_files"]
            report["summary"]["passed"] += suite_summary["passed_files"]
            report["summary"]["failed"] += suite_summary["failed_files"]
            report["summary"]["errors"] += suite_summary["error_files"]
        else:
            # Single result
            report["test_suites"][suite_name] = {
                "summary": {
                    "total_files": 1,
                    "passed_files": 1 if results["returncode"] == 0 else 0,
                    "failed_files": 0 if results["returncode"] == 0 else 1,
                    "error_files": 0
                },
                "details": [results]
            }
            
            report["summary"]["total_tests"] += 1
            if results["returncode"] == 0:
                report["summary"]["passed"] += 1
            elif results["returncode"] == -1:
                report["summary"]["errors"] += 1
            else:
                report["summary"]["failed"] += 1
    
    # Save report
    report_file = f"test_reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Test report saved to: {report_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total test files: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Errors: {report['summary']['errors']}")
    
    success_rate = (report['summary']['passed'] / report['summary']['total_tests']) * 100 if report['summary']['total_tests'] > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    return report


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for Common Supply Chain Platform")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--security", action="store_true", help="Run security tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all
    if not any([args.unit, args.integration, args.security, args.performance]):
        args.all = True
    
    print("Common Supply Chain Platform - Comprehensive Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup test environment
    setup_test_environment()
    
    all_results = {}
    
    try:
        if args.unit or args.all:
            all_results["unit_tests"] = run_unit_tests()
        
        if args.integration or args.all:
            all_results["integration_tests"] = run_integration_tests()
        
        if args.security or args.all:
            all_results["security_tests"] = run_security_tests()
        
        if args.performance or args.all:
            all_results["performance_tests"] = run_performance_tests()
        
        # Generate report
        if args.report or args.all:
            report = generate_test_report(all_results)
            
            # Check if all tests passed
            if report["summary"]["failed"] == 0 and report["summary"]["errors"] == 0:
                print("\n🎉 All tests passed!")
                return 0
            else:
                print(f"\n❌ {report['summary']['failed']} tests failed, {report['summary']['errors']} errors")
                return 1
        else:
            return 0
            
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
