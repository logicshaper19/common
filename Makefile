# Makefile for Common Supply Chain Platform Testing

.PHONY: help test test-unit test-integration test-e2e test-performance test-security test-all clean install

# Default target
help:
	@echo "🧪 Common Supply Chain Platform - Test Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install          Install dependencies"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-e2e         Run end-to-end tests only"
	@echo "  make test-performance Run performance tests only"
	@echo "  make test-security    Run security tests only"
	@echo "  make test-quick       Run quick tests (unit + integration)"
	@echo "  make test-parallel    Run tests in parallel"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo "  make test-watch       Run tests in watch mode"
	@echo "  make clean            Clean test artifacts"
	@echo "  make setup-db         Setup test database"
	@echo "  make lint             Run linting"
	@echo "  make format           Format code"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-xdist pytest-benchmark pytest-watch
	pip install bandit safety black isort flake8

# Setup test database
setup-db:
	@echo "🗄️  Setting up test database..."
	@echo "Make sure PostgreSQL is running on localhost:5432"
	@echo "Database: test_common_platform"
	@echo "User: postgres"
	@echo "Password: password"

# Run all tests
test: setup-db
	@echo "🚀 Running all tests..."
	python app/tests/run_comprehensive_tests.py \
		--parallel \
		--coverage-threshold 80 \
		--output-dir test_results

# Run unit tests
test-unit: setup-db
	@echo "🔬 Running unit tests..."
	python app/tests/run_comprehensive_tests.py \
		--categories unit \
		--parallel \
		--coverage-threshold 85 \
		--output-dir test_results/unit

# Run integration tests
test-integration: setup-db
	@echo "🔗 Running integration tests..."
	python app/tests/run_comprehensive_tests.py \
		--categories integration \
		--parallel \
		--coverage-threshold 80 \
		--output-dir test_results/integration

# Run end-to-end tests
test-e2e: setup-db
	@echo "🌐 Running end-to-end tests..."
	python app/tests/run_comprehensive_tests.py \
		--categories e2e \
		--no-parallel \
		--output-dir test_results/e2e

# Run performance tests
test-performance: setup-db
	@echo "⚡ Running performance tests..."
	python app/tests/run_comprehensive_tests.py \
		--categories performance \
		--no-parallel \
		--performance-threshold 2000 \
		--output-dir test_results/performance

# Run security tests
test-security: setup-db
	@echo "🔒 Running security tests..."
	python app/tests/run_comprehensive_tests.py \
		--categories security \
		--parallel \
		--output-dir test_results/security

# Run quick tests (unit + integration)
test-quick: setup-db
	@echo "⚡ Running quick tests..."
	python app/tests/run_comprehensive_tests.py \
		--categories unit integration \
		--parallel \
		--coverage-threshold 80 \
		--output-dir test_results/quick

# Run tests in parallel
test-parallel: setup-db
	@echo "🔄 Running tests in parallel..."
	python app/tests/run_comprehensive_tests.py \
		--parallel \
		--max-workers 8 \
		--coverage-threshold 80 \
		--output-dir test_results

# Run tests with coverage
test-coverage: setup-db
	@echo "📊 Running tests with coverage..."
	python app/tests/run_comprehensive_tests.py \
		--categories unit integration \
		--parallel \
		--coverage-threshold 85 \
		--output-dir test_results/coverage

# Run tests in watch mode
test-watch: setup-db
	@echo "👀 Running tests in watch mode..."
	pytest-watch app/tests/unit app/tests/integration \
		--runner "python app/tests/run_comprehensive_tests.py --categories unit integration"

# Run specific test file
test-file:
	@echo "📁 Running specific test file..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	pytest $(FILE) -v --tb=short

# Run tests with specific marker
test-marker:
	@echo "🏷️  Running tests with specific marker..."
	@if [ -z "$(MARKER)" ]; then \
		echo "Usage: make test-marker MARKER=marker_name"; \
		exit 1; \
	fi
	pytest -m $(MARKER) -v --tb=short

# Run linting
lint:
	@echo "🔍 Running linting..."
	flake8 app/ --max-line-length=100 --ignore=E203,W503
	black --check app/
	isort --check-only app/

# Format code
format:
	@echo "🎨 Formatting code..."
	black app/
	isort app/

# Run security scan
security-scan:
	@echo "🔒 Running security scan..."
	bandit -r app/ -f json -o security_report.json
	safety check --json --output safety_report.json

# Clean test artifacts
clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf test_results/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.db
	rm -rf security_report.json
	rm -rf safety_report.json
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development setup
dev-setup: install setup-db
	@echo "🛠️  Development environment ready!"
	@echo "Run 'make test' to start testing"

# CI/CD pipeline simulation
ci-test: clean install setup-db
	@echo "🔄 Running CI/CD pipeline simulation..."
	@echo "1. Unit Tests..."
	make test-unit
	@echo "2. Integration Tests..."
	make test-integration
	@echo "3. Security Tests..."
	make test-security
	@echo "4. Performance Tests..."
	make test-performance
	@echo "✅ CI/CD pipeline completed!"

# Test database reset
reset-db:
	@echo "🔄 Resetting test database..."
	@echo "Dropping and recreating test database..."
	psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS test_common_platform;"
	psql -h localhost -U postgres -c "CREATE DATABASE test_common_platform;"
	@echo "✅ Test database reset complete!"

# Show test results
show-results:
	@echo "📊 Test Results Summary:"
	@if [ -f "test_results/test_report.html" ]; then \
		echo "HTML Report: test_results/test_report.html"; \
	fi
	@if [ -f "test_results/test_report.json" ]; then \
		echo "JSON Report: test_results/test_report.json"; \
	fi
	@if [ -f "test_results/performance_report.json" ]; then \
		echo "Performance Report: test_results/performance_report.json"; \
	fi

# Open test results in browser
open-results:
	@echo "🌐 Opening test results in browser..."
	@if [ -f "test_results/test_report.html" ]; then \
		open test_results/test_report.html; \
	else \
		echo "No HTML report found. Run tests first."; \
	fi

# Test debugging
debug-test:
	@echo "🐛 Debug test execution..."
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make debug-test TEST=test_name"; \
		exit 1; \
	fi
	pytest -v -s --tb=long --capture=no $(TEST)

# Memory profiling
profile-memory:
	@echo "🧠 Running memory profiling..."
	pytest --profile app/tests/unit/ --profile-svg

# Test data generation
generate-test-data:
	@echo "📊 Generating test data..."
	python -c "
from app.tests.factories import create_complete_test_scenario
import json
scenario = create_complete_test_scenario()
with open('test_data.json', 'w') as f:
    json.dump(scenario, f, indent=2, default=str)
print('Test data generated: test_data.json')
"

# Show help for specific command
help-test:
	@echo "🧪 Test Command Help:"
	@echo ""
	@echo "test-file: Run a specific test file"
	@echo "  Example: make test-file FILE=app/tests/unit/test_auth.py"
	@echo ""
	@echo "test-marker: Run tests with specific marker"
	@echo "  Example: make test-marker MARKER=slow"
	@echo ""
	@echo "debug-test: Debug a specific test"
	@echo "  Example: make debug-test TEST=app/tests/unit/test_auth.py::test_login"
	@echo ""
	@echo "Available markers:"
	@echo "  - unit: Unit tests"
	@echo "  - integration: Integration tests"
	@echo "  - e2e: End-to-end tests"
	@echo "  - performance: Performance tests"
	@echo "  - security: Security tests"
	@echo "  - slow: Slow running tests"
