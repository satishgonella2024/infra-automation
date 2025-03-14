"""
Jira Agent Module for Multi-Agent Infrastructure Automation System

This module defines the JiraAgent class that specializes in interacting with
Jira for project management, issue tracking, and workflow automation.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base import BaseAgent
from src.utils.template_utils import render_template

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
        super().__init__(
            name="Jira",
            description="Manage Jira projects, issues, and workflows for infrastructure automation",
            capabilities=[
                "issue_creation",
                "issue_tracking",
                "workflow_automation",
                "project_management",
                "sprint_planning",
                "backlog_management",
                "jql_query_generation"
            ],
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize Jira-specific configurations
        self.jira_url = config.get("jira_url") if config else None
        self.jira_username = config.get("jira_username") if config else None
        self.jira_api_token = config.get("jira_api_token") if config else None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
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
        action = input_data.get("action", "")
        parameters = input_data.get("parameters", {})
        
        self.logger.info(f"Processing Jira action: {action}")
        
        # Update agent state
        self.update_state("processing")
        
        # Process the action based on the type
        result = await self.think(input_data)
        
        # Update agent state
        self.update_state("idle")
        
        return result
    
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
        # For now, we'll simulate the response
        
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
        # For now, we'll simulate the response
        
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
        prompt = f"""
        Convert the following natural language query into a valid Jira JQL query:
        
        Query: {natural_language_query}
        
        Return only the JQL query without any additional text.
        """
        
        response = await self.llm_service.generate_text(prompt)
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
        # For now, we'll simulate the response
        
        project_key = project_data.get("key", "PROJ")
        
        return {
            "project_key": project_key,
            "name": project_data.get("name", "New Project"),
            "components": ["Backend", "Frontend", "Infrastructure"],
            "versions": ["1.0", "2.0"],
            "url": f"{self.jira_url}/projects/{project_key}" if self.jira_url else f"https://jira.example.com/projects/{project_key}"
        } 