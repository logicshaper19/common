#!/usr/bin/env python3
"""
E2E Test Runner for Common Supply Chain Platform

This script runs the new modular E2E tests and generates a comprehensive report.
"""
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path


def run_pytest_with_json_report(test_path: str) -> dict:
    """Run pytest and capture JSON report."""
    cmd = [
        sys.executable, "-m", "pytest", 
        test_path,
        "--json-report",
        "--json-report-file=temp_report.json",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Try to load JSON report
        try:
            with open("temp_report.json", "r") as f:
                json_report = json.load(f)
        except FileNotFoundError:
            json_report = {"summary": {"total": 0, "passed": 0, "failed": 0}}
        
        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "json_report": json_report
        }
    except Exception as e:
        return {
            "return_code": -1,
            "error": str(e),
            "json_report": {"summary": {"total": 0, "passed": 0, "failed": 0}}
        }


def main():
    """Run E2E tests and generate report."""
    print("🚀 Running Modular E2E Tests for Common Supply Chain Platform")
    print("=" * 70)
    
    # Test suites to run
    test_suites = [
        ("Individual Farmer Journey", "tests/e2e/journeys/test_farmer_journey.py"),
        ("Individual Processor Journey", "tests/e2e/journeys/test_processor_journey.py"),
        ("Individual Retailer Journey", "tests/e2e/journeys/test_retailer_journey.py"),
        ("Individual Consumer Journey", "tests/e2e/journeys/test_consumer_journey.py"),
        ("Full Supply Chain Integration", "tests/e2e/integration/test_full_supply_chain.py"),
    ]
    
    overall_results = {
        "timestamp": datetime.now().isoformat(),
        "test_suites": {},
        "summary": {
            "total_suites": len(test_suites),
            "passed_suites": 0,
            "failed_suites": 0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
    }
    
    for suite_name, test_path in test_suites:
        print(f"\n🧪 Running {suite_name}...")
        print("-" * 50)
        
        # Check if test file exists
        if not Path(test_path).exists():
            print(f"❌ Test file not found: {test_path}")
            overall_results["test_suites"][suite_name] = {
                "status": "SKIPPED",
                "reason": "Test file not found"
            }
            continue
        
        # Run the test suite
        result = run_pytest_with_json_report(test_path)
        
        # Process results
        json_report = result["json_report"]
        summary = json_report.get("summary", {})
        
        suite_result = {
            "status": "PASS" if result["return_code"] == 0 else "FAIL",
            "return_code": result["return_code"],
            "tests_total": summary.get("total", 0),
            "tests_passed": summary.get("passed", 0),
            "tests_failed": summary.get("failed", 0),
            "stdout": result["stdout"],
            "stderr": result["stderr"]
        }
        
        overall_results["test_suites"][suite_name] = suite_result
        
        # Update overall summary
        if suite_result["status"] == "PASS":
            overall_results["summary"]["passed_suites"] += 1
        else:
            overall_results["summary"]["failed_suites"] += 1
        
        overall_results["summary"]["total_tests"] += suite_result["tests_total"]
        overall_results["summary"]["passed_tests"] += suite_result["tests_passed"]
        overall_results["summary"]["failed_tests"] += suite_result["tests_failed"]
        
        # Print results
        if suite_result["status"] == "PASS":
            print(f"✅ {suite_name}: PASSED")
            print(f"   Tests: {suite_result['tests_passed']}/{suite_result['tests_total']} passed")
        else:
            print(f"❌ {suite_name}: FAILED")
            print(f"   Tests: {suite_result['tests_passed']}/{suite_result['tests_total']} passed")
            if result["stderr"]:
                print(f"   Error: {result['stderr'][:200]}...")
    
    # Generate final report
    print("\n" + "=" * 70)
    print("📊 FINAL E2E TEST REPORT")
    print("=" * 70)
    
    summary = overall_results["summary"]
    print(f"Test Suites: {summary['passed_suites']}/{summary['total_suites']} passed")
    print(f"Individual Tests: {summary['passed_tests']}/{summary['total_tests']} passed")
    
    if summary["failed_suites"] == 0:
        print("\n🎉 ALL E2E TESTS PASSED!")
        overall_status = "PASS"
    else:
        print(f"\n⚠️  {summary['failed_suites']} test suite(s) failed")
        overall_status = "FAIL"
    
    overall_results["overall_status"] = overall_status
    
    # Save detailed report
    with open("e2e_test_report.json", "w") as f:
        json.dump(overall_results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: e2e_test_report.json")
    
    # Cleanup
    try:
        Path("temp_report.json").unlink(missing_ok=True)
    except:
        pass
    
    # Exit with appropriate code
    sys.exit(0 if overall_status == "PASS" else 1)


if __name__ == "__main__":
    main()