"""
Workflow API Module for Multi-Agent Infrastructure Automation System

This module extends the FastAPI server with endpoints for workflow management,
including definitions, instances, execution, and monitoring.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.agents.base.base_agent import BaseAgent
from src.workflow.orchestrator import WorkflowOrchestrator
from src.workflow.schema import WorkflowDefinition, WorkflowStep, AgentCapabilities
from src.workflow.init import initialize_workflow_templates

# Create a router
router = APIRouter(
    prefix="/api/workflows",
    tags=["workflows"],
    responses={404: {"description": "Not found"}},
)

# Global orchestrator instance (will be set during startup)
orchestrator = None

def get_orchestrator() -> WorkflowOrchestrator:
    """Get the global orchestrator instance."""
    global orchestrator
    if orchestrator is None:
        # Try to initialize the orchestrator with available agents
        from src.api.server import agents
        if agents:
            try:
                orchestrator = WorkflowOrchestrator(agents)
                logger.info("Workflow orchestrator initialized on-demand")
                return orchestrator
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator on-demand: {str(e)}")
                
        # If we still don't have an orchestrator, raise an exception
        raise HTTPException(
            status_code=503,
            detail="Workflow orchestrator not initialized"
        )
    return orchestrator

# --- Pydantic Models ---

class WorkflowDefinitionRequest(BaseModel):
    """Request model for creating a workflow definition."""
    name: str = Field(..., description="Name of the workflow")
    description: str = Field(..., description="Description of the workflow")
    steps: List[Dict[str, Any]] = Field(..., description="List of workflow steps")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class WorkflowDefinitionResponse(BaseModel):
    """Response model for workflow definition operations."""
    id: str = Field(..., description="Unique ID of the workflow definition")
    name: str = Field(..., description="Name of the workflow")
    description: str = Field(..., description="Description of the workflow")
    steps: List[Dict[str, Any]] = Field(..., description="List of workflow steps")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

class WorkflowInstanceRequest(BaseModel):
    """Request model for creating a workflow instance."""
    definition_id: str = Field(..., description="ID of the workflow definition")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the workflow")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class WorkflowInstanceResponse(BaseModel):
    """Response model for workflow instance operations."""
    id: str = Field(..., description="Unique ID of the workflow instance")
    definition_id: str = Field(..., description="ID of the workflow definition")
    definition_name: str = Field(..., description="Name of the workflow definition")
    status: str = Field(..., description="Workflow status")
    steps: List[Dict[str, Any]] = Field(..., description="List of workflow steps")
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow")
    output_data: Dict[str, Any] = Field(..., description="Output data from the workflow")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")

class WorkflowTemplateRequest(BaseModel):
    """Request model for creating a workflow from a template."""
    template_type: str = Field(..., description="Type of template to create")
    name: Optional[str] = Field(None, description="Custom name for the workflow")
    description: Optional[str] = Field(None, description="Custom description for the workflow")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Template parameters")

# --- API Endpoints ---

@router.get("/test", response_model=Dict[str, str])
async def test_workflow_api():
    """Test endpoint to verify the workflow API is accessible."""
    return {"status": "ok", "message": "Workflow API is accessible"}

@router.get("/", response_model=List[WorkflowDefinitionResponse])
async def list_workflow_definitions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """List all workflow definitions."""
    try:
        definitions = await orchestrator.list_workflow_definitions()
        
        # Filter by search term if provided
        if search:
            search = search.lower()
            definitions = [
                d for d in definitions
                if search in d["name"].lower() or search in d["description"].lower()
            ]
        
        # Sort by name
        definitions.sort(key=lambda d: d["name"])
        
        # Apply pagination
        return definitions[offset:offset + limit]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing workflow definitions: {str(e)}"
        )

@router.post("/", response_model=WorkflowDefinitionResponse)
async def create_workflow_definition(
    definition: WorkflowDefinitionRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Create a new workflow definition."""
    try:
        # Create the workflow definition
        workflow_def = await orchestrator.create_workflow_definition(
            name=definition.name,
            description=definition.description,
            steps=definition.steps,
            metadata=definition.metadata
        )
        
        return workflow_def
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating workflow definition: {str(e)}"
        )

@router.get("/{definition_id}", response_model=WorkflowDefinitionResponse)
async def get_workflow_definition(
    definition_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Get a workflow definition by ID."""
    try:
        definition = await orchestrator.get_workflow_definition(definition_id)
        if not definition:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow definition {definition_id} not found"
            )
        
        return definition
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting workflow definition: {str(e)}"
        )

@router.put("/{definition_id}", response_model=WorkflowDefinitionResponse)
async def update_workflow_definition(
    definition_id: str,
    definition: WorkflowDefinitionRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Update a workflow definition."""
    try:
        # Check if the definition exists
        existing_def = await orchestrator.get_workflow_definition(definition_id)
        if not existing_def:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow definition {definition_id} not found"
            )
        
        # Update the workflow definition
        updated_def = await orchestrator.update_workflow_definition(
            definition_id=definition_id,
            name=definition.name,
            description=definition.description,
            steps=definition.steps,
            metadata=definition.metadata
        )
        
        return updated_def
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating workflow definition: {str(e)}"
        )

