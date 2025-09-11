# Comprehensive Testing Guide

## Overview

This guide covers the comprehensive testing strategy for the Common Supply Chain Platform. The test suite includes unit tests, integration tests, security tests, performance tests, and end-to-end workflow tests.

## Test Structure

### Test Categories

1. **Unit Tests** (`test_*.py`)
   - Fast, isolated tests for individual components
   - Test business logic, data models, and utility functions
   - Mock external dependencies

2. **Integration Tests** (`test_*_comprehensive.py`)
   - Test component interactions
   - Test API endpoints with real database
   - Test complete workflows

3. **Security Tests** (`test_security_*.py`)
   - Authentication and authorization
   - Input validation and sanitization
   - SQL injection and XSS prevention
   - Rate limiting and abuse prevention

4. **Performance Tests** (`test_performance.py`, `test_load_*.py`)
   - Response time testing
   - Load testing
   - Stress testing
   - Memory and resource usage

5. **End-to-End Tests** (`test_integration_workflows.py`)
   - Complete supply chain workflows
   - Cross-system integration
   - User journey testing

## Test Files

### Core Test Files

- `test_auth.py` - Authentication and user management
- `test_purchase_orders_comprehensive.py` - Purchase order system
- `test_company_management.py` - Company and business relationships
- `test_products_catalog.py` - Product catalog and sector management
- `test_integration_workflows.py` - End-to-end workflows
- `test_security_comprehensive.py` - Security testing

### Supporting Files

- `conftest.py` - Pytest configuration and fixtures
- `factories.py` - Test data factories
- `run_comprehensive_tests.py` - Test runner script
- `pytest_comprehensive.ini` - Pytest configuration

## Running Tests

### Quick Start

```bash
# Run all tests
python run_comprehensive_tests.py --all

# Run specific test categories
python run_comprehensive_tests.py --unit
python run_comprehensive_tests.py --integration
python run_comprehensive_tests.py --security
python run_comprehensive_tests.py --performance

# Run with detailed reporting
python run_comprehensive_tests.py --all --report
```

### Using pytest directly

```bash
# Run all tests
pytest app/tests/ -v

# Run specific test file
pytest app/tests/test_auth.py -v

# Run tests with coverage
pytest app/tests/ --cov=app --cov-report=html

# Run tests by marker
pytest app/tests/ -m "unit"
pytest app/tests/ -m "security"
pytest app/tests/ -m "slow"
```

### Test Markers

Use markers to run specific types of tests:

```bash
# Unit tests only
pytest -m "unit"

# Security tests only
pytest -m "security"

# Performance tests only
pytest -m "performance"

# Slow tests (exclude them for quick runs)
pytest -m "not slow"

# API tests only
pytest -m "api"
```

## Test Configuration

### Environment Variables

Set these environment variables for testing:

```bash
export TESTING=true
export DATABASE_URL=sqlite:///./test_comprehensive.db
export REDIS_URL=redis://localhost:6379/1
export SECRET_KEY=test-secret-key-for-testing-only
export LOG_LEVEL=WARNING
```

### Database Configuration

Tests use SQLite for speed and isolation. Each test gets a fresh database.

### Fixtures

Key fixtures available in `conftest.py`:

- `client` - FastAPI test client
- `db_session` - Database session
- `test_companies` - Sample companies
- `test_users` - Sample users with different roles
- `test_products` - Sample products
- `test_relationships` - Business relationships
- `auth_headers` - Authentication headers factory

## Test Data

### Factories

Use factories in `factories.py` to create realistic test data:

```python
from app.tests.factories import CompanyFactory, UserFactory, ProductFactory

# Create a company
company = CompanyFactory.create_company("brand")

# Create a user for the company
user = UserFactory.create_user(company, role="admin")

# Create a product
product = ProductFactory.create_product("raw_material")
```

### Supply Chain Scenarios

Use `SupplyChainScenarioFactory` for complex scenarios:

```python
from app.tests.factories import SupplyChainScenarioFactory

# Create a simple 3-tier supply chain
scenario = SupplyChainScenarioFactory.create_simple_scenario()

# Create a complex multi-tier supply chain
complex_scenario = SupplyChainScenarioFactory.create_complex_scenario()
```

