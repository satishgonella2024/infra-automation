#!/usr/bin/env python3

import os
import sys
import subprocess
import time

def run_test(test_name):
    """Run a specific test and return True if it passes, False otherwise."""
    print(f"\n\n=== Running test: {test_name} ===\n")
    
    cmd = [
        "python", "-m", "pytest", 
        f"src/tests/test_integration.py::{test_name}", 
        "-v"
    ]
    
    env = os.environ.copy()
    env["API_URL"] = "http://localhost:8000"
    env["OLLAMA_URL"] = "http://localhost:11434"
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30  # Set a timeout of 30 seconds
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"Test {test_name} timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"Error running test {test_name}: {e}")
        return False

def main():
    """Run all tests one by one."""
    tests = [
        "test_api_health",
        "test_ollama_connection",
        "test_infrastructure_generation_basic",
        "test_infrastructure_generation_ec2",
        "test_infrastructure_generation_eks",
        "test_infrastructure_generation_vpc",
        "test_infrastructure_generation_rds",
        "test_infrastructure_generation_response_structure",
        "test_infrastructure_generation_missing_fields",
        "test_infrastructure_generation_invalid_cloud_provider",
        "test_infrastructure_generation_invalid_values"
    ]
    
    results = {}
    
    for test in tests:
        results[test] = run_test(test)
        time.sleep(1)  # Add a small delay between tests
    
    # Print summary
    print("\n\n=== Test Summary ===\n")
    passed = 0
    failed = 0
    
    for test, result in results.items():
        status = "PASSED" if result else "FAILED"
        if result:
            passed += 1
        else:
            failed += 1
        print(f"{test}: {status}")
    
    print(f"\nTotal: {len(tests)}, Passed: {passed}, Failed: {failed}")
    
    # Return non-zero exit code if any test failed
    return 1 if failed > 0 else 0

if __name__ == "__main__":
    sys.exit(main()) 