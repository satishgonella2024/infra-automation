"""
Agent RBAC Module for Multi-Agent Infrastructure Automation System

This module provides role-based access control for agents, ensuring that
each agent only has access to the resources and actions it needs.
"""

import os
import json
import logging
from typing import Dict, List, Set, Any, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)

class Permission:
    """
    Permission class for defining what actions agents can perform.
    
    Format: resource:action
    Examples: "terraform:read", "kubernetes:deploy", "*:*"
    """
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action
    
    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Permission):
            return False
        return self.resource == other.resource and self.action == other.action
    
    def __hash__(self) -> int:
        return hash((self.resource, self.action))
    
    @classmethod
    def from_string(cls, permission_str: str) -> 'Permission':
        """Create a Permission object from a string."""
        if ':' not in permission_str:
            raise ValueError(f"Invalid permission format: {permission_str}")
        
        resource, action = permission_str.split(':', 1)
        return cls(resource, action)
    
    def allows(self, resource: str, action: str) -> bool:
        """Check if this permission allows the specified resource and action."""
        return (self.resource == '*' or self.resource == resource) and \
               (self.action == '*' or self.action == action)

class Role:
    """
    Role class for grouping permissions.
    
    Examples: "admin", "reader", "terraform-writer"
    """
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.permissions: Set[Permission] = set()
    
    def add_permission(self, permission: Union[Permission, str]) -> None:
        """Add a permission to this role."""
        if isinstance(permission, str):
            permission = Permission.from_string(permission)
        
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Union[Permission, str]) -> None:
        """Remove a permission from this role."""
        if isinstance(permission, str):
            permission = Permission.from_string(permission)
        
        if permission in self.permissions:
            self.permissions.remove(permission)
    
    def has_permission(self, resource: str, action: str) -> bool:
        """Check if this role has the specified permission."""
        for permission in self.permissions:
            if permission.allows(resource, action):
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert this role to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [str(p) for p in self.permissions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Role':
        """Create a Role object from a dictionary."""
        role = cls(data["name"], data.get("description", ""))
        for perm_str in data.get("permissions", []):
            role.add_permission(perm_str)
        
        return role

class AgentRBAC:
    """
    RBAC system for controlling agent access to resources and actions.
    """
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.agent_roles: Dict[str, Set[str]] = {}
        
        # Path for persisting RBAC configuration
        self.config_file = os.environ.get("RBAC_CONFIG_FILE", "/app/data/rbac_config.json")
        
        # Initialize with default roles
        self._init_default_roles()
        
        # Load persisted configuration if available
        self._load_config()
    
    def _init_default_roles(self) -> None:
        """Initialize default roles."""
        # Admin role - can do everything
        admin_role = Role("admin", "Administrator with full access")
        admin_role.add_permission("*:*")
        self.roles[admin_role.name] = admin_role
        
        # Read-only role
        reader_role = Role("reader", "Read-only access to resources")
        reader_role.add_permission("*:read")
        reader_role.add_permission("*:list")
        reader_role.add_permission("*:describe")
        self.roles[reader_role.name] = reader_role
        
        # Infrastructure agent role
        infra_role = Role("infrastructure", "Infrastructure agent role")
        infra_role.add_permission("terraform:*")
        infra_role.add_permission("ansible:*")
        infra_role.add_permission("jenkins:*")
        infra_role.add_permission("cloudformation:*")
        self.roles[infra_role.name] = infra_role
        
        # Security agent role
        security_role = Role("security", "Security agent role")
        security_role.add_permission("terraform:read")
        security_role.add_permission("ansible:read")
        security_role.add_permission("jenkins:read")
        security_role.add_permission("cloudformation:read")
        security_role.add_permission("security:*")
        self.roles[security_role.name] = security_role
        
        # Vault agent role
        vault_role = Role("vault", "Vault agent role")
        vault_role.add_permission("vault:*")
        vault_role.add_permission("secrets:*")
        self.roles[vault_role.name] = vault_role
        
        # Jira agent role
        jira_role = Role("jira", "Jira agent role")
        jira_role.add_permission("jira:*")
        self.roles[jira_role.name] = jira_role
        
        # GitHub agent role
        github_role = Role("github", "GitHub agent role")
        github_role.add_permission("github:*")
        github_role.add_permission("git:*")
        self.roles[github_role.name] = github_role
        
        # Confluence agent role
        confluence_role = Role("confluence", "Confluence agent role")
        confluence_role.add_permission("confluence:*")
        self.roles[confluence_role.name] = confluence_role
        
        # Kubernetes agent role
        k8s_role = Role("kubernetes", "Kubernetes agent role")
        k8s_role.add_permission("kubernetes:*")
        self.roles[k8s_role.name] = k8s_role
        
        # ArgoCD agent role
        argocd_role = Role("argocd", "ArgoCD agent role")
        argocd_role.add_permission("argocd:*")
        argocd_role.add_permission("kubernetes:read")
        argocd_role.add_permission("kubernetes:list")
        self.roles[argocd_role.name] = argocd_role
    
    def _load_config(self) -> None:
        """Load RBAC configuration from file."""
        if not os.path.exists(self.config_file):
            logger.info(f"RBAC configuration file not found: {self.config_file}")
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Load roles
            for role_data in config.get("roles", []):
                role = Role.from_dict(role_data)
                self.roles[role.name] = role
            
            # Load agent roles
            self.agent_roles = {
                agent_id: set(role_names)
                for agent_id, role_names in config.get("agent_roles", {}).items()
            }
            
            logger.info(f"Loaded RBAC configuration with {len(self.roles)} roles and {len(self.agent_roles)} agent mappings")
        except Exception as e:
            logger.error(f"Error loading RBAC configuration: {str(e)}")
    
    def _save_config(self) -> None:
        """Save RBAC configuration to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Prepare configuration
            config = {
                "roles": [role.to_dict() for role in self.roles.values()],
                "agent_roles": {
                    agent_id: list(role_names)
                    for agent_id, role_names in self.agent_roles.items()
                }
            }
            
            # Write to file
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved RBAC configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving RBAC configuration: {str(e)}")
    
    def create_role(self, name: str, description: str = "", permissions: List[str] = None) -> Role:
        """
        Create a new role.
        
        Args:
            name: Role name
            description: Role description
            permissions: List of permission strings
            
        Returns:
            The created role
        """
        if name in self.roles:
            raise ValueError(f"Role already exists: {name}")
        
        role = Role(name, description)
        if permissions:
            for perm in permissions:
                role.add_permission(perm)
        
        self.roles[name] = role
        self._save_config()
        
        return role
    
    def update_role(
        self,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> Optional[Role]:
        """
        Update an existing role.
        
        Args:
            name: Role name
            description: New description (optional)
            permissions: New permissions (optional)
            
        Returns:
            The updated role or None if not found
        """
        if name not in self.roles:
            return None
        
        role = self.roles[name]
        
        if description is not None:
            role.description = description
        
        if permissions is not None:
            # Replace all permissions
            role.permissions.clear()
            for perm in permissions:
                role.add_permission(perm)
        
        self._save_config()
        
        return role
    
    def delete_role(self, name: str) -> bool:
        """
        Delete a role.
        
        Args:
            name: Role name
            
        Returns:
            True if the role was deleted, False if not found
        """
        if name not in self.roles:
            return False
        
        # Remove the role from all agents
        for agent_id, role_names in self.agent_roles.items():
            if name in role_names:
                role_names.remove(name)
        
        # Delete the role
        del self.roles[name]
        self._save_config()
        
        return True
    
    def assign_role_to_agent(self, agent_id: str, role_name: str) -> bool:
        """
        Assign a role to an agent.
        
        Args:
            agent_id: Agent ID
            role_name: Role name
            
        Returns:
            True if the role was assigned, False if the role was not found
        """
        if role_name not in self.roles:
            return False
        
        if agent_id not in self.agent_roles:
            self.agent_roles[agent_id] = set()
        
        self.agent_roles[agent_id].add(role_name)
        self._save_config()
        
        return True
    
    def revoke_role_from_agent(self, agent_id: str, role_name: str) -> bool:
        """
        Revoke a role from an agent.
        
        Args:
            agent_id: Agent ID
            role_name: Role name
            
        Returns:
            True if the role was revoked, False if the agent or role was not found
        """
        if agent_id not in self.agent_roles:
            return False
        
        if role_name not in self.agent_roles[agent_id]:
            return False
        
        self.agent_roles[agent_id].remove(role_name)
        self._save_config()
        
        return True
    
    def get_agent_roles(self, agent_id: str) -> List[Role]:
        """
        Get all roles assigned to an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of roles assigned to the agent
        """
        if agent_id not in self.agent_roles:
            return []
        
        return [
            self.roles[role_name]
            for role_name in self.agent_roles[agent_id]
            if role_name in self.roles
        ]
    
    def get_agent_permissions(self, agent_id: str) -> Set[Permission]:
        """
        Get all permissions granted to an agent through its roles.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Set of permissions
        """
        permissions = set()
        
        for role in self.get_agent_roles(agent_id):
            permissions.update(role.permissions)
        
        return permissions
    
    def check_permission(self, agent_id: str, resource: str, action: str) -> bool:
        """
        Check if an agent has permission to perform an action on a resource.
        
        Args:
            agent_id: Agent ID
            resource: Resource name
            action: Action name
            
        Returns:
            True if the agent has permission, False otherwise
        """
        # Get agent permissions
        permissions = self.get_agent_permissions(agent_id)
        
        # Check if any permission allows the action
        for permission in permissions:
            if permission.allows(resource, action):
                return True
        
        return False

def requires_permission(resource: str, action: str):
    """
    Decorator for agent methods that require specific permissions.
    
    Args:
        resource: Resource name
        action: Action name
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get agent ID
            agent_id = getattr(self, 'id', None)
            
            if agent_id is None:
                raise ValueError("Agent ID not found")
            
            # Check permission
            from src.rbac.agent_rbac import rbac_system
            if not rbac_system.check_permission(agent_id, resource, action):
                logger.warning(f"Permission denied: {agent_id} cannot {action} on {resource}")
                return {
                    "error": "Permission denied",
                    "message": f"Agent does not have permission to {action} on {resource}"
                }
            
            # Permission granted, call the original function
            return await func(self, *args, **kwargs)
        
        return wrapper
    
    return decorator

# Global instance for API use
rbac_system = AgentRBAC()

# Function to initialize the RBAC system with existing agents
def initialize_rbac(agents: Dict[str, Any]):
    """
    Initialize the RBAC system with existing agents.
    
    Args:
        agents: Dictionary of agents
    """
    # Assign default roles based on agent type
    for agent_id, agent in agents.items():
        # Skip None agents
        if agent is None:
            continue
        
        # Check if the agent already has roles
        if agent_id in rbac_system.agent_roles:
            continue
        
        # Assign default role based on agent ID
        if agent_id in rbac_system.roles:
            rbac_system.assign_role_to_agent(agent_id, agent_id)
        else:
            # Assign reader role for unknown agents
            rbac_system.assign_role_to_agent(agent_id, "reader")
    
    # Save configuration
    rbac_system._save_config()