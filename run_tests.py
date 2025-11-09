"""
Test Runner Script for Sistema GED
Runs all tests and generates coverage reports
"""
import sys
import subprocess


def run_all_tests():
    """Run all tests with coverage"""
    print("=" * 70)
    print("Running Sistema GED Test Suite")
    print("=" * 70)
    
    cmd = [
        'pytest',
        'tests/',
        '-v',
        '--cov=app',
        '--cov-report=html',
        '--cov-report=term-missing'
    ]
    
    result = subprocess.run(cmd)
    return result.returncode


def run_e2e_tests():
    """Run only end-to-end tests"""
    print("=" * 70)
    print("Running End-to-End Tests")
    print("=" * 70)
    
    cmd = [
        'pytest',
        'tests/test_e2e_flows.py',
        '-v'
    ]
    
    result = subprocess.run(cmd)
    return result.returncode


def run_security_tests():
    """Run only security tests"""
    print("=" * 70)
    print("Running Security Tests")
    print("=" * 70)
    
    cmd = [
        'pytest',
        'tests/test_security.py',
        '-v'
    ]
    
    result = subprocess.run(cmd)
    return result.returncode


def run_performance_tests():
    """Run only performance tests"""
    print("=" * 70)
    print("Running Performance Tests")
    print("=" * 70)
    
    cmd = [
        'pytest',
        'tests/test_performance.py',
        '-v',
        '-s'  # Show print statements for performance metrics
    ]
    
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'e2e':
            sys.exit(run_e2e_tests())
        elif test_type == 'security':
            sys.exit(run_security_tests())
        elif test_type == 'performance':
            sys.exit(run_performance_tests())
        else:
            print(f"Unknown test type: {test_type}")
            print("Usage: python run_tests.py [e2e|security|performance]")
            sys.exit(1)
    else:
        sys.exit(run_all_tests())
