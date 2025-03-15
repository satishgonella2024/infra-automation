"""
Workflow Initialization Module

This module provides functions to initialize the workflow system with predefined templates.
"""

import logging
from typing import Dict, Any, List

from src.workflow.schema import WorkflowRegistry, WorkflowDefinition
from src.workflow.orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

async def initialize_workflow_templates(orchestrator: WorkflowOrchestrator) -> None:
    """
    Initialize the workflow orchestrator with predefined templates.
    
    Args:
        orchestrator: The workflow orchestrator instance
    """
    try:
        # Create a workflow registry
        registry = WorkflowRegistry()
        
        # Create predefined templates
        templates = [
            "infrastructure_pipeline",
            "terraform_to_k8s",
            "security_review",
            "web_application",
            "microservices"
        ]
        
        # Register each template with the orchestrator
        for template_type in templates:
            try:
                logger.info(f"Creating workflow template: {template_type}")
                template = registry.create_workflow_template(template_type)
                
                # Convert WorkflowDefinition to dictionary
                if isinstance(template, WorkflowDefinition):
                    # Convert steps to dictionaries
                    steps = []
                    for step in template.steps:
                        step_dict = {
                            "id": step.id,
                            "name": step.name,
                            "description": step.description,
                            "agent": step.agent,
                            "action": step.action,
                            "parameters": step.parameters,
                            "depends_on": step.depends_on,
                            "condition": step.condition,
                            "max_retries": step.max_retries,
                            "timeout_seconds": step.timeout_seconds
                        }
                        steps.append(step_dict)
                    
                    # Create the workflow definition
                    await orchestrator.create_workflow_definition(
                        name=template.name,
                        description=template.description,
                        steps=steps,
                        metadata=template.metadata
                    )
                    logger.info(f"Registered workflow template: {template.name}")
                else:
                    logger.error(f"Template {template_type} is not a WorkflowDefinition")
            except Exception as e:
                logger.error(f"Error creating template {template_type}: {str(e)}")
        
        logger.info(f"Initialized {len(templates)} workflow templates")
    except Exception as e:
        logger.error(f"Error initializing workflow templates: {str(e)}") 