@router.delete("/{definition_id}")
async def delete_workflow_definition(
    definition_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Delete a workflow definition."""
    try:
        # Delete the workflow definition
        deleted = await orchestrator.delete_workflow_definition(definition_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow definition {definition_id} not found"
            )
        
        return {"message": f"Workflow definition {definition_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting workflow definition: {str(e)}"
        )

@router.post("/templates", response_model=WorkflowDefinitionResponse)
async def create_workflow_from_template(
    request: WorkflowTemplateRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Create a workflow definition from a template."""
    try:
        # Get workflow registry
        from src.workflow.schema import WorkflowRegistry
        registry = WorkflowRegistry()
        
        # Create the template
        template = registry.create_workflow_template(request.template_type)
        
        # Apply custom name and description
        if request.name:
            template.name = request.name
        if request.description:
            template.description = request.description
        
        # Apply parameters
        if request.parameters:
            # Update the steps with the parameters
            for step in template.steps:
                step_params = request.parameters.get(step.id, {})
                if step_params:
                    for param_name, param_value in step_params.items():
                        if param_name in step.parameters:
                            step.parameters[param_name] = param_value
                            
        # Convert template to definition format
        template_dict = template.dict()
        
        # Create the workflow definition
        workflow_def = await orchestrator.create_workflow_definition(
            name=template.name,
            description=template.description,
            steps=[step.dict() for step in template.steps],
            metadata=template.dict().get("metadata", {})
        )
        
        return workflow_def
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating workflow from template: {str(e)}"
        )

@router.get("/templates", response_model=List[str])
async def list_workflow_templates():
    """List available workflow template types."""
    try:
        # Return the list of template types
        return [
            "infrastructure_pipeline",
            "terraform_to_k8s",
            "security_review",
            "empty"
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing workflow templates: {str(e)}"
        )

@router.post("/instances", response_model=WorkflowInstanceResponse)
async def create_workflow_instance(
    request: WorkflowInstanceRequest,
    background_tasks: BackgroundTasks,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Create a new workflow instance."""
    try:
        # Check if the definition exists
        definition = await orchestrator.get_workflow_definition(request.definition_id)
        if not definition:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow definition {request.definition_id} not found"
            )
        
        # Create the workflow instance
        instance = await orchestrator.create_workflow_instance(
            definition_id=request.definition_id,
            input_data=request.input_data,
            metadata=request.metadata
        )
        
        return instance
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating workflow instance: {str(e)}"
        )

@router.get("/instances", response_model=List[WorkflowInstanceResponse])
async def list_workflow_instances(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    definition_id: Optional[str] = None,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """List all workflow instances."""
    try:
        instances = await orchestrator.list_workflow_instances(
            status=status,
            definition_id=definition_id,
            limit=limit,
            offset=offset
        )
        return instances
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing workflow instances: {str(e)}"
        )

@router.get("/instances/{instance_id}", response_model=WorkflowInstanceResponse)
async def get_workflow_instance(
    instance_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Get a workflow instance by ID."""
    try:
        # Get the workflow instance
        instance = await orchestrator.get_workflow_instance(instance_id)
        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow instance {instance_id} not found"
            )
        
        return instance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting workflow instance: {str(e)}"
        )

@router.post("/instances/{instance_id}/cancel")
async def cancel_workflow_instance(
    instance_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """Cancel a workflow instance."""
    try:
        # Cancel the workflow instance
        cancelled = await orchestrator.cancel_workflow(instance_id)
        if not cancelled:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow instance {instance_id} not found or already completed"
            )
        
        return {"message": f"Workflow instance {instance_id} cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cancelling workflow instance: {str(e)}"
        )

@router.get("/agents", response_model=Dict[str, Dict[str, Any]])
async def list_agent_capabilities(
    orchestrator: WorkflowOrchestrator = Depends(get_orchestrator)
):
    """List all available agents and their capabilities."""
    try:
        agent_capabilities = {}
        for name, agent in orchestrator.agents.items():
            agent_capabilities[name] = await _get_agent_actions(agent)
        return agent_capabilities
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing agent capabilities: {str(e)}"
        )

async def _get_agent_actions(agent: BaseAgent) -> Dict[str, Dict[str, Any]]:
    """Get the actions available for an agent."""
    actions = {}
    
    # Get agent capabilities
    capabilities = getattr(agent, "capabilities", [])
    
    # Convert capabilities to actions
    for capability in capabilities:
        action_name = capability.replace("_", " ").title()
        actions[capability] = {
            "name": action_name,
            "description": f"Perform {action_name.lower()} operation",
            "parameters": {}
        }
    
    return {
        "name": getattr(agent, "name", agent.__class__.__name__),
        "description": getattr(agent, "description", "AI agent for infrastructure automation"),
        "capabilities": capabilities,
        "actions": actions
    }

# Initialize the orchestrator
def initialize_orchestrator(agents: Dict[str, BaseAgent]):
    """Initialize the global orchestrator instance."""
    global orchestrator
    
    orchestrator = WorkflowOrchestrator(agents)
    
    return orchestrator