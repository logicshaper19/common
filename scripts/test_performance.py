#!/usr/bin/env python3
"""
Test Performance Optimization Script

This script provides utilities for optimizing test suite performance,
including parallel execution, test categorization, and performance analysis.
"""

import subprocess
import time
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import concurrent.futures
from dataclasses import dataclass


@dataclass
class TestResult:
    """Test execution result."""
    name: str
    duration: float
    status: str
    category: str


class TestPerformanceOptimizer:
    """Optimize test suite performance."""
    
    def __init__(self, test_dir: str = "app/tests"):
        self.test_dir = Path(test_dir)
        self.results: List[TestResult] = []
    
    def run_test_category(self, category: str, parallel: bool = True) -> Dict:
        """Run tests for a specific category."""
        print(f"\n🚀 Running {category} tests...")
        
        start_time = time.time()
        
        if parallel and category == "unit":
            # Run unit tests in parallel for speed
            cmd = [
                "python", "-m", "pytest", 
                f"-m", category,
                "-n", "auto",  # pytest-xdist for parallel execution
                "--tb=short",
                "-v"
            ]
        else:
            # Run integration/e2e tests sequentially for stability
            cmd = [
                "python", "-m", "pytest", 
                f"-m", category,
                "--tb=short",
                "-v"
            ]
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "category": category,
                "duration": duration,
                "status": "passed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr,
                "test_count": self._count_tests_in_output(result.stdout)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "category": category,
                "duration": 300,
                "status": "timeout",
                "output": "",
                "errors": "Test execution timed out",
                "test_count": 0
            }
    
    def _count_tests_in_output(self, output: str) -> int:
        """Count number of tests from pytest output."""
        lines = output.split('\n')
        for line in lines:
            if "passed" in line or "failed" in line:
                # Look for pattern like "5 passed, 2 failed"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit() and i + 1 < len(parts):
                        if parts[i + 1] in ["passed", "failed", "skipped"]:
                            return int(part)
        return 0
    
    def run_performance_analysis(self) -> Dict:
        """Run comprehensive performance analysis."""
        print("🔍 Starting Test Performance Analysis...")
        
        categories = ["unit", "integration", "auth", "api"]
        results = {}
        
        total_start = time.time()
        
        # Run each category and collect metrics
        for category in categories:
            result = self.run_test_category(category, parallel=(category == "unit"))
            results[category] = result
            
            # Print immediate feedback
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            print(f"{status_emoji} {category}: {result['test_count']} tests in {result['duration']:.2f}s")
        
        total_duration = time.time() - total_start
        
        # Generate summary
        summary = self._generate_performance_summary(results, total_duration)
        
        return {
            "results": results,
            "summary": summary,
            "total_duration": total_duration
        }
    
    def _generate_performance_summary(self, results: Dict, total_duration: float) -> Dict:
        """Generate performance summary and recommendations."""
        total_tests = sum(r["test_count"] for r in results.values())
        passed_categories = sum(1 for r in results.values() if r["status"] == "passed")
        
        # Calculate performance metrics
        fastest_category = min(results.items(), key=lambda x: x[1]["duration"])
        slowest_category = max(results.items(), key=lambda x: x[1]["duration"])
        
        # Performance recommendations
        recommendations = []
        
        if results.get("unit", {}).get("duration", 0) > 30:
            recommendations.append("Consider optimizing unit tests - they should run under 30 seconds")
        
        if results.get("integration", {}).get("duration", 0) > 120:
            recommendations.append("Integration tests are slow - consider mocking external dependencies")
        
        if total_tests > 0 and total_duration / total_tests > 2:
            recommendations.append("Average test time is high - review test setup and teardown")
        
        return {
            "total_tests": total_tests,
            "passed_categories": passed_categories,
            "total_categories": len(results),
            "fastest_category": fastest_category[0],
            "fastest_time": fastest_category[1]["duration"],
            "slowest_category": slowest_category[0],
            "slowest_time": slowest_category[1]["duration"],
            "average_test_time": total_duration / total_tests if total_tests > 0 else 0,
            "recommendations": recommendations
        }
    
    def run_quick_smoke_test(self) -> bool:
        """Run a quick smoke test to verify basic functionality."""
        print("💨 Running Quick Smoke Test...")
        
        # Run a subset of critical tests
        cmd = [
            "python", "-m", "pytest",
            "app/tests/unit/test_auth.py::test_user_login",
            "app/tests/unit/test_products.py::test_create_product_as_admin",
            "--tb=short",
            "-v"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            success = result.returncode == 0
            
            if success:
                print("✅ Smoke test passed - core functionality working")
            else:
                print("❌ Smoke test failed - check core functionality")
                print(result.stderr)
            
            return success
            
        except subprocess.TimeoutExpired:
            print("⏰ Smoke test timed out")
            return False
    
    def generate_performance_report(self, results: Dict) -> str:
        """Generate a detailed performance report."""
        report = []
        report.append("# Test Performance Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        summary = results["summary"]
        report.append("## Summary")
        report.append(f"- Total Tests: {summary['total_tests']}")
        report.append(f"- Total Duration: {results['total_duration']:.2f}s")
        report.append(f"- Average Test Time: {summary['average_test_time']:.2f}s")
        report.append(f"- Categories Passed: {summary['passed_categories']}/{summary['total_categories']}")
        report.append("")
        
        report.append("## Category Performance")
        for category, result in results["results"].items():
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            report.append(f"- {status_emoji} **{category}**: {result['test_count']} tests in {result['duration']:.2f}s")
        report.append("")
        
        if summary["recommendations"]:
            report.append("## Recommendations")
            for rec in summary["recommendations"]:
                report.append(f"- {rec}")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Performance Optimization")
    parser.add_argument("--smoke", action="store_true", help="Run quick smoke test")
    parser.add_argument("--analysis", action="store_true", help="Run full performance analysis")
    parser.add_argument("--category", help="Run specific test category")
    parser.add_argument("--report", help="Generate performance report to file")
    
    args = parser.parse_args()
    
    optimizer = TestPerformanceOptimizer()
    
    if args.smoke:
        success = optimizer.run_quick_smoke_test()
        exit(0 if success else 1)
    
    elif args.category:
        result = optimizer.run_test_category(args.category)
        print(f"\n📊 Results for {args.category}:")
        print(f"Tests: {result['test_count']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Status: {result['status']}")
    
    elif args.analysis:
        results = optimizer.run_performance_analysis()
        
        print("\n📊 Performance Analysis Complete!")
        print(f"Total Duration: {results['total_duration']:.2f}s")
        print(f"Total Tests: {results['summary']['total_tests']}")
        
        if args.report:
            report = optimizer.generate_performance_report(results)
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"📄 Report saved to {args.report}")
    
    else:
        print("Please specify --smoke, --analysis, or --category")
        parser.print_help()


if __name__ == "__main__":
    main()
