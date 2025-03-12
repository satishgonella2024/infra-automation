"""
Tests for the ChromaDB vector database service.
"""

import os
import json
import pytest
import pytest_asyncio
from typing import Dict, Any

# Set testing environment variable
os.environ["TESTING"] = "1"

from src.services.vector_db.chroma_service import ChromaService

@pytest_asyncio.fixture
async def chroma_service():
    """Create a ChromaService instance for testing."""
    service = ChromaService()
    # Clean up any existing test collections
    try:
        collections = await service.list_collections()
        if "test_collection" in collections:
            service.client.delete_collection("test_collection")
        if "infrastructure_patterns" in collections:
            service.client.delete_collection("infrastructure_patterns")
    except Exception as e:
        print(f"Error during test setup: {e}")
    
    return service  # Return the service directly, not as an async generator

@pytest.mark.asyncio
async def test_store_and_query_document(chroma_service):
    """Test storing and querying documents."""
    # Store a document
    document_id = "test-doc-1"
    text = "This is a test document about AWS infrastructure using EC2 and S3"
    metadata = {"type": "test", "cloud_provider": "aws"}
    
    result = await chroma_service.store_document(
        collection_name="test_collection",
        document_id=document_id,
        text=text,
        metadata=metadata
    )
    
    assert result["id"] == document_id
    
    # Query for similar documents
    results = await chroma_service.query_similar(
        collection_name="test_collection",
        query_text="AWS EC2 infrastructure",
        n_results=5
    )
    
    # Verify results
    assert len(results) > 0
    assert results[0]["id"] == document_id
    assert results[0]["content"] == text
    assert results[0]["metadata"]["type"] == "test"
    assert results[0]["metadata"]["cloud_provider"] == "aws"

@pytest.mark.asyncio
async def test_update_document(chroma_service):
    """Test updating documents."""
    # Store a document
    document_id = "test-doc-2"
    text = "Original document about Azure infrastructure"
    metadata = {"type": "test", "cloud_provider": "azure"}
    
    await chroma_service.store_document(
        collection_name="test_collection",
        document_id=document_id,
        text=text,
        metadata=metadata
    )
    
    # Update the document
    updated_text = "Updated document about Azure VMs and Storage Accounts"
    updated_metadata = {"type": "test", "cloud_provider": "azure", "updated": True}
    
    result = await chroma_service.update_document(
        collection_name="test_collection",
        document_id=document_id,
        text=updated_text,
        metadata=updated_metadata
    )
    
    assert result["id"] == document_id
    
    # Query to verify update
    results = await chroma_service.query_similar(
        collection_name="test_collection",
        query_text="Azure VMs",
        n_results=5
    )
    
    found = False
    for result in results:
        if result["id"] == document_id:
            assert result["content"] == updated_text
            assert result["metadata"]["updated"] is True
            found = True
            break
    
    assert found, "Updated document not found in query results"

@pytest.mark.asyncio
async def test_delete_document(chroma_service):
    """Test deleting documents."""
    # Store a document
    document_id = "test-doc-3"
    text = "Document to be deleted"
    metadata = {"type": "test"}
    
    await chroma_service.store_document(
        collection_name="test_collection",
        document_id=document_id,
        text=text,
        metadata=metadata
    )
    
    # Delete the document
    result = await chroma_service.delete_document(
        collection_name="test_collection",
        document_id=document_id
    )
    
    assert result["id"] == document_id
    
    # Query to verify deletion
    results = await chroma_service.query_similar(
        collection_name="test_collection",
        query_text="document deleted",
        n_results=5
    )
    
    for result in results:
        assert result["id"] != document_id, "Deleted document should not be found"

