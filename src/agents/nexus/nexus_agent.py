"""
Nexus Agent Module for Multi-Agent Infrastructure Automation System

This module defines the NexusAgent class that specializes in managing
Nexus repositories for artifacts, containers, and packages.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

class NexusAgent(BaseAgent):
    """
    Specialized agent for Nexus repository management.
    Capable of managing repositories, artifacts, and integrating with CI/CD pipelines.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new NexusAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "repository_management",
            "artifact_management",
            "container_registry",
            "package_management",
            "repository_health_check",
            "cleanup_policies",
            "integration_scripts"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="nexus_agent",
            description="Agent responsible for managing Nexus repositories for artifacts, containers, and packages",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize Nexus-specific configurations
        self.nexus_url = config.get("nexus_url") if config else None
        self.nexus_username = config.get("nexus_username") if config else None
        self.nexus_password = config.get("nexus_password") if config else None
        
        logger.info("Nexus agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request related to Nexus operations.
        
        Args:
            input_data: Dictionary containing the request details
                - action: The Nexus action to perform (create_repo, upload_artifact, etc.)
                - parameters: Parameters specific to the action
        
        Returns:
            Dictionary containing the results of the operation
        """
        self.update_state("processing")
        
        action = input_data.get("action", "")
        parameters = input_data.get("parameters", {})
        task_id = input_data.get("task_id", "")
        
        try:
            # First, think about how to approach the task
            thoughts = await self.think(input_data)
            
            # Process the action based on the type
            if action == "create_repository":
                result = await self.create_repository(
                    name=parameters.get("name", ""),
                    repo_type=parameters.get("repo_type", ""),
                    format=parameters.get("format", ""),
                    blob_store=parameters.get("blob_store", "default")
                )
            elif action == "upload_artifact":
                result = await self.upload_artifact(
                    repository=parameters.get("repository", ""),
                    artifact_path=parameters.get("artifact_path", ""),
                    group_id=parameters.get("group_id", ""),
                    artifact_id=parameters.get("artifact_id", ""),
                    version=parameters.get("version", "")
                )
            elif action == "create_cleanup_policy":
                result = await self.create_cleanup_policy(
                    name=parameters.get("name", ""),
                    format=parameters.get("format", ""),
                    criteria=parameters.get("criteria", {})
                )
            elif action == "generate_integration_script":
                result = {
                    "script": await self.generate_integration_script(
                        tool=parameters.get("tool", ""),
                        repository=parameters.get("repository", ""),
                        format=parameters.get("format", "")
                    )
                }
            elif action == "check_repository_health":
                result = await self.check_repository_health(
                    repository=parameters.get("repository", "")
                )
            elif action == "search_artifacts":
                result = {
                    "artifacts": await self.search_artifacts(
                        query=parameters.get("query", ""),
                        repository=parameters.get("repository")
                    )
                }
            else:
                result = {
                    "error": f"Unsupported action: {action}",
                    "supported_actions": [
                        "create_repository",
                        "upload_artifact",
                        "create_cleanup_policy",
                        "generate_integration_script",
                        "check_repository_health",
                        "search_artifacts"
                    ]
                }
            
            # Store in memory
            await self.update_memory({
                "type": "nexus_operation",
                "action": action,
                "input": parameters,
                "output": result,
                "timestamp": self.last_active_time
            })
            
            self.update_state("idle")
            return {
                "task_id": task_id,
                "action": action,
                "result": result,
                "thoughts": thoughts.get("thoughts", ""),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error during Nexus operation: {str(e)}")
            self.update_state("error")
            return {
                "task_id": task_id,
                "action": action,
                "error": str(e),
                "status": "error"
            }
    
    async def create_repository(self, name: str, repo_type: str, format: str, 
                              blob_store: str = "default") -> Dict[str, Any]:
        """
        Create a new Nexus repository.
        
        Args:
            name: Repository name
            repo_type: Repository type (hosted, proxy, group)
            format: Repository format (maven2, npm, docker, etc.)
            blob_store: Blob store name
            
        Returns:
            Dictionary containing the created repository details
        """
        # This would integrate with the Nexus API in a real implementation
        logger.info(f"Creating Nexus repository: {name} of type {repo_type} for format {format}")
        
        return {
            "name": name,
            "type": repo_type,
            "format": format,
            "url": f"{self.nexus_url}/repository/{name}" if self.nexus_url else f"https://nexus.example.com/repository/{name}",
            "status": "Created"
        }
    
    async def upload_artifact(self, repository: str, artifact_path: str, 
                            group_id: str, artifact_id: str, version: str) -> Dict[str, Any]:
        """
        Upload an artifact to a Nexus repository.
        
        Args:
            repository: Repository name
            artifact_path: Path to the artifact file
            group_id: Maven group ID
            artifact_id: Maven artifact ID
            version: Artifact version
            
        Returns:
            Dictionary containing the upload result
        """
        # This would integrate with the Nexus API in a real implementation
        logger.info(f"Uploading artifact {artifact_id}-{version} to repository {repository}")
        
        return {
            "repository": repository,
            "path": f"{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar",
            "format": "maven2",
            "status": "Uploaded",
            "url": f"{self.nexus_url}/repository/{repository}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar" if self.nexus_url else f"https://nexus.example.com/repository/{repository}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.jar"
        }
    
    async def create_cleanup_policy(self, name: str, format: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a cleanup policy for repositories.
        
        Args:
            name: Policy name
            format: Repository format (maven2, npm, docker, etc.)
            criteria: Cleanup criteria
            
        Returns:
            Dictionary containing the created policy details
        """
        # This would integrate with the Nexus API in a real implementation
        logger.info(f"Creating cleanup policy: {name} for format {format}")
        
        return {
            "name": name,
            "format": format,
            "criteria": criteria,
            "status": "Created"
        }
    
    async def generate_integration_script(self, tool: str, repository: str, 
                                        format: str) -> str:
        """
        Generate integration scripts for various tools.
        
        Args:
            tool: Tool to integrate with (maven, gradle, npm, docker, etc.)
            repository: Repository name
            format: Repository format
            
        Returns:
            Integration script as a string
        """
        # Use LLM to generate integration script
        logger.info(f"Generating {tool} integration script for {repository}")
        
        prompt = f"""
        Generate an integration script for {tool} to use the Nexus repository '{repository}' with format '{format}'.
        
        The script should include:
        1. Configuration settings
        2. Authentication setup
        3. Example usage
        
        Return only the script content without any additional text.
        """
        
        response = await self.llm_service.generate_completion(prompt)
        return response.strip()
    
    async def check_repository_health(self, repository: str) -> Dict[str, Any]:
        """
        Check the health of a Nexus repository.
        
        Args:
            repository: Repository name
            
        Returns:
            Dictionary with health information
        """
        # This would check repository health in a real implementation
        logger.info(f"Checking health of repository: {repository}")
        
        return {
            "repository": repository,
            "status": "healthy",
            "size": "1.2 GB",
            "artifact_count": 1250,
            "last_updated": "2023-01-01T00:00:00Z"
        }
    
    async def search_artifacts(self, query: str, repository: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for artifacts in Nexus.
        
        Args:
            query: Search query
            repository: Optional repository to limit search
            
        Returns:
            List of matching artifacts
        """
        # This would search for artifacts in a real implementation
        logger.info(f"Searching for artifacts matching '{query}' in {repository or 'all repositories'}")
        
        return [
            {
                "repository": repository or "maven-releases",
                "group": "org.example",
                "name": "example-lib",
                "version": "1.0.0",
                "format": "maven2",
                "last_updated": "2023-01-01T00:00:00Z"
            },
            {
                "repository": repository or "maven-releases",
                "group": "org.example",
                "name": "example-app",
                "version": "2.0.0",
                "format": "maven2",
                "last_updated": "2023-01-01T00:00:00Z"
            }
        ]