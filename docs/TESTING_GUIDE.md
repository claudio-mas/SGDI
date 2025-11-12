# Testing Guide - SGDI

## Overview

This document describes the testing strategy and procedures for SGDI. The test suite includes end-to-end integration tests, security tests, and performance tests to ensure the system meets all requirements.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_e2e_flows.py        # End-to-end integration tests
├── test_security.py         # Security and vulnerability tests
└── test_performance.py      # Performance and load tests
```

## Prerequisites

### Install Testing Dependencies

```bash
pip install -r requirements.txt
```

The following testing packages will be installed:
- pytest: Testing framework
- pytest-flask: Flask testing utilities
- pytest-cov: Code coverage reporting

### Database Setup

Tests use an in-memory SQLite database by default (configured in `config.py` under `TestingConfig`). No additional database setup is required.

## Running Tests

### Run All Tests

```bash
# Run all tests with coverage report
python run_tests.py

# Or use pytest directly
pytest tests/ -v --cov=app --cov-report=html
```

### Run Specific Test Suites

```bash
# End-to-end tests only
python run_tests.py e2e

# Security tests only
python run_tests.py security

# Performance tests only
python run_tests.py performance
```

### Run Individual Test Files

```bash
# Run specific test file
pytest tests/test_e2e_flows.py -v

# Run specific test class
pytest tests/test_e2e_flows.py::TestUserAuthenticationFlow -v

# Run specific test method
pytest tests/test_e2e_flows.py::TestUserAuthenticationFlow::test_user_login_flow -v
```

## Test Coverage

### End-to-End Integration Tests (test_e2e_flows.py)

Tests complete user workflows through the system:

#### User Authentication Flow
- ✓ User login with valid credentials
- ✓ Login failure with invalid credentials
- ✓ User logout
- ✓ Password reset request

#### Document Management Flow
- ✓ Document upload with metadata
- ✓ Document search
- ✓ Document download
- ✓ Document metadata update
- ✓ Document deletion (soft delete)

#### Permission and Sharing Flow
- ✓ Document sharing with other users
- ✓ Permission checking and enforcement

#### Workflow Approval Flow
- ✓ Document submission to workflow
- ✓ Document approval/rejection

#### Audit Logging
- ✓ Audit log creation for operations
- ✓ Audit log viewing by administrators

**Requirements Covered:** All requirements (1.1-15.3)

### Security Tests (test_security.py)

Tests security features and vulnerability protection:

#### Authentication Security
- ✓ Login required protection
- ✓ Brute force protection (account lockout)
- ✓ Session timeout
- ✓ Password hashing (bcrypt)
- ✓ Role-based access control (RBAC)

#### CSRF Protection
- ✓ CSRF token requirement
- ✓ CSRF token validation
- ✓ CSRF tokens in forms

#### Rate Limiting
- ✓ Rate limit configuration
- ✓ Rate limit enforcement

#### SQL Injection Protection
- ✓ SQL injection in login
- ✓ SQL injection in search
- ✓ Parameterized queries (ORM)
- ✓ SQL injection in filters

#### XSS Protection
- ✓ XSS in document names
- ✓ XSS in search results
- ✓ XSS in user input
- ✓ Content Security Policy

#### Security Headers
- ✓ Security headers configuration
- ✓ HTTPS enforcement
- ✓ Secure cookie settings

#### File Upload Security
- ✓ File type validation
- ✓ File size limits
- ✓ Path traversal protection

**Requirements Covered:** 14.1, 14.2, 14.3, 14.4, 14.5

### Performance Tests (test_performance.py)

Tests system performance under load:

#### Concurrent Users
- ✓ 50 concurrent login requests
- ✓ 100 concurrent document views
- ✓ 100 concurrent search requests

#### File Upload Performance
- ✓ Single 5MB file upload time
- ✓ Multiple 1MB file uploads
- ✓ 10 concurrent file uploads

#### Search Performance
- ✓ Search with 100+ documents
- ✓ Advanced search with filters
- ✓ Search pagination performance

#### Page Load Times
- ✓ Login page load time (< 2s)
- ✓ Document list page load time (< 2s)
- ✓ Document detail page load time (< 2s)
- ✓ Admin dashboard load time (< 3s)

#### Database Performance
- ✓ Document query performance
- ✓ Category hierarchy query performance

**Requirements Covered:** 13.1, 13.2, 13.3, 13.4, 13.5

## Test Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

- `app`: Flask application configured for testing
- `client`: Test client for making requests
- `db_session`: Database session with automatic cleanup
- `test_user`: Standard user for testing
- `admin_user`: Administrator user for testing
- `test_category`: Test document category
- `authenticated_client`: Pre-authenticated test client
- `admin_client`: Pre-authenticated admin client

## Performance Benchmarks

Expected performance metrics:

| Metric | Target | Test |
|--------|--------|------|
| 50 concurrent logins | < 10s | ✓ |
| 100 concurrent document views | < 15s | ✓ |
| 100 concurrent searches | < 20s | ✓ |
| 5MB file upload | < 5s | ✓ |
| 10 concurrent 1MB uploads | < 30s | ✓ |
| Search 100+ documents | < 3s | ✓ |
| Page load time | < 2s | ✓ |
| Database query (50 docs) | < 1s | ✓ |

## Coverage Reports

After running tests with coverage, view the HTML report:

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# Open report in browser (Windows)
start htmlcov/index.html

# Open report in browser (Linux/Mac)
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## Troubleshooting

### Common Issues

#### Import Errors

If you encounter import errors:

```bash
# Ensure you're in the project root directory
cd /path/to/sistema-ged

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%      # Windows
```

#### Database Errors

If database tests fail:

```bash
# Ensure SQLite is available (usually built into Python)
python -c "import sqlite3; print(sqlite3.version)"

