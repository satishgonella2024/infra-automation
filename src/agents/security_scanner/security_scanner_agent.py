"""
Security Scanner Agent Module for Multi-Agent Infrastructure Automation System

This module defines the SecurityScannerAgent class that specializes in running
security scans using tools like Checkov and Trivy.
"""

import os
import json
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SecurityScannerAgent(BaseAgent):
    """
    Agent responsible for running security scans using various tools like
    Checkov for IaC scanning and Trivy for container/filesystem scanning.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new SecurityScannerAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "iac_security_scanning",
            "container_scanning",
            "filesystem_scanning",
            "vulnerability_assessment",
            "compliance_checking",
            "misconfig_detection",
            "scan_result_analysis"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="security_scanner_agent",
            description="Agent responsible for running security scans using Checkov and Trivy",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize scanner configurations
        self.checkov_path = config.get("checkov_path", "checkov")
        self.trivy_path = config.get("trivy_path", "trivy")
        
        # Define supported scan types and frameworks
        self.supported_scanners = {
            "checkov": {
                "supported_types": ["terraform", "cloudformation", "kubernetes", "dockerfile", "ansible"],
                "frameworks": ["cis_aws", "cis_azure", "cis_gcp", "cis_kubernetes"]
            },
            "trivy": {
                "supported_types": ["container", "filesystem", "git", "sbom"],
                "severity_levels": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            }
        }
        
        logger.info("Security Scanner agent initialized")
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a security scan request.
        
        Args:
            message: Dictionary containing the scan parameters
            
        Returns:
            Dictionary with scan results
        """
        self.update_state("processing")
        
        action = message.get("action", "")
        parameters = message.get("parameters", {})
        task_id = message.get("task_id", "")
        
        # First, think about the scan implications
        thoughts = await self.think({
            "task": f"Process security scan {action}",
            "parameters": parameters,
            "action": action
        })
        
        try:
            if action == "scan_iac":
                result = await self.scan_infrastructure_code(
                    code=parameters.get("code"),
                    iac_type=parameters.get("iac_type"),
                    framework=parameters.get("framework")
                )
            elif action == "scan_container":
                result = await self.scan_container(
                    image=parameters.get("image"),
                    severity=parameters.get("severity", ["HIGH", "CRITICAL"])
                )
            elif action == "scan_filesystem":
                result = await self.scan_filesystem(
                    path=parameters.get("path"),
                    scan_type=parameters.get("scan_type", "vuln")
                )
            else:
                raise ValueError(f"Unsupported scan action: {action}")
            
            # Store in memory
            await self.update_memory({
                "type": "security_scan",
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
            logger.error(f"Error during security scan: {str(e)}")
            self.update_state("error")
            return {
                "task_id": task_id,
                "action": action,
                "error": str(e),
                "thoughts": thoughts.get("thoughts", ""),
                "status": "error"
            }
    
    async def scan_infrastructure_code(
        self,
        code: str,
        iac_type: str,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scan infrastructure code using Checkov.
        
        Args:
            code: Infrastructure code to scan
            iac_type: Type of IaC (terraform, kubernetes, etc.)
            framework: Optional specific compliance framework to check
            
        Returns:
            Dictionary with scan results
        """
        # Validate inputs
        if not code or not iac_type:
            raise ValueError("Code and IaC type are required")
        
        # Create temporary file for the code
        temp_dir = "/tmp/security_scan"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_extension = {
            "terraform": "tf",
            "kubernetes": "yaml",
            "dockerfile": "Dockerfile",
            "cloudformation": "yaml",
            "ansible": "yml"
        }.get(iac_type.lower(), "txt")
        
        temp_file = os.path.join(temp_dir, f"scan_target.{file_extension}")
        with open(temp_file, "w") as f:
            f.write(code)
        
        try:
            # Prepare Checkov command
            cmd = [self.checkov_path, "-f", temp_file, "--output", "json"]
            if framework:
                cmd.extend(["--framework", framework])
            
            # Run Checkov
            result = subprocess.run(cmd, capture_output=True, text=True)
            scan_output = json.loads(result.stdout) if result.stdout else {}
            
            # Process and analyze results
            return await self._analyze_checkov_results(scan_output)
            
        finally:
            # Cleanup
            try:
                os.remove(temp_file)
            except:
                pass
    
    async def scan_container(
        self,
        image: str,
        severity: List[str] = ["HIGH", "CRITICAL"]
    ) -> Dict[str, Any]:
        """
        Scan a container image using Trivy.
        
        Args:
            image: Container image to scan
            severity: List of severity levels to include
            
        Returns:
            Dictionary with scan results
        """
        # Validate inputs
        if not image:
            raise ValueError("Container image is required")
        
        # Prepare Trivy command
        cmd = [
            self.trivy_path,
            "image",
            "--format", "json",
            "--severity", ",".join(severity),
            image
        ]
        
        # Run Trivy
        result = subprocess.run(cmd, capture_output=True, text=True)
        scan_output = json.loads(result.stdout) if result.stdout else {}
        
        # Process and analyze results
        return await self._analyze_trivy_results(scan_output)
    
    async def scan_filesystem(
        self,
        path: str,
        scan_type: str = "vuln"
    ) -> Dict[str, Any]:
        """
        Scan a filesystem path using Trivy.
        
        Args:
            path: Path to scan
            scan_type: Type of scan (vuln, config, secret)
            
        Returns:
            Dictionary with scan results
        """
        # Validate inputs
        if not path:
            raise ValueError("Path is required")
        
        # Prepare Trivy command
        cmd = [
            self.trivy_path,
            "fs",
            "--format", "json",
            "--security-checks", scan_type,
            path
        ]
        
        # Run Trivy
        result = subprocess.run(cmd, capture_output=True, text=True)
        scan_output = json.loads(result.stdout) if result.stdout else {}
        
        # Process and analyze results
        return await self._analyze_trivy_results(scan_output)
    
    async def _analyze_checkov_results(self, scan_output: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and process Checkov scan results."""
        # Extract relevant information from scan output
        failed_checks = scan_output.get("results", {}).get("failed_checks", [])
        passed_checks = scan_output.get("results", {}).get("passed_checks", [])
        
        # Group findings by severity
        findings_by_severity = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for check in failed_checks:
            severity = check.get("severity", "").lower()
            if severity in findings_by_severity:
                findings_by_severity[severity].append({
                    "id": check.get("check_id"),
                    "name": check.get("check_name"),
                    "resource": check.get("resource"),
                    "guideline": check.get("guideline"),
                    "fixed_definition": check.get("fixed_definition")
                })
        
        # Generate summary
        summary = {
            "total_checks": len(failed_checks) + len(passed_checks),
            "failed_checks": len(failed_checks),
            "passed_checks": len(passed_checks),
            "pass_percentage": (len(passed_checks) / (len(failed_checks) + len(passed_checks))) * 100 if (len(failed_checks) + len(passed_checks)) > 0 else 0,
            "findings_by_severity": {
                severity: len(findings)
                for severity, findings in findings_by_severity.items()
            }
        }
        
        return {
            "summary": summary,
            "findings": findings_by_severity,
            "scan_type": "checkov",
            "raw_output": scan_output
        }
    
    async def _analyze_trivy_results(self, scan_output: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and process Trivy scan results."""
        # Extract vulnerabilities from scan output
        vulnerabilities = scan_output.get("Results", [])
        
        # Group findings by severity
        findings_by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        total_vulns = 0
        for result in vulnerabilities:
            for vuln in result.get("Vulnerabilities", []):
                severity = vuln.get("Severity", "UNKNOWN")
                if severity in findings_by_severity:
                    findings_by_severity[severity].append({
                        "id": vuln.get("VulnerabilityID"),
                        "package": vuln.get("PkgName"),
                        "installed_version": vuln.get("InstalledVersion"),
                        "fixed_version": vuln.get("FixedVersion"),
                        "title": vuln.get("Title"),
                        "description": vuln.get("Description")
                    })
                    total_vulns += 1
        
        # Generate summary
        summary = {
            "total_vulnerabilities": total_vulns,
            "findings_by_severity": {
                severity: len(findings)
                for severity, findings in findings_by_severity.items()
            }
        }
        
        return {
            "summary": summary,
            "findings": findings_by_severity,
            "scan_type": "trivy",
            "raw_output": scan_output
        } 