"""
Main Module for Multi-Agent Infrastructure Automation System

This is the entry point for the entire system. It sets up the agents,
services, and starts the API server.
"""

import os
import sys
import yaml
import logging
import argparse
import asyncio
from typing import Dict, Any

# Import our components
from src.services.llm.llm_service import LLMService
from src.agents.infra import InfrastructureAgent
from src.api.server import app, run_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('infra_automation.log')
    ]
)

logger = logging.getLogger("main")

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {str(e)}")
        return {}

async def setup_system(config: Dict[str, Any]):
    """Set up the system components based on configuration."""
    logger.info("Setting up multi-agent infrastructure automation system...")
    
    # Extract LLM configuration, prioritizing environment variables
    llm_config = config.get("llm", {})
    llm_provider = os.environ.get("LLM_PROVIDER") or llm_config.get("provider", "ollama")
    llm_model = os.environ.get("LLM_MODEL") or llm_config.get("model", "llama2")
    llm_api_base = os.environ.get("LLM_API_BASE") or llm_config.get("api_base", "http://localhost:11434/api")
    llm_api_key = os.environ.get("LLM_API_KEY") or llm_config.get("api_key")
    
    # Log the actual configuration being used
    logger.info(f"Using LLM configuration - provider: {llm_provider}, model: {llm_model}, api_base: {llm_api_base}")
    
    # Create LLM service
    logger.info(f"Initializing LLM service with provider: {llm_provider}, model: {llm_model}")
    llm_service = LLMService(
        provider=llm_provider,
        model=llm_model,
        api_base=llm_api_base,
        api_key=llm_api_key,
        config=llm_config
    )
    
    # Create agents
    logger.info("Initializing agents...")
    infrastructure_agent = InfrastructureAgent(
        llm_service=llm_service,
        config=config.get("infrastructure", {})
    )
    
    # In a real implementation, we would also initialize other agents here:
    # - SecurityAgent
    # - ArchitectAgent
    # - MonitoringAgent
    # etc.
    
    logger.info("System setup complete!")
    
    return {
        "llm_service": llm_service,
        "infrastructure_agent": infrastructure_agent
    }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Multi-Agent Infrastructure Automation System")
    parser.add_argument(
        "--config", 
        type=str, 
        default="configs/config.yaml",
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["api", "cli"],
        default="api",
        help="Run mode (api server or cli)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for API server"
    )
    return parser.parse_args()

async def cli_mode(components):
    """Run the system in CLI mode for testing."""
    logger.info("Starting CLI mode...")
    
    infra_agent = components["infrastructure_agent"]
    
    # Simple CLI loop for testing
    print("\nWelcome to Multi-Agent Infrastructure Automation System CLI")
    print("Type 'exit' to quit")
    
    while True:
        command = input("\nEnter command (generate, analyze, cost, exit): ").strip().lower()
        
        if command == "exit":
            break
        
        if command == "generate":
            task = input("Enter infrastructure task description: ")
            cloud = input("Cloud provider (aws, azure, gcp) [aws]: ") or "aws"
            iac_type = input("IaC type (terraform, ansible, jenkins) [terraform]: ") or "terraform"
            
            print("\nProcessing request...")
            result = await infra_agent.process({
                "task_id": "cli-test",
                "task": task,
                "requirements": {},
                "cloud_provider": cloud,
                "iac_type": iac_type
            })
            
            print("\n--- Generated Code ---\n")
            print(result["code"])
            print("\n--- Metadata ---\n")
            print(result["metadata"])
        
        elif command == "analyze":
            code = input("Enter or paste infrastructure code (end with 'EOF' on a new line):\n")
            lines = []
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            
            code = "\n".join(lines)
            iac_type = input("IaC type (terraform, ansible, jenkins) [terraform]: ") or "terraform"
            
            print("\nAnalyzing code...")
            analysis = await infra_agent.analyze_infrastructure(code, iac_type)
            
            print("\n--- Analysis Results ---\n")
            print(analysis)
        
        elif command == "cost":
            code = input("Enter or paste infrastructure code (end with 'EOF' on a new line):\n")
            lines = []
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            
            code = "\n".join(lines)
            iac_type = input("IaC type (terraform, ansible, jenkins) [terraform]: ") or "terraform"
            cloud = input("Cloud provider (aws, azure, gcp) [aws]: ") or "aws"
            
            print("\nEstimating costs...")
            costs = await infra_agent.estimate_costs(code, iac_type, cloud)
            
            print("\n--- Cost Estimation ---\n")
            print(costs)
        
        else:
            print(f"Unknown command: {command}")

async def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up the system
    components = await setup_system(config)
    
    # Run in the appropriate mode
    if args.mode == "api":
        # Start the API server
        logger.info(f"Starting API server on port {args.port}...")
        run_server()
    elif args.mode == "cli":
        # Run CLI mode for testing
        await cli_mode(components)

if __name__ == "__main__":
    asyncio.run(main())