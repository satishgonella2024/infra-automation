"""
Integration tests for ChromaDB with the agent system.
"""

import os
import pytest
import pytest_asyncio
import uuid
from typing import Dict, Any

# Set testing environment variable
os.environ["TESTING"] = "1"

from src.services.llm.llm_service import LLMService
from src.services.vector_db.chroma_service import ChromaService
from src.agents.base.base_agent import BaseAgent
from src.agents.infra.infrastructure_agent import InfrastructureAgent

class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for testing purposes."""
    
    def __init__(self, llm_service, vector_db_service=None):
        super().__init__(
            name="TestAgent",
            description="Agent for testing purposes",
            capabilities=["testing"],
            llm_service=llm_service,
            vector_db_service=vector_db_service
        )
    
    async def process(self, input_data):
        """Process test inputs."""
        return {"result": "test", "input": input_data}

@pytest_asyncio.fixture
async def llm_service():
    """Create an LLM service for testing."""
    # Mock LLM service that returns predefined responses
    class MockLLMService:
        async def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=2048):
            return f"Mock response for: {prompt[:50]}..."
    
    return MockLLMService()

@pytest_asyncio.fixture
async def chroma_service():
    """Create a ChromaService instance for testing."""
    service = ChromaService()
    # Clean up any existing test collections
    try:
        collections = await service.list_collections()
        for collection in collections:
            if collection.startswith("test_") or collection.startswith("agent_"):
                service.client.delete_collection(collection)
    except Exception as e:
        print(f"Error during test setup: {e}")
    
    return service

@pytest_asyncio.fixture
async def test_agent(llm_service, chroma_service):
    """Create a test agent with vector DB integration."""
    agent = TestAgent(llm_service, chroma_service)
    return agent

@pytest.mark.asyncio
async def test_agent_memory_storage(test_agent):
    """Test storing agent memories in vector DB."""
    # Create a memory entry
    memory_entry = {
        "type": "test_memory",
        "content": "This is a test memory for vector storage",
        "metadata": {"test": True},
        "timestamp": 1234567890
    }
    
    # Store the memory
    await test_agent.update_memory(memory_entry)
    
    # Query for similar memories
    similar_memories = await test_agent.retrieve_similar_memories(
        query="test memory vector",
        n_results=5
    )
    
    # Verify retrieval
    assert len(similar_memories) > 0
    found = False
    for memory in similar_memories:
        if memory["memory"]["type"] == "test_memory":
            assert memory["memory"]["content"] == memory_entry["content"]
            assert memory["metadata"]["agent_name"] == "TestAgent"
            found = True
            break
    
    assert found, "Stored memory not found in retrieval results"

@pytest.mark.asyncio
async def test_infrastructure_agent_rag(llm_service, chroma_service):
    """Test RAG capabilities of InfrastructureAgent."""
    # Create an infrastructure agent
    infra_agent = InfrastructureAgent(
        llm_service=llm_service,
        vector_db_service=chroma_service
    )
    
    # Add some test patterns
    test_patterns = [
        {
            "name": "Test AWS EC2 Pattern",
            "description": "Simple EC2 instance configuration",
            "code": "resource \"aws_instance\" \"example\" {\n  ami           = \"ami-0c55b159cbfafe1f0\"\n  instance_type = \"t2.micro\"\n}",
            "cloud_provider": "aws",
            "iac_type": "terraform",
            "metadata": {"test": True}
        },
        {
            "name": "Test AWS RDS Pattern",
            "description": "Amazon RDS database configuration",
            "code": "resource \"aws_db_instance\" \"default\" {\n  allocated_storage    = 10\n  engine               = \"mysql\"\n  engine_version       = \"5.7\"\n  instance_class       = \"db.t3.micro\"\n}",
            "cloud_provider": "aws",
            "iac_type": "terraform",
            "metadata": {"test": True}
        }
    ]
    
    pattern_ids = []
    for pattern in test_patterns:
        result = await infra_agent.save_pattern(
            name=pattern["name"],
            description=pattern["description"],
            code=pattern["code"],
            cloud_provider=pattern["cloud_provider"],
            iac_type=pattern["iac_type"],
            metadata=pattern["metadata"]
        )
        pattern_ids.append(result["id"])
    
    # Process a related infrastructure request
    result = await infra_agent.process({
        "task_id": str(uuid.uuid4()),
        "task": "Create an EC2 instance with RDS database",
        "requirements": {},
        "cloud_provider": "aws",
        "iac_type": "terraform"
    })
    
    # Verify metadata indicates RAG was used
    assert "metadata" in result
    assert "used_rag" in result["metadata"]
    assert result["metadata"]["used_rag"] is True
    assert result["metadata"]["similar_patterns_used"] > 0
    
    # Clean up
    for pattern_id in pattern_ids:
        await infra_agent.delete_pattern(pattern_id)

@pytest.mark.asyncio
async def test_agent_memory_retrieval_during_thinking(llm_service, chroma_service):
    """Test that agent uses vector retrieval during thinking phase."""
    # Create an infrastructure agent
    infra_agent = InfrastructureAgent(
        llm_service=llm_service,
        vector_db_service=chroma_service
    )
    
    # First, create some thinking memories
    thought_task = "Deploy a simple web application with load balancer"
    thoughts = "I need to consider high availability, scaling, and security. For high availability, I'll use multiple instances across AZs..."
    
    await infra_agent.update_memory({
        "type": "thinking",
        "input": {"task": thought_task},
        "thoughts": thoughts,
        "timestamp": 1234567890
    })
    
    # Now think about a similar task
    think_result = await infra_agent.think({
        "task": "Create a web application architecture with high availability"
    })
    
    # Since we're using a mock LLM, we can't verify the content directly,
    # but we can check that the function returned successfully
    assert "thoughts" in think_result
    assert "agent" in think_result
    assert think_result["agent"] == "Infrastructure"