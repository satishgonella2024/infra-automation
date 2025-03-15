"""
Infrastructure Automation API Service.

This module provides the main FastAPI application for the infrastructure automation service,
integrating LLM capabilities with vector storage for pattern matching and code generation.
"""

import os
import logging
import argparse
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.services.llm import LLMService
from src.services.vector_db import ChromaService
from src.agents.architect import ArchitectureAgent

# Configure logging - use only console logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Infrastructure Automation API",
    description="API for infrastructure pattern matching and code generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService(
    provider=os.getenv("LLM_PROVIDER", "ollama"),
    model=os.getenv("LLM_MODEL", "llama2"),
    api_base=os.getenv("LLM_API_BASE", "http://localhost:11434")
)
vector_db = ChromaService()
architecture_agent = ArchitectureAgent(llm_service)

# Store services in app state for easier testing
app.state.llm_service = llm_service
app.state.vector_db = vector_db
app.state.architecture_agent = architecture_agent

# Initialize and integrate workflow components
from src.workflow.api import router as workflow_router, initialize_orchestrator
from src.agents.base.base_agent import BaseAgent
from src.integration import integrate_systems, run_initialization_tasks
import asyncio

# Create a dictionary of available agents
agents = {
    "architecture": architecture_agent,
    # Add other agents as needed
}

# Use the integration module to properly set up the system
integrated_components = integrate_systems(app, agents)
orchestrator = integrated_components["orchestrator"]

# Run initialization tasks in the background
@app.on_event("startup")
async def startup_event():
    await run_initialization_tasks(agents)

class InfrastructureRequest(BaseModel):
    """Request model for infrastructure generation."""
    task: str
    requirements: str
    cloud_provider: str = "aws"
    iac_type: str = "terraform"

class PatternRequest(BaseModel):
    """Request model for pattern operations."""
    name: str
    description: str
    cloud_provider: str = "aws"
    iac_type: str = "terraform"
    code: str
    metadata: Dict[str, Any] = {}

@app.post("/infrastructure/generate")
async def generate_infrastructure(request: InfrastructureRequest):
    """Generate infrastructure code based on requirements."""
    try:
        # Search for similar patterns
        patterns = await app.state.vector_db.search_patterns(
            query=request.requirements,
            cloud_provider=request.cloud_provider,
            iac_type=request.iac_type,
            n_results=3
        )
        
        # Process the request using the architecture agent
        result = await app.state.architecture_agent.process({
            "task_id": "generate_infra",
            "code": "",  # Initial empty code to be generated
            "cloud_provider": request.cloud_provider,
            "iac_type": request.iac_type,
            "requirements": request.requirements,
            "task": request.task,
            "similar_patterns": patterns
        })
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error generating infrastructure: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patterns")
async def add_pattern(pattern: PatternRequest):
    """Add a new infrastructure pattern."""
    try:
        result = await app.state.vector_db.add_pattern({
            "name": pattern.name,
            "description": pattern.description,
            "cloud_provider": pattern.cloud_provider,
            "iac_type": pattern.iac_type,
            "code": pattern.code,
            "metadata": pattern.metadata
        })
        return {"success": True, "pattern_id": result["id"]}
    except Exception as e:
        logger.error(f"Error adding pattern: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patterns/search")
async def search_patterns(
    query: str, 
    cloud_provider: str = None, 
    iac_type: str = None, 
    n_results: int = 5
):
    """Search for infrastructure patterns."""
    try:
        patterns = await app.state.vector_db.search_patterns(
            query=query, 
            cloud_provider=cloud_provider, 
            iac_type=iac_type, 
            n_results=n_results
        )
        return {"success": True, "patterns": patterns}
    except Exception as e:
        logger.error(f"Error searching patterns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/patterns/{pattern_id}")
async def update_pattern(pattern_id: str, pattern: PatternRequest):
    """Update an existing infrastructure pattern."""
    try:
        result = await app.state.vector_db.update_pattern(
            pattern_id,
            {
                "name": pattern.name,
                "description": pattern.description,
                "cloud_provider": pattern.cloud_provider,
                "iac_type": pattern.iac_type,
                "code": pattern.code,
                "metadata": pattern.metadata
            }
        )
        return {"success": True, "pattern_id": result["id"]}
    except Exception as e:
        logger.error(f"Error updating pattern: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/patterns/{pattern_id}")
async def delete_pattern(pattern_id: str):
    """Delete an infrastructure pattern."""
    try:
        result = await app.state.vector_db.delete_pattern(pattern_id)
        return {"success": True, "pattern_id": result["id"]}
    except Exception as e:
        logger.error(f"Error deleting pattern: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "services": {
        "llm": "healthy",
        "vector_db": "healthy"
    }}

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Infrastructure Automation Service")
    parser.add_argument("--mode", choices=["api"], default="api", help="Service mode")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()
    
    if args.mode == "api":
        import uvicorn
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )

if __name__ == "__main__":
    main()