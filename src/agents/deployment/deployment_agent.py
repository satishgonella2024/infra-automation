from typing import Dict, List, Any, Optional
import json
import logging
from enum import Enum
from pydantic import BaseModel, Field
from langchain.llms import BaseLLM
import uuid

from src.agents.base.base_agent import BaseAgent
from src.infrastructure.provider_factory import CloudProviderFactory
from src.infrastructure.provider_interface import CloudProviderInterface
from src.models.deployment import DeploymentConfig, ResourceType, ServiceConfig
from src.models.workflow import WorkflowState

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"

class DeploymentResult(BaseModel):
    status: DeploymentStatus
    resources: Dict[str, Any] = Field(default_factory=dict)
    endpoints: Dict[str, str] = Field(default_factory=dict)
    logs: List[str] = Field(default_factory=list)
    error: Optional[str] = None

class DeploymentAgent(BaseAgent):
    """
    Agent responsible for provisioning infrastructure based on deployment configurations.
    
    This agent handles:
    1. Interpreting deployment configurations
    2. Selecting appropriate cloud providers
    3. Provisioning required infrastructure
    4. Tracking deployment progress
    5. Providing access information for deployed resources
    """
    
    def __init__(self, llm_service, vector_db_service=None, config=None):
        name = "DeploymentAgent"
        description = "Agent responsible for provisioning infrastructure based on deployment configurations"
        capabilities = [
            "deploy_infrastructure",
            "provision_resources",
            "manage_cloud_resources",
            "track_deployment_progress",
            "rollback_deployments"
        ]
        super().__init__(
            name=name,
            description=description,
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config or {}
        )
        self.provider_factory = CloudProviderFactory()
        self.cloud_provider_name = config.get("cloud_provider", "aws") if config else "aws"
        self.cloud_provider = self.provider_factory.get_provider(self.cloud_provider_name)
        self.logger = logging.getLogger(__name__)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return the result.
        
        Args:
            input_data: The input data to process, which can include:
                - action: The action to perform (deploy, update, rollback)
                - deployment_config: The deployment configuration
                - workflow_state: The current workflow state (if part of a workflow)
                
        Returns:
            The processed result
        """
        self.logger.info(f"Processing deployment request: {input_data.get('action', 'unknown')}")
        self.update_state("processing")
        
        try:
            # Extract the action from the input data
            action = input_data.get("action", "deploy")
            
            # Handle different actions
            if action == "deploy":
                # Check if we have a workflow state
                if "workflow_state" in input_data:
                    workflow_state = input_data["workflow_state"]
                    result = await self.execute_workflow_step(workflow_state)
                    self.update_state("idle")
                    return {"result": result}
                
                # If we have a deployment config directly
                elif "deployment_config" in input_data:
                    from src.models.deployment import DeploymentConfig
                    from src.models.workflow import WorkflowState
                    
                    # Convert to DeploymentConfig if it's a dict
                    deployment_config = input_data["deployment_config"]
                    if isinstance(deployment_config, dict):
                        deployment_config = DeploymentConfig(**deployment_config)
                    
                    # Create a workflow state
                    workflow_state = WorkflowState(
                        workflow_id=input_data.get("task_id", str(uuid.uuid4())),
                        user_id=input_data.get("user_id", "api_user"),
                        template_id=input_data.get("template_id", "api_template"),
                        status="initialized",
                        deployment_config=deployment_config,
                        inputs=input_data.get("inputs", {})
                    )
                    
                    # Execute the deployment
                    result = await self.execute_workflow_step(workflow_state)
                    self.update_state("idle")
                    return {
                        "status": result.status,
                        "deployment_status": result.deployment_status,
                        "resource_endpoints": result.resource_endpoints,
                        "errors": result.errors
                    }
                
                else:
                    self.update_state("error")
                    return {
                        "error": "Missing deployment configuration or workflow state"
                    }
            
            elif action == "update":
                # Implement update logic here
                self.update_state("idle")
                return {
                    "error": "Update action not implemented yet"
                }
            
            elif action == "rollback":
                # Implement rollback logic here
                self.update_state("idle")
                return {
                    "error": "Rollback action not implemented yet"
                }
            
            else:
                self.update_state("error")
                return {
                    "error": f"Unsupported action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing deployment request: {str(e)}")
            self.update_state("error")
            return {
                "error": str(e)
            }
    
    def switch_provider(self, provider_name: str) -> None:
        """Change the active cloud provider."""
        self.cloud_provider_name = provider_name
        self.cloud_provider = self.provider_factory.get_provider(provider_name)
    
    async def provision_infrastructure(self, deployment_config: DeploymentConfig) -> DeploymentResult:
        """
        Main method to provision infrastructure based on the provided deployment configuration.
        
        Args:
            deployment_config: The configuration specifying what resources to deploy
            
        Returns:
            DeploymentResult containing status, resources, endpoints, and logs
        """
        self.logger.info(f"Starting infrastructure provisioning with {self.cloud_provider_name}")
        result = DeploymentResult(status=DeploymentStatus.IN_PROGRESS)
        
        try:
            # Validate the configuration against provider capabilities
            self._validate_config(deployment_config)
            
            # Process each resource in the optimal order
            deployed_resources = {}
            
            # Step 1: Deploy networking components first
            network_resources = self._filter_resources_by_type(deployment_config, 
                                                             [ResourceType.VPC, ResourceType.SUBNET, ResourceType.SECURITY_GROUP])
            
            for resource_config in network_resources:
                resource_result = await self.cloud_provider.create_resource(resource_config)
                deployed_resources[resource_config.name] = resource_result
                result.logs.append(f"Created network resource: {resource_config.name}")
            
            # Step 2: Deploy storage resources
            storage_resources = self._filter_resources_by_type(deployment_config,
                                                             [ResourceType.DATABASE, ResourceType.OBJECT_STORAGE])
            
            for resource_config in storage_resources:
                resource_result = await self.cloud_provider.create_resource(resource_config)
                deployed_resources[resource_config.name] = resource_result
                result.logs.append(f"Created storage resource: {resource_config.name}")
            
            # Step 3: Deploy compute resources
            compute_resources = self._filter_resources_by_type(deployment_config,
                                                             [ResourceType.VIRTUAL_MACHINE, ResourceType.CONTAINER, 
                                                              ResourceType.SERVERLESS_FUNCTION])
            
            for resource_config in compute_resources:
                resource_result = await self.cloud_provider.create_resource(resource_config)
                deployed_resources[resource_config.name] = resource_result
                result.logs.append(f"Created compute resource: {resource_config.name}")
                
                # For compute resources, we may need to extract endpoints
                if hasattr(resource_result, 'endpoint') and resource_result.endpoint:
                    result.endpoints[resource_config.name] = resource_result.endpoint
            
            # Step 4: Deploy services
            for service_config in deployment_config.services:
                service_result = await self._deploy_service(service_config, deployed_resources)
                result.logs.append(f"Deployed service: {service_config.name}")
                
                if hasattr(service_result, 'endpoint') and service_result.endpoint:
                    result.endpoints[service_config.name] = service_result.endpoint
            
            # Record all resources in the result
            result.resources = deployed_resources
            result.status = DeploymentStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Error during infrastructure provisioning: {str(e)}")
            result.status = DeploymentStatus.FAILED
            result.error = str(e)
            
            # Attempt rollback if we have partial deployments
            if deployed_resources:
                result.status = DeploymentStatus.ROLLING_BACK
                try:
                    await self._rollback_deployment(deployed_resources)
                    result.status = DeploymentStatus.ROLLED_BACK
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {str(rollback_error)}")
                    # Keep the ROLLING_BACK status to indicate incomplete rollback
        
        return result
        
    def _validate_config(self, deployment_config: DeploymentConfig) -> None:
        """Validate that the deployment configuration is supported by the provider."""
        # Example validation logic - could be expanded based on provider capabilities
        unsupported_resources = []
        
        for resource in deployment_config.resources:
            if not self.cloud_provider.supports_resource_type(resource.type):
                unsupported_resources.append(resource.type)
        
        if unsupported_resources:
            raise ValueError(f"The selected provider ({self.cloud_provider_name}) does not support these resources: {unsupported_resources}")
    
    def _filter_resources_by_type(self, deployment_config: DeploymentConfig, 
                                resource_types: List[ResourceType]) -> List[Any]:
        """Filter resources by their types."""
        return [r for r in deployment_config.resources if r.type in resource_types]
    
    async def _deploy_service(self, service_config: ServiceConfig, 
                           available_resources: Dict[str, Any]) -> Any:
        """Deploy a service that may depend on other resources."""
        # Resolve resource dependencies
        for dependency in service_config.dependencies:
            if dependency not in available_resources:
                raise ValueError(f"Required dependency {dependency} is not available")
        
        # Deploy the service with access to dependencies
        service_result = await self.cloud_provider.deploy_service(
            service_config=service_config,
            resources=available_resources
        )
        
        return service_result
    
    async def _rollback_deployment(self, deployed_resources: Dict[str, Any]) -> None:
        """Rollback a deployment by deleting resources in reverse order."""
        # Process in reverse order of creation (compute -> storage -> network)
        resources_list = list(deployed_resources.items())
        resources_list.reverse()
        
        for name, resource in resources_list:
            try:
                await self.cloud_provider.delete_resource(resource)
                self.logger.info(f"Rolled back resource: {name}")
            except Exception as e:
                self.logger.error(f"Failed to roll back resource {name}: {str(e)}")
                # Continue trying to roll back other resources
    
    async def execute_workflow_step(self, workflow_state: WorkflowState) -> WorkflowState:
        """
        Execute the deployment step in a workflow.
        
        Args:
            workflow_state: The current state of the workflow
            
        Returns:
            Updated workflow state
        """
        self.logger.info("Executing deployment workflow step")
        
        # Extract deployment configuration from workflow state
        deployment_config = workflow_state.deployment_config
        if not deployment_config:
            workflow_state.errors.append("No deployment configuration found in workflow state")
            workflow_state.status = "failed"
            return workflow_state
        
        # Provision the infrastructure
        deployment_result = await self.provision_infrastructure(deployment_config)
        
        # Update workflow state with deployment results
        workflow_state.deployment_status = deployment_result.status
        workflow_state.deployed_resources = deployment_result.resources
        workflow_state.resource_endpoints = deployment_result.endpoints
        
        # Update overall workflow status based on deployment result
        if deployment_result.status == DeploymentStatus.COMPLETED:
            workflow_state.status = "deployment_completed"
        elif deployment_result.status == DeploymentStatus.FAILED or deployment_result.status == DeploymentStatus.ROLLING_BACK:
            workflow_state.status = "failed"
            workflow_state.errors.append(deployment_result.error or "Deployment failed")
        
        return workflow_state