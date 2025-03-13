"""
Terraform Module Agent for Multi-Agent Infrastructure Automation System

This module defines the TerraformModuleAgent class that specializes in generating
enterprise-grade Terraform modules following best practices and design patterns.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import render_template

logger = logging.getLogger(__name__)

class TerraformModuleAgent(BaseAgent):
    """
    Specialized agent for generating enterprise-grade Terraform modules.
    Focuses on modular, reusable, and well-structured Terraform code.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new TerraformModuleAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        super().__init__(
            name="Terraform Module",
            description="Generate enterprise-grade Terraform modules following best practices",
            capabilities=[
                "terraform_module_generation",
                "module_documentation",
                "module_testing",
                "module_versioning",
                "module_registry_integration",
                "enterprise_patterns"
            ],
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize tool-specific templates directory
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "templates"
        )
        
        # Enterprise patterns and best practices
        self.enterprise_patterns = {
            "module_structure": [
                "main.tf - Core resources",
                "variables.tf - Input variables with descriptions and validation",
                "outputs.tf - Output values",
                "versions.tf - Required providers and versions",
                "README.md - Comprehensive documentation",
                "examples/ - Usage examples",
                "test/ - Automated tests"
            ],
            "naming_conventions": {
                "module_name": "terraform-{provider}-{name}",
                "variable_prefix": "var.",
                "output_prefix": "output."
            },
            "best_practices": [
                "Use semantic versioning",
                "Implement input validation",
                "Provide sensible defaults",
                "Include comprehensive documentation",
                "Add automated tests",
                "Support multiple providers/regions",
                "Implement tagging strategy",
                "Use consistent formatting"
            ]
        }
        
        # Cloud provider specific module patterns
        self.provider_patterns = {
            "aws": {
                "networking": ["vpc", "subnets", "security_groups", "route_tables"],
                "compute": ["ec2", "auto_scaling", "ecs", "eks", "lambda"],
                "storage": ["s3", "ebs", "efs", "rds", "dynamodb"],
                "security": ["iam", "kms", "secrets_manager", "waf"]
            },
            "azure": {
                "networking": ["vnet", "subnets", "network_security_groups", "route_tables"],
                "compute": ["virtual_machine", "vmss", "aks", "functions"],
                "storage": ["storage_account", "managed_disks", "sql_database", "cosmos_db"],
                "security": ["active_directory", "key_vault", "role_assignments"]
            },
            "gcp": {
                "networking": ["vpc", "subnets", "firewall_rules", "cloud_router"],
                "compute": ["compute_instance", "instance_template", "gke", "cloud_functions"],
                "storage": ["cloud_storage", "persistent_disk", "cloud_sql", "firestore"],
                "security": ["iam", "kms", "secret_manager"]
            }
        }
        
        logger.info("Terraform Module agent initialized")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data to generate enterprise-grade Terraform modules.
        
        Args:
            input_data: Dictionary containing:
                - task: The description of what to generate
                - requirements: Specific module requirements
                - cloud_provider: Target cloud provider (aws, azure, gcp)
                - module_type: Type of module to generate (networking, compute, storage, security)
                
        Returns:
            Dictionary containing the generated module files and metadata
        """
        self.logger.info(f"Processing Terraform module generation request: {input_data.get('task_id', 'unknown')}")
        self.update_state("processing")
        
        # Extract key information
        task = input_data.get("task", "")
        requirements = input_data.get("requirements", {})
        cloud_provider = input_data.get("cloud_provider", "aws").lower()
        module_type = input_data.get("module_type", "compute").lower()
        module_name = input_data.get("module_name", f"terraform-{cloud_provider}-{module_type}")
        
        # First, think about the task
        thoughts = await self.think(input_data)
        
        # Generate the module files
        module_files, metadata = await self._generate_terraform_module(
            task, 
            requirements, 
            cloud_provider, 
            module_type,
            module_name
        )
        
        # Store in memory
        await self.update_memory({
            "type": "terraform_module_generation",
            "input": input_data,
            "output": {
                "module_files": module_files,
                "metadata": metadata
            },
            "timestamp": self.last_active_time
        })
        
        self.update_state("idle")
        return {
            "task_id": input_data.get("task_id", ""),
            "module_files": module_files,
            "metadata": metadata,
            "thoughts": thoughts.get("thoughts", ""),
            "module_type": module_type,
            "cloud_provider": cloud_provider,
            "module_name": module_name
        }
    
    async def _generate_terraform_module(
        self, 
        task: str, 
        requirements: Dict[str, Any],
        cloud_provider: str,
        module_type: str,
        module_name: str
    ) -> Tuple[Dict[str, str], Dict[str, Any]]:
        """Generate Terraform module files based on requirements."""
        self.logger.info(f"Generating Terraform module for {cloud_provider}/{module_type}")
        
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
                
                self.logger.info(f"Found {len(similar_patterns)} similar patterns")
            except Exception as e:
                self.logger.error(f"Error searching for patterns: {str(e)}")
        
        # Also search for similar previous generations from memory
        similar_generations = []
        try:
            memory_items = await self.get_memory_items(
                memory_type="terraform_module_generation",
                n_results=3
            )
            
            for item in memory_items:
                if (
                    item.get("input", {}).get("cloud_provider") == cloud_provider and
                    item.get("input", {}).get("module_type") == module_type
                ):
                    similar_generations.append(item)
            
            self.logger.info(f"Found {len(similar_generations)} similar generations in memory")
        except Exception as e:
            self.logger.error(f"Error retrieving memory items: {str(e)}")
        
        # Prepare examples text from similar patterns and generations
        examples_text = ""
        if similar_patterns:
            examples_text += "Here are some similar patterns for reference:\n\n"
            for i, pattern in enumerate(similar_patterns):
                examples_text += f"Pattern {i+1}:\n{pattern.get('content', '')}\n\n"
        
        if similar_generations:
            examples_text += "Here are some similar previous generations for reference:\n\n"
            for i, gen in enumerate(similar_generations):
                examples_text += f"Generation {i+1}:\n{json.dumps(gen.get('output', {}).get('module_files', {}), indent=2)}\n\n"
        
        # Get relevant provider patterns
        provider_specific_patterns = self.provider_patterns.get(cloud_provider, {}).get(module_type, [])
        
        # Prepare the prompt for the LLM to generate main.tf
        main_tf_prompt = f"""
        As an expert in Terraform module development, generate a production-ready main.tf file for an enterprise-grade Terraform module with the following details:
        
        Task: {task}
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        Cloud Provider: {cloud_provider}
        Module Type: {module_type}
        Module Name: {module_name}
        
        This module should follow these enterprise patterns:
        {json.dumps(self.enterprise_patterns, indent=2)}
        
        For this {cloud_provider}/{module_type} module, consider these specific resources:
        {json.dumps(provider_specific_patterns, indent=2)}
        
        {examples_text}
        
        Generate ONLY the main.tf file content with proper resource definitions, locals, and any necessary data sources.
        Follow HashiCorp's Terraform style conventions and best practices for enterprise modules.
        Include appropriate error handling, conditional logic, and resource dependencies.
        """
        
        # Generate variables.tf
        variables_tf_prompt = f"""
        Generate a comprehensive variables.tf file for the {module_name} Terraform module with the following details:
        
        Task: {task}
        Cloud Provider: {cloud_provider}
        Module Type: {module_type}
        
        Include all necessary variables with:
        1. Clear descriptions
        2. Appropriate type constraints
        3. Validation rules where applicable
        4. Sensible default values
        5. Variable grouping with comments
        
        The variables should support all the resources and functionality described in the requirements:
        {json.dumps(requirements, indent=2)}
        
        Return ONLY the variables.tf file content.
        """
        
        # Generate outputs.tf
        outputs_tf_prompt = f"""
        Generate an outputs.tf file for the {module_name} Terraform module with the following details:
        
        Task: {task}
        Cloud Provider: {cloud_provider}
        Module Type: {module_type}
        
        Include all relevant outputs that would be useful for:
        1. Referencing the module's resources from other modules
        2. Integration with CI/CD pipelines
        3. Operational visibility
        
        Each output should have a clear description and be properly formatted.
        
        Return ONLY the outputs.tf file content.
        """
        
        # Generate versions.tf
        versions_tf_prompt = f"""
        Generate a versions.tf file for the {module_name} Terraform module with the following details:
        
        Cloud Provider: {cloud_provider}
        
        Include:
        1. Required Terraform version (use latest stable)
        2. Required providers with appropriate version constraints
        3. Any provider configuration needed
        
        Return ONLY the versions.tf file content.
        """
        
        # Generate README.md
        readme_prompt = f"""
        Generate a comprehensive README.md file for the {module_name} Terraform module with the following details:
        
        Task: {task}
        Cloud Provider: {cloud_provider}
        Module Type: {module_type}
        
        The README should include:
        1. Module overview and purpose
        2. Prerequisites
        3. Usage examples
        4. Input variables (table format)
        5. Outputs (table format)
        6. Requirements (Terraform version, providers)
        7. Resources created
        8. Best practices
        9. License information
        
        Make it professional, well-structured, and following Terraform Registry standards.
        
        Return ONLY the README.md file content.
        """
        
        # Generate example usage
        example_prompt = f"""
        Generate an example usage file (examples/complete/main.tf) for the {module_name} Terraform module with the following details:
        
        Task: {task}
        Cloud Provider: {cloud_provider}
        Module Type: {module_type}
        
        The example should:
        1. Show a complete, working example
        2. Include all required variables
        3. Demonstrate best practices
        4. Include helpful comments
        
        Return ONLY the example file content.
        """
        
        # Generate test file
        test_prompt = f"""
        Generate a basic Terraform test file (test/module_test.go) for the {module_name} Terraform module using Terratest.
        
        The test should:
        1. Validate that the module can be initialized and applied
        2. Check that key resources are created correctly
        3. Verify outputs match expected values
        
        Return ONLY the test file content.
        """
        
        # Generate all files using LLM
        main_tf = await self.llm_service.generate(main_tf_prompt)
        variables_tf = await self.llm_service.generate(variables_tf_prompt)
        outputs_tf = await self.llm_service.generate(outputs_tf_prompt)
        versions_tf = await self.llm_service.generate(versions_tf_prompt)
        readme_md = await self.llm_service.generate(readme_prompt)
        example_tf = await self.llm_service.generate(example_prompt)
        test_file = await self.llm_service.generate(test_prompt)
        
        # Compile all files into a dictionary
        module_files = {
            "main.tf": main_tf,
            "variables.tf": variables_tf,
            "outputs.tf": outputs_tf,
            "versions.tf": versions_tf,
            "README.md": readme_md,
            "examples/complete/main.tf": example_tf,
            "test/module_test.go": test_file
        }
        
        # Generate metadata
        metadata = {
            "module_name": module_name,
            "cloud_provider": cloud_provider,
            "module_type": module_type,
            "file_count": len(module_files),
            "generated_timestamp": self.last_active_time,
            "similar_patterns_used": len(similar_patterns),
            "similar_generations_used": len(similar_generations),
            "enterprise_grade_features": [
                "Input validation",
                "Comprehensive documentation",
                "Example usage",
                "Automated tests",
                "Version constraints",
                "Best practices compliance"
            ]
        }
        
        return module_files, metadata
    
    async def think(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Think about the task and generate thoughts on how to approach it.
        
        Args:
            input_data: The input data for the task
            
        Returns:
            Dictionary containing thoughts and analysis
        """
        task = input_data.get("task", "")
        requirements = input_data.get("requirements", {})
        cloud_provider = input_data.get("cloud_provider", "aws").lower()
        module_type = input_data.get("module_type", "compute").lower()
        
        prompt = f"""
        As an expert in Terraform module development, analyze this task and think about how to approach it:
        
        Task: {task}
        
        Requirements:
        {json.dumps(requirements, indent=2)}
        
        Cloud Provider: {cloud_provider}
        Module Type: {module_type}
        
        Think about:
        1. What are the key resources needed for this module?
        2. What are potential challenges or edge cases?
        3. How should the module be structured for maximum reusability?
        4. What enterprise patterns should be applied?
        5. What security considerations are important?
        6. How can this module be made cloud-agnostic if needed?
        
        Provide your detailed thoughts on how to approach this module development.
        """
        
        thoughts = await self.llm_service.generate(prompt)
        
        return {
            "thoughts": thoughts,
            "timestamp": self.last_active_time
        }
    
    async def document_module(self, module_files: Dict[str, str]) -> str:
        """
        Generate comprehensive documentation for a Terraform module.
        
        Args:
            module_files: Dictionary of module files
            
        Returns:
            Markdown documentation
        """
        # Extract module information from files
        main_tf = module_files.get("main.tf", "")
        variables_tf = module_files.get("variables.tf", "")
        outputs_tf = module_files.get("outputs.tf", "")
        
        prompt = f"""
        Generate comprehensive documentation for this Terraform module.
        
        Main.tf:
        ```hcl
        {main_tf}
        ```
        
        Variables.tf:
        ```hcl
        {variables_tf}
        ```
        
        Outputs.tf:
        ```hcl
        {outputs_tf}
        ```
        
        The documentation should include:
        1. Module overview and purpose
        2. Architecture diagram (described in text)
        3. Usage instructions
        4. Input variables (table format)
        5. Outputs (table format)
        6. Examples
        7. Best practices
        
        Return the documentation in Markdown format.
        """
        
        documentation = await self.llm_service.generate(prompt)
        return documentation 