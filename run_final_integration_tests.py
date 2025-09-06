#!/usr/bin/env python3
"""
Final Integration and System Testing Runner

This script runs comprehensive end-to-end testing including:
- Complete user journey testing for all personas
- Cross-browser compatibility testing
- Accessibility compliance testing
- Performance testing
- Requirements validation
- API endpoint validation

Usage:
    python run_final_integration_tests.py [--quick] [--report-file output.json]
"""

import sys
import os
import json
import argparse
from datetime import datetime
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    # Import test modules
    from tests.integration.test_user_journeys import UserJourneyTestSuite
    from tests.system.test_comprehensive_system import SystemTestSuite
    from tests.validation.test_requirements_validation import RequirementsValidator
    
    # Import FastAPI test client setup
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.models.base import Base
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the project root directory and all dependencies are installed.")
    sys.exit(1)


class FinalIntegrationTestRunner:
    """Comprehensive test runner for final integration testing."""
    
    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
        self.test_results = {
            "test_suite": "Final Integration and System Testing",
            "timestamp": datetime.now().isoformat(),
            "quick_mode": quick_mode,
            "results": {},
            "summary": {}
        }
        
        # Setup test database
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test database and client."""
        print("🔧 Setting up test environment...")
        
        # Create test database
        TEST_DATABASE_URL = "sqlite:///./test_final_integration.db"
        self.test_engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        
        # Create all tables
        Base.metadata.create_all(bind=self.test_engine)
        
        # Create session factory
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.test_engine)
        self.db_session = TestingSessionLocal()
        
        # Override database dependency
        def override_get_db():
            try:
                yield self.db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create test client
        self.client = TestClient(app)
        
        print("✅ Test environment setup complete")
    
    def run_user_journey_tests(self) -> Dict[str, Any]:
        """Run complete user journey tests for all personas."""
        
        print("\n👥 Running User Journey Tests...")
        print("=" * 50)
        
        try:
            journey_suite = UserJourneyTestSuite(self.client, self.db_session)
            results = journey_suite.run_all_journeys()
            
            self.test_results["results"]["user_journeys"] = results
            
            print(f"✅ User Journey Tests Complete")
            print(f"   Success Rate: {results['summary']['success_rate']}")
            print(f"   Personas Tested: {results['personas_tested']}")
            
            return results
            
        except Exception as e:
            error_result = {
                "status": "ERROR",
                "error": str(e),
                "summary": {"success_rate": "0%", "overall_status": "ERROR"}
            }
            self.test_results["results"]["user_journeys"] = error_result
            print(f"❌ User Journey Tests Failed: {str(e)}")
            return error_result
    
    def run_system_tests(self) -> Dict[str, Any]:
        """Run comprehensive system tests."""
        
        print("\n🖥️ Running System Tests...")
        print("=" * 50)
        
        try:
            system_suite = SystemTestSuite()
            
            if self.quick_mode:
                # In quick mode, only run API and performance tests
                results = {
                    "test_suite": "System Testing (Quick Mode)",
                    "timestamp": datetime.now().isoformat(),
                    "results": {
                        "api_endpoints": system_suite.test_api_endpoints(),
                        "performance": system_suite.test_performance_metrics()
                    }
                }
                
                # Calculate quick summary
                passed_categories = sum(1 for r in results["results"].values() 
                                      if r.get("status") in ["PASS", "SKIP"])
                total_categories = len(results["results"])
                
                results["summary"] = {
                    "total_categories": total_categories,
                    "passed_categories": passed_categories,
                    "success_rate": f"{(passed_categories/total_categories)*100:.1f}%",
                    "overall_status": "PASS" if passed_categories >= total_categories else "FAIL"
                }
            else:
                # Full system testing
                results = system_suite.run_comprehensive_tests()
            
            self.test_results["results"]["system_tests"] = results
            
            print(f"✅ System Tests Complete")
            print(f"   Success Rate: {results['summary']['success_rate']}")
            print(f"   Categories Tested: {results['summary']['total_categories']}")
            
            return results
            
        except Exception as e:
            error_result = {
                "status": "ERROR",
                "error": str(e),
                "summary": {"success_rate": "0%", "overall_status": "ERROR"}
            }
            self.test_results["results"]["system_tests"] = error_result
            print(f"❌ System Tests Failed: {str(e)}")
            return error_result
    
    def run_requirements_validation(self) -> Dict[str, Any]:
        """Run requirements validation tests."""
        
        print("\n📋 Running Requirements Validation...")
        print("=" * 50)
        
        try:
            validator = RequirementsValidator(self.client, self.db_session)
            results = validator.run_requirements_validation()
            
            self.test_results["results"]["requirements_validation"] = results
            
            print(f"✅ Requirements Validation Complete")
            print(f"   Success Rate: {results['summary']['success_rate']}")
            print(f"   Requirements Tested: {results['summary']['total_requirements']}")
            
            return results
            
        except Exception as e:
            error_result = {
                "status": "ERROR",
                "error": str(e),
                "summary": {"success_rate": "0%", "overall_status": "ERROR"}
            }
            self.test_results["results"]["requirements_validation"] = error_result
            print(f"❌ Requirements Validation Failed: {str(e)}")
            return error_result
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive final test report."""
        
        print("\n📊 Generating Final Test Report...")
        print("=" * 50)
        
        # Calculate overall statistics
        test_categories = ["user_journeys", "system_tests", "requirements_validation"]
        total_categories = len(test_categories)
        passed_categories = 0
        
        category_results = {}
        
        for category in test_categories:
            if category in self.test_results["results"]:
                result = self.test_results["results"][category]
                status = result.get("summary", {}).get("overall_status", "UNKNOWN")
                
                if status in ["PASS", "PARTIAL"]:
                    passed_categories += 1
                    category_results[category] = "PASS"
                else:
                    category_results[category] = "FAIL"
            else:
                category_results[category] = "NOT_RUN"
        
        # Generate summary
        success_rate = (passed_categories / total_categories) * 100
        overall_status = "PASS" if passed_categories >= total_categories * 0.8 else "FAIL"
        
        self.test_results["summary"] = {
            "total_test_categories": total_categories,
            "passed_categories": passed_categories,
            "failed_categories": total_categories - passed_categories,
            "success_rate": f"{success_rate:.1f}%",
            "overall_status": overall_status,
            "category_results": category_results,
            "recommendations": self._generate_recommendations()
        }
        
        # Print final summary
        print(f"\n🎯 FINAL INTEGRATION TEST RESULTS")
        print("=" * 60)
        print(f"Test Categories: {total_categories}")
        print(f"Passed: {passed_categories}")
        print(f"Failed: {total_categories - passed_categories}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Overall Status: {overall_status}")
        
        print(f"\n📋 Category Breakdown:")
        for category, status in category_results.items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
            category_name = category.replace("_", " ").title()
            print(f"   {status_icon} {category_name}: {status}")
        
        if self.test_results["summary"]["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in self.test_results["summary"]["recommendations"]:
                print(f"   • {rec}")
        
        return self.test_results
    
    def _generate_recommendations(self) -> list:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Check user journey results
        if "user_journeys" in self.test_results["results"]:
            uj_result = self.test_results["results"]["user_journeys"]
            if uj_result.get("summary", {}).get("overall_status") != "PASS":
                recommendations.append("Review user journey implementations for failed personas")
        
        # Check system test results
        if "system_tests" in self.test_results["results"]:
            st_result = self.test_results["results"]["system_tests"]
            if st_result.get("summary", {}).get("overall_status") != "PASS":
                recommendations.append("Address system-level issues (performance, accessibility, browser compatibility)")
        
        # Check requirements validation
        if "requirements_validation" in self.test_results["results"]:
            rv_result = self.test_results["results"]["requirements_validation"]
            if rv_result.get("summary", {}).get("overall_status") != "PASS":
                recommendations.append("Implement missing functionality to meet requirements")
        
        # General recommendations
        if not recommendations:
            recommendations.append("All tests passed! Consider adding more comprehensive test coverage")
        else:
            recommendations.append("Run tests again after addressing issues")
            recommendations.append("Consider implementing monitoring for production deployment")
        
        return recommendations
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration and system tests."""
        
        print("\n🚀 FINAL INTEGRATION AND SYSTEM TESTING")
        print("=" * 60)
        print(f"Mode: {'Quick' if self.quick_mode else 'Comprehensive'}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        self.run_user_journey_tests()
        self.run_system_tests()
        self.run_requirements_validation()
        
        # Generate final report
        final_report = self.generate_final_report()
        
        # Cleanup
        self.cleanup()
        
        return final_report
    
    def cleanup(self):
        """Cleanup test environment."""
        try:
            self.db_session.close()
            app.dependency_overrides.clear()
            
            # Remove test database file
            if os.path.exists("./test_final_integration.db"):
                os.remove("./test_final_integration.db")
                
        except Exception as e:
            print(f"⚠️ Cleanup warning: {str(e)}")


def main():
    """Main function to run final integration tests."""
    
    parser = argparse.ArgumentParser(description="Run final integration and system tests")
    parser.add_argument("--quick", action="store_true", help="Run in quick mode (skip browser and accessibility tests)")
    parser.add_argument("--report-file", type=str, help="Output file for test results (JSON format)")
    
    args = parser.parse_args()
    
    # Run tests
    runner = FinalIntegrationTestRunner(quick_mode=args.quick)
    results = runner.run_all_tests()
    
    # Save report if requested
    if args.report_file:
        try:
            with open(args.report_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Test report saved to: {args.report_file}")
        except Exception as e:
            print(f"⚠️ Could not save report: {str(e)}")
    
    # Exit with appropriate code
    overall_status = results.get("summary", {}).get("overall_status", "FAIL")
    exit_code = 0 if overall_status == "PASS" else 1
    
    print(f"\n🏁 Testing Complete - Exit Code: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