# Clear any test database files
rm -f test.db
```

#### Performance Test Timeouts

If performance tests timeout:

- Reduce the number of concurrent requests
- Increase timeout thresholds in test assertions
- Check system resources (CPU, memory)

#### File Upload Tests

If file upload tests fail:

- Ensure upload directory exists and is writable
- Check MAX_CONTENT_LENGTH configuration
- Verify file permissions

## Best Practices

### Writing New Tests

1. **Use Fixtures**: Leverage existing fixtures for common setup
2. **Isolate Tests**: Each test should be independent
3. **Clean Up**: Use fixtures with automatic cleanup
4. **Descriptive Names**: Use clear, descriptive test names
5. **Assert Clearly**: Use specific assertions with messages

### Test Organization

```python
class TestFeatureName:
    """Test description"""
    
    def test_specific_behavior(self, fixture1, fixture2):
        """Test what this specific behavior does"""
        # Arrange
        setup_data = create_test_data()
        
        # Act
        result = perform_action(setup_data)
        
        # Assert
        assert result == expected_value
```

### Performance Testing

- Use `time.time()` for timing measurements
- Print performance metrics for visibility
- Set reasonable thresholds based on requirements
- Test with realistic data volumes

### Security Testing

- Test both positive and negative cases
- Verify error handling doesn't leak information
- Test boundary conditions
- Check for common vulnerabilities (OWASP Top 10)

## Test Maintenance

### Regular Updates

- Update tests when requirements change
- Add tests for new features
- Refactor tests to reduce duplication
- Keep fixtures up to date

### Code Coverage Goals

- Minimum: 70% overall coverage
- Critical paths: 90%+ coverage
- Security features: 100% coverage

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Flask Testing Documentation](https://flask.palletsprojects.com/en/latest/testing/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

## Support

For questions or issues with testing:

1. Check this documentation
2. Review test code comments
3. Check pytest output for detailed error messages
4. Review application logs in `logs/` directory
