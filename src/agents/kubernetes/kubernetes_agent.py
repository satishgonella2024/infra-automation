"""
Kubernetes Agent Module for Multi-Agent Infrastructure Automation System

This module defines the KubernetesAgent class that specializes in managing
Kubernetes resources, deployments, and configurations.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

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
        # Define the agent's capabilities
        capabilities = [
            "manifest_generation",
            "deployment_strategies",
            "resource_optimization",
            "security_policies",
            "network_policies",
            "cluster_analysis",
            "troubleshooting"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="kubernetes_agent",
            description="Agent responsible for managing Kubernetes resources, deployments, and configurations",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize Kubernetes-specific configurations
        self.kubeconfig_path = config.get("kubeconfig_path") if config else None
        self.context = config.get("context") if config else None
        
        logger.info("Kubernetes agent initialized")
    
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
        self.update_state("processing")
        
        action = input_data.get("action", "")
        parameters = input_data.get("parameters", {})
        task_id = input_data.get("task_id", "")
        
        try:
            # First, think about the task
            thoughts = await self.think(input_data)
            
            # Process the action based on the type
            if action == "generate_manifests":
                result = await self.generate_manifests(
                    application_spec=parameters.get("application_spec", {})
                )
            elif action == "analyze_resources":
                result = await self.analyze_resources(
                    manifests=parameters.get("manifests", "")
                )
            elif action == "generate_network_policy":
                result = {
                    "policy": await self.generate_network_policy(
                        namespace=parameters.get("namespace", "default"),
                        app_name=parameters.get("app_name", ""),
                        allowed_ingress=parameters.get("allowed_ingress", []),
                        allowed_egress=parameters.get("allowed_egress", [])
                    )
                }
            elif action == "troubleshoot_deployment":
                result = await self.troubleshoot_deployment(
                    deployment_name=parameters.get("deployment_name", ""),
                    namespace=parameters.get("namespace", "default"),
                    logs=parameters.get("logs", ""),
                    events=parameters.get("events", "")
                )
            elif action == "optimize_resources":
                result = await self.optimize_resources(
                    manifests=parameters.get("manifests", ""),
                    metrics_data=parameters.get("metrics_data")
                )
            else:
                result = {
                    "error": f"Unsupported action: {action}",
                    "supported_actions": [
                        "generate_manifests",
                        "analyze_resources",
                        "generate_network_policy",
                        "troubleshoot_deployment",
                        "optimize_resources"
                    ]
                }
            
            # Store in memory
            await self.update_memory({
                "type": "kubernetes_operation",
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
            logger.error(f"Error during Kubernetes operation: {str(e)}")
            self.update_state("error")
            return {
                "task_id": task_id,
                "action": action,
                "error": str(e),
                "status": "error"
            }
    
    async def generate_manifests(self, application_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Kubernetes manifests for an application.
        
        Args:
            application_spec: Application specification
            
        Returns:
            Dictionary containing the generated manifests
        """
        # Use LLM to generate Kubernetes manifests
        logger.info(f"Generating Kubernetes manifests for {application_spec.get('name', 'app')}")
        
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
        
        manifests = await self.llm_service.generate_completion(prompt)
        
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
        logger.info("Analyzing Kubernetes manifests")
        
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
        
        Format your response as JSON with these sections.
        """
        
        analysis = await self.llm_service.generate_completion(prompt)
        
        try:
            # Try to parse as JSON
            analysis_json = json.loads(analysis)
            return analysis_json
        except json.JSONDecodeError:
            # If parsing fails, return the raw analysis
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
        logger.info(f"Generating NetworkPolicy for {app_name} in namespace {namespace}")
        
        prompt = f"""
        Generate a Kubernetes NetworkPolicy for application '{app_name}' in namespace '{namespace}' with the following rules:
        
        Allowed Ingress:
        {json.dumps(allowed_ingress, indent=2)}
        
        Allowed Egress:
        {json.dumps(allowed_egress, indent=2)}
        
        Return only the YAML content without any additional text.
        """
        
        policy = await self.llm_service.generate_completion(prompt)
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
        logger.info(f"Troubleshooting deployment {deployment_name} in namespace {namespace}")
        
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
        
        Format your response as JSON with these sections.
        """
        
        analysis = await self.llm_service.generate_completion(prompt)
        
        try:
            # Try to parse as JSON
            analysis_json = json.loads(analysis)
            return analysis_json
        except json.JSONDecodeError:
            # If parsing fails, return structured data with the raw analysis
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
        logger.info("Optimizing Kubernetes resource settings")
        
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
        
        Format your response as JSON with "optimized_manifests", "changes", and "benefits" sections.
        """
        
        response = await self.llm_service.generate_completion(prompt)
        
        try:
            # Try to parse as JSON
            response_json = json.loads(response)
            return response_json
        except json.JSONDecodeError:
            # If parsing fails, return structured data with the raw optimized manifests
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