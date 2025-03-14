"""
Workflow Schema Module for Multi-Agent Infrastructure Automation System

This module defines the schema for workflow definitions, including validation
functions, template generation, and agent capabilities integration.
"""

import json
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator

class StepParameter(BaseModel):
    """
    Parameter for a workflow step.
    Can be a literal value or a reference to a previous step output.
    """
    name: str
    value: Union[str, int, float, bool, Dict[str, Any], List[Any]]
    description: Optional[str] = None
    type: str = "string"  # string, number, boolean, object, array
    required: bool = True
    
    @validator('type')
    def validate_type(cls, v):
        allowed_types = ["string", "number", "boolean", "object", "array"]
        if v not in allowed_types:
            raise ValueError(f"Invalid parameter type: {v}")
        return v

class WorkflowStep(BaseModel):
    """
    Definition of a workflow step.
    Each step involves a specific agent performing an action with parameters.
    """
    id: Optional[str] = None  # Will be auto-generated if not provided
    name: str
    description: Optional[str] = None
    agent: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    condition: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 600
    
    @validator('agent')
    def validate_agent(cls, v):
        # Will be validated against available agents when creating a workflow
        return v
    
    @validator('depends_on')
    def validate_depends_on(cls, v, values):
        # Make sure the step doesn't depend on itself
        if 'id' in values and values['id'] in v:
            raise ValueError("Step cannot depend on itself")
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        if v < 1 or v > 7200:  # Between 1 second and 2 hours
            raise ValueError("Timeout must be between 1 and 7200 seconds")
        return v

class WorkflowDefinition(BaseModel):
    """
    Definition of a complete workflow.
    A workflow consists of multiple steps, with dependencies and conditions.
    """
    id: Optional[str] = None  # Will be auto-generated if not provided
    name: str
    description: str
    version: str = "1.0.0"
    steps: List[WorkflowStep]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @validator('steps')
    def validate_steps(cls, v):
        # Make sure there's at least one step
        if not v:
            raise ValueError("Workflow must have at least one step")
        
        # Check for duplicate step IDs
        step_ids = [step.id for step in v if step.id]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Duplicate step IDs found")
        
        # Check for circular dependencies
        try:
            # Build dependency graph
            graph = {step.id: set(step.depends_on) for step in v if step.id}
            
            # Check for cycles
            visited = set()
            temp_visited = set()
            
            def has_cycle(node):
                if node in temp_visited:
                    return True
                if node in visited:
                    return False
                
                temp_visited.add(node)
                
                for neighbor in graph.get(node, set()):
                    if has_cycle(neighbor):
                        return True
                
                temp_visited.remove(node)
                visited.add(node)
                return False
            
            for step_id in graph:
                if has_cycle(step_id):
                    raise ValueError(f"Circular dependency detected for step {step_id}")
        except Exception as e:
            if "Circular dependency" in str(e):
                raise
            # Ignore other errors since IDs might not be assigned yet
            pass
        
        return v

class AgentCapabilities(BaseModel):
    """
    Definition of an agent's capabilities.
    Used for workflow editor to present available actions.
    """
    agent_id: str
    agent_name: str
    description: str
    actions: Dict[str, Dict[str, Any]]  # Map of action_id -> action_definition
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "infrastructure_agent",
                "agent_name": "Infrastructure Agent",
                "description": "Generates and manages infrastructure code",
                "actions": {
                    "generate": {
                        "name": "Generate Infrastructure",
                        "description": "Generate infrastructure code based on requirements",
                        "parameters": {
                            "task": {
                                "type": "string",
                                "description": "Description of what to generate",
                                "required": True
                            },
                            "cloud_provider": {
                                "type": "string",
                                "description": "Cloud provider (aws, azure, gcp)",
                                "default": "aws",
                                "required": False
                            }
                        },
                        "output_schema": {
                            "code": "string",
                            "metadata": "object"
                        }
                    }
                }
            }
        }

