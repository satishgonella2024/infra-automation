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
from src.services.llm import LLMService

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
    iac_type: str = Field(..., description="Type of IaC that was generated")
    cloud_provider: str = Field(..., description="Target cloud provider")

class AnalysisRequest(BaseModel):
    """Request model for infrastructure code analysis."""
    infrastructure_code: str = Field(..., description="Infrastructure code to analyze")
    iac_type: str = Field(..., description="Type of IaC (terraform, ansible, jenkins)")
    cloud_provider: str = Field(default="aws", description="Target cloud provider")

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

# Create LLM service and agents when the app starts
llm_service = None
infrastructure_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    global llm_service, infrastructure_agent
    
    # Get LLM configuration from environment variables
    llm_provider = os.environ.get("LLM_PROVIDER", "ollama")
    llm_model = os.environ.get("LLM_MODEL", "llama2")
    llm_api_base = os.environ.get("LLM_API_BASE", "http://localhost:11434/api")
    llm_api_key = os.environ.get("LLM_API_KEY")
    
    # Create LLM service
    llm_service = LLMService(
        provider=llm_provider,
        model=llm_model,
        api_base=llm_api_base,
        api_key=llm_api_key
    )
    
    # Create and register agents
    infrastructure_agent = InfrastructureAgent(
        llm_service=llm_service,
        config={"templates_dir": "templates"}
    )
    
    # Register agents in the global store
    agents["infrastructure"] = infrastructure_agent

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
    if not infrastructure_agent:
        raise HTTPException(status_code=503, detail="Infrastructure agent not initialized")
    
    # Create a task ID
    task_id = str(uuid.uuid4())
    
    # Process the request with the infrastructure agent
    result = await infrastructure_agent.process({
        "task_id": task_id,
        "task": request.task,
        "requirements": request.requirements,
        "cloud_provider": request.cloud_provider,
        "iac_type": request.iac_type
    })
    
    # Store the task result
    tasks[task_id] = {
        "type": "infrastructure_generation",
        "request": request.dict(),
        "result": result,
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