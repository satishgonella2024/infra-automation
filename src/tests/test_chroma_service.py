"""
Tests for the ChromaService class.

These tests verify that the ChromaService correctly handles pattern-related operations
such as adding, searching, updating, and deleting patterns.
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock

from src.services.vector_db.chroma_service import ChromaService

# Sample pattern data for tests
SAMPLE_PATTERN = {
    "name": "Test Pattern",
    "description": "A test pattern for unit testing",
    "cloud_provider": "aws",
    "iac_type": "terraform",
    "code": """
    resource "aws_s3_bucket" "example" {
      bucket = "my-test-bucket"
      acl    = "private"
      
      tags = {
        Name        = "My Test Bucket"
        Environment = "Test"
      }
    }
    """,
    "metadata": {
        "category": "storage",
        "complexity": "low",
        "tags": "s3,storage,aws"
    }
}

@pytest.fixture
def mock_chroma_client():
    """Create a mock Chroma client for testing."""
    mock_client = MagicMock()
    mock_client.get_collection = MagicMock(return_value=MagicMock())
    return mock_client

@pytest.fixture
def mock_collection():
    """Create a mock Chroma collection for testing."""
    mock_coll = MagicMock()
    mock_coll.add = MagicMock()
    mock_coll.get = MagicMock()
    mock_coll.update = MagicMock()
    mock_coll.delete = MagicMock()
    mock_coll.query = MagicMock()
    return mock_coll

@pytest.fixture
def chroma_service(mock_chroma_client, mock_collection):
    """Create a ChromaService instance with mocked dependencies for testing."""
    with patch('chromadb.Client', return_value=mock_chroma_client):
        mock_chroma_client.get_collection.return_value = mock_collection
        service = ChromaService()
        return service

@pytest.mark.asyncio
async def test_add_pattern():
    """Test adding a pattern to the collection."""
    # Create a mock for the store_document method
    with patch.object(ChromaService, 'store_document', new_callable=AsyncMock) as mock_store_document:
        # Configure the mock to return a UUID
        pattern_id = str(uuid.uuid4())
        mock_store_document.return_value = {"id": pattern_id}
        
        # Create a ChromaService instance
        service = ChromaService()
        
        # Call the method
        result = await service.add_pattern(SAMPLE_PATTERN)
        
        # Check that store_document was called correctly
        mock_store_document.assert_called_once()
        
        # Check the arguments passed to store_document
        args, kwargs = mock_store_document.call_args
        
        # Check that the document contains the pattern code
        assert kwargs["text"] == SAMPLE_PATTERN["code"]
        
        # Check that the metadata contains the pattern metadata
        assert kwargs["metadata"]["cloud_provider"] == SAMPLE_PATTERN["cloud_provider"]
        assert kwargs["metadata"]["iac_type"] == SAMPLE_PATTERN["iac_type"]
        
        # Check that an ID was generated
        assert "id" in result
        assert result["id"] == pattern_id

@pytest.mark.asyncio
async def test_search_patterns():
    """Test searching for patterns in the collection."""
    # Create a mock for the query_similar method
    with patch.object(ChromaService, 'query_similar', new_callable=AsyncMock) as mock_query_similar:
        # Configure the mock to return search results
        mock_query_similar.return_value = [
            {
                "id": "pattern1",
                "content": "Pattern 1 code",
                "metadata": {
                    "name": "Pattern 1",
                    "description": "Description 1",
                    "cloud_provider": "aws",
                    "iac_type": "terraform",
                    "category": "storage",
                    "complexity": "low",
                    "tags": "s3,storage,aws"
                },
                "similarity": 0.9
            },
            {
                "id": "pattern2",
                "content": "Pattern 2 code",
                "metadata": {
                    "name": "Pattern 2",
                    "description": "Description 2",
                    "cloud_provider": "aws",
                    "iac_type": "terraform",
                    "category": "compute",
                    "complexity": "medium",
                    "tags": "ec2,compute,aws"
                },
                "similarity": 0.8
            }
        ]
        
        # Create a ChromaService instance
        service = ChromaService()
        
        # Call the method
        results = await service.search_patterns("s3 bucket", cloud_provider="aws", iac_type="terraform")
        
        # Check that query_similar was called correctly
        mock_query_similar.assert_called_once()
        
        # Check the arguments passed to query_similar
        args, kwargs = mock_query_similar.call_args
        assert kwargs["query_text"] == "s3 bucket"
        assert kwargs["where"]["cloud_provider"] == "aws"
        assert kwargs["where"]["iac_type"] == "terraform"
        
        # Check that the results were processed correctly
        assert len(results) == 2
        assert results[0]["id"] == "pattern1"
        assert results[0]["name"] == "Pattern 1"
        assert results[0]["code"] == "Pattern 1 code"
        assert results[1]["id"] == "pattern2"
        assert results[1]["name"] == "Pattern 2"
        assert results[1]["code"] == "Pattern 2 code"

@pytest.mark.asyncio
async def test_get_pattern():
    """Test getting a pattern by ID from the collection."""
    # Create a mock for the get_collection method
    with patch.object(ChromaService, 'get_collection') as mock_get_collection:
        # Configure the mock collection
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["test-pattern-id"],
            "metadatas": [{
                "name": "Test Pattern",
                "description": "A test pattern",
                "cloud_provider": "aws",
                "iac_type": "terraform",
                "category": "storage",
                "complexity": "low",
                "tags": "s3,storage,aws"
            }],
            "documents": ["Test pattern code"]
        }
        mock_get_collection.return_value = mock_collection
        
        # Create a ChromaService instance
        service = ChromaService()
        
        # Call the method
        pattern = await service.get_pattern("test-pattern-id")
        
        # Check that the collection's get method was called correctly
        mock_collection.get.assert_called_once_with(ids=["test-pattern-id"])
        
        # Check that the pattern was processed correctly
        assert pattern["id"] == "test-pattern-id"
        assert pattern["name"] == "Test Pattern"
        assert pattern["cloud_provider"] == "aws"
        assert pattern["code"] == "Test pattern code"

@pytest.mark.asyncio
async def test_update_pattern():
    """Test updating a pattern in the collection."""
    # Create a mock for the update_document method
    with patch.object(ChromaService, 'update_document', new_callable=AsyncMock) as mock_update_document:
        # Configure the mock to return a pattern ID
        pattern_id = "test-pattern-id"
        mock_update_document.return_value = {"id": pattern_id}
        
        # Create a ChromaService instance
        service = ChromaService()
        
        # Call the method
        updated_pattern = SAMPLE_PATTERN.copy()
        updated_pattern["name"] = "Updated Pattern"
        updated_pattern["description"] = "An updated test pattern"
        
        result = await service.update_pattern(pattern_id, updated_pattern)
        
        # Check that update_document was called correctly
        mock_update_document.assert_called_once()
        
        # Check the arguments passed to update_document
        args, kwargs = mock_update_document.call_args
        assert kwargs["document_id"] == pattern_id
        assert kwargs["text"] == updated_pattern["code"]
        assert kwargs["metadata"]["name"] == updated_pattern["name"]
        assert kwargs["metadata"]["description"] == updated_pattern["description"]
        
        # Check that the result contains the pattern ID
        assert result["id"] == pattern_id

@pytest.mark.asyncio
async def test_delete_pattern():
    """Test deleting a pattern from the collection."""
    # Create a mock for the delete_document method
    with patch.object(ChromaService, 'delete_document', new_callable=AsyncMock) as mock_delete_document:
        # Configure the mock to return a pattern ID
        pattern_id = "test-pattern-id"
        mock_delete_document.return_value = {"id": pattern_id}
        
        # Create a ChromaService instance
        service = ChromaService()
        
        # Call the method
        result = await service.delete_pattern(pattern_id)
        
        # Check that delete_document was called correctly
        mock_delete_document.assert_called_once_with(
            collection_name="infrastructure_patterns",
            document_id=pattern_id
        )
        
        # Check that the result contains the pattern ID
        assert result["id"] == pattern_id

# Run the tests if this file is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 