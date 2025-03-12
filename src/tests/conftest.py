"""
Pytest configuration file for Infrastructure Automation tests.

This module provides fixtures and configuration for testing the application.
"""

import os
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.services.llm.llm_service import LLMService
from src.services.vector_db.chroma_service import ChromaService
from src.agents.architect.architecture_agent import ArchitectureAgent

# Set the TESTING environment variable
os.environ["TESTING"] = "1"

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing."""
    mock_service = MagicMock(spec=LLMService)
    mock_service.generate = AsyncMock()
    mock_service.generate_completion = AsyncMock()
    return mock_service

@pytest.fixture
def mock_vector_db():
    """Create a mock vector database service for testing."""
    mock_db = MagicMock(spec=ChromaService)
    mock_db.add_pattern = AsyncMock()
    mock_db.search_patterns = AsyncMock()
    mock_db.update_pattern = AsyncMock()
    mock_db.delete_pattern = AsyncMock()
    return mock_db

@pytest.fixture
def mock_architecture_agent():
    """Create a mock architecture agent for testing."""
    mock_agent = MagicMock(spec=ArchitectureAgent)
    mock_agent.process = AsyncMock()
    return mock_agent

@pytest.fixture
def test_app(mock_llm_service, mock_vector_db, mock_architecture_agent):
    """Create a test FastAPI app with mocked dependencies."""
    # Import here to avoid circular imports
    from src.main import app
    
    # Replace the services with mocks
    app.dependency_overrides = {}
    
    # Store the original services
    original_llm_service = app.state.llm_service if hasattr(app.state, "llm_service") else None
    original_vector_db = app.state.vector_db if hasattr(app.state, "vector_db") else None
    original_architecture_agent = app.state.architecture_agent if hasattr(app.state, "architecture_agent") else None
    
    # Set the mock services
    app.state.llm_service = mock_llm_service
    app.state.vector_db = mock_vector_db
    app.state.architecture_agent = mock_architecture_agent
    
    yield app
    
    # Restore the original services
    if original_llm_service:
        app.state.llm_service = original_llm_service
    if original_vector_db:
        app.state.vector_db = original_vector_db
    if original_architecture_agent:
        app.state.architecture_agent = original_architecture_agent

@pytest.fixture
def test_client(test_app):
    """Create a test client for the FastAPI app."""
    return TestClient(test_app) 