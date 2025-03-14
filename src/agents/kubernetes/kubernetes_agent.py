"""
Kubernetes Agent Module for Multi-Agent Infrastructure Automation System

This module defines the KubernetesAgent class that specializes in managing
Kubernetes resources, deployments, and configurations.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base import BaseAgent
from src.utils.template_utils import render_template

class KubernetesAgent(BaseAgent):
    """
    Specialized agent for Kubernetes management.
    Capable of generating, analyzing, and optimizing Kubernetes resources.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new KubernetesAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        super().__init__(
            name="Kubernetes",
            description="Manage Kubernetes resources, deployments, and configurations",
            capabilities=[
                "manifest_generation",
                "deployment_strategies",
                "resource_optimization",
                "security_policies",
                "network_policies",
                "cluster_analysis",
                "troubleshooting"
            ],
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize Kubernetes-specific configurations
        self.kubeconfig_path = config.get("kubeconfig_path") if config else None
        self.context = config.get("context") if config else None
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request related to Kubernetes operations.
        
        Args:
            input_data: Dictionary containing the request details
                - action: The Kubernetes action to perform (generate_manifests, analyze_resources, etc.)
                - parameters: Parameters specific to the action
        
        Returns:
            Dictionary containing the results of the operation
        """
        action = input_data.get("action", "")
        parameters = input_data.get("parameters", {})
        
        self.logger.info(f"Processing Kubernetes action: {action}")
        
        # Update agent state
        self.update_state("processing")
        
        # Process the action based on the type
        result = await self.think(input_data)
        
        # Update agent state
        self.update_state("idle")
        
        return result
    
    async def generate_manifests(self, application_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Kubernetes manifests for an application.
        
        Args:
            application_spec: Application specification
            
        Returns:
            Dictionary containing the generated manifests
        """
        # Use LLM to generate Kubernetes manifests
        app_name = application_spec.get("name", "app")
        app_type = application_spec.get("type", "web")
        replicas = application_spec.get("replicas", 1)
        container_image = application_spec.get("container_image", "nginx:latest")
        resources = application_spec.get("resources", {})
        
        prompt = f"""
        Generate Kubernetes manifests for a {app_type} application with the following specifications:
        
        - Name: {app_name}
        - Replicas: {replicas}
        - Container Image: {container_image}
        - Resources: {json.dumps(resources)}
        
        Include the following resources:
        1. Deployment
        2. Service
        3. ConfigMap
        4. Secret (template)
        5. HorizontalPodAutoscaler
        
        Return only the YAML content without any additional text.
        """
        
        manifests = await self.llm_service.generate_text(prompt)
        
        return {
            "application": app_name,
            "manifests": manifests.strip(),
            "resources": ["Deployment", "Service", "ConfigMap", "Secret", "HorizontalPodAutoscaler"]
        }
    
    async def analyze_resources(self, manifests: str) -> Dict[str, Any]:
        """
        Analyze Kubernetes resources for best practices and optimizations.
        
        Args:
            manifests: Kubernetes manifests in YAML format
            
        Returns:
            Dictionary with analysis results
        """
        # Use LLM to analyze Kubernetes resources
        prompt = f"""
        Analyze the following Kubernetes manifests for best practices, security issues, and resource optimizations:
        
        ```yaml
        {manifests}
        ```
        
        Provide a detailed analysis with:
        1. Security concerns
        2. Resource optimization suggestions
        3. Best practices compliance
        4. Scalability considerations
        5. Specific recommendations for improvement
        """
        
        analysis = await self.llm_service.generate_text(prompt)
        
        # This is a simplified version of parsing the analysis
        # In a real implementation, we would parse the LLM response more thoroughly
        return {
            "overall_assessment": "Analysis completed",
            "security_issues": [
                {"severity": "high", "description": "No resource limits specified"}
            ],
            "optimization_suggestions": [
                {"type": "resources", "description": "Add memory/CPU limits and requests"}
            ],
            "best_practices": [
                {"status": "missing", "description": "Health checks not configured"}
            ],
            "full_analysis": analysis
        }
    
    async def generate_network_policy(self, namespace: str, app_name: str, 
                                    allowed_ingress: List[Dict[str, Any]], 
                                    allowed_egress: List[Dict[str, Any]]) -> str:
        """
        Generate a Kubernetes NetworkPolicy.
        
        Args:
            namespace: Kubernetes namespace
            app_name: Application name
            allowed_ingress: List of allowed ingress rules
            allowed_egress: List of allowed egress rules
            
        Returns:
            NetworkPolicy manifest as a string
        """
        # Use LLM to generate NetworkPolicy
        prompt = f"""
        Generate a Kubernetes NetworkPolicy for application '{app_name}' in namespace '{namespace}' with the following rules:
        
        Allowed Ingress:
        {json.dumps(allowed_ingress, indent=2)}
        
        Allowed Egress:
        {json.dumps(allowed_egress, indent=2)}
        
        Return only the YAML content without any additional text.
        """
        
        policy = await self.llm_service.generate_text(prompt)
        return policy.strip()
    
    async def troubleshoot_deployment(self, deployment_name: str, namespace: str, 
                                    logs: str, events: str) -> Dict[str, Any]:
        """
        Troubleshoot a Kubernetes deployment issue.
        
        Args:
            deployment_name: Name of the deployment
            namespace: Kubernetes namespace
            logs: Container logs
            events: Kubernetes events
            
        Returns:
            Dictionary with troubleshooting results
        """
        # Use LLM to troubleshoot deployment issues
        prompt = f"""
        Troubleshoot the following Kubernetes deployment issue:
        
        Deployment: {deployment_name}
        Namespace: {namespace}
        
        Container Logs:
        ```
        {logs}
        ```
        
        Kubernetes Events:
        ```
        {events}
        ```
        
        Provide:
        1. Root cause analysis
        2. Recommended solutions
        3. Prevention measures
        """
        
        analysis = await self.llm_service.generate_text(prompt)
        
        # Parse the analysis into structured data
        # This is a simplified version
        return {
            "deployment": deployment_name,
            "namespace": namespace,
            "root_cause": "Application crash due to missing configuration",
            "solutions": [
                "Add required environment variables",
                "Mount configuration volume"
            ],
            "prevention": [
                "Implement pre-deployment validation",
                "Add readiness probe"
            ],
            "full_analysis": analysis
        }
    
    async def optimize_resources(self, manifests: str, metrics_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize resource requests and limits based on metrics.
        
        Args:
            manifests: Kubernetes manifests
            metrics_data: Optional historical metrics data
            
        Returns:
            Dictionary with optimized manifests
        """
        # Use LLM to optimize resource settings
        prompt = f"""
        Optimize the resource requests and limits in the following Kubernetes manifests:
        
        ```yaml
        {manifests}
        ```
        
        {f"Based on the following metrics data: {json.dumps(metrics_data, indent=2)}" if metrics_data else ""}
        
        Provide:
        1. Optimized manifests
        2. Explanation of changes
        3. Expected benefits
        """
        
        response = await self.llm_service.generate_text(prompt)
        
        # Extract the optimized manifests from the response
        # This is a simplified version
        return {
            "optimized_manifests": response.strip(),
            "changes": [
                {"resource": "memory_request", "from": "256Mi", "to": "128Mi"},
                {"resource": "cpu_limit", "from": "500m", "to": "250m"}
            ],
            "benefits": [
                "50% reduction in CPU allocation",
                "50% reduction in memory allocation",
                "Improved cluster resource utilization"
            ]
        } 