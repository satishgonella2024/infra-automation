"""
System Integration Module for Multi-Agent Infrastructure Automation System

This module integrates the various components of the system, including the
workflow orchestrator, RBAC system, and API server.
"""

import os
import sys
import logging
import asyncio
from fastapi import FastAPI
from typing import Dict, Any

# Import components
from src.agents.base.base_agent import BaseAgent
from src.workflow.orchestrator import WorkflowOrchestrator
from src.workflow.api import router as workflow_router, initialize_orchestrator
from src.rbac.agent_rbac import rbac_system, initialize_rbac

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/data/system_integration.log')
    ]
)

logger = logging.getLogger(__name__)

def integrate_systems(app: FastAPI, agents: Dict[str, BaseAgent]):
    """
    Integrate all system components.
    
    Args:
        app: FastAPI application
        agents: Dictionary of agents
    """
    logger.info("Integrating system components...")
    
    # Initialize RBAC system
    logger.info("Initializing RBAC system...")
    initialize_rbac(agents)
    
    # Initialize workflow orchestrator
    logger.info("Initializing workflow orchestrator...")
    orchestrator = initialize_orchestrator(agents)
    
    # Add workflow API routes
    logger.info("Adding workflow API routes...")
    app.include_router(workflow_router)
    
    logger.info("System integration complete!")
    
    return {
        "orchestrator": orchestrator,
        "rbac_system": rbac_system
    }

async def run_initialization_tasks(agents: Dict[str, BaseAgent]):
    """
    Run initialization tasks that need to happen after the system is up.
    
    Args:
        agents: Dictionary of agents
    """
    logger.info("Running initialization tasks...")
    
    # Initialize agent-specific components
    for agent_id, agent in agents.items():
        if agent is None:
            continue
        
        # Initialize agent if it has an initialize method
        if hasattr(agent, 'initialize') and callable(agent.initialize):
            try:
                logger.info(f"Initializing agent: {agent_id}")
                await agent.initialize()
            except Exception as e:
                logger.error(f"Error initializing agent {agent_id}: {str(e)}")
    
    # Set up predefined workflows if needed
    try:
        await _create_predefined_workflows(agents)
    except Exception as e:
        logger.error(f"Error creating predefined workflows: {str(e)}")
    
    logger.info("Initialization tasks completed!")

async def _create_predefined_workflows(agents: Dict[str, BaseAgent]):
    """
    Create predefined workflows in the system.
    
    Args:
        agents: Dictionary of agents
    """
    # Import only when needed to avoid circular imports
    from src.workflow.schema import WorkflowRegistry
    from src.workflow.orchestrator import WorkflowOrchestrator
    
    registry = WorkflowRegistry()
    
    # Register agent capabilities
    for agent_id, agent in agents.items():
        if agent is None:
            continue
        
        # Skip agents that don't have proper capabilities defined
        if not hasattr(agent, 'serialize') or not callable(agent.serialize):
            continue
        
        try:
            # Get agent metadata
            agent_info = agent.serialize()
            
            # Create agent capabilities
            from src.workflow.schema import AgentCapabilities
            
            capabilities = AgentCapabilities(
                agent_id=agent_id,
                agent_name=agent_info.get('name', agent_id),
                description=agent_info.get('description', ''),
                actions={}  # Actions are added dynamically in the API
            )
            
            # Register the agent
            registry.register_agent_capabilities(capabilities)
        except Exception as e:
            logger.error(f"Error registering agent capabilities for {agent_id}: {str(e)}")
    
    # TODO: Create sample workflows if needed
    # This can be extended later with predefined workflows

