#!/usr/bin/env python3
"""
Enhanced Comprehensive System Test Runner

This script runs the enhanced comprehensive system tests with all improvements:
- Configurable environments
- Retry mechanisms
- Security testing
- Visual regression testing
- Detailed reporting
- Parallel execution support
"""
import subprocess
import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path


def setup_environment(environment: str):
    """Set up environment variables for testing."""
    env_configs = {
        "development": {
            "TEST_ENVIRONMENT": "development",
            "TEST_BASE_URL": "http://localhost:3000",
            "TEST_API_URL": "http://localhost:8000/api/v1",
            "TEST_HEADLESS": "false",
            "TEST_SECURITY": "false",
            "TEST_VISUAL": "false"
        },
        "staging": {
            "TEST_ENVIRONMENT": "staging",
            "TEST_BASE_URL": "https://staging.common-platform.com",
            "TEST_API_URL": "https://api-staging.common-platform.com/api/v1",
            "TEST_HEADLESS": "true",
            "TEST_SECURITY": "true",
            "TEST_VISUAL": "true",
            "TEST_MAX_API_TIME": "3.0"
        },
        "production": {
            "TEST_ENVIRONMENT": "production",
            "TEST_BASE_URL": "https://common-platform.com",
            "TEST_API_URL": "https://api.common-platform.com/api/v1",
            "TEST_HEADLESS": "true",
            "TEST_SECURITY": "true",
            "TEST_VISUAL": "true",
            "TEST_MAX_API_TIME": "1.5",
            "TEST_BROWSERS": "chrome,firefox,safari,edge"
        }
    }
    
    config = env_configs.get(environment, env_configs["development"])
    
    for key, value in config.items():
        os.environ[key] = value
    
    print(f"🔧 Environment configured for: {environment}")
    for key, value in config.items():
        print(f"   {key}={value}")


