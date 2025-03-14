"""
Confluence Agent Module for Multi-Agent Infrastructure Automation System

This module defines the ConfluenceAgent class that specializes in managing
Confluence documentation, spaces, and pages for infrastructure documentation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

class ConfluenceAgent(BaseAgent):
    """
    Specialized agent for Confluence documentation management.
    Capable of creating, updating, and organizing documentation in Confluence.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new ConfluenceAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "page_creation",
            "page_update",
            "space_management",
            "documentation_generation",
            "template_management",
            "knowledge_base_organization",
            "markdown_to_confluence"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="confluence_agent",
            description="Agent responsible for managing Confluence documentation for infrastructure and processes",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize Confluence-specific configurations
        self.confluence_url = config.get("confluence_url") if config else None
        self.confluence_username = config.get("confluence_username") if config else None
        self.confluence_api_token = config.get("confluence_api_token") if config else None
        
        logger.info("Confluence agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request related to Confluence operations.
        
        Args:
            input_data: Dictionary containing the request details
                - action: The Confluence action to perform (create_page, update_page, etc.)
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
            if action == "create_page":
                result = await self.create_page(
                    space_key=parameters.get("space_key", ""),
                    title=parameters.get("title", ""),
                    content=parameters.get("content", ""),
                    parent_id=parameters.get("parent_id")
                )
            elif action == "update_page":
                result = await self.update_page(
                    page_id=parameters.get("page_id", ""),
                    title=parameters.get("title", ""),
                    content=parameters.get("content", ""),
                    version=parameters.get("version", 1)
                )
            elif action == "convert_markdown":
                result = {
                    "converted_content": await self.convert_markdown_to_confluence(
                        parameters.get("markdown_content", "")
                    )
                }
            elif action == "generate_documentation":
                result = {
                    "documentation": await self.generate_documentation(
                        parameters.get("infrastructure_code", ""),
                        parameters.get("code_type", "terraform")
                    )
                }
            elif action == "create_space":
                result = await self.create_space(
                    key=parameters.get("key", ""),
                    name=parameters.get("name", ""),
                    description=parameters.get("description", "")
                )
            else:
                result = {
                    "error": f"Unsupported action: {action}",
                    "supported_actions": [
                        "create_page",
                        "update_page",
                        "convert_markdown",
                        "generate_documentation",
                        "create_space"
                    ]
                }
            
            # Store in memory
            await self.update_memory({
                "type": "confluence_operation",
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
            logger.error(f"Error during Confluence operation: {str(e)}")
            self.update_state("error")
            return {
                "task_id": task_id,
                "action": action,
                "error": str(e),
                "status": "error"
            }
    
    async def create_page(self, space_key: str, title: str, content: str, 
                         parent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new Confluence page.
        
        Args:
            space_key: The space where the page will be created
            title: Page title
            content: Page content in Confluence storage format or markdown
            parent_id: Optional parent page ID
            
        Returns:
            Dictionary containing the created page details
        """
        # This would integrate with the Confluence API in a real implementation
        logger.info(f"Creating Confluence page: {title} in space {space_key}")
        
        page_id = f"{100000 + hash(title) % 900000}"
        
        return {
            "id": page_id,
            "title": title,
            "space": {"key": space_key},
            "status": "Created",
            "url": f"{self.confluence_url}/spaces/{space_key}/pages/{page_id}" if self.confluence_url else f"https://confluence.example.com/spaces/{space_key}/pages/{page_id}"
        }
    
    async def update_page(self, page_id: str, title: str, content: str, version: int) -> Dict[str, Any]:
        """
        Update an existing Confluence page.
        
        Args:
            page_id: The ID of the page to update
            title: New page title
            content: New page content
            version: Current page version
            
        Returns:
            Dictionary containing the updated page details
        """
        # This would integrate with the Confluence API in a real implementation
        logger.info(f"Updating Confluence page: {page_id}")
        
        return {
            "id": page_id,
            "title": title,
            "version": {"number": version + 1},
            "status": "Updated"
        }
    
    async def convert_markdown_to_confluence(self, markdown_content: str) -> str:
        """
        Convert markdown content to Confluence storage format.
        
        Args:
            markdown_content: Content in markdown format
            
        Returns:
            Content in Confluence storage format
        """
        # Use LLM to convert markdown to Confluence format
        logger.info("Converting markdown to Confluence format")
        
        prompt = f"""
        Convert the following markdown content to Confluence storage format:
        
        ```markdown
        {markdown_content}
        ```
        
        Return only the Confluence storage format XML without any additional text.
        """
        
        response = await self.llm_service.generate_completion(prompt)
        return response.strip()
    
    async def generate_documentation(self, infrastructure_code: str, code_type: str) -> str:
        """
        Generate documentation for infrastructure code.
        
        Args:
            infrastructure_code: The infrastructure code to document
            code_type: Type of code (terraform, ansible, kubernetes, etc.)
            
        Returns:
            Generated documentation in Confluence storage format
        """
        # Use LLM to generate documentation
        logger.info(f"Generating documentation for {code_type} code")
        
        prompt = f"""
        Generate comprehensive Confluence documentation for the following {code_type} code:
        
        ```{code_type}
        {infrastructure_code}
        ```
        
        The documentation should include:
        1. Overview of what this infrastructure provides
        2. Architecture diagram description
        3. Components and their relationships
        4. Configuration parameters
        5. Dependencies
        6. Deployment instructions
        7. Maintenance procedures
        
        Format the response in Confluence storage format.
        """
        
        response = await self.llm_service.generate_completion(prompt)
        return response.strip()
    
    async def create_space(self, key: str, name: str, description: str) -> Dict[str, Any]:
        """
        Create a new Confluence space.
        
        Args:
            key: Space key (short identifier)
            name: Space name
            description: Space description
            
        Returns:
            Dictionary with created space information
        """
        # This would create a space in Confluence
        logger.info(f"Creating Confluence space: {name} with key {key}")
        
        return {
            "key": key,
            "name": name,
            "description": {"plain": {"value": description}},
            "status": "Created",
            "url": f"{self.confluence_url}/spaces/{key}" if self.confluence_url else f"https://confluence.example.com/spaces/{key}"
        }