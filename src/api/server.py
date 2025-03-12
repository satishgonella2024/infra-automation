"""
API Server Module for Multi-Agent Infrastructure Automation System

This module defines the FastAPI app that serves as the interface for users
to interact with the multi-agent system.
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import our agent components
from src.agents.base import BaseAgent
from src.agents.infra import InfrastructureAgent
from src.agents.architect import ArchitectureAgent
from src.services.llm import LLMService
from src.services.vector_db import ChromaService

# Create the FastAPI app
app = FastAPI(
    title="Multi-Agent Infrastructure Automation System",
    description="A system that uses specialized AI agents to automate infrastructure provisioning, security review, architecture optimization, and more.",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Pydantic Models for Request/Response -----

class InfrastructureRequest(BaseModel):
    """Request model for infrastructure generation."""
    task: str = Field(..., description="Description of what to generate")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Specific infrastructure requirements")
    cloud_provider: str = Field(default="aws", description="Target cloud provider (aws, azure, gcp)")
    iac_type: str = Field(default="terraform", description="Type of IaC to generate (terraform, ansible, jenkins)")

class InfrastructureResponse(BaseModel):
    """Response model for infrastructure generation."""
    task_id: str = Field(..., description="Unique ID for this task")
    code: str = Field(..., description="Generated infrastructure code")
    metadata: Dict[str, Any] = Field(..., description="Metadata about the generated code")
    thoughts: str = Field(..., description="Agent's thought process")
    architecture_findings: Dict[str, Any] = Field(default_factory=dict, description="Architecture review findings")
    iac_type: str = Field(..., description="Type of IaC that was generated")
    cloud_provider: str = Field(..., description="Target cloud provider")

class AnalysisRequest(BaseModel):
    """Request model for infrastructure code analysis."""
    infrastructure_code: str = Field(..., description="Infrastructure code to analyze")
    iac_type: str = Field(..., description="Type of IaC (terraform, ansible, jenkins)")
    cloud_provider: str = Field(default="aws", description="Target cloud provider")

class ArchitectureReviewRequest(BaseModel):
    """Request model for architecture review."""
    infrastructure_code: str = Field(..., description="Infrastructure code to review")
    iac_type: str = Field(..., description="Type of IaC (terraform, ansible, jenkins)")
    cloud_provider: str = Field(default="aws", description="Target cloud provider")

class PatternCreate(BaseModel):
    """Request model for creating a pattern."""
    name: str = Field(..., description="Name of the pattern")
    description: str = Field(..., description="Description of the pattern")
    code: str = Field(..., description="Infrastructure code")
    cloud_provider: str = Field(default="aws", description="Target cloud provider")
    iac_type: str = Field(default="terraform", description="IaC type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class PatternUpdate(BaseModel):
    """Request model for updating a pattern."""
    name: Optional[str] = Field(None, description="Name of the pattern")
    description: Optional[str] = Field(None, description="Description of the pattern")
    code: Optional[str] = Field(None, description="Infrastructure code")
    cloud_provider: Optional[str] = Field(None, description="Target cloud provider")
    iac_type: Optional[str] = Field(None, description="IaC type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class PatternSearchRequest(BaseModel):
    """Request model for searching patterns."""
    query: str = Field(..., description="Search query")
    cloud_provider: Optional[str] = Field(None, description="Filter by cloud provider")
    iac_type: Optional[str] = Field(None, description="Filter by IaC type")
    n_results: int = Field(default=5, ge=1, le=20, description="Maximum number of results")

class StatusResponse(BaseModel):
    """Response model for system status requests."""
    status: str = Field(..., description="System status")
    agents: List[Dict[str, Any]] = Field(..., description="Status of all agents")
    uptime_seconds: int = Field(..., description="System uptime in seconds")
    version: str = Field(..., description="System version")

# ----- Globals and initialization -----

# Store for our agents
agents: Dict[str, BaseAgent] = {}

# In-memory task store (would be replaced with a database in production)
tasks: Dict[str, Dict[str, Any]] = {}

# System start time
start_time = datetime.now()

# Create services and agents when the app starts
llm_service = None
vector_db_service = None
infrastructure_agent = None
architecture_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    global llm_service, vector_db_service, infrastructure_agent, architecture_agent
    
    # Get LLM configuration from environment variables
    llm_provider = os.environ.get("LLM_PROVIDER", "ollama")
    llm_model = os.environ.get("LLM_MODEL", "llama3")
    llm_api_base = os.environ.get("LLM_API_BASE", "http://localhost:11434/api")
    llm_api_key = os.environ.get("LLM_API_KEY")
    
    # Get ChromaDB configuration
    chroma_db_path = os.environ.get("CHROMA_DB_PATH", "/app/chroma_data")
    
    # Create LLM service
    llm_service = LLMService(
        provider=llm_provider,
        model=llm_model,
        api_base=llm_api_base,
        api_key=llm_api_key
    )
    
    # Create ChromaDB service
    vector_db_service = ChromaService(config={"db_path": chroma_db_path})
    
    # Create and register agents
    infrastructure_agent = InfrastructureAgent(
        llm_service=llm_service,
        vector_db_service=vector_db_service,
        config={"templates_dir": "templates"}
    )
    
    # Initialize architecture agent
    architecture_agent = ArchitectureAgent(
        llm_service=llm_service,
        vector_db_service=vector_db_service,
        config={"templates_dir": "templates"}
    )
    
    # Register agents in the global store
    agents["infrastructure"] = infrastructure_agent
    agents["architecture"] = architecture_agent

# ----- API Routes -----

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint - system information."""
    return {
        "name": "Multi-Agent Infrastructure Automation System",
        "version": "0.1.0",
        "status": "running",
        "uptime": str(datetime.now() - start_time)
    }

