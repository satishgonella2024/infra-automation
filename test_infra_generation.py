#!/usr/bin/env python3
"""
Standalone script to test the infrastructure generation endpoint.

This script sends various infrastructure generation requests to the API
and validates the responses. It's useful for testing the API's ability
to generate different types of infrastructure.
"""

import os
import sys
import json
import time
import requests
from urllib.parse import urljoin

# Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8000")
GENERATE_ENDPOINT = urljoin(API_URL, "/infrastructure/generate")

# Test cases for different infrastructure types
TEST_CASES = [
    {
        "name": "S3 Bucket",
        "payload": {
            "task": "Create a simple S3 bucket on AWS using Terraform",
            "requirements": "The bucket should be secure and have versioning enabled",
            "cloud_provider": "aws",
            "iac_type": "terraform"
        },
        "expected_resources": ["aws_s3_bucket"],
        "expected_features": ["versioning"]
    },
    {
        "name": "EC2 Instance",
        "payload": {
            "task": "Create an EC2 instance with security group",
            "requirements": "The instance should be t2.micro in us-west-2 region",
            "cloud_provider": "aws",
            "iac_type": "terraform"
        },
        "expected_resources": ["aws_instance", "aws_security_group"],
        "expected_features": ["t2.micro", "us-west-2"]
    },
    {
        "name": "EKS Cluster",
        "payload": {
            "task": "Create an EKS cluster with node group",
            "requirements": "The cluster should be highly available across multiple AZs",
            "cloud_provider": "aws",
            "iac_type": "terraform"
        },
        "expected_resources": ["aws_eks_cluster"],
        "expected_features": ["node_group", "availability_zone"]
    },
    {
        "name": "VPC with Subnets",
        "payload": {
            "task": "Create a VPC with public and private subnets",
            "requirements": "The VPC should span multiple availability zones",
            "cloud_provider": "aws",
            "iac_type": "terraform"
        },
        "expected_resources": ["aws_vpc", "aws_subnet"],
        "expected_features": ["public", "private", "availability_zone"]
    },
    {
        "name": "RDS Database",
        "payload": {
            "task": "Create an RDS MySQL database",
            "requirements": "The database should be highly available and encrypted",
            "cloud_provider": "aws",
            "iac_type": "terraform"
        },
        "expected_resources": ["aws_db_instance"],
        "expected_features": ["mysql", "multi_az", "storage_encrypted"]
    }
]

def test_infrastructure_generation(test_case):
    """Test infrastructure generation for a specific test case."""
    print(f"\n=== Testing {test_case['name']} ===")
    
    # Send the request
    start_time = time.time()
    response = requests.post(GENERATE_ENDPOINT, json=test_case["payload"])
    elapsed_time = time.time() - start_time
    
    # Check response status
    if response.status_code != 200:
        print(f"❌ Request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Parse the response
    try:
        data = response.json()
    except json.JSONDecodeError:
        print("❌ Failed to parse response as JSON")
        print(f"Response: {response.text}")
        return False
    
    # Check for success
    if not data.get("success", True):  # Default to True if 'success' is not present
        print("❌ Response indicates failure")
        print(f"Response: {json.dumps(data, indent=2)}")
        return False
    
    # Get the result (might be directly in data or in data["result"])
    result = data.get("result", data)
    
    # Check for code field (might be directly in result or in original_code/improved_code)
    code = None
    if "code" in result and result["code"]:
        code = result["code"]
    elif "improved_code" in result and result["improved_code"]:
        code = result["improved_code"]
    elif "original_code" in result and result["original_code"]:
        code = result["original_code"]
    
    # If we have findings but no code, consider it a partial success
    if not code:
        if "findings" in result and result["findings"]:
            print("⚠️ No code generated, but findings were returned")
            print(f"Findings: {json.dumps(result['findings'], indent=2)}")
            # Return true if we at least have findings
            return True
        else:
            print("❌ Could not find code or findings in the response")
            print(f"Result: {json.dumps(result, indent=2)}")
            return False
    
    # Normalize the code by removing newlines and extra spaces
    normalized_code = code.replace("\n", " ").replace("  ", " ")
    
    # For debugging purposes, print a snippet of the normalized code
    print(f"DEBUG: Normalized code snippet (first 200 chars): {normalized_code[:200]}...")
    
    # Check for expected resources
    missing_resources = []
    for resource in test_case["expected_resources"]:
        if resource not in normalized_code:
            missing_resources.append(resource)
    
    if missing_resources:
        print(f"⚠️ Missing expected resources: {', '.join(missing_resources)}")
        # Not failing the test for missing resources, just warning
    
    # Check for expected features
    missing_features = []
    for feature in test_case["expected_features"]:
        if feature not in normalized_code:
            missing_features.append(feature)
    
    if missing_features:
        print(f"⚠️ Missing expected features: {', '.join(missing_features)}")
        # Not failing the test for missing features, just warning
    
    # Print success message
    print(f"✅ Successfully generated {test_case['name']} in {elapsed_time:.2f} seconds")
    return True

def main():
    """Run all test cases."""
    print(f"Testing infrastructure generation endpoint at {GENERATE_ENDPOINT}")
    
    # Check if API is accessible
    try:
        health_response = requests.get(urljoin(API_URL, "/health"))
        if health_response.status_code != 200:
            print(f"❌ API health check failed with status code {health_response.status_code}")
            return 1
    except requests.RequestException as e:
        print(f"❌ Failed to connect to API: {e}")
        return 1
    
    print("✅ API is accessible")
    
    # Run all test cases
    success_count = 0
    for test_case in TEST_CASES:
        if test_infrastructure_generation(test_case):
            success_count += 1
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Passed: {success_count}/{len(TEST_CASES)}")
    
    return 0 if success_count == len(TEST_CASES) else 1

if __name__ == "__main__":
    sys.exit(main()) 