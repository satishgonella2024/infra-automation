import logging
from typing import Dict, Any, List, Tuple

from src.agents.base.base_agent import BaseAgent
from src.services.llm.llm_service import LLMService
from src.utils.template_utils import load_template

logger = logging.getLogger(__name__)

class ArchitectureAgent(BaseAgent):
    """
    Agent responsible for reviewing and improving infrastructure architecture.
    Applies best practices from cloud provider well-architected frameworks.
    """
    
    def __init__(self, llm_service: LLMService, vector_db_service=None, config: Dict[str, Any] = None):
        # Define the agent's capabilities
        capabilities = [
            "architecture_review",
            "best_practices_application",
            "security_assessment",
            "cost_optimization",
            "performance_improvement"
        ]
        
        # Call the parent class constructor with all required parameters
        super().__init__(
            name="architecture_agent",
            description="Agent responsible for reviewing and improving infrastructure architecture based on cloud provider well-architected frameworks",
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config
        )
        
        logger.info("Architecture agent initialized")
        
    async def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message to review architecture.
        
        Args:
            message: Dictionary containing "code", "cloud_provider", etc.
            
        Returns:
            Dictionary with review results and improved code
        """
        code = message.get("code", "")
        cloud_provider = message.get("cloud_provider", "aws")
        iac_type = message.get("iac_type", "terraform")
        requirements = message.get("requirements", "")
        task = message.get("task", "")
        
        # If code is empty and requirements are provided, generate infrastructure code
        if not code and requirements:
            logger.info(f"Generating {iac_type} infrastructure for {cloud_provider} based on requirements")
            
            # Generate infrastructure code using LLM
            prompt = f"""
            You are an expert cloud architect specializing in {cloud_provider} infrastructure.
            Generate {iac_type} code for the following requirements:
            
            TASK: {task}
            REQUIREMENTS: {requirements}
            
            The code should follow best practices for {cloud_provider} and be production-ready.
            Return ONLY the {iac_type} code without any explanations, wrapped in triple backticks.
            """
            
            try:
                generated_code = await self.llm_service.generate_completion(prompt)
                code = self._extract_code_from_text(generated_code)
                
                # Now review the generated code
                improved_code, findings = await self.review_architecture(code, cloud_provider, iac_type)
                
                return {
                    "task_id": message.get("task_id"),
                    "original_code": code,
                    "improved_code": improved_code,
                    "findings": findings,
                    "cloud_provider": cloud_provider,
                    "iac_type": iac_type
                }
            except Exception as e:
                logger.error(f"Error generating infrastructure: {e}")
                return {
                    "task_id": message.get("task_id"),
                    "original_code": "",
                    "improved_code": "",
                    "findings": {"error": str(e)},
                    "cloud_provider": cloud_provider,
                    "iac_type": iac_type
                }
        
        # Otherwise, review existing code
        improved_code, findings = await self.review_architecture(code, cloud_provider, iac_type)
        
        return {
            "task_id": message.get("task_id"),
            "original_code": code,
            "improved_code": improved_code,
            "findings": findings,
            "cloud_provider": cloud_provider,
            "iac_type": iac_type
        }
        
    async def review_architecture(self, code: str, cloud_provider: str, iac_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Review the generated infrastructure code and identify architectural improvements.
        
        Args:
            code: The infrastructure code to review
            cloud_provider: The cloud provider (aws, azure, gcp)
            iac_type: The infrastructure as code type (terraform, ansible, etc.)
            
        Returns:
            Tuple containing:
                - Improved infrastructure code
                - Dictionary of architectural findings and recommendations
        """
        logger.info(f"Reviewing {iac_type} architecture for {cloud_provider}")
        
        # Analyze architecture using LLM
        template_name = f"architecture_review_{iac_type}.j2"
        try:
            analysis_prompt = load_template(template_name).render(
                code=code,
                cloud_provider=cloud_provider
            )
        except Exception as e:
            logger.warning(f"Failed to load template {template_name}, falling back to default: {e}")
            analysis_prompt = f"""
            You are an expert cloud architect specializing in {cloud_provider} infrastructure.
            Review the following {iac_type} code and identify architectural issues, areas for improvement,
            and best practices that should be applied according to the {cloud_provider} Well-Architected Framework.

            CODE TO REVIEW:
            ```
            {code}
            ```

            Analyze this code for:
            1. Reliability issues
            2. Security concerns
            3. Cost optimization opportunities
            4. Performance improvements
            5. Operational excellence enhancements

            Provide your analysis in JSON format with these keys:
            "reliability", "security", "cost_optimization", "performance", "operational_excellence", 
            "critical_issues", "recommendations"

            Each key should contain an array of findings or recommendations.
            """
        
        try:
            analysis_result = await self.llm_service.generate_completion(analysis_prompt)
            findings = self._parse_findings(analysis_result)
            
            # If no critical issues found, return original code with findings
            if not self._has_critical_issues(findings):
                logger.info("No critical architecture issues found")
                return code, findings
                
            # Generate improved code
            template_name = f"architecture_improve_{iac_type}.j2"
            try:
                improvement_prompt = load_template(template_name).render(
                    original_code=code,
                    findings=findings,
                    cloud_provider=cloud_provider
                )
            except Exception as e:
                logger.warning(f"Failed to load template {template_name}, falling back to default: {e}")
                improvement_prompt = f"""
                You are an expert cloud architect specializing in {cloud_provider} infrastructure.
                Improve the following {iac_type} code based on these architectural findings:

                ORIGINAL CODE:
                ```
                {code}
                ```

                ARCHITECTURAL FINDINGS:
                {self._format_findings_text(findings)}

                Rewrite the {iac_type} code to address these issues, particularly the critical ones.
                Focus on implementing the top recommendations while preserving the original functionality.

                Return ONLY the improved code without any explanations, wrapped in triple backticks.
                """
            
            logger.info("Generating improved infrastructure code")
            improved_code_response = await self.llm_service.generate_completion(improvement_prompt)
            improved_code = self._extract_code_from_text(improved_code_response)
            
            if not improved_code or improved_code.strip() == "":
                logger.warning("Failed to generate improved code, returning original")
                return code, findings
                
            logger.info("Generated improved infrastructure code")
            return improved_code, findings
            
        except Exception as e:
            logger.error(f"Error during architecture review: {e}")
            return code, {"error": str(e)}
    
    def _parse_findings(self, analysis_result: str) -> Dict[str, Any]:
        """Parse the LLM analysis result into structured findings"""
        # Try to parse as JSON first
        import json
        import re
        
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
            logger.warning("Failed to parse JSON findings, falling back to text parsing")
            
            findings = {
                "reliability": [],
                "security": [],
                "cost_optimization": [],
                "performance": [],
                "operational_excellence": [],
                "critical_issues": [],
                "recommendations": []
            }
            
            # Simple parsing logic for section headers and bullet points
            current_section = None
            for line in analysis_result.split('\n'):
                line = line.strip()
                
                # Check for section headers
                if line.startswith('##') or line.startswith('**'):
                    section_name = line.lstrip('#').lstrip('*').strip().lower()
                    section_name = section_name.replace(':', '').replace(' ', '_')
                    
                    if section_name in findings:
                        current_section = section_name
                    else:
                        current_section = None
                        
                # Check for bullet points
                elif current_section and (line.startswith('-') or line.startswith('*')):
                    item = line.lstrip('-').lstrip('*').strip()
                    if item and current_section in findings:
                        findings[current_section].append(item)
            
            return findings
    
    def _has_critical_issues(self, findings: Dict[str, Any]) -> bool:
        """Check if findings contain critical issues that require fixing"""
        return len(findings.get("critical_issues", [])) > 0
    
    def _format_findings_text(self, findings: Dict[str, Any]) -> str:
        """Format findings dictionary as text for prompts"""
        text = ""
        for category, issues in findings.items():
            if issues:
                text += f"{category.upper()}:\n"
                for issue in issues:
                    text += f"- {issue}\n"
                text += "\n"
        return text
        
    def _extract_code_from_text(self, text: str) -> str:
        """
        Extract code blocks from text, typically from LLM responses.
        
        Args:
            text: Text containing code blocks (typically within triple backticks)
            
        Returns:
            Extracted code
        """
        if not text:
            return ""
            
        # Try to extract code from markdown code blocks
        import re
        code_pattern = r'```(?:\w+)?\s*([\s\S]*?)\s*```'
        code_matches = re.findall(code_pattern, text)
        
        if code_matches:
            # Return the first code block found
            return code_matches[0].strip()
        
        # If no code blocks found, return the entire text
        # This handles cases where the LLM forgets to wrap code in backticks
        return text.strip()
