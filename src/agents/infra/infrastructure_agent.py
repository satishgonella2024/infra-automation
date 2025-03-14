"""
Infrastructure Agent Module for Multi-Agent Infrastructure Automation System

This module defines the InfrastructureAgent class that specializes in generating
infrastructure as code (Terraform, Ansible, Jenkins) based on user requirements.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

class InfrastructureAgent(BaseAgent):
    """
    Specialized agent for infrastructure provisioning and code generation.
    Capable of generating Terraform, Ansible, and Jenkins configurations.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new InfrastructureAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "terraform_generation",
            "ansible_generation",
            "jenkins_generation",
            "infrastructure_analysis",
            "cost_estimation",
            "pattern_management"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="infrastructure_agent",
            description="Agent responsible for generating infrastructure as code based on user requirements",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize tool-specific templates directory
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "templates"
        )
        
        # Map of cloud providers and their specific configurations
        self.cloud_providers = {
            "aws": {
                "service_mapping": {
                    "compute": "aws_instance",
                    "storage": "aws_s3_bucket",
                    "database": "aws_db_instance",
                    "network": "aws_vpc"
                }
            },
            "azure": {
                "service_mapping": {
                    "compute": "azurerm_virtual_machine",
                    "storage": "azurerm_storage_account",
                    "database": "azurerm_mysql_server",
                    "network": "azurerm_virtual_network"
                }
            },
            "gcp": {
                "service_mapping": {
                    "compute": "google_compute_instance",
                    "storage": "google_storage_bucket",
                    "database": "google_sql_database_instance",
                    "network": "google_compute_network"
                }
            }
        }
        
        logger.info("Infrastructure Agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data to generate infrastructure code.
        
        Args:
            input_data: Dictionary containing:
                - task: The description of what to generate
                - requirements: Specific infrastructure requirements
                - cloud_provider: Target cloud provider (aws, azure, gcp)
                - iac_type: Type of IaC to generate (terraform, ansible, jenkins)
                
        Returns:
            Dictionary containing the generated code and metadata
        """
        self.update_state("processing")
        
        task = input_data.get("task", "")
        requirements = input_data.get("requirements", {})
        cloud_provider = input_data.get("cloud_provider", "aws").lower()
        iac_type = input_data.get("iac_type", "terraform").lower()
        task_id = input_data.get("task_id", "")
        
        try:
            # First, think about the task
            thoughts = await self.think(input_data)
            
            # Generate the appropriate infrastructure code
            if iac_type == "terraform":
                code, metadata = await self._generate_terraform(task, requirements, cloud_provider)
            elif iac_type == "ansible":
                code, metadata = await self._generate_ansible(task, requirements, cloud_provider)
            elif iac_type == "jenkins":
                code, metadata = await self._generate_jenkins(task, requirements)
            else:
                raise ValueError(f"Unsupported IaC type: {iac_type}. Supported types: terraform, ansible, jenkins")
            
            # Store in memory
            await self.update_memory({
                "type": "infrastructure_generation",
                "input": input_data,
                "output": {
                    "code": code,
                    "metadata": metadata
                },
                "timestamp": self.last_active_time
            })
            
            self.update_state("idle")
            return {
                "task_id": task_id,
                "code": code,
                "metadata": metadata,
                "thoughts": thoughts.get("thoughts", ""),
                "iac_type": iac_type,
                "cloud_provider": cloud_provider,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error during infrastructure generation: {str(e)}")
            self.update_state("error")
            return {
                "task_id": task_id,
                "error": str(e),
                "iac_type": iac_type,
                "cloud_provider": cloud_provider,
                "status": "error"
            }
    
    async def _generate_terraform(
        self, 
        task: str, 
        requirements: Dict[str, Any],
        cloud_provider: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate Terraform code based on requirements."""
        logger.info(f"Generating Terraform code for {cloud_provider}")
        
        # Search for similar patterns if we have a vector DB service
        similar_patterns = []
        if self.vector_db_service:
            try:
                # Combine task and requirements for a more comprehensive search
                search_query = f"{task} {json.dumps(requirements)}"
                
                # Search for similar patterns
                similar_patterns = await self.vector_db_service.search_patterns(
                    query=search_query,
                    cloud_provider=cloud_provider,
                    iac_type="terraform",
                    n_results=3
                )
                
                logger.info(f"Found {len(similar_patterns)} similar patterns")
            except Exception as e:
                logger.error(f"Error searching for patterns: {str(e)}")
        
        # Also search for similar previous generations from memory
        similar_generations = []
        if self.vector_db_service:
            try:
                similar_memories = await self.retrieve_similar_memories(
                    query=task,
                    n_results=2,
                    memory_type="infrastructure_generation"
                )
                
                for memory in similar_memories:
                    memory_data = memory.get("memory", {})
                    if "output" in memory_data and "code" in memory_data["output"]:
                        similar_generations.append({
                            "task": memory_data.get("input", {}).get("task", ""),
                            "code": memory_data["output"]["code"]
                        })
                
                logger.info(f"Found {len(similar_generations)} similar past generations")
            except Exception as e:
                logger.error(f"Error retrieving similar generations: {str(e)}")
        
        # Prepare examples from similar patterns
        examples_text = ""
        if similar_patterns:
            examples_text = "Here are some similar infrastructure patterns that may be relevant:\n\n"
            for i, pattern in enumerate(similar_patterns):
                examples_text += f"Pattern {i+1}: {pattern['name']}\n"
                examples_text += f"Description: {pattern['description']}\n"
                examples_text += f"Code:\n```terraform\n{pattern['code'][:1000]}...\n```\n\n"
        
        # Add examples from similar generations
        if similar_generations:
            if examples_text:
                examples_text += "\n"
            examples_text += "Here are some similar infrastructures I've generated before:\n\n"
            for i, gen in enumerate(similar_generations):
                examples_text += f"Example {i+1}: {gen['task']}\n"
                examples_text += f"Code:\n```terraform\n{gen['code'][:1000]}...\n```\n\n"
        
        # Prepare the prompt for the LLM
        prompt = f"""
        As an expert in Infrastructure as Code, generate a complete Terraform configuration for the following task:
        
        {task}
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        Target Cloud Provider: {cloud_provider}
        
        {examples_text}
        
        Generate a complete, production-ready Terraform configuration including:
        1. Provider configuration
        2. Variables and outputs
        3. Resource definitions with appropriate naming conventions
        4. Security best practices
        5. Any necessary modules or data sources
        
        Return ONLY the Terraform code without explanations or markdown formatting.
        """
        
        # Generate the code using LLM
        terraform_code = await self.llm_service.generate_completion(prompt)
        
        # Parse and analyze the generated code for metadata
        resources_count = terraform_code.count("resource ")
        module_count = terraform_code.count("module ")
        
        # Simple estimation of provisioning time (very basic heuristic)
        estimated_minutes = resources_count * 2 + module_count * 5
        
        metadata = {
            "resource_count": resources_count,
            "module_count": module_count,
            "estimated_provisioning_time_minutes": estimated_minutes,
            "cloud_provider": cloud_provider,
            "generated_timestamp": self.last_active_time,
            "similar_patterns_used": len(similar_patterns),
            "similar_generations_used": len(similar_generations),
            "used_rag": (len(similar_patterns) > 0 or len(similar_generations) > 0)
        }
        
        # Automatically store as pattern if it seems meaningful
        if len(terraform_code) > 200 and resources_count > 1 and self.vector_db_service:
            try:
                await self.save_pattern(
                    name=f"Auto-generated: {task[:50]}{'...' if len(task) > 50 else ''}",
                    description=task,
                    code=terraform_code,
                    cloud_provider=cloud_provider,
                    iac_type="terraform",
                    metadata={
                        "auto_generated": True,
                        "requirements": requirements,
                        "resource_count": resources_count,
                        "module_count": module_count
                    }
                )
                logger.info("Stored generated code as a pattern for future use")
            except Exception as e:
                logger.error(f"Error storing pattern: {str(e)}")
        
        return terraform_code, metadata
    
    async def _generate_ansible(
        self, 
        task: str, 
        requirements: Dict[str, Any],
        cloud_provider: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate Ansible playbook based on requirements."""
        logger.info(f"Generating Ansible playbook for {cloud_provider}")
        
        # Search for similar patterns if we have a vector DB service
        similar_patterns = []
        if self.vector_db_service:
            try:
                search_query = f"{task} {json.dumps(requirements)}"
                similar_patterns = await self.vector_db_service.search_patterns(
                    query=search_query,
                    cloud_provider=cloud_provider,
                    iac_type="ansible",
                    n_results=2
                )
                logger.info(f"Found {len(similar_patterns)} similar Ansible patterns")
            except Exception as e:
                logger.error(f"Error searching for Ansible patterns: {str(e)}")
        
        # Prepare examples from similar patterns
        examples_text = ""
        if similar_patterns:
            examples_text = "Here are some similar Ansible playbooks that may be relevant:\n\n"
            for i, pattern in enumerate(similar_patterns):
                examples_text += f"Pattern {i+1}: {pattern['name']}\n"
                examples_text += f"Description: {pattern['description']}\n"
                examples_text += f"Code:\n```yaml\n{pattern['code'][:1000]}...\n```\n\n"
        
        # Prepare the prompt for the LLM
        prompt = f"""
        As an expert in configuration management, generate a complete Ansible playbook for the following task:
        
        {task}
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        Target Environment: {cloud_provider}
        
        {examples_text}
        
        Generate a complete, production-ready Ansible playbook including:
        1. Host definitions
        2. Variables
        3. Tasks with appropriate naming and organization
        4. Handlers if needed
        5. Security best practices
        6. Error handling
        
        Return ONLY the Ansible YAML code without explanations or markdown formatting.
        """
        
        # Generate the code using LLM
        ansible_code = await self.llm_service.generate_completion(prompt)
        
        # Parse and analyze the generated code for metadata
        task_count = ansible_code.count("- name:")
        role_count = ansible_code.count("roles:")
        
        metadata = {
            "task_count": task_count,
            "role_count": role_count,
            "estimated_execution_time_minutes": task_count * 1.5,
            "environment": cloud_provider,
            "generated_timestamp": self.last_active_time,
            "similar_patterns_used": len(similar_patterns),
            "used_rag": (len(similar_patterns) > 0)
        }
        
        # Automatically store as pattern if it seems meaningful
        if len(ansible_code) > 200 and task_count > 3 and self.vector_db_service:
            try:
                await self.save_pattern(
                    name=f"Auto-generated: {task[:50]}{'...' if len(task) > 50 else ''}",
                    description=task,
                    code=ansible_code,
                    cloud_provider=cloud_provider,
                    iac_type="ansible",
                    metadata={
                        "auto_generated": True,
                        "requirements": requirements,
                        "task_count": task_count,
                        "role_count": role_count
                    }
                )
                logger.info("Stored generated Ansible code as a pattern for future use")
            except Exception as e:
                logger.error(f"Error storing Ansible pattern: {str(e)}")
        
        return ansible_code, metadata
    
    async def _generate_jenkins(
        self, 
        task: str, 
        requirements: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate Jenkins pipeline configuration based on requirements."""
        logger.info("Generating Jenkins pipeline")
        
        # Search for similar patterns if we have a vector DB service
        similar_patterns = []
        if self.vector_db_service:
            try:
                search_query = f"{task} {json.dumps(requirements)}"
                similar_patterns = await self.vector_db_service.search_patterns(
                    query=search_query,
                    iac_type="jenkins",
                    n_results=2
                )
                logger.info(f"Found {len(similar_patterns)} similar Jenkins patterns")
            except Exception as e:
                logger.error(f"Error searching for Jenkins patterns: {str(e)}")
        
        # Prepare examples from similar patterns
        examples_text = ""
        if similar_patterns:
            examples_text = "Here are some similar Jenkins pipelines that may be relevant:\n\n"
            for i, pattern in enumerate(similar_patterns):
                examples_text += f"Pattern {i+1}: {pattern['name']}\n"
                examples_text += f"Description: {pattern['description']}\n"
                examples_text += f"Code:\n```groovy\n{pattern['code'][:1000]}...\n```\n\n"
        
        # Prepare the prompt for the LLM
        prompt = f"""
        As an expert in CI/CD pipelines, generate a complete Jenkins pipeline configuration for the following task:
        
        {task}
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        {examples_text}
        
        Generate a complete, production-ready Jenkinsfile including:
        1. Pipeline stages
        2. Environment variables
        3. Appropriate agents/nodes
        4. Error handling and notifications
        5. Security best practices
        6. Parallel execution where appropriate
        
        Return ONLY the Jenkins pipeline code (Jenkinsfile) without explanations or markdown formatting.
        """
        
        # Generate the code using LLM
        jenkins_code = await self.llm_service.generate_completion(prompt)
        
        # Parse and analyze the generated code for metadata
        stage_count = jenkins_code.count("stage(")
        parallel_count = jenkins_code.count("parallel")
        
        metadata = {
            "stage_count": stage_count,
            "parallel_count": parallel_count,
            "estimated_pipeline_time_minutes": stage_count * 3 - (parallel_count * 2),
            "generated_timestamp": self.last_active_time,
            "similar_patterns_used": len(similar_patterns),
            "used_rag": (len(similar_patterns) > 0)
        }
        
        # Automatically store as pattern if it seems meaningful
        if len(jenkins_code) > 200 and stage_count > 2 and self.vector_db_service:
            try:
                await self.save_pattern(
                    name=f"Auto-generated: {task[:50]}{'...' if len(task) > 50 else ''}",
                    description=task,
                    code=jenkins_code,
                    cloud_provider="any",
                    iac_type="jenkins",
                    metadata={
                        "auto_generated": True,
                        "requirements": requirements,
                        "stage_count": stage_count,
                        "parallel_count": parallel_count
                    }
                )
                logger.info("Stored generated Jenkins code as a pattern for future use")
            except Exception as e:
                logger.error(f"Error storing Jenkins pattern: {str(e)}")
        
        return jenkins_code, metadata
    
    async def analyze_infrastructure(self, infrastructure_code: str, iac_type: str) -> Dict[str, Any]:
        """
        Analyze existing infrastructure code and provide insights.
        
        Args:
            infrastructure_code: The IaC code to analyze
            iac_type: The type of IaC (terraform, ansible, jenkins)
            
        Returns:
            Analysis results including issues, optimizations, and security concerns
        """
        logger.info(f"Analyzing {iac_type} infrastructure code")
        self.update_state("analyzing")
        
        # Prepare the prompt for the LLM
        prompt = f"""
        As an expert in {iac_type}, analyze the following infrastructure code and provide insights:
        
        ```
        {infrastructure_code}
        ```
        
        Provide a comprehensive analysis including:
        1. Potential security issues
        2. Cost optimization opportunities
        3. Performance considerations
        4. Best practice violations
        5. Maintainability concerns
        
        Format your response as structured JSON with the following keys:
        - security_issues: Array of objects with 'severity', 'description', and 'recommendation'
        - cost_optimizations: Array of objects with 'potential_savings', 'description', and 'recommendation'
        - performance_considerations: Array of objects with 'impact', 'description', and 'recommendation'
        - best_practice_violations: Array of objects with 'importance', 'description', and 'recommendation'
        - maintainability_concerns: Array of objects with 'importance', 'description', and 'recommendation'
        - overall_score: Number from 1 to 10
        - summary: String with overall assessment
        """
        
        # Generate the analysis using LLM
        analysis_json = await self.llm_service.generate_completion(prompt)
        
        # Parse the JSON response
        try:
            analysis = json.loads(analysis_json)
        except json.JSONDecodeError:
            logger.error("Failed to parse analysis JSON")
            analysis = {
                "error": "Failed to parse analysis",
                "raw_output": analysis_json,
                "overall_score": 0
            }
        
        self.update_state("idle")
        return analysis
    
    async def estimate_costs(
        self, 
        infrastructure_code: str,
        iac_type: str,
        cloud_provider: str
    ) -> Dict[str, Any]:
        """
        Estimate the costs of the infrastructure defined in the code.
        
        Args:
            infrastructure_code: The IaC code to analyze
            iac_type: The type of IaC (terraform, ansible, jenkins)
            cloud_provider: The target cloud provider
            
        Returns:
            Cost estimation results
        """
        logger.info(f"Estimating costs for {cloud_provider} using {iac_type}")
        self.update_state("estimating")
        
        # Prepare the prompt for the LLM
        prompt = f"""
        As a {cloud_provider} cost optimization expert, estimate the monthly costs for the following {iac_type} code:
        
        ```
        {infrastructure_code}
        ```
        
        Provide a detailed cost breakdown including:
        1. Compute costs (EC2, VMs, etc.)
        2. Storage costs (S3, disks, etc.)
        3. Database costs
        4. Networking costs
        5. Other service costs
        
        Format your response as a JSON object with the following structure:
        {{
            "estimated_monthly_cost": 0,
            "estimated_yearly_cost": 0,
            "breakdown": {{
                "compute": {{
                    "details": [
                        {{"service": "", "instance_type": "", "count": 0, "monthly_cost": 0}}
                    ],
                    "subtotal": 0
                }},
                "storage": {{
                    "details": [
                        {{"service": "", "size_gb": 0, "monthly_cost": 0}}
                    ],
                    "subtotal": 0
                }},
                "database": {{
                    "details": [
                        {{"service": "", "instance_type": "", "monthly_cost": 0}}
                    ],
                    "subtotal": 0
                }},
                "networking": {{
                    "details": [
                        {{"service": "", "description": "", "monthly_cost": 0}}
                    ],
                    "subtotal": 0
                }},
                "other": {{
                    "details": [
                        {{"service": "", "description": "", "monthly_cost": 0}}
                    ],
                    "subtotal": 0
                }}
            }},
            "savings_opportunities": [
                {{"description": "", "potential_monthly_savings": 0, "implementation_difficulty": ""}}
            ]
        }}
        """
        
        # Generate the cost estimation using LLM
        cost_json = await self.llm_service.generate_completion(prompt)
        
        # Parse the JSON response
        try:
            cost_estimate = json.loads(cost_json)
        except json.JSONDecodeError:
            logger.error("Failed to parse cost estimation JSON")
            cost_estimate = {
                "error": "Failed to parse cost estimation",
                "raw_output": cost_json,
                "estimated_monthly_cost": "unknown"
            }
        
        self.update_state("idle")
        return cost_estimate
        
    # Pattern Repository Methods
    
    async def save_pattern(
        self, 
        name: str,
        description: str,
        code: str,
        cloud_provider: str,
        iac_type: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Save an infrastructure pattern to the pattern repository.
        
        Args:
            name: Name of the pattern
            description: Description of the pattern
            code: The infrastructure code
            cloud_provider: Target cloud provider
            iac_type: Type of IaC
            metadata: Additional metadata
            
        Returns:
            Dictionary with the pattern ID
        """
        if not self.vector_db_service:
            return {"error": "Vector DB service not available"}
        
        pattern = {
            "name": name,
            "description": description,
            "code": code,
            "cloud_provider": cloud_provider,
            "iac_type": iac_type,
            "metadata": metadata or {}
        }
        
        return await self.vector_db_service.add_pattern(pattern)

    async def find_patterns(
        self,
        query: str,
        cloud_provider: Optional[str] = None,
        iac_type: Optional[str] = None,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find infrastructure patterns similar to the query.
        
        Args:
            query: The search query
            cloud_provider: Optional filter for cloud provider
            iac_type: Optional filter for IaC type
            n_results: Maximum number of results to return
            
        Returns:
            List of similar patterns
        """
        if not self.vector_db_service:
            return []
        
        return await self.vector_db_service.search_patterns(
            query=query,
            cloud_provider=cloud_provider,
            iac_type=iac_type,
            n_results=n_results
        )
        
    async def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a pattern by ID.
        
        Args:
            pattern_id: ID of the pattern to retrieve
            
        Returns:
            Pattern data or None if not found
        """
        if not self.vector_db_service:
            return None
            
        return await self.vector_db_service.get_pattern(pattern_id)
        
    async def update_pattern(
        self,
        pattern_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        code: Optional[str] = None,
        cloud_provider: Optional[str] = None,
        iac_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an existing pattern.
        
        Args:
            pattern_id: ID of the pattern to update
            name: New name (optional)
            description: New description (optional)
            code: New code (optional)
            cloud_provider: New cloud provider (optional)
            iac_type: New IaC type (optional)
            metadata: New metadata (optional)
            
        Returns:
            Dictionary with the pattern ID
        """
        if not self.vector_db_service:
            return {"error": "Vector DB service not available"}
            
        # Get the existing pattern
        existing_pattern = await self.vector_db_service.get_pattern(pattern_id)
        if not existing_pattern:
            return {"error": f"Pattern {pattern_id} not found"}
            
        # Update pattern with new values, keeping existing ones if not provided
        updated_pattern = {
            "name": name if name is not None else existing_pattern["name"],
            "description": description if description is not None else existing_pattern["description"],
            "code": code if code is not None else existing_pattern["code"],
            "cloud_provider": cloud_provider if cloud_provider is not None else existing_pattern["cloud_provider"],
            "iac_type": iac_type if iac_type is not None else existing_pattern["iac_type"],
            "metadata": {**existing_pattern["metadata"], **(metadata or {})}
        }
        
        return await self.vector_db_service.update_pattern(pattern_id, updated_pattern)
        
    async def delete_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """
        Delete a pattern.
        
        Args:
            pattern_id: ID of the pattern to delete
            
        Returns:
            Dictionary with the pattern ID
        """
        if not self.vector_db_service:
            return {"error": "Vector DB service not available"}
            
        return await self.vector_db_service.delete_pattern(pattern_id)