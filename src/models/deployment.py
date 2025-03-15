from typing import Dict, List, Any, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

class ResourceType(str, Enum):
    VPC = "vpc"
    SUBNET = "subnet"
    SECURITY_GROUP = "security_group"
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER = "container"
    SERVERLESS_FUNCTION = "serverless_function"
    DATABASE = "database"
    OBJECT_STORAGE = "object_storage"
    LOAD_BALANCER = "load_balancer"
    CDN = "cdn"
    DNS = "dns"

class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITAL_OCEAN = "digital_ocean"

class ResourceRequirement(BaseModel):
    cpu: Optional[str] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    network: Optional[str] = None

class ResourceTag(BaseModel):
    key: str
    value: str

class ResourceConfig(BaseModel):
    name: str
    type: ResourceType
    provider_specific: Dict[str, Any] = Field(default_factory=dict)
    requirements: Optional[ResourceRequirement] = None
    region: Optional[str] = None
    tags: List[ResourceTag] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)

class SecurityRule(BaseModel):
    protocol: str
    port_range: str
    source: str
    description: Optional[str] = None

class NetworkConfig(BaseModel):
    vpc_cidr: Optional[str] = None
    subnet_cidrs: List[str] = Field(default_factory=list)
    security_rules: List[SecurityRule] = Field(default_factory=list)

class DatabaseConfig(BaseModel):
    engine: str
    version: str
    size: str
    replicas: int = 0
    backup_retention_days: int = 7
    encryption_enabled: bool = True

class ServiceConfig(BaseModel):
    name: str
    type: str
    source: Optional[str] = None  # Could be a Git repo URL, container image, etc.
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    scaling: Optional[Dict[str, Any]] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)

class DeploymentConfig(BaseModel):
    """
    Configuration for a complete infrastructure deployment.
    
    This includes all resources, services, networking, and provider-specific settings
    required to deploy an application infrastructure.
    """
    name: str
    description: Optional[str] = None
    provider: CloudProvider
    region: str
    resources: List[ResourceConfig] = Field(default_factory=list)
    services: List[ServiceConfig] = Field(default_factory=list)
    network: Optional[NetworkConfig] = None
    tags: List[ResourceTag] = Field(default_factory=list)
    estimated_cost: Optional[float] = None

class DeploymentTemplate(BaseModel):
    """
    A template for generating deployment configurations.
    
    Templates contain parameterized versions of deployment configurations
    that can be filled with specific values to create concrete deployment configs.
    """
    id: str
    name: str
    description: str
    template_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    base_config: DeploymentConfig
    
    def generate_deployment_config(self, parameter_values: Dict[str, Any]) -> DeploymentConfig:
        """
        Generate a concrete deployment configuration by applying parameter values.
        
        Args:
            parameter_values: Values for the template parameters
            
        Returns:
            A complete DeploymentConfig ready for provisioning
        """
        # Start with a copy of the base config
        config_dict = self.base_config.dict()
        
        # Apply parameter values (this is a simplified approach)
        # A more robust implementation would use a templating engine
        # or parameter substitution system
        for param_name, param_value in parameter_values.items():
            if param_name in self.parameters:
                # Here we would apply the parameter value to the config
                # This is a placeholder for more sophisticated parameter application
                if param_name == "name":
                    config_dict["name"] = param_value
                elif param_name == "region":
                    config_dict["region"] = param_value
                # Additional parameter handling would go here
        
        # Convert back to a DeploymentConfig
        return DeploymentConfig(**config_dict)