@pytest.mark.asyncio
async def test_pattern_repository_functions(chroma_service):
    """Test pattern repository functionality."""
    # Add a pattern
    pattern = {
        "name": "Test Pattern",
        "description": "A test infrastructure pattern for AWS",
        "code": "resource \"aws_instance\" \"example\" {\n  ami           = \"ami-0c55b159cbfafe1f0\"\n  instance_type = \"t2.micro\"\n}",
        "cloud_provider": "aws",
        "iac_type": "terraform",
        "metadata": {"test": True, "purpose": "testing"}
    }
    
    result = await chroma_service.add_pattern(pattern)
    pattern_id = result["id"]
    
    # Get the pattern
    retrieved_pattern = await chroma_service.get_pattern(pattern_id)
    assert retrieved_pattern is not None
    assert retrieved_pattern["name"] == pattern["name"]
    assert retrieved_pattern["description"] == pattern["description"]
    assert retrieved_pattern["code"] == pattern["code"]
    assert retrieved_pattern["cloud_provider"] == pattern["cloud_provider"]
    assert retrieved_pattern["iac_type"] == pattern["iac_type"]
    assert retrieved_pattern["metadata"]["test"] is True
    
    # Search for patterns
    search_results = await chroma_service.search_patterns(
        query="AWS instance",
        cloud_provider="aws",
        iac_type="terraform"
    )
    
    assert len(search_results) > 0
    found = False
    for result in search_results:
        if result["id"] == pattern_id:
            found = True
            break
    assert found, "Pattern should be found in search results"
    
    # Update the pattern
    updated_pattern = {
        "name": "Updated Test Pattern",
        "description": pattern["description"],
        "code": pattern["code"],
        "cloud_provider": pattern["cloud_provider"],
        "iac_type": pattern["iac_type"],
        "metadata": {"test": True, "updated": True}
    }
    
    update_result = await chroma_service.update_pattern(pattern_id, updated_pattern)
    assert update_result["id"] == pattern_id
    
    # Verify update
    retrieved_pattern = await chroma_service.get_pattern(pattern_id)
    assert retrieved_pattern["name"] == "Updated Test Pattern"
    assert retrieved_pattern["metadata"]["updated"] is True
    
    # Delete the pattern
    delete_result = await chroma_service.delete_pattern(pattern_id)
    assert delete_result["id"] == pattern_id
    
    # Verify deletion
    retrieved_pattern = await chroma_service.get_pattern(pattern_id)
    assert retrieved_pattern is None

@pytest.mark.asyncio
async def test_multiple_patterns_search(chroma_service):
    """Test searching across multiple patterns."""
    # Add multiple patterns
    patterns = [
        {
            "name": "AWS EKS Cluster",
            "description": "Kubernetes cluster with autoscaling node groups",
            "code": "module \"eks\" {\n  source  = \"terraform-aws-modules/eks/aws\"\n  version = \"~> 18.0\"\n  cluster_name = \"my-cluster\"\n  subnet_ids = module.vpc.private_subnets\n}",
            "cloud_provider": "aws",
            "iac_type": "terraform",
            "metadata": {"purpose": "container orchestration"}
        },
        {
            "name": "AWS S3 Website",
            "description": "Static website hosted on S3 with CloudFront",
            "code": "resource \"aws_s3_bucket\" \"website\" {\n  bucket = \"my-website-bucket\"\n  acl    = \"public-read\"\n}",
            "cloud_provider": "aws",
            "iac_type": "terraform",
            "metadata": {"purpose": "web hosting"}
        },
        {
            "name": "Azure VM Deployment",
            "description": "Virtual machines with load balancer",
            "code": "resource \"azurerm_virtual_machine\" \"vm\" {\n  name                  = \"my-vm\"\n  location              = azurerm_resource_group.example.location\n  resource_group_name   = azurerm_resource_group.example.name\n}",
            "cloud_provider": "azure",
            "iac_type": "terraform",
            "metadata": {"purpose": "compute"}
        }
    ]
    
    pattern_ids = []
    for pattern in patterns:
        result = await chroma_service.add_pattern(pattern)
        pattern_ids.append(result["id"])
    
    # Test filtering by cloud provider
    aws_results = await chroma_service.search_patterns(
        query="infrastructure",
        cloud_provider="aws",
        n_results=10
    )
    
    assert len([r for r in aws_results if r["cloud_provider"] == "aws"]) == 2
    
    # Test filtering by IaC type
    terraform_results = await chroma_service.search_patterns(
        query="infrastructure",
        iac_type="terraform",
        n_results=10
    )
    
    assert len(terraform_results) == 3
    
    # Test semantic search accuracy
    kubernetes_results = await chroma_service.search_patterns(
        query="kubernetes container orchestration",
        n_results=1
    )
    
    assert len(kubernetes_results) == 1
    assert "eks" in kubernetes_results[0]["code"].lower()
    
    # Test combined filters
    azure_terraform_results = await chroma_service.search_patterns(
        query="virtual machine",
        cloud_provider="azure",
        iac_type="terraform",
        n_results=10
    )
    
    assert len(azure_terraform_results) == 1
    assert azure_terraform_results[0]["name"] == "Azure VM Deployment"
    
    # Clean up
    for pattern_id in pattern_ids:
        await chroma_service.delete_pattern(pattern_id)

@pytest.mark.asyncio
async def test_list_collections(chroma_service):
    """Test listing collections."""
    # Create some test documents in different collections
    await chroma_service.store_document(
        collection_name="test_collection_1",
        document_id="test-1",
        text="Test document 1",
        metadata={"test": "value1"}  # Non-empty metadata required by ChromaDB
    )
    
    await chroma_service.store_document(
        collection_name="test_collection_2",
        document_id="test-2",
        text="Test document 2",
        metadata={"test": "value2"}  # Non-empty metadata required by ChromaDB
    )
    
    # List collections
    collections = await chroma_service.list_collections()
    
    # Verify both collections are in the list
    assert "test_collection_1" in collections
    assert "test_collection_2" in collections