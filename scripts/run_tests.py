#!/usr/bin/env python3
"""
Comprehensive test runner for the Common supply chain platform.
"""
import os
import sys
import subprocess
import argparse
import time
from typing import List, Dict, Any
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """Comprehensive test runner with different test categories."""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "app" / "tests"
        self.results = {}
    
    def run_unit_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "unit",
            "--tb=short",
            "--durations=10"
        ]
        
        if verbose:
            cmd.append("-v")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "category": "unit",
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "-m", "integration",
            "--tb=short",
            "--durations=10"
        ]
        
        if verbose:
            cmd.append("-v")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "category": "integration",
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_e2e_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run end-to-end tests."""
        print("🎯 Running End-to-End Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "test_end_to_end.py"),
            "--tb=short",
            "--durations=10"
        ]
        
        if verbose:
            cmd.append("-v")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "category": "e2e",
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_load_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run load tests."""
        print("⚡ Running Load Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "test_load_testing.py"),
            "--tb=short",
            "--durations=10",
            "-x"  # Stop on first failure for load tests
        ]
        
        if verbose:
            cmd.append("-v")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "category": "load",
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_performance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run performance tests."""
        print("🚀 Running Performance Tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "test_performance.py"),
            "--tb=short",
            "--durations=10"
        ]
        
        if verbose:
            cmd.append("-v")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "category": "performance",
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> Dict[str, Any]:
        """Run a specific test file or test function."""
        print(f"🎯 Running Specific Test: {test_path}")
        
        cmd = [
            "python", "-m", "pytest",
            test_path,
            "--tb=short",
            "--durations=10"
        ]
        
        if verbose:
            cmd.append("-v")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "category": "specific",
            "test_path": test_path,
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_coverage_report(self) -> Dict[str, Any]:
        """Run tests with coverage report."""
        print("📊 Running Tests with Coverage...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        duration = time.time() - start_time
        
        return {
            "category": "coverage",
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_all_tests(self, verbose: bool = False, include_load: bool = False) -> List[Dict[str, Any]]:
        """Run all test categories."""
        print("🚀 Running All Tests...")
        
        results = []
        
        # Run unit tests
        results.append(self.run_unit_tests(verbose))
        
        # Run integration tests
        results.append(self.run_integration_tests(verbose))
        
        # Run e2e tests
        results.append(self.run_e2e_tests(verbose))
        
        # Run performance tests
        results.append(self.run_performance_tests(verbose))
        
        # Optionally run load tests (can be resource intensive)
        if include_load:
            results.append(self.run_load_tests(verbose))
        
        return results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print test results summary."""
        print("\n" + "="*60)
        print("📋 TEST RESULTS SUMMARY")
        print("="*60)
        
        total_duration = 0
        total_success = 0
        total_tests = len(results)
        
        for result in results:
            category = result["category"]
            duration = result["duration"]
            success = result["success"]
            
            total_duration += duration
            if success:
                total_success += 1
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{category.upper():15} | {status} | {duration:.2f}s")
            
            if not success and result.get("stderr"):
                print(f"                Error: {result['stderr'][:100]}...")
        
        print("-" * 60)
        print(f"TOTAL:          | {total_success}/{total_tests} | {total_duration:.2f}s")
        
        if total_success == total_tests:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total_tests - total_success} test category(s) failed")
        
        return total_success == total_tests
    
    def setup_test_environment(self):
        """Setup test environment."""
        print("🔧 Setting up test environment...")
        
        # Set test environment variables
        os.environ["TESTING"] = "true"
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        os.environ["REDIS_URL"] = "redis://localhost:6379/1"
        
        # Create test directories if they don't exist
        (self.project_root / "htmlcov").mkdir(exist_ok=True)
        (self.project_root / "test-reports").mkdir(exist_ok=True)
        
        print("✅ Test environment ready")
    
    def cleanup_test_environment(self):
        """Cleanup test environment."""
        print("🧹 Cleaning up test environment...")
        
        # Remove test database files
        test_db_files = [
            "test.db",
            "test_comprehensive.db",
            "test_performance.db"
        ]
        
        for db_file in test_db_files:
            db_path = self.project_root / db_file
            if db_path.exists():
                db_path.unlink()
        
        print("✅ Test environment cleaned")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run Common platform tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=["unit", "integration", "e2e", "load", "performance", "all", "coverage"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--include-load",
        action="store_true",
        help="Include load tests in 'all' run"
    )
    parser.add_argument(
        "--test-path",
        help="Specific test file or function to run"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip cleanup after tests"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    try:
        # Setup test environment
        runner.setup_test_environment()
        
        # Run tests based on type
        if args.test_path:
            results = [runner.run_specific_test(args.test_path, args.verbose)]
        elif args.test_type == "unit":
            results = [runner.run_unit_tests(args.verbose)]
        elif args.test_type == "integration":
            results = [runner.run_integration_tests(args.verbose)]
        elif args.test_type == "e2e":
            results = [runner.run_e2e_tests(args.verbose)]
        elif args.test_type == "load":
            results = [runner.run_load_tests(args.verbose)]
        elif args.test_type == "performance":
            results = [runner.run_performance_tests(args.verbose)]
        elif args.test_type == "coverage":
            results = [runner.run_coverage_report()]
        elif args.test_type == "all":
            results = runner.run_all_tests(args.verbose, args.include_load)
        
        # Print summary
        all_passed = runner.print_summary(results)
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)
    
    finally:
        # Cleanup unless explicitly disabled
        if not args.no_cleanup:
            runner.cleanup_test_environment()


if __name__ == "__main__":
    main()
