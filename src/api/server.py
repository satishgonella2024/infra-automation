"""
API Server Module for Multi-Agent Infrastructure Automation System

This module defines the FastAPI app that serves as the interface for users
to interact with the multi-agent system.
"""

import os
import json
import uuid
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Import our agent components
from src.agents.base import BaseAgent
from src.agents.infra import InfrastructureAgent
from src.agents.architect import ArchitectureAgent
from src.agents.security import SecurityAgent
from src.agents.cost import CostAgent
from src.agents.terraform import TerraformModuleAgent  # Add import for terraform module agent
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
    allow_origins=["http://192.168.5.199", "http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
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
    security_findings: Dict[str, Any] = Field(default_factory=dict, description="Security review findings")
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

class SecurityReviewRequest(BaseModel):
    """Request model for security review."""
    infrastructure_code: str = Field(..., description="Infrastructure code to review")
    iac_type: str = Field(..., description="Type of IaC (terraform, ansible, jenkins)")
    cloud_provider: str = Field(default="aws", description="Target cloud provider")
    compliance_framework: Optional[str] = Field(None, description="Specific compliance framework to check against")

class CostOptimizationRequest(BaseModel):
    """Request model for cost optimization."""
    code: str = Field(..., description="Infrastructure code to analyze")
    cloud_provider: str = Field(default="aws", description="Target cloud provider (aws, azure, gcp)")
    iac_type: str = Field(default="terraform", description="Type of IaC (terraform, ansible, jenkins)")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for tracking")

class CostOptimizationResponse(BaseModel):
    """Response model for cost optimization."""
    task_id: str = Field(..., description="Unique ID for this task")
    original_code: str = Field(..., description="Original infrastructure code")
    optimized_code: str = Field(..., description="Cost-optimized infrastructure code")
    cost_analysis: Dict[str, Any] = Field(..., description="Cost analysis results")
    optimization_summary: Dict[str, Any] = Field(..., description="Summary of optimizations made")
    thoughts: str = Field(..., description="Agent's thought process")
    cloud_provider: str = Field(..., description="Target cloud provider")
    iac_type: str = Field(..., description="Type of IaC that was analyzed")

class SystemMetrics(BaseModel):
    """Response model for system metrics."""
    gpu_usage: Optional[Dict[str, Any]] = None
    cpu_usage: float
    memory_usage: Dict[str, float]
    disk_usage: Dict[str, Union[str, float]] = Field(
        default_factory=lambda: {
            "total": "0",
            "used": "0",
            "percent": 0.0
        }
    )
    llm_metrics: Dict[str, Any]

class TerraformModuleRequest(BaseModel):
    """Request model for Terraform module generation."""
    task: str = Field(..., description="Description of the module to generate")
    requirements: Dict[str, Any] = Field(..., description="Specific module requirements")
    cloud_provider: str = Field(default="aws", description="Target cloud provider (aws, azure, gcp)")
    module_type: str = Field(default="compute", description="Type of module (networking, compute, storage, security)")
    module_name: Optional[str] = Field(default=None, description="Custom module name")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for tracking")

class TerraformModuleResponse(BaseModel):
    """Response model for Terraform module generation."""
    task_id: str = Field(..., description="Unique ID for this task")
    module_files: Dict[str, str] = Field(..., description="Generated module files")
    metadata: Dict[str, Any] = Field(..., description="Module metadata")
    thoughts: str = Field(..., description="Agent's thought process")
    module_type: str = Field(..., description="Type of module that was generated")
    cloud_provider: str = Field(..., description="Target cloud provider")
    module_name: str = Field(..., description="Name of the generated module")

# ----- Globals and initialization -----

# Store for our agents
agents: Dict[str, BaseAgent] = {}

# In-memory task store (would be replaced with a database in production)
tasks: Dict[str, Dict[str, Any]] = {}

# File path for persisting tasks
TASKS_FILE = os.environ.get("TASKS_FILE", "/app/data/tasks.json")

# Function to save tasks to a file
def save_tasks():
    """Save tasks to a file for persistence."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
        
        # Ensure directory has write permissions
        os.chmod(os.path.dirname(TASKS_FILE), 0o777)
        
        # Convert tasks to a serializable format
        serializable_tasks = {}
        for task_id, task_data in tasks.items():
            # Create a copy of the task data
            task_copy = task_data.copy()
            # Convert any non-serializable objects to strings
            for key, value in task_copy.items():
                if isinstance(value, (datetime, bytes)):
                    task_copy[key] = str(value)
            serializable_tasks[task_id] = task_copy
        
        # Write to file with proper permissions
        with open(TASKS_FILE, 'w') as f:
            json.dump(serializable_tasks, f, indent=2, default=str)
        
        # Set file permissions
        os.chmod(TASKS_FILE, 0o666)
        print(f"Tasks saved to {TASKS_FILE}")
    except Exception as e:
        print(f"Error saving tasks to file: {str(e)}")
        import traceback
        traceback.print_exc()

# Function to load tasks from a file
def load_tasks():
    """Load tasks from a file."""
    global tasks
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                loaded_tasks = json.load(f)
            
            # Convert the loaded tasks back to the original format
            tasks.clear()  # Clear existing tasks
            tasks.update(loaded_tasks)  # Update with loaded tasks
            
            print(f"Loaded {len(tasks)} tasks from {TASKS_FILE}")
        else:
            print(f"No tasks file found at {TASKS_FILE}, starting with empty task list")
            tasks.clear()  # Ensure we start with an empty dict
    except Exception as e:
        print(f"Error loading tasks from file: {str(e)}")
        import traceback
        traceback.print_exc()
        tasks.clear()  # Reset to empty dict on error

# System start time
start_time = datetime.now()

# Create services and agents when the app starts
llm_service = None
vector_db_service = None
infrastructure_agent = None
architecture_agent = None
security_agent = None
cost_agent = None
terraform_module_agent = None  # Add terraform module agent variable

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    global llm_service, vector_db_service, infrastructure_agent, architecture_agent, security_agent, cost_agent, terraform_module_agent  # Add terraform_module_agent to globals
    
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
    
    # Initialize security agent
    security_agent = SecurityAgent(
        llm_service=llm_service,
        vector_db_service=vector_db_service,
        config={"templates_dir": "templates"}
    )
    
    # Initialize cost optimization agent
    cost_agent = CostAgent(
        llm_service=llm_service,
        vector_db_service=vector_db_service,
        config={"templates_dir": "templates"}
    )
    
    # Initialize terraform module agent
    terraform_module_agent = TerraformModuleAgent(
        llm_service=llm_service,
        vector_db_service=vector_db_service,
        config={"templates_dir": "templates"}
    )
    
    # Register agents in the global store
    agents["infrastructure"] = infrastructure_agent
    agents["architecture"] = architecture_agent
    agents["security"] = security_agent
    agents["cost"] = cost_agent
    agents["terraform_module"] = terraform_module_agent  # Register terraform module agent
    
    # Load tasks from file
    load_tasks()

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

@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Get the current status of the server and all registered agents.
    
    Returns:
        A dictionary containing server status information and agent states
    """
    try:
        # Calculate uptime
        uptime_seconds = (datetime.now() - start_time).total_seconds()
        
        # Get agent statuses
        agent_statuses = []
        for agent_name, agent in agents.items():
            try:
                agent_status = agent.serialize()
                agent_statuses.append(agent_status)
            except Exception as e:
                print(f"Error getting status for agent {agent_name}: {str(e)}")
                # Add a fallback status for the failed agent
                agent_statuses.append({
                    "id": "unknown",
                    "name": agent_name,
                    "description": "Agent status unavailable",
                    "state": "error",
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "online",
            "version": "1.0.0",
            "uptime_seconds": uptime_seconds,
            "agents": agent_statuses,
            "tasks_count": len(tasks),
            "last_task_time": get_last_task_time(tasks, start_time)
        }
    except Exception as e:
        print(f"Error getting system status: {str(e)}")
        return {
            "status": "error",
            "version": "1.0.0",
            "error": str(e),
            "uptime_seconds": 0,
            "agents": [],
            "tasks_count": 0
        }

def get_last_task_time(tasks, default_time):
    """Get the most recent task timestamp, handling string and datetime formats."""
    try:
        # Filter out None timestamps and convert string timestamps to datetime objects
        valid_timestamps = []
        for task in tasks.values():
            timestamp = task.get("timestamp")
            if timestamp:
                # If timestamp is a string, convert to datetime
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                        valid_timestamps.append(timestamp)
                    except ValueError:
                        # Skip invalid timestamp formats
                        pass
                elif isinstance(timestamp, datetime):
                    valid_timestamps.append(timestamp)
        
        # Get the max timestamp if there are any valid ones
        if valid_timestamps:
            return max(valid_timestamps)
        return default_time
    except Exception as e:
        print(f"Error getting last task time: {str(e)}")
        return default_time

@app.post("/infrastructure/generate", response_model=InfrastructureResponse)
async def generate_infrastructure(request: InfrastructureRequest):
    """Generate infrastructure as code based on requirements."""
    if not infrastructure_agent or not architecture_agent or not security_agent:
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
    arch_findings = arch_result.get("findings", {})
    
    # Review security with the security agent
    security_result = await security_agent.process({
        "task_id": task_id,
        "code": improved_code,
        "cloud_provider": request.cloud_provider,
        "iac_type": request.iac_type
    })
    
    # Get the security-enhanced code and findings
    security_enhanced_code = security_result.get("remediated_code", improved_code)
    security_vulnerabilities = security_result.get("vulnerabilities", [])
    
    # Convert vulnerabilities list to a dictionary for the response
    security_findings = {
        "vulnerabilities": security_vulnerabilities,
        "summary": security_result.get("remediation_summary", ""),
        "risk_score": security_result.get("risk_score", 0),
        "compliance_results": security_result.get("compliance_results", {})
    }
    
    # Update the result with architecture and security findings
    result = {
        "task_id": task_id,
        "code": security_enhanced_code,  # Use the security-enhanced code
        "metadata": infra_result.get("metadata", {}),
        "thoughts": infra_result.get("thoughts", ""),
        "architecture_findings": arch_findings,
        "security_findings": security_findings,
        "iac_type": request.iac_type,
        "cloud_provider": request.cloud_provider
    }
    
    # Add architecture and security findings to metadata
    if "metadata" in result:
        result["metadata"]["architecture_findings"] = arch_findings
        result["metadata"]["security_findings"] = security_findings
    
    # Store the task result
    tasks[task_id] = {
        "type": "infrastructure_generation",
        "request": request.dict(),
        "result": result,
        "original_code": generated_code,  # Store the original code for reference
        "improved_code": improved_code,  # Store the architecture-improved code
        "secured_code": security_enhanced_code,  # Store the security-enhanced code
        "timestamp": datetime.now().isoformat()
    }
    
    # Save tasks to file
    save_tasks()
    
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

@app.post("/infrastructure/optimize-costs", response_model=CostOptimizationResponse)
async def optimize_costs(request: CostOptimizationRequest):
    """Analyze and optimize infrastructure costs."""
    if not cost_agent:
        raise HTTPException(status_code=503, detail="Cost optimization agent not initialized")
    
    # Generate a task ID if not provided
    task_id = request.task_id or str(uuid.uuid4())
    
    try:
        # Process the request with the cost agent
        result = await cost_agent.process({
            "task_id": task_id,
            "code": request.code,
            "cloud_provider": request.cloud_provider,
            "iac_type": request.iac_type
        })
        
        # Save the task
        tasks[task_id] = {
            "type": "cost_optimization",
            "request": request.dict(),
            "result": result,
            "timestamp": datetime.now()
        }
        save_tasks()
        
        return {
            "task_id": task_id,
            "original_code": result["original_code"],
            "optimized_code": result["optimized_code"],
            "cost_analysis": result["cost_analysis"],
            "optimization_summary": result["optimization_summary"],
            "thoughts": result["thoughts"],
            "cloud_provider": result["cloud_provider"],
            "iac_type": result["iac_type"]
        }
        
    except Exception as e:
        logger.error(f"Error during cost optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Add a new endpoint for security review
@app.post("/security/review", response_model=Dict[str, Any])
async def review_security(request: SecurityReviewRequest):
    """Review infrastructure security and suggest improvements."""
    if not security_agent:
        raise HTTPException(status_code=503, detail="Security agent not initialized")
    
    # Create a task ID
    task_id = str(uuid.uuid4())
    
    # Review security with the security agent
    result = await security_agent.process({
        "task_id": task_id,
        "code": request.infrastructure_code,
        "cloud_provider": request.cloud_provider,
        "iac_type": request.iac_type,
        "compliance_framework": request.compliance_framework
    })
    
    # Store the task result
    tasks[task_id] = {
        "type": "security_review",
        "request": request.dict(),
        "result": result,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save tasks to file
    save_tasks()
    
    return result

# Add a new endpoint for infrastructure visualization
@app.get("/infrastructure/visualize/{task_id}", response_model=Dict[str, Any])
async def visualize_infrastructure(task_id: str):
    """Generate a visualization of the infrastructure for a specific task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task_data = tasks[task_id]
    
    # Check if this is an infrastructure generation task
    if task_data.get("type") != "infrastructure_generation":
        raise HTTPException(status_code=400, detail="Task is not an infrastructure generation task")
    
    # Get the infrastructure code from the task
    code = task_data.get("result", {}).get("code", "")
    if not code:
        raise HTTPException(status_code=404, detail="No infrastructure code found for this task")
    
    # Generate a simple visualization based on the infrastructure code
    # This is a simplified example - in a real implementation, you would parse the
    # infrastructure code and generate a more accurate visualization
    
    # Example visualization for common infrastructure components
    visualization = {
        "nodes": [],
        "edges": []
    }
    
    # Add nodes based on keywords in the code
    node_id = 1
    node_mapping = {}
    
    # Check for common infrastructure components
    components = [
        {"keyword": "vpc", "label": "VPC", "color": "#1976d2"},
        {"keyword": "subnet", "label": "Subnet", "color": "#4caf50"},
        {"keyword": "security_group", "label": "Security Group", "color": "#ff9800"},
        {"keyword": "instance", "label": "EC2 Instance", "color": "#f44336"},
        {"keyword": "database", "label": "Database", "color": "#9c27b0"},
        {"keyword": "bucket", "label": "S3 Bucket", "color": "#00bcd4"},
        {"keyword": "load_balancer", "label": "Load Balancer", "color": "#3f51b5"},
        {"keyword": "lambda", "label": "Lambda Function", "color": "#795548"},
        {"keyword": "api_gateway", "label": "API Gateway", "color": "#607d8b"},
        {"keyword": "cloudfront", "label": "CloudFront", "color": "#9e9e9e"}
    ]
    
    # Check for each component in the code
    for component in components:
        if component["keyword"] in code.lower():
            # Add the node
            visualization["nodes"].append({
                "id": node_id,
                "label": component["label"],
                "color": component["color"]
            })
            node_mapping[component["keyword"]] = node_id
            node_id += 1
    
    # If no components were found, create a sample visualization
    if not visualization["nodes"]:
        visualization["nodes"] = [
            {"id": 1, "label": "VPC", "color": "#1976d2"},
            {"id": 2, "label": "Public Subnet", "color": "#4caf50"},
            {"id": 3, "label": "Private Subnet", "color": "#ff9800"},
            {"id": 4, "label": "EC2 Instance", "color": "#f44336"},
            {"id": 5, "label": "RDS Database", "color": "#9c27b0"},
            {"id": 6, "label": "S3 Bucket", "color": "#00bcd4"},
            {"id": 7, "label": "Load Balancer", "color": "#3f51b5"}
        ]
        visualization["edges"] = [
            {"from": 1, "to": 2},
            {"from": 1, "to": 3},
            {"from": 2, "to": 4},
            {"from": 2, "to": 7},
            {"from": 3, "to": 5},
            {"from": 7, "to": 4},
            {"from": 4, "to": 5},
            {"from": 4, "to": 6}
        ]
        return visualization
    
    # Add edges based on common relationships
    # VPC to Subnet
    if "vpc" in node_mapping and "subnet" in node_mapping:
        visualization["edges"].append({
            "from": node_mapping["vpc"],
            "to": node_mapping["subnet"]
        })
    
    # Subnet to Instance
    if "subnet" in node_mapping and "instance" in node_mapping:
        visualization["edges"].append({
            "from": node_mapping["subnet"],
            "to": node_mapping["instance"]
        })
    
    # Security Group to Instance
    if "security_group" in node_mapping and "instance" in node_mapping:
        visualization["edges"].append({
            "from": node_mapping["security_group"],
            "to": node_mapping["instance"]
        })
    
    # Instance to Database
    if "instance" in node_mapping and "database" in node_mapping:
        visualization["edges"].append({
            "from": node_mapping["instance"],
            "to": node_mapping["database"]
        })
    
    # Instance to S3 Bucket
    if "instance" in node_mapping and "bucket" in node_mapping:
        visualization["edges"].append({
            "from": node_mapping["instance"],
            "to": node_mapping["bucket"]
        })
    
    # Load Balancer to Instance
    if "load_balancer" in node_mapping and "instance" in node_mapping:
        visualization["edges"].append({
            "from": node_mapping["load_balancer"],
            "to": node_mapping["instance"]
        })
    
    return visualization

@app.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get system metrics including CPU, memory, disk, and GPU usage."""
    try:
        # Initialize metrics with default values
        metrics = {
            "gpu_usage": None,
            "cpu_usage": 0.0,
            "memory_usage": {"total_gb": 0, "used_gb": 0, "percent": 0},
            "disk_usage": {"total": "0", "used": "0", "percent": 0},
            "llm_metrics": {
                "total_requests": len(tasks),
                "active_requests": sum(1 for t in tasks.values() if t.get("status") == "running"),
                "last_request_time": None
            }
        }

        # Try to get GPU metrics using nvidia-smi
        try:
            gpu_cmd = "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits"
            gpu_output = subprocess.check_output(gpu_cmd, shell=True, text=True)
            gpu_metrics = gpu_output.strip().split(',')
            metrics["gpu_usage"] = {
                "utilization_percent": float(gpu_metrics[0]),
                "memory_used_gb": float(gpu_metrics[1]) / 1024,
                "memory_total_gb": float(gpu_metrics[2]) / 1024
            }
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError, IndexError) as e:
            print(f"GPU metrics collection failed: {str(e)}")
            # Keep gpu_usage as None to indicate no GPU metrics available

        # Get CPU usage
        try:
            cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
            cpu_output = subprocess.check_output(cpu_cmd, shell=True, text=True)
            metrics["cpu_usage"] = float(cpu_output.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            print(f"CPU metrics collection failed: {str(e)}")
            metrics["cpu_usage"] = 0.0

        # Get memory usage
        try:
            mem_cmd = "free -m | grep 'Mem:' | awk '{print $2,$3}'"
            mem_output = subprocess.check_output(mem_cmd, shell=True, text=True)
            total_mem, used_mem = map(float, mem_output.strip().split())
            metrics["memory_usage"] = {
                "total_gb": total_mem / 1024,
                "used_gb": used_mem / 1024,
                "percent": (used_mem / total_mem) * 100
            }
        except (subprocess.CalledProcessError, ValueError) as e:
            print(f"Memory metrics collection failed: {str(e)}")

        # Get disk usage
        try:
            disk_cmd = "df -h / | tail -1 | awk '{print $2,$3,$5}'"
            disk_output = subprocess.check_output(disk_cmd, shell=True, text=True)
            total_disk, used_disk, percent_disk = disk_output.strip().split()
            metrics["disk_usage"] = {
                "total": total_disk,  # Keep as string with units
                "used": used_disk,    # Keep as string with units
                "percent": float(percent_disk.rstrip('%'))
            }
        except (subprocess.CalledProcessError, ValueError) as e:
            print(f"Disk metrics collection failed: {str(e)}")

        # Try to get the last request time
        try:
            # Filter out None timestamps and convert string timestamps to datetime objects
            valid_timestamps = []
            for task in tasks.values():
                timestamp = task.get("timestamp")
                if timestamp:
                    # If timestamp is a string, convert to datetime
                    if isinstance(timestamp, str):
                        try:
                            timestamp = datetime.fromisoformat(timestamp)
                            valid_timestamps.append(timestamp)
                        except ValueError:
                            # Skip invalid timestamp formats
                            pass
                    elif isinstance(timestamp, datetime):
                        valid_timestamps.append(timestamp)
            
            # Get the max timestamp if there are any valid ones
            if valid_timestamps:
                last_timestamp = max(valid_timestamps)
                metrics["llm_metrics"]["last_request_time"] = last_timestamp.isoformat()
        except Exception as e:
            print(f"Error processing timestamps: {str(e)}")

        return metrics
    except Exception as e:
        print(f"Error getting system metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error getting system metrics",
                "message": str(e)
            }
        )

@app.post("/terraform/module", response_model=TerraformModuleResponse)
async def generate_terraform_module(
    request: TerraformModuleRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate an enterprise-grade Terraform module based on the provided requirements.
    
    This endpoint uses the Terraform Module Agent to create a complete, production-ready
    Terraform module following best practices and enterprise patterns.
    """
    # Ensure the terraform module agent is available
    if "terraform_module" not in agents:
        raise HTTPException(
            status_code=503,
            detail="Terraform Module Agent is not available"
        )
    
    # Generate a task ID if not provided
    task_id = request.task_id or str(uuid.uuid4())
    
    # Create a task object
    task = {
        "id": task_id,
        "type": "terraform_module_generation",
        "status": "submitted",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "request": request.dict(),
        "result": None
    }
    
    # Store the task
    tasks[task_id] = task
    save_tasks()
    
    # Process the request in the background
    background_tasks.add_task(
        process_terraform_module_request,
        task_id=task_id,
        request=request
    )
    
    # Return the task ID immediately
    return JSONResponse(
        status_code=202,
        content={
            "task_id": task_id,
            "status": "submitted",
            "message": "Terraform module generation started"
        }
    )

async def process_terraform_module_request(task_id: str, request: TerraformModuleRequest):
    """Process a Terraform module generation request in the background."""
    try:
        # Update task status
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        save_tasks()
        
        # Prepare the input for the agent
        agent_input = {
            "task_id": task_id,
            "task": request.task,
            "requirements": request.requirements,
            "cloud_provider": request.cloud_provider,
            "module_type": request.module_type,
            "module_name": request.module_name
        }
        
        # Process the request with the Terraform Module Agent
        result = await agents["terraform_module"].process(agent_input)
        
        # Update the task with the result
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        save_tasks()
        
    except Exception as e:
        # Handle errors
        error_message = str(e)
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = error_message
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        save_tasks()
        
        print(f"Error processing Terraform module request: {error_message}")
        import traceback
        traceback.print_exc()

@app.get("/terraform/module/{task_id}", response_model=Dict[str, Any])
async def get_terraform_module_status(task_id: str):
    """Get the status of a Terraform module generation task."""
    if task_id not in tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    
    task = tasks[task_id]
    
    # If the task is completed, return the full result
    if task["status"] == "completed":
        return task
    
    # Otherwise, return just the status information
    return {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"]
    }

@app.get("/terraform/module/{task_id}/download")
async def download_terraform_module(task_id: str):
    """
    Download a Terraform module as a zip file.
    
    This endpoint creates a zip file containing all the files in the Terraform module
    and returns it for download.
    """
    import io
    import zipfile
    from fastapi.responses import StreamingResponse
    
    if task_id not in tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Task with ID {task_id} not found"
        )
    
    task = tasks[task_id]
    
    # Check if the task is a Terraform module generation task
    if task.get("type") != "terraform_module_generation":
        raise HTTPException(
            status_code=400,
            detail="Task is not a Terraform module generation task"
        )
    
    # Check if the task is completed
    if task.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Terraform module generation is not yet complete"
        )
    
    # Check if the task has a result with module files
    if not task.get("result") or not task.get("result").get("module_files"):
        raise HTTPException(
            status_code=404,
            detail="No module files found for this task"
        )
    
    # Get the module files
    module_files = task["result"]["module_files"]
    
    # Get the module name
    module_name = task["result"].get("module_name", "terraform-module")
    
    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, file_content in module_files.items():
            # Add each file to the zip
            zip_file.writestr(f"{module_name}/{file_path}", file_content)
    
    # Seek to the beginning of the buffer
    zip_buffer.seek(0)
    
    # Return the zip file as a streaming response
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{module_name}.zip"'
        }
    )

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