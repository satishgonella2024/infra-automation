"""
Jira Agent Module for Multi-Agent Infrastructure Automation System

This module defines the JiraAgent class that specializes in interacting with
Jira for project management, issue tracking, and workflow automation.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

class JiraAgent(BaseAgent):
    """
    Specialized agent for Jira integration and automation.
    Capable of creating, updating, and querying Jira issues, projects, and workflows.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new JiraAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "issue_creation",
            "issue_tracking",
            "workflow_automation",
            "project_management",
            "sprint_planning",
            "backlog_management",
            "jql_query_generation"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="jira_agent",
            description="Agent responsible for managing Jira projects, issues, and workflows",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize Jira-specific configurations
        self.jira_url = config.get("jira_url") if config else None
        self.jira_username = config.get("jira_username") if config else None
        self.jira_api_token = config.get("jira_api_token") if config else None
        
        logger.info("Jira agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request related to Jira operations.
        
        Args:
            input_data: Dictionary containing the request details
                - action: The Jira action to perform (create_issue, update_issue, etc.)
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
            if action == "create_issue":
                result = await self.create_issue(
                    project_key=parameters.get("project_key", ""),
                    issue_type=parameters.get("issue_type", ""),
                    summary=parameters.get("summary", ""),
                    description=parameters.get("description", ""),
                    additional_fields=parameters.get("additional_fields")
                )
            elif action == "query_issues":
                result = {"issues": await self.query_issues(
                    jql_query=parameters.get("jql_query", "")
                )}
            elif action == "generate_jql":
                result = {"jql": await self.generate_jql_query(
                    natural_language_query=parameters.get("query", "")
                )}
            elif action == "create_project":
                result = await self.create_project_structure(
                    project_data=parameters.get("project_data", {})
                )
            else:
                result = {
                    "error": f"Unsupported action: {action}",
                    "supported_actions": [
                        "create_issue",
                        "query_issues",
                        "generate_jql",
                        "create_project"
                    ]
                }
            
            # Store in memory
            await self.update_memory({
                "type": "jira_operation",
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
            logger.error(f"Error during Jira operation: {str(e)}")
            self.update_state("error")
            return {
                "task_id": task_id,
                "action": action,
                "error": str(e),
                "status": "error"
            }
    
    async def create_issue(self, project_key: str, issue_type: str, summary: str, 
                          description: str, additional_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new Jira issue.
        
        Args:
            project_key: The project key where the issue will be created
            issue_type: The type of issue (Bug, Task, Story, etc.)
            summary: Issue summary/title
            description: Detailed description of the issue
            additional_fields: Any additional fields to set on the issue
            
        Returns:
            Dictionary containing the created issue details
        """
        # This would integrate with the Jira API in a real implementation
        logger.info(f"Creating Jira issue in project {project_key}: {summary}")
        
        issue_data = {
            "project": {"key": project_key},
            "issuetype": {"name": issue_type},
            "summary": summary,
            "description": description
        }
        
        if additional_fields:
            issue_data.update(additional_fields)
            
        # Simulate API call
        issue_key = f"{project_key}-{100 + hash(summary) % 900}"
        
        return {
            "issue_key": issue_key,
            "summary": summary,
            "status": "Created",
            "url": f"{self.jira_url}/browse/{issue_key}" if self.jira_url else f"https://jira.example.com/browse/{issue_key}"
        }
    
    async def query_issues(self, jql_query: str) -> List[Dict[str, Any]]:
        """
        Query Jira issues using JQL.
        
        Args:
            jql_query: The JQL query string
            
        Returns:
            List of issues matching the query
        """
        # This would integrate with the Jira API in a real implementation
        logger.info(f"Querying Jira issues with JQL: {jql_query}")
        
        # Simulate a few issues
        return [
            {
                "key": "PROJ-123",
                "summary": "Example issue 1",
                "status": "In Progress",
                "assignee": "John Doe"
            },
            {
                "key": "PROJ-124",
                "summary": "Example issue 2",
                "status": "To Do",
                "assignee": "Jane Smith"
            }
        ]
    
    async def generate_jql_query(self, natural_language_query: str) -> str:
        """
        Generate a JQL query from a natural language description.
        
        Args:
            natural_language_query: Natural language description of the query
            
        Returns:
            JQL query string
        """
        # Use LLM to generate JQL
        logger.info(f"Generating JQL from natural language: {natural_language_query}")
        
        prompt = f"""
        Convert the following natural language query into a valid Jira JQL query:
        
        Query: {natural_language_query}
        
        Return only the JQL query without any additional text.
        """
        
        response = await self.llm_service.generate_completion(prompt)
        return response.strip()
    
    async def create_project_structure(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a complete project structure in Jira including components, versions, etc.
        
        Args:
            project_data: Dictionary containing project structure details
            
        Returns:
            Dictionary with created project information
        """
        # This would create a project with components, versions, etc.
        logger.info(f"Creating Jira project structure: {project_data.get('name', 'New Project')}")
        
        project_key = project_data.get("key", "PROJ")
        
        return {
            "project_key": project_key,
            "name": project_data.get("name", "New Project"),
            "components": ["Backend", "Frontend", "Infrastructure"],
            "versions": ["1.0", "2.0"],
            "url": f"{self.jira_url}/projects/{project_key}" if self.jira_url else f"https://jira.example.com/projects/{project_key}"
        }