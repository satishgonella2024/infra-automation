"""
Tests for the SecurityAgent class.

These tests verify that the SecurityAgent correctly identifies and remediates
security vulnerabilities in infrastructure code.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.agents.security.security_agent import SecurityAgent
from src.services.llm.llm_service import LLMService

# Sample data for tests
SAMPLE_INSECURE_S3_CODE = """
resource "aws_s3_bucket" "insecure_bucket" {
  bucket = "my-insecure-bucket"
  acl    = "public-read"
}
"""

SAMPLE_SECURE_S3_CODE = """
resource "aws_s3_bucket" "secure_bucket" {
  bucket = "my-secure-bucket"
}

resource "aws_s3_bucket_acl" "bucket_acl" {
  bucket = aws_s3_bucket.secure_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_encryption" {
  bucket = aws_s3_bucket.secure_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bucket_public_access_block" {
  bucket = aws_s3_bucket.secure_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
"""

SAMPLE_VULNERABILITIES = [
    {
        "severity": "high",
        "title": "Public S3 Bucket",
        "description": "The S3 bucket is configured with public-read ACL which allows anyone to read the contents.",
        "remediation": "Change ACL to private and use aws_s3_bucket_public_access_block to block public access."
    },
    {
        "severity": "high",
        "title": "Unencrypted S3 Bucket",
        "description": "The S3 bucket does not have server-side encryption enabled.",
        "remediation": "Configure server-side encryption using aws_s3_bucket_server_side_encryption_configuration."
    }
]

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    mock_service = MagicMock(spec=LLMService)
    mock_service.generate_completion = AsyncMock()
    return mock_service

@pytest.fixture
def security_agent(mock_llm_service):
    """Create a SecurityAgent instance for testing."""
    return SecurityAgent(llm_service=mock_llm_service)

@pytest.mark.asyncio
async def test_analyze_security(security_agent, mock_llm_service):
    """Test that the analyze_security method correctly identifies vulnerabilities."""
    # Configure the mock to return a JSON string with vulnerabilities
    mock_llm_service.generate_completion.return_value = """
    {
        "vulnerabilities": [
            {
                "severity": "high",
                "title": "Public S3 Bucket",
                "description": "The S3 bucket is configured with public-read ACL which allows anyone to read the contents.",
                "remediation": "Change ACL to private and use aws_s3_bucket_public_access_block to block public access."
            },
            {
                "severity": "high",
                "title": "Unencrypted S3 Bucket",
                "description": "The S3 bucket does not have server-side encryption enabled.",
                "remediation": "Configure server-side encryption using aws_s3_bucket_server_side_encryption_configuration."
            }
        ],
        "compliance_results": {
            "CIS AWS Benchmark": [
                "4.1 Ensure S3 buckets employ encryption-at-rest"
            ]
        },
        "risk_score": 8,
        "priority_remediation": [
            "Enable server-side encryption",
            "Block public access"
        ]
    }
    """
    
    # Call the method
    vulnerabilities, compliance_results = await security_agent.analyze_security(
        SAMPLE_INSECURE_S3_CODE, "aws", "terraform"
    )
    
    # Check that the LLM service was called correctly
    mock_llm_service.generate_completion.assert_called_once()
    
    # Check that the vulnerabilities were parsed correctly
    assert len(vulnerabilities) == 2
    assert vulnerabilities[0]["severity"] == "high"
    assert vulnerabilities[0]["title"] == "Public S3 Bucket"
    assert vulnerabilities[1]["title"] == "Unencrypted S3 Bucket"
    
    # Check that the compliance results were parsed correctly
    assert "CIS AWS Benchmark" in compliance_results
    assert len(compliance_results["CIS AWS Benchmark"]) == 1

@pytest.mark.asyncio
async def test_remediate_security_issues(security_agent, mock_llm_service):
    """Test that the remediate_security_issues method correctly remediates vulnerabilities."""
    # Configure the mock to return remediated code
    mock_llm_service.generate_completion.return_value = f"```\n{SAMPLE_SECURE_S3_CODE}\n```"
    
    # Call the method
    remediated_code, remediation_summary = await security_agent.remediate_security_issues(
        SAMPLE_INSECURE_S3_CODE, SAMPLE_VULNERABILITIES, "aws", "terraform"
    )
    
    # Check that the LLM service was called correctly
    mock_llm_service.generate_completion.assert_called_once()
    
    # Check that the remediated code was extracted correctly
    assert "private" in remediated_code
    assert "server_side_encryption" in remediated_code
    assert "public_access_block" in remediated_code
    
    # Check that the remediation summary was created correctly
    assert remediation_summary["remediated_issues_count"] == 2
    assert remediation_summary["critical_issues_fixed"] == 2

@pytest.mark.asyncio
async def test_process(security_agent, mock_llm_service):
    """Test that the process method correctly handles security scanning requests."""
    # Configure the mock to return vulnerabilities and remediated code
    mock_llm_service.generate_completion.side_effect = [
        # First call is for thinking
        "The S3 bucket has security issues including public access and lack of encryption.",
        
        # Second call is for security analysis
        """
        {
            "vulnerabilities": [
                {
                    "severity": "high",
                    "title": "Public S3 Bucket",
                    "description": "The S3 bucket is configured with public-read ACL which allows anyone to read the contents.",
                    "remediation": "Change ACL to private and use aws_s3_bucket_public_access_block to block public access."
                },
                {
                    "severity": "high",
                    "title": "Unencrypted S3 Bucket",
                    "description": "The S3 bucket does not have server-side encryption enabled.",
                    "remediation": "Configure server-side encryption using aws_s3_bucket_server_side_encryption_configuration."
                }
            ],
            "compliance_results": {
                "CIS AWS Benchmark": [
                    "4.1 Ensure S3 buckets employ encryption-at-rest"
                ]
            },
            "risk_score": 8,
            "priority_remediation": [
                "Enable server-side encryption",
                "Block public access"
            ]
        }
        """,
        
        # Third call is for remediation
        f"```\n{SAMPLE_SECURE_S3_CODE}\n```"
    ]
    
    # Call the method
    result = await security_agent.process({
        "task_id": "test_security_scan",
        "code": SAMPLE_INSECURE_S3_CODE,
        "cloud_provider": "aws",
        "iac_type": "terraform"
    })
    
    # Check that the method returns the expected fields
    assert "task_id" in result
    assert "original_code" in result
    assert "remediated_code" in result
    assert "vulnerabilities" in result
    assert "compliance_results" in result
    assert "remediation_summary" in result
    assert "thoughts" in result
    
    # Check that the values are correct
    assert result["task_id"] == "test_security_scan"
    assert result["original_code"] == SAMPLE_INSECURE_S3_CODE
    assert "private" in result["remediated_code"]
    assert "server_side_encryption" in result["remediated_code"]
    assert result["vulnerabilities"][0]["title"] == "Public S3 Bucket"
    assert "CIS AWS Benchmark" in result["compliance_results"]

@pytest.mark.asyncio
async def test_detect_pattern_vulnerabilities(security_agent):
    """Test that the _detect_pattern_vulnerabilities method correctly identifies common vulnerabilities."""
    # Test with insecure S3 code
    vulnerabilities = security_agent._detect_pattern_vulnerabilities(
        SAMPLE_INSECURE_S3_CODE, "aws", "terraform"
    )
    
    # Should detect at least one vulnerability (public access)
    assert len(vulnerabilities) > 0
    assert any("Public Access" in vuln["title"] for vuln in vulnerabilities)
    
    # Test with secure S3 code
    vulnerabilities = security_agent._detect_pattern_vulnerabilities(
        SAMPLE_SECURE_S3_CODE, "aws", "terraform"
    )
    
    # Should not detect public access vulnerability
    assert not any("Public Access" in vuln["title"] for vuln in vulnerabilities)

@pytest.mark.asyncio
async def test_check_compliance(security_agent, mock_llm_service):
    """Test that the check_compliance method correctly checks against compliance frameworks."""
    # Configure the mock to return compliance results
    mock_llm_service.generate_completion.return_value = """
    {
        "compliance_score": 70,
        "passing_controls": ["1.1", "1.2", "2.1"],
        "failing_controls": [
            {
                "id": "2.2",
                "description": "Ensure S3 Bucket has encryption enabled",
                "remediation": "Configure server-side encryption"
            }
        ],
        "documentation_gaps": ["Missing encryption documentation"],
        "summary": "70% compliant with CIS AWS Benchmark"
    }
    """
    
    # Call the method
    compliance_results = await security_agent.check_compliance(
        SAMPLE_INSECURE_S3_CODE, "CIS AWS Benchmark", "aws", "terraform"
    )
    
    # Check that the LLM service was called correctly
    mock_llm_service.generate_completion.assert_called_once()
    
    # Check that the compliance results were parsed correctly
    assert compliance_results["compliance_score"] == 70
    assert len(compliance_results["passing_controls"]) == 3
    assert len(compliance_results["failing_controls"]) == 1
    assert compliance_results["failing_controls"][0]["id"] == "2.2"

@pytest.mark.asyncio
async def test_scan_for_threats(security_agent, mock_llm_service):
    """Test that the scan_for_threats method correctly identifies threats."""
    # Configure the mock to return threat model results
    mock_llm_service.generate_completion.return_value = """
    {
        "threats": [
            {
                "category": "Information Disclosure",
                "description": "Public S3 bucket could expose sensitive data",
                "likelihood": "high",
                "impact": "high",
                "risk_score": 9,
                "mitigations": ["Configure bucket as private", "Enable default encryption"]
            }
        ],
        "overall_risk": "high",
        "top_mitigations": ["Configure bucket as private"]
    }
    """
    
    # Call the method
    threat_model = await security_agent.scan_for_threats(
        SAMPLE_INSECURE_S3_CODE, "aws", "terraform"
    )
    
    # Check that the LLM service was called correctly
    mock_llm_service.generate_completion.assert_called_once()
    
    # Check that the threat model was parsed correctly
    assert len(threat_model["threats"]) == 1
    assert threat_model["threats"][0]["category"] == "Information Disclosure"
    assert threat_model["overall_risk"] == "high"
    assert len(threat_model["top_mitigations"]) == 1

# Run the tests if this file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])