async def create_docker_containers():
    """
    Set up Docker containers for third-party tools (Jira, Confluence, Vault).
    This function creates and configures the necessary containers.
    """
    # Check if Docker is available
    import subprocess
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except Exception:
        logger.error("Docker is not available. Cannot set up containers.")
        return
    
    # Create docker-compose file for third-party tools
    compose_file = """
version: '3.8'

services:
  # Vault for secret management
  vault:
    image: vault:latest
    container_name: devops-vault
    ports:
      - "8200:8200"
    environment:
      - VAULT_DEV_ROOT_TOKEN_ID=devops-root-token
    cap_add:
      - IPC_LOCK
    volumes:
      - vault-data:/vault/data
    command: server -dev -dev-root-token-id=devops-root-token
    networks:
      - devops-network

  # Jira for project management
  jira:
    image: atlassian/jira-software:latest
    container_name: devops-jira
    ports:
      - "8080:8080"
    environment:
      - ATL_JDBC_URL=jdbc:postgresql://jira-db:5432/jira
      - ATL_JDBC_USER=jira
      - ATL_JDBC_PASSWORD=jira
      - ATL_DB_DRIVER=org.postgresql.Driver
      - ATL_DB_TYPE=postgres72
    volumes:
      - jira-data:/var/atlassian/application-data/jira
    depends_on:
      - jira-db
    networks:
      - devops-network

  # PostgreSQL for Jira
  jira-db:
    image: postgres:13
    container_name: devops-jira-db
    environment:
      - POSTGRES_USER=jira
      - POSTGRES_PASSWORD=jira
      - POSTGRES_DB=jira
    volumes:
      - jira-db-data:/var/lib/postgresql/data
    networks:
      - devops-network

  # Confluence for documentation
  confluence:
    image: atlassian/confluence:latest
    container_name: devops-confluence
    ports:
      - "8090:8090"
    environment:
      - ATL_JDBC_URL=jdbc:postgresql://confluence-db:5432/confluence
      - ATL_JDBC_USER=confluence
      - ATL_JDBC_PASSWORD=confluence
      - ATL_DB_TYPE=postgresql
    volumes:
      - confluence-data:/var/atlassian/application-data/confluence
    depends_on:
      - confluence-db
    networks:
      - devops-network

  # PostgreSQL for Confluence
  confluence-db:
    image: postgres:13
    container_name: devops-confluence-db
    environment:
      - POSTGRES_USER=confluence
      - POSTGRES_PASSWORD=confluence
      - POSTGRES_DB=confluence
    volumes:
      - confluence-db-data:/var/lib/postgresql/data
    networks:
      - devops-network

volumes:
  vault-data:
  jira-data:
  jira-db-data:
  confluence-data:
  confluence-db-data:

networks:
  devops-network:
    driver: bridge
"""
    
    # Write docker-compose file
    try:
        with open('/app/data/third_party_tools.yml', 'w') as f:
            f.write(compose_file)
    except Exception as e:
        logger.error(f"Error writing docker-compose file: {str(e)}")
        return
    
    # Start containers
    try:
        subprocess.run(
            ["docker-compose", "-f", "/app/data/third_party_tools.yml", "up", "-d"],
            check=True,
            capture_output=True
        )
        logger.info("Third-party tool containers started successfully!")
    except Exception as e:
        logger.error(f"Error starting containers: {str(e)}")
        return
    
    # Wait for containers to be ready
    await asyncio.sleep(30)
    
    # Initialize Vault
    try:
        # Configure Vault policies
        policy = """
# Dev servers have version 2 of KV secrets engine mounted by default, so will
# need these paths to grant permissions:
path "secret/data/*" {
  capabilities = ["create", "update", "read", "delete"]
}

path "secret/metadata/*" {
  capabilities = ["list"]
}

# Dev servers have version 2 of KV secrets engine mounted by default, so will
# need these paths to grant permissions:
path "kv/data/*" {
  capabilities = ["create", "update", "read", "delete"]
}

path "kv/metadata/*" {
  capabilities = ["list"]
}
"""
        
        with open('/tmp/devops-policy.hcl', 'w') as f:
            f.write(policy)
        
        # Create Vault policy
        subprocess.run(
            ["docker", "exec", "devops-vault", "vault", "policy", "write", "devops-policy", "/tmp/devops-policy.hcl"],
            check=True,
            capture_output=True,
            env={"VAULT_TOKEN": "devops-root-token"}
        )
        
        # Enable KV secrets engine
        subprocess.run(
            ["docker", "exec", "devops-vault", "vault", "secrets", "enable", "-path=kv", "kv-v2"],
            check=True,
            capture_output=True,
            env={"VAULT_TOKEN": "devops-root-token"}
        )
        
        # Create an initial secret
        subprocess.run(
            ["docker", "exec", "devops-vault", "vault", "kv", "put", "kv/devops-automation", "api_key=initial-setup-key"],
            check=True,
            capture_output=True,
            env={"VAULT_TOKEN": "devops-root-token"}
        )
        
        logger.info("Vault initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing Vault: {str(e)}")
    
    # Save container info
    container_info = {
        "vault": {
            "url": "http://localhost:8200",
            "token": "devops-root-token"
        },
        "jira": {
            "url": "http://localhost:8080",
            "username": "admin",  # Will need to be set during Jira setup
            "password": "admin"   # Will need to be set during Jira setup
        },
        "confluence": {
            "url": "http://localhost:8090",
            "username": "admin",  # Will need to be set during Confluence setup
            "password": "admin"   # Will need to be set during Confluence setup
        }
    }
    
    try:
        with open('/app/data/container_info.json', 'w') as f:
            import json
            json.dump(container_info, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving container info: {str(e)}")