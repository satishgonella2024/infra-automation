"""
Tests for the ArchitectureAgent class.

These tests verify that the ArchitectureAgent correctly reviews and improves
infrastructure code, and can generate new infrastructure based on requirements.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.agents.architect.architecture_agent import ArchitectureAgent
from src.services.llm.llm_service import LLMService

# Sample data for tests
SAMPLE_EKS_CODE = """
resource "aws_eks_cluster" "example" {
  name     = "example"
  role_arn = aws_iam_role.example.arn

  vpc_config {
    subnet_ids = [aws_subnet.example1.id, aws_subnet.example2.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.example-AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.example-AmazonEKSVPCResourceController,
  ]
}
"""

IMPROVED_EKS_CODE = """
resource "aws_eks_cluster" "example" {
  name     = "example"
  role_arn = aws_iam_role.example.arn

  vpc_config {
    subnet_ids = [aws_subnet.example1.id, aws_subnet.example2.id]
    security_group_ids = [aws_security_group.eks_cluster.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.example-AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.example-AmazonEKSVPCResourceController,
  ]
  
  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
"""

SAMPLE_FINDINGS = {
    "reliability": ["Single point of failure: only two subnets used"],
    "security": ["No security groups specified"],
    "cost_optimization": [],
    "performance": [],
    "operational_excellence": ["Missing resource tagging"],
    "critical_issues": ["No security groups specified"],
    "recommendations": ["Add security groups", "Add resource tagging"]
}

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    mock_service = MagicMock(spec=LLMService)
    mock_service.generate_completion = AsyncMock()
    return mock_service

@pytest.fixture
def architecture_agent(mock_llm_service):
    """Create an ArchitectureAgent instance for testing."""
    return ArchitectureAgent(llm_service=mock_llm_service)

@pytest.mark.asyncio
async def test_review_architecture(architecture_agent, mock_llm_service):
    """Test that the review_architecture method correctly analyzes infrastructure code."""
    # Configure the mock to return a JSON string with findings
    mock_llm_service.generate_completion.return_value = """
    {
        "reliability": ["Single point of failure: only two subnets used"],
        "security": ["No security groups specified"],
        "cost_optimization": [],
        "performance": [],
        "operational_excellence": ["Missing resource tagging"],
        "critical_issues": ["No security groups specified"],
        "recommendations": ["Add security groups", "Add resource tagging"]
    }
    """
    
    # Configure the mock to return improved code on the second call
    mock_llm_service.generate_completion.side_effect = [
        # First call returns findings
        """
        {
            "reliability": ["Single point of failure: only two subnets used"],
            "security": ["No security groups specified"],
            "cost_optimization": [],
            "performance": [],
            "operational_excellence": ["Missing resource tagging"],
            "critical_issues": ["No security groups specified"],
            "recommendations": ["Add security groups", "Add resource tagging"]
        }
        """,
        # Second call returns improved code
        f"```\n{IMPROVED_EKS_CODE}\n```"
    ]
    
    # Call the method
    improved_code, findings = await architecture_agent.review_architecture(
        SAMPLE_EKS_CODE, "aws", "terraform"
    )
    
    # Check that the LLM service was called correctly
    assert mock_llm_service.generate_completion.call_count == 2
    
    # Check that the findings were parsed correctly
    assert "reliability" in findings
    assert "security" in findings
    assert "critical_issues" in findings
    assert "No security groups specified" in findings["security"]
    
    # Check that the improved code was extracted correctly
    assert "security_group_ids" in improved_code
    assert "tags" in improved_code

@pytest.mark.asyncio
async def test_process_review(architecture_agent, mock_llm_service):
    """Test that the process method correctly handles code review requests."""
    # Configure the mock to return findings and improved code
    mock_llm_service.generate_completion.side_effect = [
        # First call returns findings
        """
        {
            "reliability": ["Single point of failure: only two subnets used"],
            "security": ["No security groups specified"],
            "cost_optimization": [],
            "performance": [],
            "operational_excellence": ["Missing resource tagging"],
            "critical_issues": ["No security groups specified"],
            "recommendations": ["Add security groups", "Add resource tagging"]
        }
        """,
        # Second call returns improved code
        f"```\n{IMPROVED_EKS_CODE}\n```"
    ]
    
    # Call the method
    result = await architecture_agent.process({
        "task_id": "review_infra",
        "code": SAMPLE_EKS_CODE,
        "cloud_provider": "aws",
        "iac_type": "terraform"
    })
    
    # Check that the result contains the expected fields
    assert "task_id" in result
    assert "original_code" in result
    assert "improved_code" in result
    assert "findings" in result
    
    # Check that the values are correct
    assert result["task_id"] == "review_infra"
    assert result["original_code"] == SAMPLE_EKS_CODE
    assert "security_group_ids" in result["improved_code"]
    assert "No security groups specified" in result["findings"]["security"]

@pytest.mark.asyncio
async def test_process_generate(architecture_agent, mock_llm_service):
    """Test that the process method correctly handles infrastructure generation requests."""
    # Configure the mock to return generated code, findings, and improved code
    mock_llm_service.generate_completion.side_effect = [
        # First call returns generated code
        f"```\n{SAMPLE_EKS_CODE}\n```",
        # Second call returns findings
        """
        {
            "reliability": ["Single point of failure: only two subnets used"],
            "security": ["No security groups specified"],
            "cost_optimization": [],
            "performance": [],
            "operational_excellence": ["Missing resource tagging"],
            "critical_issues": ["No security groups specified"],
            "recommendations": ["Add security groups", "Add resource tagging"]
        }
        """,
        # Third call returns improved code
        f"```\n{IMPROVED_EKS_CODE}\n```"
    ]
    
    # Call the method
    result = await architecture_agent.process({
        "task_id": "generate_infra",
        "code": "",  # Empty code indicates generation request
        "requirements": "Need a Kubernetes cluster with high availability",
        "task": "Create an EKS cluster",
        "cloud_provider": "aws",
        "iac_type": "terraform"
    })
    
    # Check that the result contains the expected fields
    assert "task_id" in result
    assert "original_code" in result
    assert "improved_code" in result
    assert "findings" in result
    
    # Check that the values are correct
    assert result["task_id"] == "generate_infra"
    assert "aws_eks_cluster" in result["original_code"]
    assert "security_group_ids" in result["improved_code"]
    assert "No security groups specified" in result["findings"]["security"]

@pytest.mark.asyncio
async def test_extract_code_from_text(architecture_agent):
    """Test that the _extract_code_from_text method correctly extracts code from text."""
    # Test with code wrapped in backticks
    text_with_backticks = """
    Here's the code:
    
    ```
    resource "aws_eks_cluster" "example" {
      name = "example"
    }
    ```
    
    Hope this helps!
    """
    
    extracted_code = architecture_agent._extract_code_from_text(text_with_backticks)
    assert "resource" in extracted_code
    assert "name" in extracted_code
    
    # Test with code not wrapped in backticks
    text_without_backticks = """
    resource "aws_eks_cluster" "example" {
      name = "example"
    }
    """
    
    extracted_code = architecture_agent._extract_code_from_text(text_without_backticks)
    assert "resource" in extracted_code
    assert "name" in extracted_code

@pytest.mark.asyncio
async def test_parse_findings(architecture_agent):
    """Test that the _parse_findings method correctly parses JSON findings."""
    # Test with valid JSON
    valid_json = """
    {
        "reliability": ["Issue 1", "Issue 2"],
        "security": ["Security issue"],
        "cost_optimization": [],
        "performance": [],
        "operational_excellence": ["Missing tags"],
        "critical_issues": ["Critical issue"],
        "recommendations": ["Recommendation 1", "Recommendation 2"]
    }
    """
    
    findings = architecture_agent._parse_findings(valid_json)
    assert "reliability" in findings
    assert len(findings["reliability"]) == 2
    assert "Issue 1" in findings["reliability"]
    assert "Critical issue" in findings["critical_issues"]
    
    # Test with invalid JSON (should fall back to text parsing)
    invalid_json = """
    ## Reliability
    - Issue 1
    - Issue 2
    
    ## Security
    - Security issue
    
    ## Critical Issues
    - Critical issue
    
    ## Recommendations
    - Recommendation 1
    - Recommendation 2
    """
    
    findings = architecture_agent._parse_findings(invalid_json)
    assert "reliability" in findings
    assert "security" in findings
    assert "critical_issues" in findings
    assert "recommendations" in findings

# Run the tests if this file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 