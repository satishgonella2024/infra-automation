"""
Cost Agent Module for Multi-Agent Infrastructure Automation System

This module defines the CostAgent class that specializes in analyzing and optimizing
infrastructure costs across different cloud providers.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

class CostAgent(BaseAgent):
    """
    Agent responsible for analyzing and optimizing infrastructure costs.
    Provides cost estimates, identifies savings opportunities, and suggests optimizations.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new CostAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "cost_analysis",
            "savings_identification",
            "resource_optimization",
            "budget_planning",
            "cost_forecasting"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="cost_agent",
            description="Agent responsible for analyzing and optimizing infrastructure costs",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize cost optimization patterns for different cloud providers
        self.cost_patterns = {
            "aws": {
                "compute": {
                    "right_sizing": ["t3.micro", "t3.small", "t3.medium"],
                    "spot_instances": True,
                    "reserved_instances": True,
                    "savings_plans": True
                },
                "storage": {
                    "s3_lifecycle": True,
                    "ebs_optimization": True,
                    "storage_classes": ["Standard", "Standard-IA", "One Zone-IA", "Glacier"]
                },
                "database": {
                    "instance_types": ["db.t3.micro", "db.t3.small", "db.t3.medium"],
                    "multi_az": False,
                    "read_replicas": False
                }
            },
            "azure": {
                "compute": {
                    "right_sizing": ["Standard_B1s", "Standard_B1ms", "Standard_B2s"],
                    "spot_instances": True,
                    "reserved_instances": True
                },
                "storage": {
                    "lifecycle_management": True,
                    "storage_tiers": ["Hot", "Cool", "Archive"]
                },
                "database": {
                    "instance_types": ["GP_Gen5_2", "GP_Gen5_4"],
                    "geo_replication": False
                }
            },
            "gcp": {
                "compute": {
                    "right_sizing": ["e2-micro", "e2-small", "e2-medium"],
                    "preemptible_instances": True,
                    "committed_use": True
                },
                "storage": {
                    "lifecycle_rules": True,
                    "storage_classes": ["Standard", "Nearline", "Coldline", "Archive"]
                },
                "database": {
                    "instance_types": ["db-f1-micro", "db-g1-small"],
                    "high_availability": False
                }
            }
        }
        
        logger.info("Cost optimization agent initialized")
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message to analyze and optimize infrastructure costs.
        
        Args:
            message: Dictionary containing "code", "cloud_provider", "iac_type", etc.
            
        Returns:
            Dictionary with cost analysis results and optimized code
        """
        self.update_state("processing")
        
        code = message.get("code", "")
        cloud_provider = message.get("cloud_provider", "aws").lower()
        iac_type = message.get("iac_type", "terraform").lower()
        task_id = message.get("task_id", "")
        
        # First, think about cost implications
        thoughts = await self.think({
            "task": f"Analyze cost optimization opportunities in {iac_type} code for {cloud_provider}",
            "code": code[:500] + "..." if len(code) > 500 else code,  # Truncate for thinking
            "cloud_provider": cloud_provider,
            "iac_type": iac_type
        })
        
        # Perform cost analysis
        cost_analysis = await self.analyze_costs(
            code=code,
            cloud_provider=cloud_provider,
            iac_type=iac_type
        )
        
        # Generate optimized code
        optimized_code, optimization_summary = await self.optimize_costs(
            code=code,
            cost_analysis=cost_analysis,
            cloud_provider=cloud_provider,
            iac_type=iac_type
        )
        
        # Store in memory
        await self.update_memory({
            "type": "cost_analysis",
            "input": message,
            "output": {
                "cost_analysis": cost_analysis,
                "optimized_code": optimized_code,
                "optimization_summary": optimization_summary
            },
            "timestamp": self.last_active_time
        })
        
        self.update_state("idle")
        return {
            "task_id": task_id,
            "original_code": code,
            "optimized_code": optimized_code,
            "cost_analysis": cost_analysis,
            "optimization_summary": optimization_summary,
            "thoughts": thoughts.get("thoughts", ""),
            "cloud_provider": cloud_provider,
            "iac_type": iac_type
        }
    
    async def analyze_costs(
        self,
        code: str,
        cloud_provider: str,
        iac_type: str
    ) -> Dict[str, Any]:
        """
        Analyze infrastructure code for cost optimization opportunities.
        
        Args:
            code: The infrastructure code to analyze
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type
            
        Returns:
            Dictionary containing cost analysis results
        """
        logger.info(f"Analyzing {iac_type} code for {cloud_provider} cost optimization opportunities")
        
        # Prepare the prompt for the LLM
        try:
            template_name = f"cost_analysis_{iac_type}.j2"
            analysis_prompt = load_template(template_name).render(
                code=code,
                cloud_provider=cloud_provider,
                cost_patterns=self.cost_patterns[cloud_provider]
            )
        except Exception as e:
            logger.warning(f"Failed to load template {template_name}, using default: {str(e)}")
            # Default prompt if template loading fails
            analysis_prompt = f"""
            You are a cost optimization expert specializing in {cloud_provider} infrastructure.
            Analyze the following {iac_type} code for cost optimization opportunities.

            CODE TO ANALYZE:
            ```
            {code}
            ```

            Consider these aspects:
            1. Resource sizing and utilization
            2. Reserved/spot instance opportunities
            3. Storage optimization possibilities
            4. Networking cost optimizations
            5. Database configuration costs
            6. Auto-scaling efficiencies

            Return your analysis as a JSON object with these fields:
            - "current_estimated_cost": estimated monthly cost in USD
            - "potential_savings": estimated monthly savings in USD
            - "optimization_opportunities": array of objects with "category", "description", "potential_savings", "implementation_effort" (high/medium/low)
            - "resource_recommendations": array of objects with "resource_type", "current_config", "recommended_config", "savings"
            - "priority_optimizations": array of strings describing the most impactful optimizations to implement
            """
        
        try:
            analysis_result = await self.llm_service.generate_completion(analysis_prompt)
            return json.loads(analysis_result)
        except json.JSONDecodeError:
            logger.error("Failed to parse cost analysis result as JSON")
            return {
                "error": "Failed to parse analysis result",
                "raw_output": analysis_result
            }
        except Exception as e:
            logger.error(f"Error during cost analysis: {str(e)}")
            return {"error": str(e)}
    
    async def optimize_costs(
        self,
        code: str,
        cost_analysis: Dict[str, Any],
        cloud_provider: str,
        iac_type: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Optimize infrastructure code for cost efficiency.
        
        Args:
            code: The infrastructure code to optimize
            cost_analysis: Results from the cost analysis
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type
            
        Returns:
            Tuple containing:
                - Optimized infrastructure code
                - Optimization summary
        """
        logger.info(f"Optimizing {iac_type} code for {cloud_provider} cost efficiency")
        
        # Prepare the prompt for the LLM
        try:
            template_name = f"cost_optimize_{iac_type}.j2"
            optimization_prompt = load_template(template_name).render(
                code=code,
                cost_analysis=cost_analysis,
                cloud_provider=cloud_provider,
                cost_patterns=self.cost_patterns[cloud_provider]
            )
        except Exception as e:
            logger.warning(f"Failed to load template {template_name}, using default: {str(e)}")
            # Default prompt if template loading fails
            optimization_prompt = f"""
            You are a cost optimization expert specializing in {cloud_provider} infrastructure.
            Optimize the following {iac_type} code based on the cost analysis results.

            ORIGINAL CODE:
            ```
            {code}
            ```

            COST ANALYSIS RESULTS:
            {json.dumps(cost_analysis, indent=2)}

            Generate an optimized version of the code that implements the recommended cost optimizations.
            Focus on the highest impact changes while maintaining the infrastructure's functionality.
            Add comments explaining the cost optimization changes made.

            Return ONLY the optimized code without any explanations, wrapped in triple backticks.
            """
        
        try:
            # Generate optimized code
            optimized_code_result = await self.llm_service.generate_completion(optimization_prompt)
            
            # Extract code from the response
            import re
            code_pattern = r'```(?:\w+)?\s*([\s\S]*?)\s*```'
            code_matches = re.findall(code_pattern, optimized_code_result)
            optimized_code = code_matches[0].strip() if code_matches else optimized_code_result.strip()
            
            # Prepare optimization summary
            optimization_summary = {
                "original_cost": cost_analysis.get("current_estimated_cost", 0),
                "optimized_cost": cost_analysis.get("current_estimated_cost", 0) - cost_analysis.get("potential_savings", 0),
                "total_savings": cost_analysis.get("potential_savings", 0),
                "implemented_optimizations": cost_analysis.get("priority_optimizations", []),
                "optimization_details": cost_analysis.get("optimization_opportunities", [])
            }
            
            return optimized_code, optimization_summary
            
        except Exception as e:
            logger.error(f"Error during cost optimization: {str(e)}")
            return code, {"error": str(e)}
    
    async def forecast_costs(
        self,
        code: str,
        cloud_provider: str,
        iac_type: str,
        forecast_months: int = 12
    ) -> Dict[str, Any]:
        """
        Generate a cost forecast for the infrastructure.
        
        Args:
            code: The infrastructure code to analyze
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type
            forecast_months: Number of months to forecast
            
        Returns:
            Cost forecast results
        """
        logger.info(f"Generating {forecast_months}-month cost forecast for {cloud_provider} using {iac_type}")
        
        # Prepare the prompt for the LLM
        prompt = f"""
        You are a cost forecasting expert specializing in {cloud_provider} infrastructure.
        Generate a {forecast_months}-month cost forecast for the following {iac_type} code.

        CODE TO ANALYZE:
        ```
        {code}
        ```

        Consider:
        1. Resource usage patterns and growth
        2. Seasonal variations
        3. Reserved instance/savings plans benefits
        4. Potential cost increases
        5. Industry trends

        Return your forecast as a JSON object with these fields:
        - "monthly_forecasts": array of objects with "month", "estimated_cost", "confidence_level"
        - "total_forecasted_cost": total cost over the forecast period
        - "cost_drivers": array of major factors influencing the forecast
        - "assumptions": array of assumptions made in the forecast
        - "recommendations": array of actions to manage forecasted costs
        """
        
        try:
            forecast_result = await self.llm_service.generate_completion(prompt)
            return json.loads(forecast_result)
        except json.JSONDecodeError:
            logger.error("Failed to parse cost forecast result as JSON")
            return {
                "error": "Failed to parse forecast result",
                "raw_output": forecast_result
            }
        except Exception as e:
            logger.error(f"Error during cost forecasting: {str(e)}")
            return {"error": str(e)} 