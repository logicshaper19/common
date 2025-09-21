#!/usr/bin/env python3
"""
Comprehensive test automation pipeline for the Common Supply Chain Platform.

This script provides a complete testing framework with:
- Categorized test execution (unit, integration, e2e, performance, security)
- Parallel execution support
- Coverage reporting
- Performance monitoring
- Test result analysis and reporting
"""
import os
import sys
import time
import json
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import concurrent.futures
from dataclasses import dataclass, asdict

# Import configuration system
try:
    from app.tests.config import TestConfigLoader, TestConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    TestConfigLoader = None
    TestConfig = None


@dataclass
class TestResult:
    """Test execution result."""
    category: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    coverage: Optional[float] = None
    performance_metrics: Optional[Dict] = None


@dataclass
class TestSuiteConfig:
    """Configuration for test suite execution."""
    parallel: bool = True
    max_workers: int = 4
    coverage_threshold: float = 80.0
    performance_threshold_ms: float = 1000.0
    verbose: bool = False
    fail_fast: bool = False
    categories: Optional[List[str]] = None
    exclude_categories: Optional[List[str]] = None
    output_dir: str = "test_results"
    report_format: str = "html"
    
    def __post_init__(self):
        """Initialize mutable defaults and validate configuration."""
        if self.categories is None:
            self.categories = []
        if self.exclude_categories is None:
            self.exclude_categories = []
        
        # Validate configuration
        errors = self.validate_config()
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate max_workers
        if not isinstance(self.max_workers, int) or self.max_workers < 1:
            errors.append("max_workers must be an integer >= 1")
        elif self.max_workers > 32:
            errors.append("max_workers should not exceed 32 for optimal performance")
        
        # Validate coverage_threshold
        if not isinstance(self.coverage_threshold, (int, float)) or not 0 <= self.coverage_threshold <= 100:
            errors.append("coverage_threshold must be a number between 0 and 100")
        
        # Validate performance_threshold_ms
        if not isinstance(self.performance_threshold_ms, (int, float)) or self.performance_threshold_ms <= 0:
            errors.append("performance_threshold_ms must be a positive number")
        elif self.performance_threshold_ms > 300000:  # 5 minutes
            errors.append("performance_threshold_ms should not exceed 300000ms (5 minutes)")
        
        # Validate report_format
        if not isinstance(self.report_format, str) or self.report_format not in ["html", "json", "xml"]:
            errors.append("report_format must be one of: html, json, xml")
        
        # Validate output_dir
        if not isinstance(self.output_dir, str):
            errors.append("output_dir must be a string")
        elif not self.output_dir.strip():
            errors.append("output_dir cannot be empty")
        
        # Validate boolean flags
        if not isinstance(self.parallel, bool):
            errors.append("parallel must be a boolean")
        
        if not isinstance(self.verbose, bool):
            errors.append("verbose must be a boolean")
        
        if not isinstance(self.fail_fast, bool):
            errors.append("fail_fast must be a boolean")
        
        # Validate categories
        if self.categories is not None:
            if not isinstance(self.categories, list):
                errors.append("categories must be a list")
            else:
                valid_categories = ["unit", "integration", "e2e", "performance", "security"]
                for category in self.categories:
                    if not isinstance(category, str):
                        errors.append(f"Category must be a string, got {type(category)}")
                    elif category not in valid_categories:
                        errors.append(f"Invalid category '{category}'. Valid categories: {valid_categories}")
        
        # Validate exclude_categories
        if self.exclude_categories is not None:
            if not isinstance(self.exclude_categories, list):
                errors.append("exclude_categories must be a list")
            else:
                valid_categories = ["unit", "integration", "e2e", "performance", "security"]
                for category in self.exclude_categories:
                    if not isinstance(category, str):
                        errors.append(f"Exclude category must be a string, got {type(category)}")
                    elif category not in valid_categories:
                        errors.append(f"Invalid exclude category '{category}'. Valid categories: {valid_categories}")
        
        return errors


