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
        elif template_type == "wordpress":
            return self._create_wordpress_deployment_template()
        elif template_type == "web_application":
            return self._create_web_application_template()
        elif template_type == "microservices":
            return self._create_microservices_template()
        elif template_type == "serverless":
            return WorkflowDefinition(name="Serverless Template", description="Serverless application template", steps=[WorkflowStep(id="dummy", name="Dummy Step", description="Placeholder step", agent="placeholder", action="noop")])
        elif template_type == "empty":
            return WorkflowDefinition(
                name="Empty Workflow",
                description="An empty workflow with no steps",
                steps=[]
            )
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
    
    def _create_wordpress_deployment_template(self) -> WorkflowDefinition:
        """Create a template for end-to-end WordPress deployment."""
        return WorkflowDefinition(
            name="WordPress Deployment Pipeline",
            description="End-to-end WordPress deployment from requirements to live site",
            steps=[
                WorkflowStep(
                    id="architecture_design",
                    name="Architecture Design",
                    description="Design the WordPress architecture",
                    agent="architect",
                    action="process",
                    parameters={
                        "task": "Design architecture for WordPress site",
                        "requirements": "input.requirements"
                    }
                ),
                WorkflowStep(
                    id="generate_infra",
                    name="Infrastructure Generation",
                    description="Generate infrastructure code for WordPress deployment",
                    agent="infrastructure",
                    action="process",
                    parameters={
                        "task": "Generate infrastructure for WordPress site",
                        "cloud_provider": "input.cloud_provider",
                        "iac_type": "terraform",
                        "requirements": {
                            "wordpress": True,
                            "database": True,
                            "high_availability": "input.high_availability",
                            "environment": "input.environment"
                        }
                    },
                    depends_on=["architecture_design"]
                ),
                WorkflowStep(
                    id="security_review",
                    name="Security Review",
                    description="Review and remediate security issues",
                    agent="security",
                    action="process",
                    parameters={
                        "code": "${generate_infra.code}",
                        "cloud_provider": "input.cloud_provider",
                        "iac_type": "terraform"
                    },
                    depends_on=["generate_infra"]
                ),
                WorkflowStep(
                    id="cost_optimization",
                    name="Cost Optimization",
                    description="Optimize infrastructure for cost",
                    agent="cost",
                    action="process",
                    parameters={
                        "code": "${security_review.remediated_code}",
                        "cloud_provider": "input.cloud_provider",
                        "iac_type": "terraform"
                    },
                    depends_on=["security_review"]
                ),
                WorkflowStep(
                    id="create_github_repo",
                    name="Create GitHub Repository",
                    description="Create a GitHub repository for the WordPress infrastructure",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_repository",
                        "parameters": {
                            "name": "input.project_name",
                            "description": "WordPress infrastructure for ${input.project_name}",
                            "private": True
                        }
                    }
                ),
                WorkflowStep(
                    id="commit_infrastructure",
                    name="Commit Infrastructure Code",
                    description="Commit the infrastructure code to GitHub",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_pull_request",
                        "parameters": {
                            "repo": "${create_github_repo.result.name}",
                            "title": "Initial infrastructure code",
                            "body": "Infrastructure code for WordPress deployment",
                            "head": "feature/initial-infrastructure",
                            "base": "main",
                            "changes": {
                                "main.tf": "${cost_optimization.optimized_code}",
                                "variables.tf": "variable \"environment\" {\n  type = string\n  default = \"${input.environment}\"\n}\n\nvariable \"region\" {\n  type = string\n  default = \"${input.region}\"\n}",
                                "outputs.tf": "output \"wordpress_url\" {\n  value = module.wordpress.url\n}\n\noutput \"admin_url\" {\n  value = module.wordpress.admin_url\n}"
                            }
                        }
                    },
                    depends_on=["create_github_repo", "cost_optimization"]
                ),
                WorkflowStep(
                    id="create_jira_project",
                    name="Create Jira Project",
                    description="Create a Jira project for tracking deployment tasks",
                    agent="jira",
                    action="process",
                    parameters={
                        "action": "create_project_structure", 
                        "parameters": {
                            "project_data": {
                                "key": "input.jira_project_key",
                                "name": "input.project_name",
                                "description": "WordPress deployment project"
                            }
                        }
                    }
                ),
                WorkflowStep(
                    id="create_deployment_task",
                    name="Create Deployment Task",
                    description="Create a Jira task for the deployment",
                    agent="jira",
                    action="process",
                    parameters={
                        "action": "create_issue",
                        "parameters": {
                            "project_key": "${create_jira_project.result.project_key}",
                            "issue_type": "Task",
                            "summary": "Deploy WordPress infrastructure",
                            "description": "Deploy the WordPress infrastructure using Terraform.\n\nGitHub PR: ${commit_infrastructure.result.html_url}"
                        }
                    },
                    depends_on=["create_jira_project", "commit_infrastructure"]
                ),
                WorkflowStep(
                    id="deploy_infrastructure",
                    name="Deploy Infrastructure",
                    description="Deploy the WordPress infrastructure",
                    agent="deployment",  # This is the new DeploymentAgent we need to implement
                    action="process",
                    parameters={
                        "action": "deploy_infrastructure",
                        "parameters": {
                            "code": "${cost_optimization.optimized_code}",
                            "variables": {
                                "environment": "input.environment",
                                "region": "input.region",
                                "domain": "input.domain"
                            }
                        }
                    },
                    depends_on=["commit_infrastructure"]
                ),
                WorkflowStep(
                    id="deploy_wordpress",
                    name="Deploy WordPress",
                    description="Deploy and configure WordPress",
                    agent="deployment",
                    action="process",
                    parameters={
                        "action": "deploy_application",
                        "parameters": {
                            "app_type": "wordpress",
                            "infra_outputs": "${deploy_infrastructure.result.outputs}",
                            "config": {
                                "site_title": "input.site_title",
                                "admin_user": "input.admin_user",
                                "admin_email": "input.admin_email",
                                "theme": "input.wordpress_theme"
                            }
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="setup_domain",
                    name="Setup Domain",
                    description="Configure DNS for the WordPress site",
                    agent="deployment",
                    action="process",
                    parameters={
                        "action": "setup_domain",
                        "parameters": {
                            "domain": "input.domain",
                            "ip_address": "${deploy_infrastructure.result.outputs.load_balancer_ip}"
                        }
                    },
                    depends_on=["deploy_wordpress"]
                ),
                WorkflowStep(
                    id="create_documentation",
                    name="Create Documentation",
                    description="Create documentation for the WordPress deployment",
                    agent="confluence",
                    action="process",
                    parameters={
                        "action": "create_page",
                        "parameters": {
                            "space_key": "DOCS",
                            "title": "${input.project_name} - WordPress Deployment",
                            "content": "# ${input.project_name} WordPress Deployment\n\n## Overview\nThis page documents the WordPress deployment for ${input.project_name}.\n\n## Architecture\n${architecture_design.result.diagram}\n\n## Infrastructure\n```terraform\n${cost_optimization.optimized_code}\n```\n\n## Access Details\n- WordPress URL: ${deploy_wordpress.result.site_url}\n- WordPress Admin URL: ${deploy_wordpress.result.admin_url}\n- Admin Username: ${input.admin_user}\n\n## Monitoring\nMonitoring is available at: ${deploy_infrastructure.result.outputs.monitoring_url}\n\n## Cost Estimation\nEstimated monthly cost: $${cost_optimization.optimization_summary.optimized_cost}\n\n## Security\nSecurity review results: ${security_review.vulnerabilities.length} vulnerabilities identified and remediated."
                        }
                    },
                    depends_on=["setup_domain"]
                ),
                WorkflowStep(
                    id="update_jira_task",
                    name="Update Jira Task",
                    description="Update the Jira task with deployment details",
                    agent="jira",
                    action="process",
                    parameters={
                        "action": "update_issue",
                        "parameters": {
                            "issue_key": "${create_deployment_task.result.issue_key}",
                            "fields": {
                                "status": "Done",
                                "description": "WordPress deployment completed successfully.\n\n- Site URL: ${deploy_wordpress.result.site_url}\n- Admin URL: ${deploy_wordpress.result.admin_url}\n- Documentation: ${create_documentation.result.url}"
                            }
                        }
                    },
                    depends_on=["create_documentation"]
                )
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "requirements": {
                        "type": "string",
                        "description": "Project requirements"
                    },
                    "cloud_provider": {
                        "type": "string",
                        "enum": ["aws", "azure", "gcp"],
                        "default": "aws",
                        "description": "Cloud provider"
                    },
                    "region": {
                        "type": "string",
                        "default": "us-west-2",
                        "description": "Cloud region"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["development", "staging", "production"],
                        "default": "development",
                        "description": "Deployment environment"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain name for the WordPress site"
                    },
                    "site_title": {
                        "type": "string",
                        "description": "WordPress site title"
                    },
                    "admin_user": {
                        "type": "string",
                        "default": "admin",
                        "description": "WordPress admin username"
                    },
                    "admin_email": {
                        "type": "string",
                        "description": "WordPress admin email"
                    },
                    "wordpress_theme": {
                        "type": "string",
                        "default": "twentytwentytwo",
                        "description": "WordPress theme"
                    },
                    "high_availability": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to deploy in high-availability mode"
                    },
                    "jira_project_key": {
                        "type": "string",
                        "description": "Jira project key"
                    }
                },
                "required": ["project_name", "domain", "site_title", "admin_email", "jira_project_key"]
            }
        )
    
    def _create_web_application_template(self) -> WorkflowDefinition:
        """Create a template for deploying custom web applications."""
        return WorkflowDefinition(
            name="Web Application Deployment Pipeline",
            description="End-to-end web application deployment with CI/CD",
            steps=[
                WorkflowStep(
                    id="architecture_design",
                    name="Architecture Design",
                    description="Design the application architecture",
                    agent="architect",
                    action="process",
                    parameters={
                        "task": "Design architecture for web application",
                        "requirements": "input.requirements",
                        "application_type": "input.application_type"
                    }
                ),
                WorkflowStep(
                    id="generate_infra",
                    name="Infrastructure Generation",
                    description="Generate infrastructure code for application deployment",
                    agent="infrastructure",
                    action="process",
                    parameters={
                        "task": "Generate infrastructure for ${input.application_type} application",
                        "cloud_provider": "input.cloud_provider",
                        "iac_type": "terraform",
                        "requirements": {
                            "application_type": "input.application_type",
                            "database_type": "input.database_type",
                            "high_availability": "input.high_availability",
                            "environment": "input.environment"
                        }
                    },
                    depends_on=["architecture_design"]
                ),
                WorkflowStep(
                    id="security_review",
                    name="Security Review",
                    description="Review and remediate security issues",
                    agent="security",
                    action="process",
                    parameters={
                        "code": "${generate_infra.code}",
                        "cloud_provider": "input.cloud_provider",
                        "iac_type": "terraform"
                    },
                    depends_on=["generate_infra"]
                ),
                WorkflowStep(
                    id="create_github_repo",
                    name="Create Application Repository",
                    description="Create GitHub repository for the application code",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_repository",
                        "parameters": {
                            "name": "input.project_name",
                            "description": "${input.application_type} application",
                            "private": True
                        }
                    }
                ),
                WorkflowStep(
                    id="create_infrastructure_repo",
                    name="Create Infrastructure Repository",
                    description="Create GitHub repository for the infrastructure code",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_repository",
                        "parameters": {
                            "name": "${input.project_name}-infrastructure",
                            "description": "Infrastructure code for ${input.project_name}",
                            "private": True
                        }
                    }
                ),
                WorkflowStep(
                    id="commit_infrastructure",
                    name="Commit Infrastructure Code",
                    description="Commit the infrastructure code to GitHub",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_pull_request",
                        "parameters": {
                            "repo": "${create_infrastructure_repo.result.name}",
                            "title": "Initial infrastructure code",
                            "body": "Infrastructure code for ${input.application_type} application",
                            "head": "feature/initial-infrastructure",
                            "base": "main",
                            "changes": {
                                "main.tf": "${security_review.remediated_code}",
                                "variables.tf": "variable \"environment\" {\n  type = string\n  default = \"${input.environment}\"\n}\n\nvariable \"region\" {\n  type = string\n  default = \"${input.region}\"\n}",
                                "outputs.tf": "output \"app_url\" {\n  value = module.app.url\n}\n\noutput \"database_connection_string\" {\n  value = module.database.connection_string\n  sensitive = true\n}"
                            }
                        }
                    },
                    depends_on=["create_infrastructure_repo", "security_review"]
                ),
                WorkflowStep(
                    id="generate_ci_workflow",
                    name="Generate CI Workflow",
                    description="Generate GitHub Actions CI workflow",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "generate_workflow",
                        "parameters": {
                            "repo_type": "input.application_type",
                            "language": "input.programming_language",
                            "ci_requirements": [
                                "build",
                                "test",
                                "package",
                                "deploy"
                            ]
                        }
                    },
                    depends_on=["create_github_repo"]
                ),
                WorkflowStep(
                    id="commit_ci_workflow",
                    name="Commit CI Workflow",
                    description="Commit the CI workflow to GitHub",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_pull_request",
                        "parameters": {
                            "repo": "${create_github_repo.result.name}",
                            "title": "Add CI workflow",
                            "body": "Adds GitHub Actions CI workflow",
                            "head": "feature/ci-workflow",
                            "base": "main",
                            "changes": {
                                ".github/workflows/ci.yml": "${generate_ci_workflow.result.workflow}"
                            }
                        }
                    },
                    depends_on=["generate_ci_workflow"]
                ),
                WorkflowStep(
                    id="create_jira_project",
                    name="Create Jira Project",
                    description="Create a Jira project for tracking development tasks",
                    agent="jira",
                    action="process",
                    parameters={
                        "action": "create_project_structure", 
                        "parameters": {
                            "project_data": {
                                "key": "input.jira_project_key",
                                "name": "input.project_name",
                                "description": "${input.application_type} application project"
                            }
                        }
                    }
                ),
                WorkflowStep(
                    id="deploy_infrastructure",
                    name="Deploy Infrastructure",
                    description="Deploy the application infrastructure",
                    agent="deployment",
                    action="process",
                    parameters={
                        "action": "deploy_infrastructure",
                        "parameters": {
                            "code": "${security_review.remediated_code}",
                            "variables": {
                                "environment": "input.environment",
                                "region": "input.region",
                                "domain": "input.domain"
                            }
                        }
                    },
                    depends_on=["commit_infrastructure"]
                ),
                WorkflowStep(
                    id="generate_kubernetes_manifests",
                    name="Generate Kubernetes Manifests",
                    description="Generate Kubernetes manifests for the application",
                    agent="kubernetes",
                    action="process",
                    parameters={
                        "action": "generate_manifests",
                        "parameters": {
                            "application_spec": {
                                "name": "input.project_name",
                                "type": "input.application_type",
                                "replicas": 2,
                                "container_image": "${input.project_name}:latest"
                            }
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="create_argocd_application",
                    name="Create ArgoCD Application",
                    description="Create ArgoCD application for continuous deployment",
                    agent="argocd",
                    action="process",
                    parameters={
                        "action": "create_application",
                        "parameters": {
                            "name": "input.project_name",
                            "repo_url": "${create_github_repo.result.clone_url}",
                            "path": "kubernetes",
                            "namespace": "input.environment"
                        }
                    },
                    depends_on=["generate_kubernetes_manifests"]
                ),
                WorkflowStep(
                    id="setup_domain",
                    name="Setup Domain",
                    description="Configure DNS for the application",
                    agent="deployment",
                    action="process",
                    parameters={
                        "action": "setup_domain",
                        "parameters": {
                            "domain": "input.domain",
                            "ip_address": "${deploy_infrastructure.result.outputs.load_balancer_ip}"
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="create_documentation",
                    name="Create Documentation",
                    description="Create documentation for the application",
                    agent="confluence",
                    action="process",
                    parameters={
                        "action": "create_page",
                        "parameters": {
                            "space_key": "DOCS",
                            "title": "${input.project_name} - Application Documentation",
                            "content": "# ${input.project_name} Application\n\n## Overview\nThis page documents the ${input.application_type} application deployment.\n\n## Architecture\n${architecture_design.result.diagram}\n\n## Infrastructure\n```terraform\n${security_review.remediated_code}\n```\n\n## Application\n- Application URL: ${deploy_infrastructure.result.outputs.app_url}\n- GitHub Repository: ${create_github_repo.result.html_url}\n- CI/CD Pipeline: ${create_github_repo.result.html_url}/actions\n\n## Deployment Pipeline\n- Infrastructure Repository: ${create_infrastructure_repo.result.html_url}\n- ArgoCD Application: ${create_argocd_application.result.url}\n\n## Monitoring\nMonitoring is available at: ${deploy_infrastructure.result.outputs.monitoring_url}"
                        }
                    },
                    depends_on=["setup_domain", "create_argocd_application"]
                ),
                WorkflowStep(
                    id="create_epics",
                    name="Create Jira Epics",
                    description="Create epics for development, testing, and operations",
                    agent="jira",
                    action="process",
                    parameters={
                        "action": "create_epics",
                        "parameters": {
                            "project_key": "${create_jira_project.result.project_key}",
                            "epics": [
                                {
                                    "name": "${service.name} Development",
                                    "description": "Development tasks for ${service.name} microservice"
                                }
                                for service in "input.services"
                            ]
                        }
                    },
                    depends_on=["create_jira_project", "create_documentation"]
                )
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "requirements": {
                        "type": "string",
                        "description": "Project requirements"
                    },
                    "application_type": {
                        "type": "string",
                        "enum": ["java", "node", "python", "dotnet", "ruby"],
                        "description": "Application type"
                    },
                    "programming_language": {
                        "type": "string",
                        "enum": ["java", "javascript", "typescript", "python", "csharp", "ruby"],
                        "description": "Programming language"
                    },
                    "database_type": {
                        "type": "string",
                        "enum": ["mysql", "postgresql", "mongodb", "dynamodb", "cosmosdb"],
                        "description": "Database type"
                    },
                    "cloud_provider": {
                        "type": "string",
                        "enum": ["aws", "azure", "gcp"],
                        "default": "aws",
                        "description": "Cloud provider"
                    },
                    "region": {
                        "type": "string",
                        "default": "us-west-2",
                        "description": "Cloud region"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["development", "staging", "production"],
                        "default": "development",
                        "description": "Deployment environment"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain name for the application"
                    },
                    "high_availability": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to deploy in high-availability mode"
                    },
                    "jira_project_key": {
                        "type": "string",
                        "description": "Jira project key"
                    }
                },
                "required": ["project_name", "application_type", "programming_language", "database_type", "domain", "jira_project_key"]
            }
        )
    
    def _create_microservices_template(self) -> WorkflowDefinition:
        """Create a template for deploying a microservices architecture."""
        return WorkflowDefinition(
            name="Microservices Deployment Pipeline",
            description="End-to-end microservices architecture deployment with Kubernetes",
            steps=[
                WorkflowStep(
                    id="architecture_design",
                    name="Architecture Design",
                    description="Design the microservices architecture",
                    agent="architect",
                    action="process",
                    parameters={
                        "task": "Design microservices architecture",
                        "requirements": "input.requirements",
                        "services": "input.services"
                    }
                ),
                WorkflowStep(
                    id="generate_infra",
                    name="Infrastructure Generation",
                    description="Generate infrastructure code for Kubernetes cluster",
                    agent="infrastructure",
                    action="process",
                    parameters={
                        "task": "Generate Kubernetes infrastructure on ${input.cloud_provider}",
                        "cloud_provider": "input.cloud_provider",
                        "iac_type": "terraform",
                        "requirements": {
                            "kubernetes": True,
                            "ingress": True,
                            "monitoring": True,
                            "logging": True,
                            "high_availability": "input.high_availability"
                        }
                    },
                    depends_on=["architecture_design"]
                ),
                WorkflowStep(
                    id="deploy_infrastructure",
                    name="Deploy Infrastructure",
                    description="Deploy the Kubernetes infrastructure",
                    agent="deployment",
                    action="process",
                    parameters={
                        "action": "deploy_infrastructure",
                        "parameters": {
                            "code": "${generate_infra.code}",
                            "variables": {
                                "cluster_name": "input.project_name",
                                "environment": "input.environment",
                                "region": "input.region"
                            }
                        }
                    },
                    depends_on=["generate_infra"]
                ),
                WorkflowStep(
                    id="setup_argocd",
                    name="Setup ArgoCD",
                    description="Deploy ArgoCD for continuous delivery",
                    agent="argocd",
                    action="process",
                    parameters={
                        "action": "setup_argocd",
                        "parameters": {
                            "cluster_config": "${deploy_infrastructure.result.kubeconfig}"
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="create_org",
                    name="Create GitHub Organization",
                    description="Create a GitHub organization for microservices",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_organization",
                        "parameters": {
                            "name": "input.organization_name",
                            "description": "Organization for ${input.project_name} microservices"
                        }
                    }
                ),
                WorkflowStep(
                    id="create_infrastructure_repo",
                    name="Create Infrastructure Repository",
                    description="Create GitHub repository for the infrastructure code",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "create_repository",
                        "parameters": {
                            "org": "${create_org.result.name}",
                            "name": "infrastructure",
                            "description": "Infrastructure code for ${input.project_name}",
                            "private": True
                        }
                    },
                    depends_on=["create_org"]
                ),
                WorkflowStep(
                    id="create_jira_project",
                    name="Create Jira Project",
                    description="Create a Jira project for tracking development",
                    agent="jira",
                    action="process",
                    parameters={
                        "action": "create_project_structure", 
                        "parameters": {
                            "project_data": {
                                "key": "input.jira_project_key",
                                "name": "input.project_name",
                                "description": "Microservices project for ${input.project_name}"
                            }
                        }
                    }
                ),
                WorkflowStep(
                    id="create_confluence_space",
                    name="Create Confluence Space",
                    description="Create a Confluence space for documentation",
                    agent="confluence",
                    action="process",
                    parameters={
                        "action": "create_space",
                        "parameters": {
                            "key": "input.confluence_space_key",
                            "name": "input.project_name",
                            "description": "Documentation for ${input.project_name} microservices"
                        }
                    }
                ),
                WorkflowStep(
                    id="generate_service_repositories",
                    name="Generate Service Repositories",
                    description="Generate GitHub repositories for each microservice",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "generate_repositories",
                        "parameters": {
                            "org": "${create_org.result.name}",
                            "services": "input.services",
                            "template_repo": "input.template_repository"
                        }
                    },
                    depends_on=["create_org"]
                ),
                WorkflowStep(
                    id="generate_kubernetes_manifests",
                    name="Generate Kubernetes Manifests",
                    description="Generate Kubernetes manifests for all microservices",
                    agent="kubernetes",
                    action="process",
                    parameters={
                        "action": "generate_manifests",
                        "parameters": {
                            "services": "input.services",
                            "namespace": "input.environment"
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="setup_ci_cd_pipelines",
                    name="Setup CI/CD Pipelines",
                    description="Set up CI/CD pipelines for all services",
                    agent="github",
                    action="process",
                    parameters={
                        "action": "setup_workflows",
                        "parameters": {
                            "org": "${create_org.result.name}",
                            "services": "input.services",
                            "workflow_template": "github_workflows/microservice_ci_cd.yml"
                        }
                    },
                    depends_on=["generate_service_repositories"]
                ),
                WorkflowStep(
                    id="deploy_service_mesh",
                    name="Deploy Service Mesh",
                    description="Deploy Istio service mesh",
                    agent="kubernetes",
                    action="process",
                    parameters={
                        "action": "deploy_service_mesh",
                        "parameters": {
                            "mesh_type": "istio",
                            "config": {
                                "mtls_enabled": True,
                                "tracing_enabled": True
                            }
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="deploy_monitoring",
                    name="Deploy Monitoring",
                    description="Deploy Prometheus and Grafana for monitoring",
                    agent="kubernetes",
                    action="process",
                    parameters={
                        "action": "deploy_monitoring",
                        "parameters": {
                            "monitoring_type": "prometheus",
                            "config": {
                                "grafana_enabled": True,
                                "alerting_enabled": True
                            }
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="deploy_logging",
                    name="Deploy Logging",
                    description="Deploy ELK stack for logging",
                    agent="kubernetes",
                    action="process",
                    parameters={
                        "action": "deploy_logging",
                        "parameters": {
                            "logging_type": "elk",
                            "config": {
                                "kibana_enabled": True,
                                "retention_days": 7
                            }
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="setup_argocd_applications",
                    name="Setup ArgoCD Applications",
                    description="Set up ArgoCD applications for all services",
                    agent="argocd",
                    action="process",
                    parameters={
                        "action": "create_applications",
                        "parameters": {
                            "applications": [
                                {
                                    "name": "${service}",
                                    "repo_url": "${create_org.result.html_url}/${service}",
                                    "path": "kubernetes",
                                    "namespace": "input.environment"
                                }
                                for service in "input.services"
                            ]
                        }
                    },
                    depends_on=["setup_argocd", "generate_kubernetes_manifests"]
                ),
                WorkflowStep(
                    id="setup_domain",
                    name="Setup Domain",
                    description="Configure DNS for the application gateway",
                    agent="deployment",
                    action="process",
                    parameters={
                        "action": "setup_domain",
                        "parameters": {
                            "domain": "input.domain",
                            "ip_address": "${deploy_infrastructure.result.outputs.ingress_ip}"
                        }
                    },
                    depends_on=["deploy_infrastructure"]
                ),
                WorkflowStep(
                    id="create_architecture_documentation",
                    name="Create Architecture Documentation",
                    description="Create architecture documentation in Confluence",
                    agent="confluence",
                    action="process",
                    parameters={
                        "action": "create_page",
                        "parameters": {
                            "space_key": "${create_confluence_space.result.key}",
                            "title": "Architecture Overview",
                            "content": "# ${input.project_name} Architecture\n\n## Overview\nThis page documents the microservices architecture for ${input.project_name}.\n\n## Architecture Diagram\n${architecture_design.result.diagram}\n\n## Services\n{% for service in input.services %}\n### ${service.name}\n${service.description}\n\n- Repository: ${create_org.result.html_url}/${service.name}\n- Responsibilities: ${service.responsibilities}\n- Dependencies: ${service.dependencies}\n{% endfor %}\n\n## Infrastructure\n```terraform\n${generate_infra.code}\n```\n\n## Service Mesh\nService mesh: Istio\n\n## Monitoring\nPrometheus and Grafana dashboards are available at: ${deploy_monitoring.result.grafana_url}\n\n## Logging\nElasticsearch and Kibana are available at: ${deploy_logging.result.kibana_url}\n"
                        }
                    },
                    depends_on=["create_confluence_space", "deploy_monitoring", "deploy_logging"]
                ),
                WorkflowStep(
                    id="create_runbook",
                    name="Create Operations Runbook",
                    description="Create operations runbook in Confluence",
                    agent="confluence",
                    action="process",
                    parameters={
                        "action": "create_page",
                        "parameters": {
                            "space_key": "${create_confluence_space.result.key}",
                            "title": "Operations Runbook",
                            "content": "# ${input.project_name} Operations Runbook\n\n## Environments\n- Development: ${deploy_infrastructure.result.outputs.cluster_endpoint}\n\n## Access\n- Kubernetes Dashboard: ${deploy_infrastructure.result.outputs.kubernetes_dashboard}\n- ArgoCD: ${setup_argocd.result.argocd_url}\n- Prometheus: ${deploy_monitoring.result.prometheus_url}\n- Grafana: ${deploy_monitoring.result.grafana_url}\n- Kibana: ${deploy_logging.result.kibana_url}\n\n## Common Operations\n### Deployment\nAll services are deployed via ArgoCD. To trigger a new deployment, push to the main branch of the respective service repository.\n\n### Scaling\nServices can be scaled by updating the replicas in the Kubernetes manifests.\n\n### Troubleshooting\n- Check logs in Kibana\n- Check metrics in Grafana\n- Check ArgoCD for deployment status\n"
                        }
                    },
                    depends_on=["create_architecture_documentation"]
                ),
                WorkflowStep(
                    id="create_jira_epics",
                    name="Create Jira Epics",
                    description="Create epics for each service in Jira",
                    agent="jira",
                    action="process",
                    parameters={
                        "action": "create_epics",
                        "parameters": {
                            "project_key": "${create_jira_project.result.project_key}",
                            "epics": [
                                {
                                    "name": "${service.name} Development",
                                    "description": "Development tasks for ${service.name} microservice"
                                }
                                for service in "input.services"
                            ]
                        }
                    },
                    depends_on=["create_jira_project"]
                )
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "requirements": {
                        "type": "string",
                        "description": "Project requirements"
                    },
                    "organization_name": {
                        "type": "string",
                        "description": "GitHub organization name"
                    },
                    "services": {
                        "type": "array",
                        "description": "List of microservices",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Service name"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Service description"
                                },
                                "language": {
                                    "type": "string",
                                    "description": "Programming language"
                                },
                                "responsibilities": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Service responsibilities"
                                },
                                "dependencies": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Service dependencies"
                                }
                            },
                            "required": ["name", "description", "language"]
                        }
                    },
                    "template_repository": {
                        "type": "string",
                        "description": "Template repository for microservices"
                    },
                    "cloud_provider": {
                        "type": "string",
                        "enum": ["aws", "azure", "gcp"],
                        "default": "aws",
                        "description": "Cloud provider"
                    },
                    "region": {
                        "type": "string",
                        "default": "us-west-2",
                        "description": "Cloud region"
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["development", "staging", "production"],
                        "default": "development",
                        "description": "Deployment environment"
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain name for the ingress gateway"
                    },
                    "high_availability": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether to deploy in high-availability mode"
                    },
                    "jira_project_key": {
                        "type": "string",
                        "description": "Jira project key"
                    },
                    "confluence_space_key": {
                        "type": "string",
                        "description": "Confluence space key"
                    }
                },
                "required": ["project_name", "organization_name", "services", "domain", "jira_project_key", "confluence_space_key"]
            }
        )
    

    

    


