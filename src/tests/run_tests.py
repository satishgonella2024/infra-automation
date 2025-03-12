#!/usr/bin/env python3
"""
Test runner script for the Infrastructure Automation service.

This script runs all the tests in the tests directory and generates a report.
"""

import os
import sys
import pytest
import time
import argparse
from datetime import datetime

def run_tests(include_integration=False):
    """Run all tests and generate a report.
    
    Args:
        include_integration: Whether to include integration tests that require
            running services.
    """
    print("=" * 80)
    print(f"Starting Infrastructure Automation tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get the directory of this script
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Start timer
    start_time = time.time()
    
    # Run the tests with pytest
    test_files = [
        os.path.join(tests_dir, "test_api_endpoints.py"),
        os.path.join(tests_dir, "test_architecture_agent.py"),
        os.path.join(tests_dir, "test_llm_service.py"),
        os.path.join(tests_dir, "test_chroma_service.py")
    ]
    
    # Add integration tests if requested
    if include_integration:
        test_files.append(os.path.join(tests_dir, "test_integration.py"))
        print("Including integration tests that require running services")
    
    # Run tests with verbose output and stop on first failure
    result = pytest.main(["-xvs"] + test_files)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print(f"Test execution completed in {execution_time:.2f} seconds")
    
    if result == 0:
        print("✅ All tests passed successfully!")
    else:
        print(f"❌ Tests failed with exit code {result}")
    
    print("=" * 80)
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Infrastructure Automation tests")
    parser.add_argument("--integration", action="store_true", 
                        help="Include integration tests that require running services")
    args = parser.parse_args()
    
    sys.exit(run_tests(include_integration=args.integration)) 