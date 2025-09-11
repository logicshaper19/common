#!/usr/bin/env python3
"""
Test Coverage Analysis Script

Analyzes test coverage across the codebase and identifies gaps in testing.
"""

import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class CoverageGap:
    """Represents a gap in test coverage."""
    file_path: str
    line_numbers: List[int]
    function_name: str
    severity: str  # 'critical', 'high', 'medium', 'low'


class TestCoverageAnalyzer:
    """Analyze test coverage and identify gaps."""
    
    def __init__(self, source_dir: str = "app"):
        self.source_dir = Path(source_dir)
        self.coverage_data = {}
        self.gaps: List[CoverageGap] = []
    
    def run_coverage_analysis(self) -> Dict:
        """Run comprehensive coverage analysis."""
        print("🔍 Running Test Coverage Analysis...")
        
        # Run tests with coverage
        cmd = [
            "python", "-m", "pytest",
            "--cov=app",
            "--cov-branch",
            "--cov-report=json",
            "--cov-report=term-missing",
            "--cov-fail-under=0",  # Don't fail on low coverage for analysis
            "-q"  # Quiet mode for cleaner output
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Load coverage data
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                with open(coverage_file) as f:
                    self.coverage_data = json.load(f)
            
            return self._analyze_coverage_data()
            
        except subprocess.TimeoutExpired:
            print("⏰ Coverage analysis timed out")
            return {}
        except Exception as e:
            print(f"❌ Coverage analysis failed: {e}")
            return {}
    
    def _analyze_coverage_data(self) -> Dict:
        """Analyze coverage data and identify gaps."""
        if not self.coverage_data:
            return {"error": "No coverage data available"}
        
        files = self.coverage_data.get("files", {})
        totals = self.coverage_data.get("totals", {})
        
        # Overall metrics
        overall_coverage = totals.get("percent_covered", 0)
        
        # Analyze each file
        file_analysis = {}
        critical_gaps = []
        
        for file_path, file_data in files.items():
            if not file_path.startswith("app/"):
                continue
                
            analysis = self._analyze_file_coverage(file_path, file_data)
            file_analysis[file_path] = analysis
            
            # Identify critical gaps
            if analysis["coverage_percent"] < 50:
                critical_gaps.append({
                    "file": file_path,
                    "coverage": analysis["coverage_percent"],
                    "missing_lines": len(analysis["missing_lines"])
                })
        
        # Generate recommendations
        recommendations = self._generate_coverage_recommendations(
            overall_coverage, file_analysis, critical_gaps
        )
        
        return {
            "overall_coverage": overall_coverage,
            "file_analysis": file_analysis,
            "critical_gaps": critical_gaps,
            "recommendations": recommendations,
            "summary": {
                "total_files": len(file_analysis),
                "well_covered_files": len([f for f in file_analysis.values() if f["coverage_percent"] >= 80]),
                "poorly_covered_files": len([f for f in file_analysis.values() if f["coverage_percent"] < 50]),
                "average_coverage": sum(f["coverage_percent"] for f in file_analysis.values()) / len(file_analysis) if file_analysis else 0
            }
        }
    
    def _analyze_file_coverage(self, file_path: str, file_data: Dict) -> Dict:
        """Analyze coverage for a specific file."""
        executed_lines = set(file_data.get("executed_lines", []))
        missing_lines = file_data.get("missing_lines", [])
        excluded_lines = set(file_data.get("excluded_lines", []))
        
        total_lines = len(executed_lines) + len(missing_lines)
        coverage_percent = (len(executed_lines) / total_lines * 100) if total_lines > 0 else 0
        
        # Categorize missing lines by function/class
        missing_functions = self._identify_missing_functions(file_path, missing_lines)
        
        return {
            "coverage_percent": round(coverage_percent, 2),
            "executed_lines": len(executed_lines),
            "missing_lines": missing_lines,
            "total_lines": total_lines,
            "missing_functions": missing_functions,
            "priority": self._calculate_file_priority(file_path, coverage_percent)
        }
    
    def _identify_missing_functions(self, file_path: str, missing_lines: List[int]) -> List[str]:
        """Identify functions/methods that are missing coverage."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            missing_functions = []
            current_function = None
            
            for i, line in enumerate(lines, 1):
                # Check if this line defines a function or method
                if re.match(r'\s*(def|class)\s+(\w+)', line):
                    match = re.match(r'\s*(def|class)\s+(\w+)', line)
                    current_function = match.group(2)
                
                # If this line is missing coverage and we're in a function
                if i in missing_lines and current_function:
                    if current_function not in missing_functions:
                        missing_functions.append(current_function)
            
            return missing_functions
            
        except Exception:
            return []
    
    def _calculate_file_priority(self, file_path: str, coverage_percent: float) -> str:
        """Calculate priority for improving coverage in this file."""
        # High priority: Core business logic with low coverage
        if any(keyword in file_path for keyword in ["models/", "services/", "api/"]):
            if coverage_percent < 60:
                return "high"
            elif coverage_percent < 80:
                return "medium"
        
        # Medium priority: Other important files
        if any(keyword in file_path for keyword in ["core/", "utils/"]):
            if coverage_percent < 50:
                return "high"
            elif coverage_percent < 70:
                return "medium"
        
        # Low priority: Test files, config, etc.
        if any(keyword in file_path for keyword in ["tests/", "migrations/", "scripts/"]):
            return "low"
        
        return "medium" if coverage_percent < 70 else "low"
    
    def _generate_coverage_recommendations(self, overall_coverage: float, 
                                         file_analysis: Dict, 
                                         critical_gaps: List[Dict]) -> List[str]:
        """Generate recommendations for improving coverage."""
        recommendations = []
        
        if overall_coverage < 70:
            recommendations.append(f"Overall coverage is {overall_coverage:.1f}% - aim for 80%+ coverage")
        
        if critical_gaps:
            recommendations.append(f"Focus on {len(critical_gaps)} files with <50% coverage")
            
            # Prioritize by file type
            api_files = [g for g in critical_gaps if "api/" in g["file"]]
            model_files = [g for g in critical_gaps if "models/" in g["file"]]
            service_files = [g for g in critical_gaps if "services/" in g["file"]]
            
            if api_files:
                recommendations.append(f"Priority: Add tests for {len(api_files)} API endpoints")
            if model_files:
                recommendations.append(f"Priority: Add tests for {len(model_files)} data models")
            if service_files:
                recommendations.append(f"Priority: Add tests for {len(service_files)} business services")
        
        # Identify specific improvement areas
        high_priority_files = [
            f for f, analysis in file_analysis.items() 
            if analysis["priority"] == "high"
        ]
        
        if high_priority_files:
            recommendations.append(f"High priority files needing tests: {len(high_priority_files)} files")
        
        return recommendations
    
    def generate_coverage_report(self, analysis: Dict) -> str:
        """Generate a detailed coverage report."""
        report = []
        report.append("# Test Coverage Analysis Report")
        report.append(f"Overall Coverage: {analysis['overall_coverage']:.1f}%")
        report.append("")
        
        summary = analysis["summary"]
        report.append("## Summary")
        report.append(f"- Total Files Analyzed: {summary['total_files']}")
        report.append(f"- Well Covered Files (≥80%): {summary['well_covered_files']}")
        report.append(f"- Poorly Covered Files (<50%): {summary['poorly_covered_files']}")
        report.append(f"- Average Coverage: {summary['average_coverage']:.1f}%")
        report.append("")
        
        if analysis["critical_gaps"]:
            report.append("## Critical Coverage Gaps")
            for gap in analysis["critical_gaps"][:10]:  # Top 10
                report.append(f"- **{gap['file']}**: {gap['coverage']:.1f}% coverage ({gap['missing_lines']} missing lines)")
            report.append("")
        
        if analysis["recommendations"]:
            report.append("## Recommendations")
            for rec in analysis["recommendations"]:
                report.append(f"- {rec}")
            report.append("")
        
        # Top priority files
        high_priority = [
            (f, data) for f, data in analysis["file_analysis"].items()
            if data["priority"] == "high"
        ]
        
        if high_priority:
            report.append("## High Priority Files for Testing")
            for file_path, data in high_priority[:10]:
                report.append(f"- **{file_path}**: {data['coverage_percent']:.1f}% coverage")
                if data["missing_functions"]:
                    report.append(f"  - Missing: {', '.join(data['missing_functions'][:5])}")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Coverage Analysis")
    parser.add_argument("--report", help="Generate coverage report to file")
    parser.add_argument("--json", help="Save analysis data as JSON")
    
    args = parser.parse_args()
    
    analyzer = TestCoverageAnalyzer()
    analysis = analyzer.run_coverage_analysis()
    
    if not analysis or "error" in analysis:
        print("❌ Coverage analysis failed")
        exit(1)
    
    print(f"\n📊 Coverage Analysis Complete!")
    print(f"Overall Coverage: {analysis['overall_coverage']:.1f}%")
    print(f"Files Analyzed: {analysis['summary']['total_files']}")
    print(f"Critical Gaps: {len(analysis['critical_gaps'])}")
    
    if args.report:
        report = analyzer.generate_coverage_report(analysis)
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to {args.report}")
    
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"📄 Analysis data saved to {args.json}")


if __name__ == "__main__":
    main()