def run_system_tests(test_categories: list = None, parallel: bool = False) -> dict:
    """Run system tests with specified categories."""
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest", "tests/system/test_comprehensive_system.py", "-v"]
    
    # Add specific test categories if specified
    if test_categories:
        test_functions = []
        category_mapping = {
            "api": "test_api_endpoints_with_retry",
            "browser": "test_cross_browser_compatibility", 
            "accessibility": "test_accessibility_compliance",
            "performance": "test_performance_thresholds",
            "security": "test_security_testing",
            "visual": "test_visual_regression",
            "comprehensive": "test_enhanced_comprehensive_system_testing"
        }
        
        for category in test_categories:
            if category in category_mapping:
                test_functions.append(f"tests/system/test_comprehensive_system.py::{category_mapping[category]}")
        
        if test_functions:
            cmd = [sys.executable, "-m", "pytest"] + test_functions + ["-v"]
    
    # Add parallel execution if requested
    if parallel:
        cmd.extend(["-n", "auto"])  # Requires pytest-xdist
    
    # Add JSON reporting
    cmd.extend(["--json-report", "--json-report-file=system_test_report.json"])
    
    # Add coverage if available
    try:
        import pytest_cov
        cmd.extend(["--cov=app", "--cov-report=html:htmlcov_system"])
    except ImportError:
        pass
    
    print(f"🧪 Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        # Load JSON report if available
        json_report = {}
        try:
            with open("system_test_report.json", "r") as f:
                json_report = json.load(f)
        except FileNotFoundError:
            pass
        
        return {
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "json_report": json_report
        }
        
    except subprocess.TimeoutExpired:
        return {
            "return_code": -1,
            "error": "Test execution timed out after 30 minutes",
            "json_report": {}
        }
    except Exception as e:
        return {
            "return_code": -1,
            "error": str(e),
            "json_report": {}
        }


def generate_comprehensive_report(results: dict, environment: str) -> dict:
    """Generate comprehensive test report."""
    
    timestamp = datetime.now().isoformat()
    
    report = {
        "timestamp": timestamp,
        "environment": environment,
        "test_execution": {
            "return_code": results["return_code"],
            "status": "PASS" if results["return_code"] == 0 else "FAIL",
            "stdout_lines": len(results.get("stdout", "").split("\n")),
            "stderr_lines": len(results.get("stderr", "").split("\n"))
        },
        "test_results": results.get("json_report", {}),
        "recommendations": []
    }
    
    # Analyze results and add recommendations
    if results["return_code"] != 0:
        report["recommendations"].append("❌ Tests failed - check detailed output for specific issues")
        
        if "security" in results.get("stderr", "").lower():
            report["recommendations"].append("🔒 Security vulnerabilities detected - review security test results")
        
        if "timeout" in results.get("stderr", "").lower():
            report["recommendations"].append("⏱️ Performance issues detected - check API response times")
        
        if "webdriver" in results.get("stderr", "").lower():
            report["recommendations"].append("🌐 Browser compatibility issues - check WebDriver setup")
    
    else:
        report["recommendations"].append("✅ All tests passed successfully")
        report["recommendations"].append("📊 Review detailed metrics for optimization opportunities")
    
    # Add environment-specific recommendations
    if environment == "production":
        report["recommendations"].append("🚀 Production testing complete - monitor for any performance degradation")
    elif environment == "staging":
        report["recommendations"].append("🔄 Staging validation complete - ready for production deployment")
    else:
        report["recommendations"].append("🛠️ Development testing complete - consider running staging tests before deployment")
    
    return report


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Enhanced Comprehensive System Test Runner")
    parser.add_argument("--environment", "-e", choices=["development", "staging", "production"], 
                       default="development", help="Test environment")
    parser.add_argument("--categories", "-c", nargs="+", 
                       choices=["api", "browser", "accessibility", "performance", "security", "visual", "comprehensive"],
                       help="Specific test categories to run")
    parser.add_argument("--parallel", "-p", action="store_true", help="Run tests in parallel")
    parser.add_argument("--update-baselines", action="store_true", help="Update visual regression baselines")
    
    args = parser.parse_args()
    
    print("🚀 Enhanced Comprehensive System Test Runner")
    print("=" * 60)
    
    # Set up environment
    setup_environment(args.environment)
    
    # Update visual baselines if requested
    if args.update_baselines:
        print("\n🔄 Updating visual regression baselines...")
        from tests.system.visual_regression import VisualRegressionTester
        from tests.system.config import EnvironmentConfig
        
        config = EnvironmentConfig.get_config(args.environment)
        visual_tester = VisualRegressionTester(config)
        visual_tester.update_baselines()
        return
    
    # Run tests
    print(f"\n🧪 Running System Tests for {args.environment} environment...")
    if args.categories:
        print(f"📋 Test Categories: {', '.join(args.categories)}")
    if args.parallel:
        print("⚡ Parallel execution enabled")
    
    results = run_system_tests(args.categories, args.parallel)
    
    # Generate report
    report = generate_comprehensive_report(results, args.environment)
    
    # Print summary
    print(f"\n📊 SYSTEM TEST SUMMARY")
    print("=" * 40)
    print(f"Environment: {args.environment}")
    print(f"Status: {report['test_execution']['status']}")
    print(f"Return Code: {report['test_execution']['return_code']}")
    
    if report["recommendations"]:
        print(f"\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"comprehensive_system_test_report_{args.environment}_{timestamp}.json"
    
    os.makedirs("test_reports", exist_ok=True)
    report_path = os.path.join("test_reports", report_filename)
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Print test output if failed
    if results["return_code"] != 0:
        print(f"\n❌ TEST OUTPUT:")
        print("-" * 40)
        print(results.get("stdout", ""))
        if results.get("stderr"):
            print("\nERRORS:")
            print(results["stderr"])
    
    # Exit with test result code
    sys.exit(results["return_code"])


if __name__ == "__main__":
    main()