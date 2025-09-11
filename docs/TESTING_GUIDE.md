# Testing Guide

This guide provides comprehensive information about testing practices, patterns, and tools used in the Common Supply Chain Platform.

## Overview

Our test suite is designed with enterprise-grade quality standards, featuring:

- **Comprehensive Business Logic Validation**: Tests validate real business rules and edge cases
- **Standardized Infrastructure**: Centralized fixtures and reusable patterns
- **Performance Optimization**: Parallel execution and categorized test runs
- **Coverage Analysis**: Detailed coverage reporting and gap identification

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 30 seconds total)
- **Scope**: Single functions, methods, or classes
- **Dependencies**: Minimal, use mocks for external services

```bash
# Run all unit tests
pytest -m unit

# Run unit tests in parallel
pytest -m unit -n auto
```

### Integration Tests (`@pytest.mark.integration`)
- **Purpose**: Test component interactions
- **Speed**: Medium (30-120 seconds)
- **Scope**: Multiple components working together
- **Dependencies**: Database, some external services

```bash
# Run integration tests
pytest -m integration
```

### End-to-End Tests (`@pytest.mark.e2e`)
- **Purpose**: Test complete user workflows
- **Speed**: Slow (2-10 minutes)
- **Scope**: Full application stack
- **Dependencies**: All services, external APIs

```bash
# Run e2e tests
pytest -m e2e
```

## Domain-Specific Test Categories

### Authentication Tests (`@pytest.mark.auth`)
- User login/logout flows
- Token validation and refresh
- Role-based access control
- Security boundary testing

### API Tests (`@pytest.mark.api`)
- Endpoint functionality
- Request/response validation
- Error handling
- Rate limiting

### Business Logic Tests (`@pytest.mark.business_logic`)
- Supply chain rules
- Purchase order validation
- Product composition requirements
- Compliance checking

## Test Infrastructure

### Centralized Fixtures (`app/tests/conftest.py`)

Our test infrastructure provides standardized fixtures for consistent testing:

```python
# Database and session management
def db_session():
    """Provides clean database session for each test."""

# Authentication helpers
def authenticated_client(role="buyer"):
    """Returns client with authentication headers."""

# Business entity fixtures
def test_company():
    """Standard test company with business context."""

def test_user():
    """Standard test user with proper relationships."""

def test_purchase_order():
    """Standard PO with business validation."""
```

### Business Logic Validators

Reusable validation helpers ensure consistent business rule testing:

```python
def business_logic_validator():
    """Provides business logic validation helpers."""
    
    # Token validation
    validator.validate_token_response(data)
    
    # User permissions
    validator.validate_user_permissions(user_data, role)
    
    # Purchase order validation
    validator.validate_purchase_order(po_data)
```

## Writing Quality Tests

### Business Logic Validation Pattern

Our tests follow a comprehensive business logic validation pattern:

```python
def test_purchase_order_business_logic(db_session, test_purchase_order, business_logic_validator):
    """Test purchase order business logic validation."""
    po = test_purchase_order
    
    # Business Logic: PO should have valid business relationships
    assert po.buyer_company_id is not None
    assert po.seller_company_id is not None
    assert po.buyer_company_id != po.seller_company_id
    
    # Business Logic: Financial validation
    assert po.quantity > 0
    assert po.unit_price > 0
    assert po.total_value == po.quantity * po.unit_price
    
    # Business Logic: Status workflow validation
    valid_statuses = ["draft", "sent", "confirmed", "fulfilled", "cancelled"]
    assert po.status in valid_statuses
    
    # Use business logic validator for complex rules
    business_logic_validator.validate_purchase_order({
        "id": str(po.id),
        "status": po.status,
        "total_value": float(po.total_value)
    })
```

### Test Naming Conventions

- **Function Names**: `test_[component]_[business_scenario]_business_logic`
- **Descriptive**: Clearly indicate what business rule is being tested
- **Consistent**: Follow established patterns across the codebase

### Test Structure

1. **Arrange**: Set up test data and context
2. **Act**: Execute the functionality being tested
3. **Assert**: Validate business logic and expected outcomes

```python
def test_user_authentication_business_logic(db_session, test_user):
    """Test user authentication business logic."""
    
    # Arrange: Set up test context
    user = test_user
    
    # Act: Perform authentication
    response = client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": "testpassword123"
    })
    
    # Assert: Validate business logic
    assert response.status_code == 200
    data = response.json()
    
    # Business Logic: Token structure validation
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Business Logic: Token expiration validation
    assert 900 <= data["access_expires_in"] <= 3600
```