## Writing Tests

### Test Structure

Follow this structure for new tests:

```python
class TestFeatureName:
    """Test feature description."""
    
    def test_specific_functionality(self, fixture_name):
        """Test specific functionality with given fixture."""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_error_case(self, fixture_name):
        """Test error handling."""
        # Test error scenarios
        pass
```

### Authentication in Tests

Use the `auth_headers` fixture for authenticated requests:

```python
def test_authenticated_endpoint(auth_headers):
    headers = auth_headers("user@example.com")
    response = client.get("/api/v1/protected", headers=headers)
    assert response.status_code == 200
```

### Database Testing

Use the `db_session` fixture for database operations:

```python
def test_database_operation(db_session):
    # Create test data
    company = Company(name="Test Company")
    db_session.add(company)
    db_session.commit()
    
    # Test database query
    result = db_session.query(Company).filter_by(name="Test Company").first()
    assert result is not None
```

## Test Coverage

### Coverage Goals

- Overall coverage: 80%+
- Critical paths: 95%+
- Security functions: 100%
- API endpoints: 90%+

### Coverage Reports

Coverage reports are generated in:
- HTML: `test_coverage/html/index.html`
- XML: `test_coverage/coverage.xml`
- Terminal: Displayed during test run

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled runs

### Test Matrix

Tests run on:
- Python 3.8, 3.9, 3.10, 3.11
- SQLite (default)
- PostgreSQL (integration tests)
- Redis (caching tests)

## Debugging Tests

### Verbose Output

```bash
# Very verbose output
pytest app/tests/test_auth.py -vvv

# Show local variables on failure
pytest app/tests/test_auth.py -l

# Drop into debugger on failure
pytest app/tests/test_auth.py --pdb
```

### Test Isolation

Each test runs in isolation:
- Fresh database
- Clean Redis cache
- Mocked external services
- Independent test data

### Common Issues

1. **Database conflicts**: Ensure tests use `db_session` fixture
2. **Authentication errors**: Use `auth_headers` fixture
3. **External service calls**: Mock external APIs
4. **Async tests**: Use `pytest-asyncio` markers

## Performance Testing

### Load Testing

```bash
# Run load tests
pytest app/tests/test_load_testing.py -v

# Run performance tests
pytest app/tests/test_performance.py -v -m "slow"
```

### Benchmarking

Performance tests measure:
- Response times
- Throughput (requests/second)
- Memory usage
- Database query performance

## Security Testing

### Security Test Categories

1. **Authentication Security**
   - Brute force protection
   - Account lockout
   - Password strength
   - Token expiration

2. **Authorization Security**
   - Role-based access control
   - Data isolation
   - Privilege escalation prevention

3. **Input Validation**
   - SQL injection prevention
   - XSS prevention
   - Input length validation
   - Type coercion attacks

4. **API Security**
   - Rate limiting
   - Request size limiting
   - Malicious header handling

## Best Practices

### Test Naming

- Use descriptive test names
- Include the scenario being tested
- Use `test_` prefix for all test functions

### Test Organization

- Group related tests in classes
- Use fixtures for common setup
- Keep tests independent
- Use factories for test data

### Assertions

- Use specific assertions
- Test both success and failure cases
- Verify side effects
- Check error messages

### Mocking

- Mock external services
- Mock time-dependent functions
- Mock random functions
- Use `unittest.mock.patch`

## Troubleshooting

### Common Errors

1. **ImportError**: Check Python path and virtual environment
2. **Database errors**: Ensure test database is clean
3. **Authentication errors**: Check token generation
4. **Timeout errors**: Increase timeout for slow tests

### Debug Commands

```bash
# Run single test with debug output
pytest app/tests/test_auth.py::test_user_login -vvv -s

# Run tests with coverage and debug
pytest app/tests/ --cov=app --cov-report=term-missing -vvv

# Run tests and stop on first failure
pytest app/tests/ -x
```

## Contributing

### Adding New Tests

1. Create test file following naming convention
2. Use appropriate fixtures
3. Add proper markers
4. Write comprehensive test cases
5. Update this guide if needed

### Test Review

When reviewing tests:
- Check test coverage
- Verify test independence
- Ensure proper mocking
- Validate assertions
- Check performance impact

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
