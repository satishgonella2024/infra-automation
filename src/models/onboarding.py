from typing import Dict, List, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ToolType(str, Enum):
    JIRA = "jira"
    CONFLUENCE = "confluence"
    GITLAB = "gitlab"
    JENKINS = "jenkins"
    NEXUS = "nexus"
    VAULT = "vault"
    KUBERNETES = "kubernetes"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    ALL = "all"

class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEMO = "demo"

class OnboardingRequest(BaseModel):
    """
    Request model for creating a new environment with all necessary tools.
    """
    environment_name: str
    environment_type: EnvironmentType
    user_id: str
    tools: List[ToolType] = Field(default_factory=list)
    custom_domain: Optional[str] = None
    resource_limits: Optional[Dict[str, Any]] = None
    description: Optional[str] = None

class OnboardingResponse(BaseModel):
    """
    Response model for the onboarding request.
    """
    environment_id: str
    status: str
    access_url: Optional[str] = None
    ready: bool
    message: str
    tool_endpoints: Dict[str, str] = Field(default_factory=dict)
    credentials_path: Optional[str] = None

class EnvironmentConfig(BaseModel):
    """
    Configuration for a complete environment setup.
    """
    environment_id: str
    environment_name: str
    environment_type: EnvironmentType
    user_id: str
    tools: List[ToolType]
    custom_domain: Optional[str] = None
    resource_limits: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    created_at: str
    status: str = "initializing"
    tool_endpoints: Dict[str, str] = Field(default_factory=dict)
    credentials: Dict[str, Dict[str, str]] = Field(default_factory=dict) 