# Sistema SGDI Test Suite

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Tests

```bash
# Run all tests
python run_tests.py

# Or use pytest directly
pytest tests/ -v
```

## Test Files

- `conftest.py` - Pytest configuration and fixtures
- `test_e2e_flows.py` - End-to-end integration tests
- `test_security.py` - Security and vulnerability tests
- `test_performance.py` - Performance and load tests

## Requirements Coverage

### Task 25.1: End-to-End Testing ✓
- User registration and login flow
- Document upload, search, and download flow
- Permission and sharing functionality
- Workflow approval process
- Audit logging verification

### Task 25.2: Security Testing ✓
- Authentication and authorization
- CSRF protection
- Rate limiting
- SQL injection protection
- XSS protection

### Task 25.3: Performance Testing ✓
- Concurrent user load testing
- File upload performance
- Search performance
- Page load times

## Documentation

See `docs/TESTING_GUIDE.md` for comprehensive testing documentation.