## Performance Optimization

### Parallel Test Execution

Use pytest-xdist for parallel execution of unit tests:

```bash
# Automatic parallel execution
pytest -m unit -n auto

# Specific number of workers
pytest -m unit -n 4
```

### Test Performance Analysis

Use our performance analysis script:

```bash
# Quick smoke test
python scripts/test_performance.py --smoke

# Full performance analysis
python scripts/test_performance.py --analysis

# Category-specific analysis
python scripts/test_performance.py --category unit
```

## Coverage Analysis

### Running Coverage Analysis

```bash
# Basic coverage
pytest --cov=app --cov-report=term-missing

# Detailed coverage with HTML report
pytest --cov=app --cov-branch --cov-report=html

# Coverage analysis script
python scripts/test_coverage_analysis.py --report coverage_report.md
```

### Coverage Goals

- **Overall Coverage**: 80%+ across the codebase
- **Critical Components**: 90%+ for models, services, and API endpoints
- **Business Logic**: 95%+ for core business rules and validations

## Common Testing Patterns

### Authentication Testing

```python
def test_protected_endpoint_requires_auth(client):
    """Test that protected endpoints require authentication."""
    response = client.get("/api/v1/protected-endpoint")
    assert response.status_code == 401
    
def test_role_based_access_control(authenticated_client):
    """Test role-based access control."""
    # Test with buyer role
    buyer_client = authenticated_client(role="buyer")
    response = buyer_client.get("/api/v1/purchase-orders")
    assert response.status_code == 200
    
    # Test with admin role
    admin_client = authenticated_client(role="admin")
    response = admin_client.get("/api/v1/admin/users")
    assert response.status_code == 200
```

### Database Testing

```python
def test_model_relationships(db_session, test_company, test_user):
    """Test database model relationships."""
    company = test_company
    user = test_user
    
    # Business Logic: User should belong to company
    assert user.company_id == company.id
    assert user in company.users
```

### API Testing

```python
def test_api_endpoint_validation(client, authenticated_client):
    """Test API endpoint input validation."""
    client = authenticated_client()
    
    # Test valid input
    valid_data = {"name": "Test Product", "category": "palm_oil"}
    response = client.post("/api/v1/products", json=valid_data)
    assert response.status_code == 201
    
    # Test invalid input
    invalid_data = {"name": "", "category": "invalid"}
    response = client.post("/api/v1/products", json=invalid_data)
    assert response.status_code == 422
```

## Best Practices

1. **Test Business Logic**: Focus on validating business rules, not just technical functionality
2. **Use Descriptive Names**: Test names should clearly indicate what business scenario is being tested
3. **Maintain Test Data**: Use factories and fixtures for consistent, realistic test data
4. **Isolate Tests**: Each test should be independent and not rely on other tests
5. **Mock External Dependencies**: Use mocks for external APIs, services, and slow operations
6. **Validate Edge Cases**: Test boundary conditions and error scenarios
7. **Keep Tests Fast**: Unit tests should run quickly; use integration tests for slower scenarios
8. **Document Complex Logic**: Add comments explaining complex business rules being tested

## Troubleshooting

### Common Issues

1. **Database Conflicts**: Use unique test data to avoid constraint violations
2. **Authentication Failures**: Ensure test users have proper roles and permissions
3. **Slow Tests**: Profile test execution and optimize database operations
4. **Flaky Tests**: Identify and fix non-deterministic behavior

### Debugging Tests

```bash
# Run with verbose output
pytest -v

# Run specific test with debugging
pytest -v -s app/tests/unit/test_auth.py::test_user_login

# Run with pdb debugger
pytest --pdb app/tests/unit/test_auth.py::test_user_login
```

## Continuous Integration

Our CI pipeline runs tests in multiple stages:

1. **Smoke Tests**: Quick validation of core functionality
2. **Unit Tests**: Fast, isolated component tests
3. **Integration Tests**: Component interaction validation
4. **Coverage Analysis**: Ensure adequate test coverage
5. **Performance Analysis**: Monitor test execution performance

## Contributing

When adding new tests:

1. Follow the established patterns and naming conventions
2. Include comprehensive business logic validation
3. Add appropriate test markers for categorization
4. Update documentation for new testing patterns
5. Ensure tests pass in CI environment

For questions or guidance on testing practices, refer to this guide or consult with the development team.
