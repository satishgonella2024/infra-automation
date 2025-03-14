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
    if orchestrator is None:
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
    """List workflow instances."""
    try:
        # List workflow instances
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
    """List agent capabilities for use in the workflow editor."""
    agents = orchestrator.agents
    
    # Extract capabilities from agents
    capabilities = {}
    for agent_id, agent in agents.items():
        if not agent:
            continue
            
        agent_info = agent.serialize()
        
        # Add agent capabilities
        capabilities[agent_id] = {
            "name": agent_info.get("name", agent_id),
            "description": agent_info.get("description", ""),
            "capabilities": agent_info.get("capabilities", []),
            "actions": await _get_agent_actions(agent)
        }
    
    return capabilities

async def _get_agent_actions(agent: BaseAgent) -> Dict[str, Dict[str, Any]]:
    """Extract available actions from an agent."""
    # This is a simplified version - in a full implementation,
    # agents would provide their actions through a standard interface
    
    # Basic actions for all agents
    basic_actions = {
        "process": {
            "name": "Process",
            "description": "Process a generic request",
            "parameters": {
                "action": {
                    "type": "string",
                    "description": "The action to perform",
                    "required": True
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the action",
                    "required": True
                }
            }
        }
    }
    
    # Agent-specific actions based on capabilities
    agent_actions = {}
    
    # Get agent capabilities
    capabilities = getattr(agent, "capabilities", [])
    
    # Map capabilities to actions
    capability_mappings = {
        # Infrastructure agent
        "terraform_generation": {
            "generate_terraform": {
                "name": "Generate Terraform",
                "description": "Generate Terraform code from requirements",
                "parameters": {
                    "task": {
                        "type": "string",
                        "description": "Description of what to generate",
                        "required": True
                    },
                    "cloud_provider": {
                        "type": "string",
                        "description": "Target cloud provider (aws, azure, gcp)",
                        "default": "aws",
                        "required": False
                    },
                    "requirements": {
                        "type": "object",
                        "description": "Specific infrastructure requirements",
                        "required": False
                    }
                }
            }
        },
        
        # Security agent
        "vulnerability_scanning": {
            "review": {
                "name": "Security Review",
                "description": "Review infrastructure code for security vulnerabilities",
                "parameters": {
                    "code": {
                        "type": "string",
                        "description": "Infrastructure code to review",
                        "required": True
                    },
                    "cloud_provider": {
                        "type": "string",
                        "description": "Target cloud provider (aws, azure, gcp)",
                        "default": "aws",
                        "required": False
                    },
                    "iac_type": {
                        "type": "string",
                        "description": "Type of IaC (terraform, ansible, etc.)",
                        "default": "terraform",
                        "required": False
                    }
                }
            }
        },
        
        # Cost agent
        "cost_optimization": {
            "optimize": {
                "name": "Cost Optimization",
                "description": "Optimize infrastructure code for cost",
                "parameters": {
                    "code": {
                        "type": "string",
                        "description": "Infrastructure code to optimize",
                        "required": True
                    },
                    "cloud_provider": {
                        "type": "string",
                        "description": "Target cloud provider (aws, azure, gcp)",
                        "default": "aws",
                        "required": False
                    },
                    "iac_type": {
                        "type": "string",
                        "description": "Type of IaC (terraform, ansible, etc.)",
                        "default": "terraform",
                        "required": False
                    }
                }
            }
        },
        
        # Jira agent
        "issue_creation": {
            "create_issue": {
                "name": "Create Jira Issue",
                "description": "Create a new Jira issue",
                "parameters": {
                    "project_key": {
                        "type": "string",
                        "description": "Jira project key",
                        "required": True
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type (Bug, Story, etc.)",
                        "default": "Story",
                        "required": False
                    },
                    "summary": {
                        "type": "string",
                        "description": "Issue summary",
                        "required": True
                    },
                    "description": {
                        "type": "string",
                        "description": "Issue description",
                        "required": False
                    }
                }
            },
            "update_issue": {
                "name": "Update Jira Issue",
                "description": "Update an existing Jira issue",
                "parameters": {
                    "issue_key": {
                        "type": "string",
                        "description": "Jira issue key",
                        "required": True
                    },
                    "fields": {
                        "type": "object",
                        "description": "Fields to update",
                        "required": True
                    }
                }
            }
        },
        
        # GitHub agent
        "repository_management": {
            "create_repository": {
                "name": "Create GitHub Repository",
                "description": "Create a new GitHub repository",
                "parameters": {
                    "name": {
                        "type": "string",
                        "description": "Repository name",
                        "required": True
                    },
                    "description": {
                        "type": "string",
                        "description": "Repository description",
                        "required": False
                    },
                    "private": {
                        "type": "boolean",
                        "description": "Whether the repository should be private",
                        "default": False,
                        "required": False
                    }
                }
            }
        },
        "branch_management": {
            "create_branch": {
                "name": "Create GitHub Branch",
                "description": "Create a new branch in a GitHub repository",
                "parameters": {
                    "repo": {
                        "type": "string",
                        "description": "Repository name",
                        "required": True
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name",
                        "required": True
                    },
                    "base_branch": {
                        "type": "string",
                        "description": "Base branch",
                        "default": "main",
                        "required": False
                    }
                }
            }
        },
        "pull_request_automation": {
            "create_pr": {
                "name": "Create GitHub PR",
                "description": "Create a pull request in GitHub",
                "parameters": {
                    "repo": {
                        "type": "string",
                        "description": "Repository name",
                        "required": True
                    },
                    "title": {
                        "type": "string",
                        "description": "PR title",
                        "required": True
                    },
                    "body": {
                        "type": "string",
                        "description": "PR description",
                        "required": False
                    },
                    "head": {
                        "type": "string",
                        "description": "Head branch",
                        "required": True
                    },
                    "base": {
                        "type": "string",
                        "description": "Base branch",
                        "default": "main",
                        "required": False
                    }
                }
            }
        },
        
        # Confluence agent
        "page_creation": {
            "create_page": {
                "name": "Create Confluence Page",
                "description": "Create a new Confluence page",
                "parameters": {
                    "space_key": {
                        "type": "string",
                        "description": "Confluence space key",
                        "required": True
                    },
                    "title": {
                        "type": "string",
                        "description": "Page title",
                        "required": True
                    },
                    "content": {
                        "type": "string",
                        "description": "Page content",
                        "required": True
                    }
                }
            }
        }
    }
    
    # Add actions based on capabilities
    for capability in capabilities:
        if capability in capability_mappings:
            agent_actions.update(capability_mappings[capability])
    
    # Combine basic and agent-specific actions
    return {**basic_actions, **agent_actions}

# Initialize the orchestrator
def initialize_orchestrator(agents: Dict[str, BaseAgent]):
    """Initialize the global orchestrator instance."""
    global orchestrator
    
    orchestrator = WorkflowOrchestrator(agents)
    
    return orchestrator