@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get the current system status."""
    return {
        "status": "running",
        "agents": [agent.serialize() for agent in agents.values()],
        "uptime_seconds": int((datetime.now() - start_time).total_seconds()),
        "version": "0.1.0"
    }

@app.post("/infrastructure/generate", response_model=InfrastructureResponse)
async def generate_infrastructure(request: InfrastructureRequest):
    """Generate infrastructure as code based on requirements."""
    if not infrastructure_agent or not architecture_agent:
        raise HTTPException(status_code=503, detail="Required agents not initialized")
    
    # Create a task ID
    task_id = str(uuid.uuid4())
    
    # Process the request with the infrastructure agent
    infra_result = await infrastructure_agent.process({
        "task_id": task_id,
        "task": request.task,
        "requirements": request.requirements,
        "cloud_provider": request.cloud_provider,
        "iac_type": request.iac_type
    })
    
    # Get the generated code
    generated_code = infra_result.get("code", "")
    
    # Review architecture with the architecture agent
    arch_result = await architecture_agent.process({
        "task_id": task_id,
        "code": generated_code,
        "cloud_provider": request.cloud_provider,
        "iac_type": request.iac_type
    })
    
    # Get the improved code and findings
    improved_code = arch_result.get("improved_code", generated_code)
    findings = arch_result.get("findings", {})
    
    # Update the result with architecture findings
    result = {
        "task_id": task_id,
        "code": improved_code,  # Use the improved code
        "metadata": infra_result.get("metadata", {}),
        "thoughts": infra_result.get("thoughts", ""),
        "architecture_findings": findings,
        "iac_type": request.iac_type,
        "cloud_provider": request.cloud_provider
    }
    
    # Add architecture findings to metadata
    if "metadata" in result:
        result["metadata"]["architecture_findings"] = findings
    
    # Store the task result
    tasks[task_id] = {
        "type": "infrastructure_generation",
        "request": request.dict(),
        "result": result,
        "original_code": generated_code,  # Store the original code for reference
        "improved_code": improved_code,  # Store the improved code
        "timestamp": datetime.now().isoformat()
    }
    
    return result

@app.post("/infrastructure/analyze", response_model=Dict[str, Any])
async def analyze_infrastructure(request: AnalysisRequest):
    """Analyze existing infrastructure code."""
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    
    # Analyze the infrastructure code
    analysis = await infrastructure_agent.analyze_infrastructure(
        infrastructure_code=request.infrastructure_code,
        iac_type=request.iac_type
    )
    
    return analysis

@app.post("/architecture/review", response_model=Dict[str, Any])
async def review_architecture(request: ArchitectureReviewRequest):
    """Review infrastructure architecture and suggest improvements."""
    if not architecture_agent:
        raise HTTPException(status_code=503, detail="Architecture agent not initialized")
    
    # Create a task ID
    task_id = str(uuid.uuid4())
    
    # Review architecture with the architecture agent
    result = await architecture_agent.process({
        "task_id": task_id,
        "code": request.infrastructure_code,
        "cloud_provider": request.cloud_provider,
        "iac_type": request.iac_type
    })
    
    # Store the task result
    tasks[task_id] = {
        "type": "architecture_review",
        "request": request.dict(),
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
    
    return result

@app.post("/infrastructure/estimate-costs", response_model=Dict[str, Any])
async def estimate_costs(request: AnalysisRequest):
    """Estimate costs for infrastructure code."""
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    
    # Estimate costs for the infrastructure code
    cost_estimate = await infrastructure_agent.estimate_costs(
        infrastructure_code=request.infrastructure_code,
        iac_type=request.iac_type,
        cloud_provider=request.cloud_provider
    )
    
    return cost_estimate

# ----- Pattern Repository Endpoints -----

@app.post("/patterns", response_model=Dict[str, Any])
async def create_pattern(pattern: PatternCreate):
    """Create a new infrastructure pattern."""
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    if not infrastructure_agent.vector_db_service:
        raise HTTPException(status_code=503, detail="Vector DB service not available")
    
    # Save the pattern
    result = await infrastructure_agent.save_pattern(
        name=pattern.name,
        description=pattern.description,
        code=pattern.code,
        cloud_provider=pattern.cloud_provider,
        iac_type=pattern.iac_type,
        metadata=pattern.metadata
    )
    
    return result

@app.get("/patterns/{pattern_id}", response_model=Dict[str, Any])
async def get_pattern(pattern_id: str):
    """Get a pattern by ID."""
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    if not infrastructure_agent.vector_db_service:
        raise HTTPException(status_code=503, detail="Vector DB service not available")
    
    # Get the pattern
    pattern = await infrastructure_agent.get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
    
    return pattern

@app.put("/patterns/{pattern_id}", response_model=Dict[str, Any])
async def update_pattern(pattern_id: str, pattern: PatternUpdate):
    """Update an existing pattern."""
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    if not infrastructure_agent.vector_db_service:
        raise HTTPException(status_code=503, detail="Vector DB service not available")
    
    # Update the pattern
    result = await infrastructure_agent.update_pattern(
        pattern_id=pattern_id,
        name=pattern.name,
        description=pattern.description,
        code=pattern.code,
        cloud_provider=pattern.cloud_provider,
        iac_type=pattern.iac_type,
        metadata=pattern.metadata
    )
    
    return result

@app.delete("/patterns/{pattern_id}", response_model=Dict[str, Any])
async def delete_pattern(pattern_id: str):
    """Delete a pattern."""
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    if not infrastructure_agent.vector_db_service:
        raise HTTPException(status_code=503, detail="Vector DB service not available")
    
    # Delete the pattern
    result = await infrastructure_agent.delete_pattern(pattern_id)
    
    return result

@app.post("/patterns/search", response_model=List[Dict[str, Any]])
async def search_patterns(request: PatternSearchRequest):
    """Search for infrastructure patterns."""
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    if not infrastructure_agent.vector_db_service:
        raise HTTPException(status_code=503, detail="Vector DB service not available")
    
    # Search for patterns
    patterns = await infrastructure_agent.find_patterns(
        query=request.query,
        cloud_provider=request.cloud_provider,
        iac_type=request.iac_type,
        n_results=request.n_results
    )
    
    return patterns

@app.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(task_id: str):
    """Get the details of a specific task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    return tasks[task_id]

@app.get("/tasks", response_model=List[Dict[str, Any]])
async def list_tasks(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    task_type: Optional[str] = Query(None)
):
    """List all tasks, with optional filtering."""
    # Filter tasks by type if specified
    filtered_tasks = [
        {"task_id": task_id, **task_data}
        for task_id, task_data in tasks.items()
        if task_type is None or task_data.get("type") == task_type
    ]
    
    # Sort by timestamp (newest first)
    sorted_tasks = sorted(
        filtered_tasks,
        key=lambda t: t.get("timestamp", ""),
        reverse=True
    )
    
    # Apply pagination
    paginated_tasks = sorted_tasks[offset:offset + limit]
    
    return paginated_tasks

# ----- Main function to run the server -----

def run_server():
    """Run the FastAPI server."""
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    run_server()