from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.deployment import DeploymentConfig

class WorkflowState(BaseModel):
    """
    Represents the current state of a workflow execution.
    
    Tracks all information related to a deployment workflow, including
    configurations, current status, and outputs.
    """
    workflow_id: str
    user_id: str
    template_id: Optional[str] = None
    status: str  # initialized, validating, validated, deploying, deployment_completed, failed, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Input configuration
    deployment_config: Optional[DeploymentConfig] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Tracking deployment
    deployment_status: Optional[str] = None
    deployed_resources: Dict[str, Any] = Field(default_factory=dict)
    resource_endpoints: Dict[str, str] = Field(default_factory=dict)
    
    # Errors and logs
    errors: List[str] = Field(default_factory=list)
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_log(self, agent: str, message: str, level: str = "info") -> None:
        """Add a log entry to the workflow state."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "level": level,
            "message": message
        })
        self.updated_at = datetime.utcnow()
    
    def add_error(self, error_message: str) -> None:
        """Add an error message to the workflow state."""
        self.errors.append(error_message)
        self.add_log("workflow", error_message, level="error")
        if self.status != "failed":
            self.status = "failed"
    
    def update_status(self, new_status: str) -> None:
        """Update the workflow status."""
        self.status = new_status
        self.add_log("workflow", f"Status updated to: {new_status}")
        self.updated_at = datetime.utcnow()

class WorkflowTemplate(BaseModel):
    """
    Template for creating workflows.
    
    Defines the structure of a workflow including steps, agents,
    and validation rules.
    """
    id: str
    name: str
    description: str
    version: str
    
    # Workflow structure
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    
    # UI configuration for gathering inputs
    input_form: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation rules
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    
    # Default deployment configuration template
    default_deployment_template_id: Optional[str] = None

class WorkflowManager:
    """
    Manages workflow execution and state transitions.
    
    This class coordinates the execution of workflow steps,
    manages state transitions, and handles errors.
    """
    
    def __init__(self):
        self.workflow_templates = {}  # Dict to store available workflow templates
    
    def register_template(self, template: WorkflowTemplate) -> None:
        """Register a workflow template."""
        self.workflow_templates[template.id] = template
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by ID."""
        return self.workflow_templates.get(template_id)
    
    async def initialize_workflow(self, template_id: str, user_id: str, inputs: Dict[str, Any]) -> WorkflowState:
        """Initialize a new workflow based on a template."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Workflow template not found: {template_id}")
        
        # Generate a unique workflow ID
        workflow_id = f"wf-{user_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create initial workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            user_id=user_id,
            template_id=template_id,
            status="initialized",
            inputs=inputs
        )
        
        workflow_state.add_log("workflow_manager", f"Initialized workflow from template: {template.name}")
        
        return workflow_state
    
    async def execute_workflow(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute a workflow from start to finish.
        
        Args:
            workflow_state: The initial workflow state
            
        Returns:
            The final workflow state after execution
        """
        if workflow_state.status != "initialized":
            workflow_state.add_log("workflow_manager", "Workflow already in progress or completed", "warning")
            return workflow_state
        
        template = self.get_template(workflow_state.template_id)
        if not template:
            workflow_state.add_error(f"Workflow template not found: {workflow_state.template_id}")
            return workflow_state
        
        try:
            # Execute each step in the workflow
            for step in template.steps:
                step_id = step["id"]
                agent_name = step["agent"]
                
                workflow_state.update_status(f"executing_step_{step_id}")
                workflow_state.add_log("workflow_manager", f"Executing step: {step_id} with agent: {agent_name}")
                
                # In a real implementation, you would instantiate and call the appropriate agent here
                # For now, we'll just simulate the step execution
                
                # If any step fails, break the workflow
                if workflow_state.status == "failed":
                    break
            
            # If we made it through all steps without failure, mark as completed
            if workflow_state.status != "failed":
                workflow_state.update_status("completed")
                workflow_state.add_log("workflow_manager", "Workflow completed successfully")
        
        except Exception as e:
            workflow_state.add_error(f"Workflow execution error: {str(e)}")
        
        return workflow_state