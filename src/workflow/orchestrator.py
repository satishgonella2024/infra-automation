"""
Workflow Orchestrator Module for Multi-Agent Infrastructure Automation System

This module defines the WorkflowOrchestrator class that coordinates the execution
of multi-agent workflows, managing state, dependencies, and agent interactions.
"""

import os
import uuid
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple, Union

from src.agents.base.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class WorkflowStatus:
    """Status constants for workflows and tasks."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"

class WorkflowOrchestrator:
    """
    Orchestrates workflows involving multiple agents, tracking dependencies,
    states, and results throughout the workflow execution.
    """
    
    def __init__(self, agents: Dict[str, BaseAgent]):
        """
        Initialize a new WorkflowOrchestrator.
        
        Args:
            agents: Dictionary of available agents by name
        """
        self.agents = agents
        self.workflows = {}  # Store active workflows
        self.workflow_definitions = {}  # Store workflow templates/definitions
        
        # File path for persisting workflows
        self.workflows_file = os.environ.get("WORKFLOWS_FILE", "/app/data/workflows.json")
        self.definitions_file = os.environ.get("WORKFLOW_DEFINITIONS_FILE", "/app/data/workflow_definitions.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.workflows_file), exist_ok=True)
        
        # Restore persisted data
        self._load_persisted_data()
        
        logger.info(f"Workflow orchestrator initialized with {len(self.agents)} agents")
    
    def _load_persisted_data(self):
        """Load persisted workflow data from files."""
        # Load workflow definitions
        try:
            if os.path.exists(self.definitions_file):
                with open(self.definitions_file, 'r') as f:
                    self.workflow_definitions = json.load(f)
                logger.info(f"Loaded {len(self.workflow_definitions)} workflow definitions")
        except Exception as e:
            logger.error(f"Error loading workflow definitions: {str(e)}")
            self.workflow_definitions = {}
        
        # Load active workflows
        try:
            if os.path.exists(self.workflows_file):
                with open(self.workflows_file, 'r') as f:
                    self.workflows = json.load(f)
                logger.info(f"Loaded {len(self.workflows)} active workflows")
        except Exception as e:
            logger.error(f"Error loading active workflows: {str(e)}")
            self.workflows = {}
    
    def _save_persisted_data(self):
        """Save workflow data to persistent storage."""
        # Save workflow definitions
        try:
            with open(self.definitions_file, 'w') as f:
                json.dump(self.workflow_definitions, f, indent=2, default=str)
            logger.info(f"Saved {len(self.workflow_definitions)} workflow definitions")
        except Exception as e:
            logger.error(f"Error saving workflow definitions: {str(e)}")
        
        # Save active workflows
        try:
            # Convert non-serializable objects to strings
            serializable_workflows = {}
            for wf_id, workflow in self.workflows.items():
                serializable_workflows[wf_id] = self._make_serializable(workflow)
            
            with open(self.workflows_file, 'w') as f:
                json.dump(serializable_workflows, f, indent=2, default=str)
            logger.info(f"Saved {len(self.workflows)} active workflows")
        except Exception as e:
            logger.error(f"Error saving active workflows: {str(e)}")
    
    def _make_serializable(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (datetime, set)):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            # Convert custom objects to dictionaries
            return {
                '__type__': obj.__class__.__name__,
                **{k: self._make_serializable(v) for k, v in obj.__dict__.items() 
                   if not k.startswith('_') and not callable(v)}
            }
        else:
            return obj
    
    async def create_workflow_definition(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new workflow definition that can be instantiated multiple times.
        
        Args:
            name: Name of the workflow
            description: Description of the workflow
            steps: List of workflow steps with agent, action, and dependencies
            metadata: Additional metadata for the workflow
        
        Returns:
            Dictionary with the workflow definition
        """
        # Validate steps
        for step in steps:
            if 'agent' not in step:
                raise ValueError(f"Step must include 'agent' field: {step}")
            if 'action' not in step:
                raise ValueError(f"Step must include 'action' field: {step}")
            if step['agent'] not in self.agents:
                raise ValueError(f"Unknown agent '{step['agent']}' in workflow step")
        
        # Generate a unique ID
        definition_id = str(uuid.uuid4())
        
        # Create the workflow definition
        workflow_def = {
            "id": definition_id,
            "name": name,
            "description": description,
            "steps": steps,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store the definition
        self.workflow_definitions[definition_id] = workflow_def
        
        # Save to persistent storage
        self._save_persisted_data()
        
        return workflow_def
    
    async def get_workflow_definition(self, definition_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow definition by ID.
        
        Args:
            definition_id: ID of the workflow definition
            
        Returns:
            Workflow definition or None if not found
        """
        return self.workflow_definitions.get(definition_id)
    
    async def list_workflow_definitions(self) -> List[Dict[str, Any]]:
        """
        List all available workflow definitions.
        
        Returns:
            List of workflow definitions
        """
        return list(self.workflow_definitions.values())
    
    async def update_workflow_definition(
        self,
        definition_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing workflow definition.
        
        Args:
            definition_id: ID of the workflow definition to update
            name: New name (optional)
            description: New description (optional)
            steps: New steps (optional)
            metadata: New metadata (optional)
            
        Returns:
            Updated workflow definition or None if not found
        """
        if definition_id not in self.workflow_definitions:
            return None
        
        # Get the existing definition
        workflow_def = self.workflow_definitions[definition_id]
        
        # Update fields if provided
        if name is not None:
            workflow_def["name"] = name
        
        if description is not None:
            workflow_def["description"] = description
        
        if steps is not None:
            # Validate steps
            for step in steps:
                if 'agent' not in step:
                    raise ValueError(f"Step must include 'agent' field: {step}")
                if 'action' not in step:
                    raise ValueError(f"Step must include 'action' field: {step}")
                if step['agent'] not in self.agents:
                    raise ValueError(f"Unknown agent '{step['agent']}' in workflow step")
            
            workflow_def["steps"] = steps
        
        if metadata is not None:
            workflow_def["metadata"] = metadata
        
        # Update timestamp
        workflow_def["updated_at"] = datetime.now().isoformat()
        
        # Save to persistent storage
        self._save_persisted_data()
        
        return workflow_def
    
    async def delete_workflow_definition(self, definition_id: str) -> bool:
        """
        Delete a workflow definition.
        
        Args:
            definition_id: ID of the workflow definition to delete
            
        Returns:
            True if deleted, False if not found
        """
        if definition_id not in self.workflow_definitions:
            return False
        
        del self.workflow_definitions[definition_id]
        
        # Save to persistent storage
        self._save_persisted_data()
        
        return True
    
    async def create_workflow_instance(
        self,
        definition_id: str,
        input_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new workflow instance from a definition.
        
        Args:
            definition_id: ID of the workflow definition to instantiate
            input_data: Input data for the workflow
            metadata: Additional metadata for the workflow instance
            
        Returns:
            Dictionary with the workflow instance
        """
        if definition_id not in self.workflow_definitions:
            raise ValueError(f"Workflow definition {definition_id} not found")
        
        # Get the workflow definition
        workflow_def = self.workflow_definitions[definition_id]
        
        # Generate a unique ID for the workflow instance
        workflow_id = str(uuid.uuid4())
        
        # Create step instances from the definition
        steps = []
        for i, step_def in enumerate(workflow_def["steps"]):
            step_id = f"{workflow_id}-step-{i}"
            steps.append({
                "id": step_id,
                "name": step_def.get("name", f"Step {i+1}"),
                "agent": step_def["agent"],
                "action": step_def["action"],
                "parameters": step_def.get("parameters", {}),
                "depends_on": step_def.get("depends_on", []),
                "condition": step_def.get("condition"),
                "status": WorkflowStatus.PENDING,
                "result": None,
                "error": None,
                "start_time": None,
                "end_time": None,
                "retries": 0,
                "max_retries": step_def.get("max_retries", 3)
            })
        
        # Create the workflow instance
        workflow = {
            "id": workflow_id,
            "definition_id": definition_id,
            "definition_name": workflow_def["name"],
            "status": WorkflowStatus.PENDING,
            "steps": steps,
            "input_data": input_data,
            "output_data": {},
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None
        }
        
        # Store the workflow instance
        self.workflows[workflow_id] = workflow
        
        # Save to persistent storage
        self._save_persisted_data()
        
        # Start the workflow execution in the background
        asyncio.create_task(self._execute_workflow(workflow_id))
        
        return workflow
    
    async def get_workflow_instance(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow instance by ID.
        
        Args:
            workflow_id: ID of the workflow instance
            
        Returns:
            Workflow instance or None if not found
        """
        return self.workflows.get(workflow_id)
    
    async def list_workflow_instances(
        self,
        status: Optional[str] = None,
        definition_id: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List workflow instances with optional filtering.
        
        Args:
            status: Filter by workflow status
            definition_id: Filter by definition ID
            limit: Maximum number of instances to return
            offset: Offset for pagination
            
        Returns:
            List of workflow instances
        """
        # Filter workflows
        filtered = []
        for workflow in self.workflows.values():
            if status and workflow["status"] != status:
                continue
            if definition_id and workflow["definition_id"] != definition_id:
                continue
            filtered.append(workflow)
        
        # Sort by creation time (newest first)
        sorted_workflows = sorted(
            filtered,
            key=lambda w: w.get("created_at", ""),
            reverse=True
        )
        
        # Apply pagination
        return sorted_workflows[offset:offset + limit]
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            workflow_id: ID of the workflow to cancel
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        
        # Cannot cancel completed workflows
        if workflow["status"] in [WorkflowStatus.SUCCEEDED, WorkflowStatus.FAILED]:
            return False
        
        # Update workflow status
        workflow["status"] = WorkflowStatus.CANCELLED
        workflow["updated_at"] = datetime.now().isoformat()
        
        # Cancel all pending or running steps
        for step in workflow["steps"]:
            if step["status"] in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.WAITING]:
                step["status"] = WorkflowStatus.CANCELLED
        
        # Save to persistent storage
        self._save_persisted_data()
        
        return True
    
    async def _execute_workflow(self, workflow_id: str):
        """
        Execute a workflow by processing its steps based on dependencies.
        
        Args:
            workflow_id: ID of the workflow to execute
        """
        if workflow_id not in self.workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return
        
        workflow = self.workflows[workflow_id]
        workflow["status"] = WorkflowStatus.RUNNING
        workflow["started_at"] = datetime.now().isoformat()
        workflow["updated_at"] = datetime.now().isoformat()
        
        # Save the updated workflow state
        self._save_persisted_data()
        
        logger.info(f"Starting workflow execution: {workflow_id}")
        
        try:
            # Continue until all steps are completed, failed, or cancelled
            while await self._has_runnable_steps(workflow):
                # Find all steps that can be run now
                runnable_steps = await self._get_runnable_steps(workflow)
                
                if not runnable_steps:
                    # If no steps can run but workflow is not complete,
                    # there might be a dependency cycle
                    if not await self._is_workflow_complete(workflow):
                        logger.warning(f"Possible dependency cycle in workflow {workflow_id}")
                        workflow["error"] = "Dependency cycle detected"
                        workflow["status"] = WorkflowStatus.FAILED
                        break
                    else:
                        # All steps completed
                        break
                
                # Execute runnable steps in parallel
                await asyncio.gather(*[
                    self._execute_step(workflow, step)
                    for step in runnable_steps
                ])
                
                # Update workflow state
                workflow["updated_at"] = datetime.now().isoformat()
                self._save_persisted_data()
            
            # Check if all steps completed successfully
            all_succeeded = all(
                step["status"] == WorkflowStatus.SUCCEEDED
                for step in workflow["steps"]
            )
            
            any_failed = any(
                step["status"] == WorkflowStatus.FAILED
                for step in workflow["steps"]
            )
            
            # Set final workflow status
            if workflow["status"] != WorkflowStatus.CANCELLED:
                if all_succeeded:
                    workflow["status"] = WorkflowStatus.SUCCEEDED
                elif any_failed:
                    workflow["status"] = WorkflowStatus.FAILED
            
            # Set completion time
            workflow["completed_at"] = datetime.now().isoformat()
            workflow["updated_at"] = datetime.now().isoformat()
            
            # Gather output data from all steps
            workflow["output_data"] = await self._gather_output_data(workflow)
            
            logger.info(f"Workflow {workflow_id} completed with status {workflow['status']}")
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            workflow["status"] = WorkflowStatus.FAILED
            workflow["error"] = str(e)
            workflow["completed_at"] = datetime.now().isoformat()
            workflow["updated_at"] = datetime.now().isoformat()
        
        # Save the final workflow state
        self._save_persisted_data()
    
    async def _has_runnable_steps(self, workflow: Dict[str, Any]) -> bool:
        """
        Check if the workflow has any steps that can be run.
        
        Args:
            workflow: Workflow instance
            
        Returns:
            True if there are runnable steps, False otherwise
        """
        # If workflow is cancelled or completed, no steps should be run
        if workflow["status"] in [WorkflowStatus.CANCELLED, WorkflowStatus.SUCCEEDED, WorkflowStatus.FAILED]:
            return False
        
        # Check if there are any pending steps
        return any(
            step["status"] == WorkflowStatus.PENDING
            for step in workflow["steps"]
        )
    
    async def _get_runnable_steps(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all steps that can be run now.
        
        Args:
            workflow: Workflow instance
            
        Returns:
            List of runnable steps
        """
        runnable_steps = []
        
        for step in workflow["steps"]:
            # Skip steps that are not pending
            if step["status"] != WorkflowStatus.PENDING:
                continue
            
            # Check if all dependencies are satisfied
            dependencies_met = True
            for dep_step_id in step["depends_on"]:
                # Find the dependency step
                dep_steps = [s for s in workflow["steps"] if s["id"] == dep_step_id]
                if not dep_steps:
                    logger.warning(f"Dependency step {dep_step_id} not found in workflow {workflow['id']}")
                    dependencies_met = False
                    break
                
                dep_step = dep_steps[0]
                
                # Check if the dependency completed successfully
                if dep_step["status"] != WorkflowStatus.SUCCEEDED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                # Check if step condition is met
                if "condition" in step and step["condition"]:
                    condition_met = await self._evaluate_condition(
                        workflow,
                        step["condition"]
                    )
                    if not condition_met:
                        # Skip this step and mark as succeeded (condition not met)
                        step["status"] = WorkflowStatus.SUCCEEDED
                        step["result"] = {"skipped": True, "reason": "Condition not met"}
                        continue
                
                runnable_steps.append(step)
        
        return runnable_steps
    
    async def _execute_step(self, workflow: Dict[str, Any], step: Dict[str, Any]):
        """
        Execute a single workflow step.
        
        Args:
            workflow: Workflow instance
            step: Step to execute
        """
        agent_name = step["agent"]
        action = step["action"]
        parameters = step["parameters"].copy()
        
        # Update step status
        step["status"] = WorkflowStatus.RUNNING
        step["start_time"] = datetime.now().isoformat()
        
        logger.info(f"Executing step {step['id']} with agent {agent_name}, action {action}")
        
        try:
            # Resolve parameter references to previous step outputs
            await self._resolve_parameter_references(workflow, parameters)
            
            # Add task_id to parameters
            parameters["task_id"] = step["id"]
            
            # Add workflow input data if not already present
            for key, value in workflow["input_data"].items():
                if key not in parameters:
                    parameters[key] = value
            
            # Get the agent
            if agent_name not in self.agents:
                raise ValueError(f"Agent {agent_name} not found")
            
            agent = self.agents[agent_name]
            
            # Prepare the agent request
            agent_request = {
                "action": action,
                "parameters": parameters,
                "task_id": step["id"]
            }
            
            # Execute the agent action
            result = await agent.process(agent_request)
            
            # Update step status
            step["status"] = WorkflowStatus.SUCCEEDED
            step["result"] = result
            step["end_time"] = datetime.now().isoformat()
            
            logger.info(f"Step {step['id']} completed successfully")
            
        except Exception as e:
            logger.error(f"Error executing step {step['id']}: {str(e)}")
            
            # Check if retries are available
            if step["retries"] < step["max_retries"]:
                # Increment retry count
                step["retries"] += 1
                step["status"] = WorkflowStatus.PENDING
                logger.info(f"Retrying step {step['id']} ({step['retries']}/{step['max_retries']})")
            else:
                # Mark as failed
                step["status"] = WorkflowStatus.FAILED
                step["error"] = str(e)
                step["end_time"] = datetime.now().isoformat()
    
    async def _resolve_parameter_references(self, workflow: Dict[str, Any], parameters: Dict[str, Any]):
        """
        Resolve parameter references to outputs of previous steps.
        Format: ${step_id.output_path}
        
        Args:
            workflow: Workflow instance
            parameters: Parameters to resolve
        """
        # Recursively process parameters
        for key, value in list(parameters.items()):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                # Extract reference
                ref = value[2:-1]
                parts = ref.split(".")
                if len(parts) < 2:
                    continue
                
                step_id = parts[0]
                output_path = ".".join(parts[1:])
                
                # Find the referenced step
                ref_steps = [s for s in workflow["steps"] if s["id"] == step_id]
                if not ref_steps or ref_steps[0]["status"] != WorkflowStatus.SUCCEEDED:
                    # Reference not found or step not completed
                    continue
                
                # Extract the output value
                result = ref_steps[0]["result"]
                for part in output_path.split("."):
                    if isinstance(result, dict) and part in result:
                        result = result[part]
                    else:
                        # Path not found
                        result = None
                        break
                
                # Replace the reference with the actual value
                parameters[key] = result
            elif isinstance(value, dict):
                # Recursively process nested dictionaries
                await self._resolve_parameter_references(workflow, value)
            elif isinstance(value, list):
                # Process list items
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        await self._resolve_parameter_references(workflow, item)
                    elif isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                        # Extract reference
                        ref = item[2:-1]
                        parts = ref.split(".")
                        if len(parts) < 2:
                            continue
                        
                        step_id = parts[0]
                        output_path = ".".join(parts[1:])
                        
                        # Find the referenced step
                        ref_steps = [s for s in workflow["steps"] if s["id"] == step_id]
                        if not ref_steps or ref_steps[0]["status"] != WorkflowStatus.SUCCEEDED:
                            # Reference not found or step not completed
                            continue
                        
                        # Extract the output value
                        result = ref_steps[0]["result"]
                        for part in output_path.split("."):
                            if isinstance(result, dict) and part in result:
                                result = result[part]
                            else:
                                # Path not found
                                result = None
                                break
                        
                        # Replace the reference with the actual value
                        value[i] = result
    
    async def _evaluate_condition(self, workflow: Dict[str, Any], condition: str) -> bool:
        """
        Evaluate a step condition.
        Format: ${step_id.output_path} [operator] [value]
        
        Args:
            workflow: Workflow instance
            condition: Condition to evaluate
            
        Returns:
            True if condition is met, False otherwise
        """
        # Simplified condition evaluation
        # In a real implementation, this would be more sophisticated
        
        # Process references in the condition
        processed_condition = condition
        
        # Find all references in the format ${step_id.output_path}
        import re
        refs = re.findall(r'\${([^}]+)}', condition)
        
        for ref in refs:
            parts = ref.split(".")
            if len(parts) < 2:
                continue
            
            step_id = parts[0]
            output_path = ".".join(parts[1:])
            
            # Find the referenced step
            ref_steps = [s for s in workflow["steps"] if s["id"] == step_id]
            if not ref_steps or ref_steps[0]["status"] != WorkflowStatus.SUCCEEDED:
                # Reference not found or step not completed
                return False
            
            # Extract the output value
            result = ref_steps[0]["result"]
            for part in output_path.split("."):
                if isinstance(result, dict) and part in result:
                    result = result[part]
                else:
                    # Path not found
                    result = None
                    break
            
            # Replace the reference with the actual value
            processed_condition = processed_condition.replace(f"${{{ref}}}", repr(result))
        
        # Evaluate the condition
        try:
            # Security note: eval is used here for simplicity
            # In a production system, use a safer approach
            return bool(eval(processed_condition))
        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {str(e)}")
            return False
    
    async def _is_workflow_complete(self, workflow: Dict[str, Any]) -> bool:
        """
        Check if all workflow steps are completed, failed, or cancelled.
        
        Args:
            workflow: Workflow instance
            
        Returns:
            True if workflow is complete, False otherwise
        """
        return all(
            step["status"] in [
                WorkflowStatus.SUCCEEDED,
                WorkflowStatus.FAILED,
                WorkflowStatus.CANCELLED
            ]
            for step in workflow["steps"]
        )
    
    async def _gather_output_data(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gather output data from all completed steps.
        
        Args:
            workflow: Workflow instance
            
        Returns:
            Dictionary with output data
        """
        output_data = {}
        
        for step in workflow["steps"]:
            if step["status"] == WorkflowStatus.SUCCEEDED and step["result"]:
                # Add step result to output data
                step_name = step.get("name", step["id"])
                output_data[step_name] = step["result"]
        
        return output_data