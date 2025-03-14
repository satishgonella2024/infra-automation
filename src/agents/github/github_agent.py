"""
GitHub Agent Module for Multi-Agent Infrastructure Automation System

This module defines the GitHubAgent class that specializes in managing
GitHub repositories, pull requests, issues, and workflows.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

class GitHubAgent(BaseAgent):
    """
    Specialized agent for GitHub integration and automation.
    Capable of managing repositories, branches, pull requests, and GitHub Actions workflows.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new GitHubAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "repository_management",
            "pull_request_automation",
            "code_review",
            "issue_tracking",
            "github_actions_workflow",
            "branch_management",
            "release_management"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="github_agent",
            description="Agent responsible for managing GitHub repositories, code, and workflows",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize GitHub-specific configurations
        self.github_token = config.get("github_token") if config else None
        self.github_username = config.get("github_username") if config else None
        self.github_org = config.get("github_org") if config else None
        
        logger.info("GitHub agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request related to GitHub operations.
        
        Args:
            input_data: Dictionary containing the request details
                - action: The GitHub action to perform (create_repo, create_pr, etc.)
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
                    description=parameters.get("description", ""),
                    private=parameters.get("private", False),
                    template_repo=parameters.get("template_repo")
                )
            elif action == "create_pull_request":
                result = await self.create_pull_request(
                    repo=parameters.get("repo", ""),
                    title=parameters.get("title", ""),
                    body=parameters.get("body", ""),
                    head=parameters.get("head", ""),
                    base=parameters.get("base", "main")
                )
            elif action == "generate_workflow":
                result = {
                    "workflow": await self.generate_github_actions_workflow(
                        repo_type=parameters.get("repo_type", ""),
                        language=parameters.get("language", ""),
                        ci_requirements=parameters.get("ci_requirements", [])
                    )
                }
            elif action == "review_code":
                result = await self.review_code(
                    code=parameters.get("code", ""),
                    language=parameters.get("language", ""),
                    review_focus=parameters.get("review_focus", [])
                )
            elif action == "manage_release":
                result = await self.manage_releases(
                    repo=parameters.get("repo", ""),
                    version=parameters.get("version", ""),
                    release_notes=parameters.get("release_notes", ""),
                    target_branch=parameters.get("target_branch", "main")
                )
            else:
                result = {
                    "error": f"Unsupported action: {action}",
                    "supported_actions": [
                        "create_repository",
                        "create_pull_request",
                        "generate_workflow",
                        "review_code",
                        "manage_release"
                    ]
                }
            
            # Store in memory
            await self.update_memory({
                "type": "github_operation",
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
            logger.error(f"Error during GitHub operation: {str(e)}")
            self.update_state("error")
            return {
                "task_id": task_id,
                "action": action,
                "error": str(e),
                "status": "error"
            }
    
    async def create_repository(self, name: str, description: str, private: bool = False, 
                              template_repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new GitHub repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether the repository should be private
            template_repo: Optional template repository to use
            
        Returns:
            Dictionary containing the created repository details
        """
        # This would integrate with the GitHub API in a real implementation
        logger.info(f"Creating GitHub repository: {name}")
        
        org_or_user = self.github_org if self.github_org else self.github_username
        repo_url = f"https://github.com/{org_or_user}/{name}"
        
        return {
            "name": name,
            "full_name": f"{org_or_user}/{name}",
            "description": description,
            "private": private,
            "html_url": repo_url,
            "clone_url": f"{repo_url}.git",
            "created_at": "2023-01-01T00:00:00Z"
        }
    
    async def create_pull_request(self, repo: str, title: str, body: str, 
                                head: str, base: str = "main") -> Dict[str, Any]:
        """
        Create a new pull request.
        
        Args:
            repo: Repository name (owner/repo)
            title: PR title
            body: PR description
            head: Head branch
            base: Base branch
            
        Returns:
            Dictionary containing the created PR details
        """
        # This would integrate with the GitHub API in a real implementation
        logger.info(f"Creating GitHub PR in {repo}: {title}")
        
        pr_number = hash(f"{repo}:{title}") % 1000
        
        return {
            "number": pr_number,
            "title": title,
            "body": body,
            "state": "open",
            "html_url": f"https://github.com/{repo}/pull/{pr_number}",
            "head": {"ref": head},
            "base": {"ref": base}
        }
    
    async def generate_github_actions_workflow(self, repo_type: str, language: str, 
                                             ci_requirements: List[str]) -> str:
        """
        Generate a GitHub Actions workflow file.
        
        Args:
            repo_type: Type of repository (web, api, library, etc.)
            language: Programming language
            ci_requirements: List of CI requirements
            
        Returns:
            GitHub Actions workflow YAML as a string
        """
        # Use LLM to generate GitHub Actions workflow
        logger.info(f"Generating GitHub Actions workflow for {language} {repo_type}")
        
        prompt = f"""
        Generate a GitHub Actions workflow YAML file for a {repo_type} project written in {language}.
        
        The workflow should include the following CI steps:
        {', '.join(ci_requirements)}
        
        Return only the YAML content without any additional text.
        """
        
        response = await self.llm_service.generate_completion(prompt)
        return response.strip()
    
    async def review_code(self, code: str, language: str, review_focus: List[str]) -> Dict[str, Any]:
        """
        Review code and provide feedback.
        
        Args:
            code: Code to review
            language: Programming language
            review_focus: Aspects to focus on (security, performance, etc.)
            
        Returns:
            Dictionary with review comments and suggestions
        """
        # Use LLM to review code
        logger.info(f"Reviewing {language} code focusing on {', '.join(review_focus)}")
        
        prompt = f"""
        Review the following {language} code focusing on {', '.join(review_focus)}:
        
        ```{language}
        {code}
        ```
        
        Provide a detailed review with:
        1. Overall assessment
        2. Specific issues found
        3. Suggested improvements
        4. Code examples for fixes
        """
        
        response = await self.llm_service.generate_completion(prompt)
        
        # Parse the response into structured feedback
        # This is a simplified version
        return {
            "overall_assessment": "Review completed",
            "issues": [
                {"line": 1, "severity": "medium", "message": "Example issue"}
            ],
            "suggestions": [
                {"description": "Example suggestion", "code": "Example code"}
            ],
            "full_review": response
        }
    
    async def manage_releases(self, repo: str, version: str, release_notes: str, 
                            target_branch: str = "main") -> Dict[str, Any]:
        """
        Create a new release.
        
        Args:
            repo: Repository name (owner/repo)
            version: Release version
            release_notes: Release notes
            target_branch: Branch to create release from
            
        Returns:
            Dictionary with release information
        """
        # This would create a release in GitHub
        logger.info(f"Creating release v{version} for {repo}")
        
        return {
            "tag_name": f"v{version}",
            "name": f"Release v{version}",
            "body": release_notes,
            "draft": False,
            "prerelease": False,
            "created_at": "2023-01-01T00:00:00Z",
            "published_at": "2023-01-01T00:00:00Z",
            "html_url": f"https://github.com/{repo}/releases/tag/v{version}"
        }