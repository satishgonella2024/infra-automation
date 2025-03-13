"""
Security Agent Module for Multi-Agent Infrastructure Automation System

This module defines the SecurityAgent class that specializes in identifying and remediating
security vulnerabilities in infrastructure code.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from src.agents.base.base_agent import BaseAgent
from src.utils.template_utils import load_template, extract_code_from_text

logger = logging.getLogger(__name__)

class SecurityAgent(BaseAgent):
    """
    Agent responsible for analyzing and improving infrastructure security.
    Applies security best practices and identifies vulnerabilities.
    """
    
    def __init__(
        self,
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new SecurityAgent.
        
        Args:
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        # Define the agent's capabilities
        capabilities = [
            "vulnerability_scanning",
            "compliance_checking",
            "security_remediation",
            "threat_modeling",
            "policy_enforcement"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="security_agent",
            description="Agent responsible for securing infrastructure and identifying vulnerabilities",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        # Initialize security frameworks and mappings
        self.security_frameworks = {
            "aws": ["CIS AWS Benchmark", "AWS Well-Architected Security Pillar"],
            "azure": ["CIS Azure Benchmark", "Azure Security Benchmark"],
            "gcp": ["CIS GCP Benchmark", "GCP Security Best Practices"]
        }
        
        # Common vulnerability patterns to check
        self.vulnerability_patterns = {
            "terraform": {
                "aws": {
                    "unencrypted_storage": r".*aws_s3_bucket.*server_side_encryption_configuration.*",
                    "public_access": r".*public_access.*true.*",
                    "default_security_group": r".*aws_default_security_group.*",
                    "admin_ports_open": r".*port.*[\"\'](22|3389)[\"\']\s*.*0\.0\.0\.0/0.*"
                },
                "azure": {
                    "unencrypted_storage": r".*azurerm_storage_account.*encryption.*",
                    "public_ip": r".*azurerm_public_ip.*",
                    "network_security_group": r".*azurerm_network_security_group.*"
                },
                "gcp": {
                    "public_bucket": r".*google_storage_bucket_acl.*predefined_acl.*public.*",
                    "default_network": r".*google_compute_network.*auto_create_subnetworks.*true.*",
                    "legacy_metadata": r".*google_compute_instance.*metadata.*"
                }
            }
        }
        
        logger.info("Security agent initialized")
    
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message to scan for security vulnerabilities and provide remediations.
        
        Args:
            message: Dictionary containing "code", "cloud_provider", "iac_type", etc.
            
        Returns:
            Dictionary with security analysis results and remediated code
        """
        self.update_state("processing")
        
        code = message.get("code", "")
        cloud_provider = message.get("cloud_provider", "aws").lower()
        iac_type = message.get("iac_type", "terraform").lower()
        task_id = message.get("task_id", "")
        compliance_framework = message.get("compliance_framework", None)
        
        # First, think about the security implications
        thoughts = await self.think({
            "task": f"Analyze security of {iac_type} code for {cloud_provider}",
            "code": code[:500] + "..." if len(code) > 500 else code,  # Truncate for thinking
            "cloud_provider": cloud_provider,
            "iac_type": iac_type,
            "compliance_framework": compliance_framework
        })
        
        # Then, perform a detailed security analysis
        vulnerabilities, compliance_results = await self.analyze_security(
            code=code,
            cloud_provider=cloud_provider,
            iac_type=iac_type,
            compliance_framework=compliance_framework
        )
        
        # Generate remediated code
        remediated_code, remediation_summary = await self.remediate_security_issues(
            code=code,
            vulnerabilities=vulnerabilities,
            cloud_provider=cloud_provider,
            iac_type=iac_type
        )
        
        # Store in memory
        await self.update_memory({
            "type": "security_analysis",
            "input": message,
            "output": {
                "vulnerabilities": vulnerabilities,
                "compliance_results": compliance_results,
                "remediated_code": remediated_code,
                "remediation_summary": remediation_summary
            },
            "timestamp": self.last_active_time
        })
        
        self.update_state("idle")
        return {
            "task_id": task_id,
            "original_code": code,
            "remediated_code": remediated_code,
            "vulnerabilities": vulnerabilities,
            "compliance_results": compliance_results,
            "remediation_summary": remediation_summary,
            "thoughts": thoughts.get("thoughts", ""),
            "cloud_provider": cloud_provider,
            "iac_type": iac_type
        }
    
    async def analyze_security(
        self, 
        code: str, 
        cloud_provider: str,
        iac_type: str,
        compliance_framework: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Analyze infrastructure code for security vulnerabilities and compliance.
        
        Args:
            code: The infrastructure code to analyze
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type (terraform, etc.)
            compliance_framework: Optional specific compliance framework to check
            
        Returns:
            Tuple containing:
                - List of identified vulnerabilities
                - Compliance results dictionary
        """
        logger.info(f"Analyzing {iac_type} code for {cloud_provider} security vulnerabilities")
        
        # Perform preliminary pattern-based vulnerability detection
        detected_vulnerabilities = self._detect_pattern_vulnerabilities(
            code=code,
            cloud_provider=cloud_provider,
            iac_type=iac_type
        )
        
        # Determine frameworks to check
        frameworks = []
        if compliance_framework:
            frameworks.append(compliance_framework)
        elif cloud_provider in self.security_frameworks:
            frameworks = self.security_frameworks[cloud_provider]
        
        # Prepare the prompt for the LLM
        try:
            # Try to load the template
            template_name = f"security_scan_{iac_type}.j2"
            analysis_prompt = load_template(template_name).render(
                code=code,
                cloud_provider=cloud_provider,
                frameworks=frameworks,
                detected_vulnerabilities=detected_vulnerabilities
            )
        except Exception as e:
            logger.warning(f"Failed to load template {template_name}, using default: {str(e)}")
            # Default prompt if template loading fails
            frameworks_str = ", ".join(frameworks)
            analysis_prompt = f"""
            You are a security expert specializing in cloud infrastructure.
            Analyze the following {iac_type} code for {cloud_provider} for security vulnerabilities
            and compliance with {frameworks_str}.

            CODE TO ANALYZE:
            ```
            {code}
            ```

            I've already detected these potential issues using pattern matching:
            {json.dumps(detected_vulnerabilities, indent=2)}

            Please perform a comprehensive security analysis and identify:
            1. Security vulnerabilities (including severity, description, and remediation steps)
            2. Compliance issues with relevant frameworks
            3. Best practices violations

            Focus on:
            - Identity and access management issues
            - Data protection concerns
            - Network security problems
            - Logging and monitoring gaps
            - Insecure configurations
            - Resource exposure risks

            Return your analysis as a JSON object with these fields:
            - "vulnerabilities": array of objects with "severity" (high/medium/low), "title", "description", "remediation"
            - "compliance_results": object with framework names as keys and arrays of compliance issues as values
            - "risk_score": number from 1-10 indicating overall security risk
            - "priority_remediation": array of strings describing the most critical issues to fix

            Be thorough but avoid false positives.
            """
        
        # Analyze using LLM
        try:
            analysis_result = await self.llm_service.generate_completion(analysis_prompt)
            security_analysis = self._parse_security_analysis(analysis_result)
            
            # Combine with pattern-detected vulnerabilities
            all_vulnerabilities = security_analysis.get("vulnerabilities", [])
            
            # Add pattern-detected vulnerabilities that aren't already in the LLM results
            existing_titles = {v.get("title", "") for v in all_vulnerabilities}
            for vuln in detected_vulnerabilities:
                if vuln.get("title", "") not in existing_titles:
                    all_vulnerabilities.append(vuln)
            
            # Sort vulnerabilities by severity (high, medium, low)
            sorted_vulnerabilities = sorted(
                all_vulnerabilities,
                key=lambda v: {"high": 0, "medium": 1, "low": 2}.get(v.get("severity", "").lower(), 3)
            )
            
            return sorted_vulnerabilities, security_analysis.get("compliance_results", {})
            
        except Exception as e:
            logger.error(f"Error during security analysis: {str(e)}")
            return detected_vulnerabilities, {"error": str(e)}
    
    async def remediate_security_issues(
        self,
        code: str,
        vulnerabilities: List[Dict[str, Any]],
        cloud_provider: str,
        iac_type: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate code with security issues remediated.
        
        Args:
            code: Original infrastructure code
            vulnerabilities: List of identified vulnerabilities
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type (terraform, etc.)
            
        Returns:
            Tuple containing:
                - Remediated code
                - Remediation summary
        """
        logger.info(f"Remediating security issues in {iac_type} code for {cloud_provider}")
        
        # Skip remediation if no vulnerabilities found
        if not vulnerabilities:
            logger.info("No vulnerabilities to remediate")
            return code, {
                "remediated_issues_count": 0,
                "summary": "No security issues found to remediate"
            }
        
        # Count critical vulnerabilities
        critical_count = sum(1 for v in vulnerabilities if v.get("severity", "").lower() == "high")
        
        # Prepare the prompt for the LLM
        try:
            # Try to load the template
            template_name = f"security_remediate_{iac_type}.j2"
            remediation_prompt = load_template(template_name).render(
                original_code=code,
                vulnerabilities=vulnerabilities,
                cloud_provider=cloud_provider
            )
        except Exception as e:
            logger.warning(f"Failed to load template {template_name}, using default: {str(e)}")
            # Default prompt if template loading fails
            remediation_prompt = f"""
            You are a security expert specializing in {cloud_provider} infrastructure security.
            
            I need you to remediate the following security vulnerabilities in this {iac_type} code:
            
            ORIGINAL CODE:
            ```
            {code}
            ```
            
            SECURITY VULNERABILITIES:
            {json.dumps(vulnerabilities, indent=2)}
            
            Please provide a fully remediated version of the code that fixes all the vulnerabilities.
            Follow these guidelines:
            1. Maintain the original functionality and structure
            2. Focus on fixing the high-severity issues first
            3. Add explanatory comments for significant changes
            4. Follow {cloud_provider} security best practices
            5. Make sure the code remains valid {iac_type} syntax
            
            Return ONLY the remediated code without any explanations, wrapped in triple backticks.
            """
        
        # Generate remediated code using LLM
        try:
            remediation_result = await self.llm_service.generate_completion(remediation_prompt)
            remediated_code = extract_code_from_text(remediation_result)
            
            # If no code was extracted or the extraction is very short, return the original
            if not remediated_code or len(remediated_code) < len(code) * 0.5:
                logger.warning("Remediation failed to produce valid code, returning original")
                return code, {
                    "remediated_issues_count": 0,
                    "summary": "Remediation failed to produce valid code"
                }
            
            # Generate a summary of changes
            remediation_summary = {
                "remediated_issues_count": len(vulnerabilities),
                "critical_issues_fixed": critical_count,
                "issues_by_severity": {
                    "high": sum(1 for v in vulnerabilities if v.get("severity", "").lower() == "high"),
                    "medium": sum(1 for v in vulnerabilities if v.get("severity", "").lower() == "medium"),
                    "low": sum(1 for v in vulnerabilities if v.get("severity", "").lower() == "low")
                },
                "summary": f"Fixed {len(vulnerabilities)} security issues ({critical_count} critical)"
            }
            
            return remediated_code, remediation_summary
            
        except Exception as e:
            logger.error(f"Error during security remediation: {str(e)}")
            return code, {"error": str(e)}
    
    def _detect_pattern_vulnerabilities(
        self,
        code: str,
        cloud_provider: str,
        iac_type: str
    ) -> List[Dict[str, Any]]:
        """
        Detect common vulnerabilities using regex pattern matching.
        
        Args:
            code: The infrastructure code to analyze
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type
            
        Returns:
            List of detected vulnerabilities
        """
        vulnerabilities = []
        
        # Check if we have patterns for this IaC type and cloud provider
        if (
            iac_type in self.vulnerability_patterns and
            cloud_provider in self.vulnerability_patterns[iac_type]
        ):
            patterns = self.vulnerability_patterns[iac_type][cloud_provider]
            
            # Check each pattern
            for vuln_type, pattern in patterns.items():
                # If the pattern is NOT found, it might be a vulnerability
                # (e.g., missing encryption)
                if vuln_type == "unencrypted_storage":
                    if not re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                        vulnerabilities.append({
                            "severity": "high",
                            "title": f"Unencrypted Storage for {cloud_provider}",
                            "description": f"Storage resources are not configured with encryption",
                            "remediation": "Enable server-side encryption for all storage resources"
                        })
                # If the pattern IS found, it might be a vulnerability
                # (e.g., public access allowed)
                elif vuln_type == "public_access" or vuln_type == "public_bucket":
                    if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                        vulnerabilities.append({
                            "severity": "high",
                            "title": "Public Access Enabled",
                            "description": f"Resources have public access enabled, which is a security risk",
                            "remediation": "Disable public access for all resources or restrict to specific IPs"
                        })
                elif vuln_type == "default_security_group" or vuln_type == "default_network":
                    if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                        vulnerabilities.append({
                            "severity": "medium",
                            "title": "Using Default Network/Security Groups",
                            "description": "Using default security groups or networks which often have overly permissive rules",
                            "remediation": "Create custom security groups with least privilege access"
                        })
                elif vuln_type == "admin_ports_open":
                    if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                        vulnerabilities.append({
                            "severity": "high",
                            "title": "Admin Ports Open to the Internet",
                            "description": "Administrative ports (SSH/RDP) are open to the world (0.0.0.0/0)",
                            "remediation": "Restrict access to admin ports to specific trusted IP ranges"
                        })
        
        return vulnerabilities
    
    def _parse_security_analysis(self, analysis_result: str) -> Dict[str, Any]:
        """Parse the LLM analysis result into structured security findings"""
        # Try to parse as JSON first
        try:
            # Try to extract JSON if wrapped in backticks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', analysis_result)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
                
            # Try direct JSON parsing
            return json.loads(analysis_result)
        except (json.JSONDecodeError, AttributeError):
            # If JSON parsing fails, fall back to structured text parsing
            logger.warning("Failed to parse JSON security analysis, falling back to text parsing")
            
            security_analysis = {
                "vulnerabilities": [],
                "compliance_results": {},
                "risk_score": 5,
                "priority_remediation": []
            }
            
            # Simple parsing logic for section headers and bullet points
            current_section = None
            current_vuln = None
            
            for line in analysis_result.split('\n'):
                line = line.strip()
                
                # Check for section headers
                if line.lower().startswith('vulnerabilities'):
                    current_section = "vulnerabilities"
                elif line.lower().startswith('compliance'):
                    current_section = "compliance_results"
                elif line.lower().startswith('risk score'):
                    try:
                        score_match = re.search(r'(\d+)', line)
                        if score_match:
                            security_analysis["risk_score"] = int(score_match.group(1))
                    except:
                        pass
                elif line.lower().startswith('priority'):
                    current_section = "priority_remediation"
                
                # Process vulnerabilities
                elif current_section == "vulnerabilities":
                    # Check for vulnerability severity
                    sev_match = re.search(r'^\[(high|medium|low)\]', line.lower())
                    if sev_match:
                        if current_vuln:
                            security_analysis["vulnerabilities"].append(current_vuln)
                        
                        title_match = re.search(r'^\[(high|medium|low)\]\s*(.+)$', line, re.IGNORECASE)
                        title = title_match.group(2) if title_match else "Unnamed vulnerability"
                        
                        current_vuln = {
                            "severity": sev_match.group(1).lower(),
                            "title": title,
                            "description": "",
                            "remediation": ""
                        }
                    elif current_vuln and line.lower().startswith("description"):
                        desc_match = re.search(r'^description[:\s]\s*(.+)$', line, re.IGNORECASE)
                        if desc_match:
                            current_vuln["description"] = desc_match.group(1)
                    elif current_vuln and line.lower().startswith("remediation"):
                        rem_match = re.search(r'^remediation[:\s]\s*(.+)$', line, re.IGNORECASE)
                        if rem_match:
                            current_vuln["remediation"] = rem_match.group(1)
                
                # Process compliance results
                elif current_section == "compliance_results":
                    framework_match = re.search(r'^([A-Za-z0-9\s\-]+):', line)
                    if framework_match:
                        framework = framework_match.group(1).strip()
                        security_analysis["compliance_results"][framework] = []
                    
                    issue_match = re.search(r'^\s*-\s*(.+)$', line)
                    if issue_match and framework:
                        security_analysis["compliance_results"][framework].append(issue_match.group(1))
                
                # Process priority remediation
                elif current_section == "priority_remediation":
                    issue_match = re.search(r'^\s*-\s*(.+)$', line)
                    if issue_match:
                        security_analysis["priority_remediation"].append(issue_match.group(1))
            
            # Add the last vulnerability if there is one
            if current_vuln:
                security_analysis["vulnerabilities"].append(current_vuln)
                
            return security_analysis
    
    async def check_compliance(
        self,
        code: str,
        framework: str,
        cloud_provider: str,
        iac_type: str
    ) -> Dict[str, Any]:
        """
        Check infrastructure code against a specific compliance framework.
        
        Args:
            code: The infrastructure code to check
            framework: The compliance framework to check against
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type
            
        Returns:
            Compliance check results
        """
        logger.info(f"Checking {iac_type} code for {cloud_provider} against {framework}")
        
        # Prepare the prompt for the LLM
        prompt = f"""
        You are a compliance expert specializing in cloud infrastructure.
        Check the following {iac_type} code for {cloud_provider} against the {framework} framework.

        CODE TO CHECK:
        ```
        {code}
        ```

        Please return a detailed compliance report including:
        1. Overall compliance score (percentage)
        2. Control findings (passing and failing)
        3. Remediation steps for failing controls
        4. Documentation gaps

        Format your response as a structured JSON object with these fields:
        - "compliance_score": percentage (0-100)
        - "passing_controls": array of control IDs that pass
        - "failing_controls": array of objects with "id", "description", "remediation"
        - "documentation_gaps": array of items that need documentation
        - "summary": text summary of compliance status
        """
        
        # Generate compliance check using LLM
        try:
            compliance_result = await self.llm_service.generate_completion(prompt)
            
            # Try to parse as JSON
            try:
                return json.loads(compliance_result)
            except json.JSONDecodeError:
                logger.warning("Failed to parse compliance result as JSON")
                return {
                    "error": "Failed to parse compliance result",
                    "raw_output": compliance_result
                }
            
        except Exception as e:
            logger.error(f"Error during compliance check: {str(e)}")
            return {"error": str(e)}
    
    async def scan_for_threats(
        self,
        code: str,
        cloud_provider: str,
        iac_type: str
    ) -> Dict[str, Any]:
        """
        Perform a threat modeling scan on infrastructure code.
        
        Args:
            code: The infrastructure code to scan
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type
            
        Returns:
            Threat model results
        """
        logger.info(f"Scanning {iac_type} code for {cloud_provider} for threats")
        
        # Prepare the prompt for the LLM
        prompt = f"""
        You are a security architect specializing in threat modeling.
        Analyze the following {iac_type} code for {cloud_provider} and identify potential threats.

        CODE TO ANALYZE:
        ```
        {code}
        ```

        Please perform a comprehensive threat modeling analysis using the STRIDE model:
        - Spoofing
        - Tampering
        - Repudiation
        - Information Disclosure
        - Denial of Service
        - Elevation of Privilege

        For each identified threat:
        1. Describe the threat scenario
        2. Assess the risk (likelihood and impact)
        3. Recommend mitigations

        Format your response as a structured JSON object with these fields:
        - "threats": array of objects with "category", "description", "likelihood", "impact", "risk_score", "mitigations"
        - "overall_risk": assessment of the overall risk level (low/medium/high)
        - "top_mitigations": array of the most important mitigations to implement
        """
        
        # Generate threat model using LLM
        try:
            threat_result = await self.llm_service.generate_completion(prompt)
            
            # Try to parse as JSON
            try:
                return json.loads(threat_result)
            except json.JSONDecodeError:
                logger.warning("Failed to parse threat model result as JSON")
                return {
                    "error": "Failed to parse threat model result",
                    "raw_output": threat_result
                }
            
        except Exception as e:
            logger.error(f"Error during threat modeling: {str(e)}")
            return {"error": str(e)}