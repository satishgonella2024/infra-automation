"""
Tests for the API endpoints.

These tests verify that the API endpoints correctly handle requests and responses.
"""

import pytest
import json
from fastapi.testclient import TestClient

# Sample data for tests
SAMPLE_EKS_CODE = """
resource "aws_eks_cluster" "example" {
  name     = "example"
  role_arn = aws_iam_role.example.arn

  vpc_config {
    subnet_ids = [aws_subnet.example1.id, aws_subnet.example2.id]
  }
}
"""

SAMPLE_PATTERN = {
    "name": "EKS Cluster",
    "description": "A basic EKS cluster",
    "cloud_provider": "aws",
    "iac_type": "terraform",
    "code": SAMPLE_EKS_CODE,
    "metadata": {
        "category": "container",
        "complexity": "medium",
        "tags": ["eks", "kubernetes", "aws"]
    }
}

def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "services": {
            "llm": "healthy",
            "vector_db": "healthy"
        }
    }

def test_add_pattern(test_client, mock_vector_db):
    """Test adding a pattern."""
    # Configure the mock to return a pattern ID
    mock_vector_db.add_pattern.return_value = {"id": "test-pattern-id"}
    
    # Make the request
    response = test_client.post(
        "/patterns",
        json=SAMPLE_PATTERN
    )
    
    # Check the response
    assert response.status_code == 200
    assert response.json() == {"success": True, "pattern_id": "test-pattern-id"}
    
    # Check that the vector DB was called correctly
    mock_vector_db.add_pattern.assert_called_once()
    args = mock_vector_db.add_pattern.call_args[0][0]
    assert args["name"] == SAMPLE_PATTERN["name"]
    assert args["code"] == SAMPLE_PATTERN["code"]

def test_search_patterns(test_client, mock_vector_db):
    """Test searching for patterns."""
    # Configure the mock to return patterns
    mock_vector_db.search_patterns.return_value = [
        {
            "id": "pattern1",
            "name": "EKS Cluster",
            "description": "A basic EKS cluster",
            "cloud_provider": "aws",
            "iac_type": "terraform",
            "code": SAMPLE_EKS_CODE,
            "metadata": {
                "category": "container",
                "complexity": "medium",
                "tags": ["eks", "kubernetes", "aws"]
            }
        }
    ]
    
    # Make the request
    response = test_client.get(
        "/patterns/search?query=eks&cloud_provider=aws&iac_type=terraform"
    )
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["patterns"]) == 1
    assert response.json()["patterns"][0]["id"] == "pattern1"
    
    # Check that the vector DB was called correctly
    mock_vector_db.search_patterns.assert_called_once_with(
        query="eks",
        cloud_provider="aws",
        iac_type="terraform",
        n_results=5
    )

def test_update_pattern(test_client, mock_vector_db):
    """Test updating a pattern."""
    # Configure the mock to return a pattern ID
    mock_vector_db.update_pattern.return_value = {"id": "test-pattern-id"}
    
    # Make the request
    response = test_client.put(
        "/patterns/test-pattern-id",
        json=SAMPLE_PATTERN
    )
    
    # Check the response
    assert response.status_code == 200
    assert response.json() == {"success": True, "pattern_id": "test-pattern-id"}
    
    # Check that the vector DB was called correctly
    mock_vector_db.update_pattern.assert_called_once()
    args = mock_vector_db.update_pattern.call_args[0]
    assert args[0] == "test-pattern-id"
    assert args[1]["name"] == SAMPLE_PATTERN["name"]
    assert args[1]["code"] == SAMPLE_PATTERN["code"]

def test_delete_pattern(test_client, mock_vector_db):
    """Test deleting a pattern."""
    # Configure the mock to return a pattern ID
    mock_vector_db.delete_pattern.return_value = {"id": "test-pattern-id"}
    
    # Make the request
    response = test_client.delete("/patterns/test-pattern-id")
    
    # Check the response
    assert response.status_code == 200
    assert response.json() == {"success": True, "pattern_id": "test-pattern-id"}
    
    # Check that the vector DB was called correctly
    mock_vector_db.delete_pattern.assert_called_once_with("test-pattern-id")

def test_generate_infrastructure(test_client, mock_vector_db, mock_architecture_agent):
    """Test generating infrastructure."""
    # Configure the mocks
    mock_vector_db.search_patterns.return_value = []
    mock_architecture_agent.process.return_value = {
        "task_id": "generate_infra",
        "original_code": SAMPLE_EKS_CODE,
        "improved_code": SAMPLE_EKS_CODE,
        "findings": {
            "reliability": [],
            "security": [],
            "cost_optimization": [],
            "performance": [],
            "operational_excellence": [],
            "critical_issues": [],
            "recommendations": []
        }
    }
    
    # Make the request
    response = test_client.post(
        "/infrastructure/generate",
        json={
            "task": "Create an EKS cluster",
            "requirements": "Need a Kubernetes cluster",
            "cloud_provider": "aws",
            "iac_type": "terraform"
        }
    )
    
    # Check the response
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["result"]["task_id"] == "generate_infra"
    assert "original_code" in response.json()["result"]
    
    # Check that the services were called correctly
    mock_vector_db.search_patterns.assert_called_once()
    mock_architecture_agent.process.assert_called_once()
    args = mock_architecture_agent.process.call_args[0][0]
    assert args["task"] == "Create an EKS cluster"
    assert args["requirements"] == "Need a Kubernetes cluster"
    assert args["cloud_provider"] == "aws"
    assert args["iac_type"] == "terraform"

# Run the tests if this file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 