class WorkflowRegistry:
    """
    Registry for workflow definitions and agent capabilities.
    Used by the workflow editor and workflow orchestrator.
    """
    def __init__(self):
        self.workflow_definitions = {}
        self.agent_capabilities = {}
    
    def register_agent_capabilities(self, capabilities: AgentCapabilities):
        """Register an agent's capabilities for use in the workflow editor."""
        self.agent_capabilities[capabilities.agent_id] = capabilities
    
    def get_agent_capabilities(self, agent_id: str) -> Optional[AgentCapabilities]:
        """Get an agent's capabilities by ID."""
        return self.agent_capabilities.get(agent_id)
    
    def list_agent_capabilities(self) -> List[AgentCapabilities]:
        """List all registered agent capabilities."""
        return list(self.agent_capabilities.values())
    
    def register_workflow_definition(self, workflow: WorkflowDefinition):
        """Register a workflow definition."""
        if not workflow.id:
            raise ValueError("Workflow definition ID is required")
        
        # Validate against available agents
        for step in workflow.steps:
            if step.agent not in self.agent_capabilities:
                raise ValueError(f"Unknown agent in step: {step.agent}")
            
            agent_caps = self.agent_capabilities[step.agent]
            if step.action not in agent_caps.actions:
                raise ValueError(f"Unknown action '{step.action}' for agent '{step.agent}'")
        
        self.workflow_definitions[workflow.id] = workflow
    
    def get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        return self.workflow_definitions.get(workflow_id)
    
    def list_workflow_definitions(self) -> List[WorkflowDefinition]:
        """List all registered workflow definitions."""
        return list(self.workflow_definitions.values())
    
    def create_workflow_template(self, template_type: str) -> WorkflowDefinition:
        """Create a workflow template based on the template type."""
        if template_type == "infrastructure_pipeline":
            return self._create_infrastructure_pipeline_template()
        elif template_type == "terraform_to_k8s":
            return self._create_terraform_to_k8s_template()
        elif template_type == "security_review":
            return self._create_security_review_template()
        else:
            raise ValueError(f"Unknown template type: {template_type}")
    
    def _create_infrastructure_pipeline_template(self) -> WorkflowDefinition:
        """Create a template for an infrastructure generation pipeline."""
        return WorkflowDefinition(
            name="Infrastructure Pipeline",
            description="Generate, review, and deploy infrastructure with security and cost optimization",
            steps=[
                WorkflowStep(
                    id="generate_infra",
                    name="Generate Infrastructure",
                    description="Generate infrastructure code based on requirements",
                    agent="infrastructure",
                    action="generate",
                    parameters={
                        "task": "Generate AWS infrastructure",
                        "cloud_provider": "aws",
                        "iac_type": "terraform"
                    }
                ),
                WorkflowStep(
                    id="security_review",
                    name="Security Review",
                    description="Review infrastructure for security issues",
                    agent="security",
                    action="review",
                    parameters={
                        "code": "${generate_infra.code}",
                        "cloud_provider": "aws",
                        "iac_type": "terraform"
                    },
                    depends_on=["generate_infra"]
                ),
                WorkflowStep(
                    id="cost_optimization",
                    name="Cost Optimization",
                    description="Optimize infrastructure for cost",
                    agent="cost",
                    action="optimize",
                    parameters={
                        "code": "${security_review.remediated_code}",
                        "cloud_provider": "aws",
                        "iac_type": "terraform"
                    },
                    depends_on=["security_review"]
                ),
                WorkflowStep(
                    id="create_jira_story",
                    name="Create Jira Story",
                    description="Create a Jira story for the infrastructure",
                    agent="jira",
                    action="create_issue",
                    parameters={
                        "project_key": "INFRA",
                        "issue_type": "Story",
                        "summary": "Deploy new infrastructure",
                        "description": "Deploy the following infrastructure:\n${cost_optimization.optimized_code}"
                    },
                    depends_on=["cost_optimization"]
                ),
                WorkflowStep(
                    id="create_github_branch",
                    name="Create GitHub Branch",
                    description="Create a GitHub branch for the infrastructure code",
                    agent="github",
                    action="create_branch",
                    parameters={
                        "repo": "infrastructure-repo",
                        "branch": "feature/new-infrastructure",
                        "base_branch": "main"
                    },
                    depends_on=["cost_optimization"]
                ),
                WorkflowStep(
                    id="create_github_commit",
                    name="Create GitHub Commit",
                    description="Commit the infrastructure code to GitHub",
                    agent="github",
                    action="create_commit",
                    parameters={
                        "repo": "infrastructure-repo",
                        "branch": "feature/new-infrastructure",
                        "message": "Add new infrastructure",
                        "files": {
                            "main.tf": "${cost_optimization.optimized_code}"
                        }
                    },
                    depends_on=["create_github_branch"]
                ),
                WorkflowStep(
                    id="create_confluence_page",
                    name="Create Confluence Page",
                    description="Create a Confluence page for the infrastructure",
                    agent="confluence",
                    action="create_page",
                    parameters={
                        "space_key": "INFRA",
                        "title": "New Infrastructure Documentation",
                        "content": "# New Infrastructure\n\nThis infrastructure was generated by the Infrastructure Automation System.\n\n## Code\n\n```terraform\n${cost_optimization.optimized_code}\n```\n\n## Security Review\n\n${security_review.vulnerabilities}\n\n## Cost Optimization\n\n${cost_optimization.optimization_summary}"
                    },
                    depends_on=["create_github_commit"]
                ),
                WorkflowStep(
                    id="create_github_pr",
                    name="Create GitHub PR",
                    description="Create a GitHub PR for the infrastructure code",
                    agent="github",
                    action="create_pr",
                    parameters={
                        "repo": "infrastructure-repo",
                        "title": "New Infrastructure",
                        "body": "This PR adds new infrastructure. See ${create_confluence_page.url} for details.",
                        "head": "feature/new-infrastructure",
                        "base": "main"
                    },
                    depends_on=["create_confluence_page"]
                ),
                WorkflowStep(
                    id="update_jira_story",
                    name="Update Jira Story",
                    description="Update the Jira story with the PR and Confluence page",
                    agent="jira",
                    action="update_issue",
                    parameters={
                        "issue_key": "${create_jira_story.issue_key}",
                        "fields": {
                            "description": "Deploy the following infrastructure:\n\nGitHub PR: ${create_github_pr.html_url}\nConfluence Page: ${create_confluence_page.url}"
                        }
                    },
                    depends_on=["create_github_pr"]
                )
            ]
        )
    
    def _create_terraform_to_k8s_template(self) -> WorkflowDefinition:
        """Create a template for a Terraform to Kubernetes deployment pipeline."""
        return WorkflowDefinition(
            name="Terraform to Kubernetes Pipeline",
            description="Generate infrastructure, deploy to Kubernetes, and manage with ArgoCD",
            steps=[
                WorkflowStep(
                    id="generate_infra",
                    name="Generate Infrastructure",
                    description="Generate Terraform infrastructure code",
                    agent="infrastructure",
                    action="generate",
                    parameters={
                        "task": "Generate Kubernetes infrastructure",
                        "cloud_provider": "aws",
                        "iac_type": "terraform"
                    }
                ),
                WorkflowStep(
                    id="security_review",
                    name="Security Review",
                    description="Review infrastructure for security issues",
                    agent="security",
                    action="review",
                    parameters={
                        "code": "${generate_infra.code}",
                        "cloud_provider": "aws",
                        "iac_type": "terraform"
                    },
                    depends_on=["generate_infra"]
                ),
                WorkflowStep(
                    id="generate_k8s_manifests",
                    name="Generate Kubernetes Manifests",
                    description="Generate Kubernetes manifests",
                    agent="kubernetes",
                    action="generate_manifests",
                    parameters={
                        "application_spec": {
                            "name": "my-app",
                            "type": "web",
                            "replicas": 3,
                            "container_image": "nginx:latest"
                        }
                    },
                    depends_on=["security_review"]
                ),
                WorkflowStep(
                    id="create_github_repo",
                    name="Create GitHub Repository",
                    description="Create a GitHub repository for the Kubernetes manifests",
                    agent="github",
                    action="create_repository",
                    parameters={
                        "name": "kubernetes-manifests",
                        "description": "Kubernetes manifests for my application",
                        "private": False
                    }
                ),
                WorkflowStep(
                    id="create_github_commit",
                    name="Create GitHub Commit",
                    description="Commit the Kubernetes manifests to GitHub",
                    agent="github",
                    action="create_commit",
                    parameters={
                        "repo": "kubernetes-manifests",
                        "branch": "main",
                        "message": "Add Kubernetes manifests",
                        "files": {
                            "manifests.yaml": "${generate_k8s_manifests.manifests}"
                        }
                    },
                    depends_on=["create_github_repo", "generate_k8s_manifests"]
                ),
                WorkflowStep(
                    id="create_argocd_app",
                    name="Create ArgoCD Application",
                    description="Create an ArgoCD application for the Kubernetes manifests",
                    agent="argocd",
                    action="create_application",
                    parameters={
                        "name": "my-app",
                        "repo_url": "${create_github_repo.clone_url}",
                        "path": ".",
                        "namespace": "default"
                    },
                    depends_on=["create_github_commit"]
                ),
                WorkflowStep(
                    id="sync_argocd_app",
                    name="Sync ArgoCD Application",
                    description="Sync the ArgoCD application",
                    agent="argocd",
                    action="sync_application",
                    parameters={
                        "name": "my-app"
                    },
                    depends_on=["create_argocd_app"]
                )
            ]
        )
    
    def _create_security_review_template(self) -> WorkflowDefinition:
        """Create a template for a security review workflow."""
        return WorkflowDefinition(
            name="Security Review Pipeline",
            description="Security review, vulnerability scanning, and remediation for infrastructure code",
            steps=[
                WorkflowStep(
                    id="security_review",
                    name="Security Review",
                    description="Review infrastructure for security issues",
                    agent="security",
                    action="review",
                    parameters={
                        "code": "input.infrastructure_code",
                        "cloud_provider": "input.cloud_provider",
                        "iac_type": "input.iac_type"
                    }
                ),
                WorkflowStep(
                    id="security_scan",
                    name="Security Scan",
                    description="Scan infrastructure for vulnerabilities",
                    agent="security_scanner",
                    action="scan_iac",
                    parameters={
                        "code": "input.infrastructure_code",
                        "iac_type": "input.iac_type",
                        "framework": "input.compliance_framework"
                    }
                ),
                WorkflowStep(
                    id="create_jira_vulnerabilities",
                    name="Create Jira Vulnerabilities",
                    description="Create Jira issues for vulnerabilities",
                    agent="jira",
                    action="create_issue",
                    parameters={
                        "project_key": "SEC",
                        "issue_type": "Bug",
                        "summary": "Security vulnerabilities in infrastructure code",
                        "description": "The following vulnerabilities were found:\n\n${security_review.vulnerabilities}\n\n${security_scan.result.findings}"
                    },
                    depends_on=["security_review", "security_scan"]
                ),
                WorkflowStep(
                    id="create_confluence_report",
                    name="Create Confluence Report",
                    description="Create a Confluence page with the security report",
                    agent="confluence",
                    action="create_page",
                    parameters={
                        "space_key": "SEC",
                        "title": "Security Review Report",
                        "content": "# Security Review Report\n\n## Overview\n\nThis report contains the results of a security review of infrastructure code.\n\n## Vulnerabilities\n\n${security_review.vulnerabilities}\n\n## Scan Results\n\n${security_scan.result.findings}\n\n## Remediated Code\n\n```terraform\n${security_review.remediated_code}\n```"
                    },
                    depends_on=["security_review", "security_scan"]
                ),
                WorkflowStep(
                    id="create_github_pr",
                    name="Create GitHub PR",
                    description="Create a GitHub PR with the security fixes",
                    agent="github",
                    action="create_pr",
                    parameters={
                        "repo": "input.github_repo",
                        "title": "Security fixes",
                        "body": "This PR fixes security vulnerabilities. See ${create_confluence_report.url} for details.",
                        "head": "security-fixes",
                        "base": "main",
                        "changes": {
                            "main.tf": "${security_review.remediated_code}"
                        }
                    },
                    depends_on=["create_confluence_report"],
                    condition="input.create_pr === true"
                )
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "infrastructure_code": {
                        "type": "string",
                        "description": "Infrastructure code to review"
                    },
                    "cloud_provider": {
                        "type": "string",
                        "description": "Cloud provider (aws, azure, gcp)"
                    },
                    "iac_type": {
                        "type": "string",
                        "description": "Type of IaC (terraform, ansible, etc.)"
                    },
                    "compliance_framework": {
                        "type": "string",
                        "description": "Compliance framework to check against"
                    },
                    "github_repo": {
                        "type": "string",
                        "description": "GitHub repository name"
                    },
                    "create_pr": {
                        "type": "boolean",
                        "description": "Whether to create a PR with the security fixes"
                    }
                },
                "required": ["infrastructure_code", "cloud_provider", "iac_type"]
            }
        )