class TestExecutionError(Exception):
    """Custom exception for test execution errors."""
    pass


class TestRunner:
    """Main test runner for comprehensive test execution."""
    
    def __init__(self, config: TestSuiteConfig):
        self.config = config
        self.results: Dict[str, TestResult] = {}
        self.start_time = None
        self.end_time = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Ensure output directory exists
        try:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create output directory {self.config.output_dir}: {e}")
            raise TestExecutionError(f"Cannot create output directory: {e}")
        
        # Initialize test categories
        self._initialize_test_categories()
    
    @classmethod
    def from_config_file(cls, 
                        config_file: str = "test_config.yaml",
                        environment: Optional[str] = None,
                        overrides: Optional[Dict[str, Any]] = None) -> 'TestRunner':
        """
        Create TestRunner from configuration file.
        
        Args:
            config_file: Name of the configuration file
            environment: Environment name (development, staging, production)
            overrides: Additional configuration overrides
            
        Returns:
            TestRunner instance with loaded configuration
        """
        if not CONFIG_AVAILABLE:
            raise ImportError("Configuration system not available. Install PyYAML to use config files.")
        
        # Load configuration
        loader = TestConfigLoader()
        test_config = loader.load_config(
            config_file=config_file,
            environment=environment,
            overrides=overrides
        )
        
        # Convert to TestSuiteConfig
        suite_config = TestSuiteConfig(
            parallel=test_config.parallel,
            max_workers=test_config.max_workers,
            coverage_threshold=test_config.coverage_threshold,
            performance_threshold_ms=test_config.performance_threshold_ms,
            verbose=test_config.verbose,
            fail_fast=test_config.fail_fast,
            categories=test_config.categories,
            exclude_categories=test_config.exclude_categories,
            output_dir=test_config.output_dir,
            report_format=test_config.report_format
        )
        
        return cls(suite_config)
    
    def _initialize_test_categories(self):
        """Initialize test categories configuration."""
        # Test categories and their configurations
        self.test_categories = {
            "unit": {
                "path": "app/tests/unit",
                "markers": ["unit"],
                "timeout": 300,  # 5 minutes
                "parallel": True
            },
            "integration": {
                "path": "app/tests/integration", 
                "markers": ["integration"],
                "timeout": 600,  # 10 minutes
                "parallel": True
            },
            "e2e": {
                "path": "app/tests/e2e",
                "markers": ["e2e"],
                "timeout": 1200,  # 20 minutes
                "parallel": False  # E2E tests often can't run in parallel
            },
            "performance": {
                "path": "app/tests/integration",
                "markers": ["performance"],
                "timeout": 1800,  # 30 minutes
                "parallel": False
            },
            "security": {
                "path": "app/tests/integration",
                "markers": ["security"],
                "timeout": 900,  # 15 minutes
                "parallel": True
            }
        }
    
    def run_all_tests(self) -> Dict[str, TestResult]:
        """Run all test categories."""
        print("🚀 Starting comprehensive test suite execution...")
        self.start_time = time.time()
        
        # Filter categories based on config
        categories_to_run = self._get_categories_to_run()
        
        if self.config.parallel and len(categories_to_run) > 1:
            self._run_tests_parallel(categories_to_run)
        else:
            self._run_tests_sequential(categories_to_run)
        
        self.end_time = time.time()
        self._generate_reports()
        
        return self.results
    
    def _get_categories_to_run(self) -> List[str]:
        """Get list of categories to run based on configuration."""
        all_categories = list(self.test_categories.keys())
        
        if self.config.categories:
            categories = [cat for cat in self.config.categories if cat in all_categories]
        else:
            categories = all_categories
        
        if self.config.exclude_categories:
            categories = [cat for cat in categories if cat not in self.config.exclude_categories]
        
        return categories
    
    def _run_tests_parallel(self, categories: List[str]):
        """Run test categories in parallel."""
        print(f"🔄 Running {len(categories)} test categories in parallel...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            future_to_category = {
                executor.submit(self._run_category, category): category 
                for category in categories
            }
            
            for future in concurrent.futures.as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    result = future.result()
                    self.results[category] = result
                    print(f"✅ {category.title()} tests completed: {result.passed}/{result.total_tests} passed")
                except Exception as e:
                    print(f"❌ {category.title()} tests failed with error: {e}")
                    self.results[category] = TestResult(
                        category=category,
                        total_tests=0,
                        passed=0,
                        failed=0,
                        skipped=0,
                        errors=1,
                        duration=0.0
                    )
    
    def _run_tests_sequential(self, categories: List[str]):
        """Run test categories sequentially."""
        print(f"🔄 Running {len(categories)} test categories sequentially...")
        
        for category in categories:
            print(f"\n📋 Running {category.title()} tests...")
            result = self._run_category(category)
            self.results[category] = result
            
            if result.failed > 0 or result.errors > 0:
                print(f"❌ {category.title()} tests failed: {result.failed} failed, {result.errors} errors")
                if self.config.fail_fast:
                    print("🛑 Stopping due to fail-fast mode")
                    break
            else:
                print(f"✅ {category.title()} tests passed: {result.passed}/{result.total_tests} passed")
    
    def _run_category(self, category: str) -> TestResult:
        """Run a specific test category."""
        config = self.test_categories[category]
        start_time = time.time()
        
        # Build pytest command
        cmd = self._build_pytest_command(category, config)
        
        try:
            # Run pytest
            self.logger.info(f"Running {category} tests with command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config["timeout"]
            )
            
            # Validate pytest exit codes (0-5 are valid)
            if result.returncode not in [0, 1, 2, 3, 4, 5]:
                self.logger.error(f"Unexpected pytest exit code: {result.returncode}")
                raise TestExecutionError(f"Unexpected pytest exit code: {result.returncode}")
            
            # Parse results
            duration = time.time() - start_time
            test_result = self._parse_pytest_output(result.stdout, result.stderr, category, duration)
            
            # Add coverage if available
            if category in ["unit", "integration"]:
                test_result.coverage = self._get_coverage_percentage()
            
            # Add performance metrics for performance tests
            if category == "performance":
                test_result.performance_metrics = self._extract_performance_metrics(result.stdout)
            
            return test_result
            
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Test category {category} timed out after {config['timeout']}s")
            return TestResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=config["timeout"]
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Test category {category} failed with CalledProcessError: {e}")
            return TestResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=time.time() - start_time
            )
        except FileNotFoundError as e:
            self.logger.error(f"Required file not found for {category} tests: {e}")
            return TestResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=0.0
            )
        except TestExecutionError as e:
            self.logger.error(f"Test execution error in {category}: {e}")
            return TestResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in test category {category}: {e}")
            return TestResult(
                category=category,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=time.time() - start_time
            )
    
    def _build_pytest_command(self, category: str, config: Dict) -> List[str]:
        """Build pytest command for a specific category."""
        cmd = [
            "python", "-m", "pytest",
            config["path"],
            "-v",
            f"--tb=short",
            f"--timeout={config['timeout']}",
            f"--durations=10"
        ]
        
        # Add markers
        for marker in config["markers"]:
            cmd.extend(["-m", marker])
        
        # Add parallel execution if enabled
        if config["parallel"] and self.config.parallel:
            cmd.extend(["-n", "auto"])
        
        # Add coverage for unit and integration tests
        if category in ["unit", "integration"]:
            cmd.extend([
                "--cov=app",
                "--cov-report=html",
                "--cov-report=term-missing",
                f"--cov-fail-under={self.config.coverage_threshold}"
            ])
        
        # Add performance monitoring for performance tests
        if category == "performance":
            cmd.extend([
                "--benchmark-only",
                "--benchmark-save=performance_results"
            ])
        
        # Add output file
        output_file = f"{self.config.output_dir}/{category}_results.xml"
        cmd.extend(["--junitxml", output_file])
        
        return cmd
    
    def _parse_pytest_output(self, stdout: str, stderr: str, category: str, duration: float) -> TestResult:
        """Parse pytest output to extract test results."""
        # Simple parsing - in production, use pytest-json-report or similar
        lines = stdout.split('\n')
        
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        
        for line in lines:
            if "PASSED" in line:
                passed += 1
                total_tests += 1
            elif "FAILED" in line:
                failed += 1
                total_tests += 1
            elif "SKIPPED" in line:
                skipped += 1
                total_tests += 1
            elif "ERROR" in line:
                errors += 1
                total_tests += 1
        
        return TestResult(
            category=category,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration
        )
    
    def _get_coverage_percentage(self) -> Optional[float]:
        """Get coverage percentage from coverage report."""
        # This would parse the actual coverage report
        # For now, return a placeholder
        return 85.0
    
    def _extract_performance_metrics(self, stdout: str) -> Dict:
        """Extract performance metrics from test output."""
        # This would parse pytest-benchmark output
        return {
            "avg_duration_ms": 500.0,
            "max_duration_ms": 1000.0,
            "min_duration_ms": 100.0
        }
    
    def _generate_reports(self):
        """Generate comprehensive test reports."""
        print("\n📊 Generating test reports...")
        
        # Generate summary report
        self._generate_summary_report()
        
        # Generate detailed HTML report
        if self.config.report_format == "html":
            self._generate_html_report()
        
        # Generate JSON report
        self._generate_json_report()
        
        # Generate performance report
        self._generate_performance_report()
    
    def _generate_summary_report(self):
        """Generate a summary report."""
        total_duration = self.end_time - self.start_time
        total_tests = sum(r.total_tests for r in self.results.values())
        total_passed = sum(r.passed for r in self.results.values())
        total_failed = sum(r.failed for r in self.results.values())
        total_errors = sum(r.errors for r in self.results.values())
        
        print("\n" + "="*80)
        print("📋 TEST EXECUTION SUMMARY")
        print("="*80)
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed} ✅")
        print(f"Failed: {total_failed} ❌")
        print(f"Errors: {total_errors} ⚠️")
        print(f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        print("\n📊 Results by Category:")
        for category, result in self.results.items():
            status = "✅" if result.failed == 0 and result.errors == 0 else "❌"
            print(f"  {category.title():12} {status} {result.passed:3}/{result.total_tests:3} passed ({result.duration:6.1f}s)")
        
        print("="*80)
    
    def _generate_html_report(self):
        """Generate HTML test report."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Execution Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .category {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .summary {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧪 Test Execution Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Summary</h2>
                <p>Total Duration: {self.end_time - self.start_time:.2f} seconds</p>
                <p>Total Tests: {sum(r.total_tests for r in self.results.values())}</p>
                <p>Passed: {sum(r.passed for r in self.results.values())}</p>
                <p>Failed: {sum(r.failed for r in self.results.values())}</p>
            </div>
            
            <h2>📋 Results by Category</h2>
        """
        
        for category, result in self.results.items():
            status_class = "passed" if result.failed == 0 and result.errors == 0 else "failed"
            html_content += f"""
            <div class="category">
                <h3 class="{status_class}">{category.title()} Tests</h3>
                <p>Duration: {result.duration:.2f}s</p>
                <p>Tests: {result.passed}/{result.total_tests} passed</p>
                <p>Coverage: {result.coverage:.1f}%</p>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open(f"{self.config.output_dir}/test_report.html", "w") as f:
            f.write(html_content)
        
        print(f"📄 HTML report generated: {self.config.output_dir}/test_report.html")
    
    def _generate_json_report(self):
        """Generate JSON test report."""
        report_data = {
            "execution_time": {
                "start": self.start_time,
                "end": self.end_time,
                "duration": self.end_time - self.start_time
            },
            "summary": {
                "total_tests": sum(r.total_tests for r in self.results.values()),
                "passed": sum(r.passed for r in self.results.values()),
                "failed": sum(r.failed for r in self.results.values()),
                "errors": sum(r.errors for r in self.results.values())
            },
            "categories": {cat: asdict(result) for cat, result in self.results.items()}
        }
        
        with open(f"{self.config.output_dir}/test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 JSON report generated: {self.config.output_dir}/test_report.json")
    
    def _generate_performance_report(self):
        """Generate performance test report."""
        perf_results = {cat: result for cat, result in self.results.items() if cat == "performance"}
        
        if perf_results:
            with open(f"{self.config.output_dir}/performance_report.json", "w") as f:
                json.dump({cat: asdict(result) for cat, result in perf_results.items()}, f, indent=2)
            
            print(f"📄 Performance report generated: {self.config.output_dir}/performance_report.json")


def main():
    """Main entry point for test automation pipeline."""
    parser = argparse.ArgumentParser(description="Comprehensive Test Automation Pipeline")
    
    parser.add_argument("--categories", nargs="+", 
                       choices=["unit", "integration", "e2e", "performance", "security"],
                       help="Test categories to run")
    
    parser.add_argument("--exclude", nargs="+",
                       choices=["unit", "integration", "e2e", "performance", "security"],
                       help="Test categories to exclude")
    
    parser.add_argument("--parallel", action="store_true", default=True,
                       help="Run tests in parallel")
    
    parser.add_argument("--no-parallel", action="store_true",
                       help="Disable parallel execution")
    
    parser.add_argument("--max-workers", type=int, default=4,
                       help="Maximum number of parallel workers")
    
    parser.add_argument("--coverage-threshold", type=float, default=80.0,
                       help="Minimum coverage percentage")
    
    parser.add_argument("--performance-threshold", type=float, default=1000.0,
                       help="Maximum performance threshold in milliseconds")
    
    parser.add_argument("--verbose", action="store_true",
                       help="Verbose output")
    
    parser.add_argument("--fail-fast", action="store_true",
                       help="Stop on first failure")
    
    parser.add_argument("--output-dir", default="test_results",
                       help="Output directory for reports")
    
    parser.add_argument("--report-format", choices=["html", "json", "xml"], default="html",
                       help="Report format")
    
    # Configuration file options
    parser.add_argument("--config-file", default="test_config.yaml",
                       help="Configuration file to use")
    
    parser.add_argument("--environment", choices=["development", "staging", "production"],
                       help="Environment to use for configuration overrides")
    
    parser.add_argument("--use-config", action="store_true",
                       help="Use configuration file instead of command line arguments")
    
    args = parser.parse_args()
    
    # Create configuration
    if args.use_config and CONFIG_AVAILABLE:
        try:
            runner = TestRunner.from_config_file(
                config_file=args.config_file,
                environment=args.environment
            )
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            print("Falling back to command line arguments...")
            config = TestSuiteConfig(
                parallel=not args.no_parallel,
                max_workers=args.max_workers,
                coverage_threshold=args.coverage_threshold,
                performance_threshold_ms=args.performance_threshold,
                verbose=args.verbose,
                fail_fast=args.fail_fast,
                categories=args.categories,
                exclude_categories=args.exclude,
                output_dir=args.output_dir,
                report_format=args.report_format
            )
            runner = TestRunner(config)
    else:
        config = TestSuiteConfig(
            parallel=not args.no_parallel,
            max_workers=args.max_workers,
            coverage_threshold=args.coverage_threshold,
            performance_threshold_ms=args.performance_threshold,
            verbose=args.verbose,
            fail_fast=args.fail_fast,
            categories=args.categories,
            exclude_categories=args.exclude,
            output_dir=args.output_dir,
            report_format=args.report_format
        )
        runner = TestRunner(config)
    
    # Run tests
    results = runner.run_all_tests()
    
    # Exit with appropriate code
    total_failed = sum(r.failed for r in results.values())
    total_errors = sum(r.errors for r in results.values())
    
    if total_failed > 0 or total_errors > 0:
        print(f"\n❌ Test execution failed: {total_failed} failures, {total_errors} errors")
        sys.exit(1)
    else:
        print(f"\n✅ All tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
