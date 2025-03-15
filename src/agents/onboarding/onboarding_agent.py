import os
import json
import uuid
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.agents.base.base_agent import BaseAgent
from src.models.onboarding import EnvironmentConfig, ToolType, EnvironmentType
from src.models.workflow import WorkflowState
from src.models.deployment import DeploymentConfig, ResourceConfig, ResourceType, ServiceConfig, CloudProvider

logger = logging.getLogger(__name__)

class OnboardingAgent(BaseAgent):
    """
    Agent responsible for setting up complete development environments.
    
    This agent handles:
    1. Creating Docker Compose environments with all requested tools
    2. Configuring initial settings for each tool
    3. Setting up integrations between tools
    4. Managing credentials securely
    5. Providing access information
    """
    
    def __init__(self, llm_service, vector_db_service=None, config=None):
        name = "OnboardingAgent"
        description = "Agent responsible for setting up complete development environments"
        capabilities = [
            "environment_setup",
            "tool_configuration",
            "integration_setup",
            "credential_management",
            "access_management"
        ]
        
        super().__init__(
            name=name,
            description=description,
            capabilities=capabilities,
            llm_service=llm_service,
            vector_db_service=vector_db_service,
            config=config or {}
        )
        
        # Set up environment storage
        self.environments_dir = config.get("environments_dir", "/app/data/environments")
        os.makedirs(self.environments_dir, exist_ok=True)
        
        # Load existing environments
        self.environments = {}
        self._load_environments()
        
        # Load dashboard template
        self.dashboard_template = self._load_dashboard_template()
        
        # Check if we're running in host deployment mode
        self.host_deployment = os.environ.get("HOST_DEPLOYMENT", "false").lower() == "true"
        logger.info(f"Host deployment mode: {self.host_deployment}")
        
        # Tool descriptions and icons
        self.tool_info = {
            ToolType.JIRA: {
                "name": "Jira",
                "description": "Issue tracking and project management",
                "icon": "https://wac-cdn.atlassian.com/assets/img/favicons/atlassian/favicon.png"
            },
            ToolType.CONFLUENCE: {
                "name": "Confluence",
                "description": "Team collaboration and documentation",
                "icon": "https://wac-cdn.atlassian.com/assets/img/favicons/confluence/favicon.png"
            },
            ToolType.GITLAB: {
                "name": "GitLab",
                "description": "Git repository management and CI/CD",
                "icon": "https://about.gitlab.com/images/press/logo/png/gitlab-icon-rgb.png"
            },
            ToolType.JENKINS: {
                "name": "Jenkins",
                "description": "Continuous integration and delivery",
                "icon": "https://www.jenkins.io/images/logos/jenkins/jenkins.png"
            },
            ToolType.NEXUS: {
                "name": "Nexus",
                "description": "Repository manager for artifacts",
                "icon": "https://help.sonatype.com/docs/files/331022/34537964/3/1564671303641/NexusRepo_Icon.png"
            },
            ToolType.VAULT: {
                "name": "Vault",
                "description": "Secrets management",
                "icon": "https://www.hashicorp.com/img/logos/vault/vault-icon-on-white.svg"
            },
            ToolType.KUBERNETES: {
                "name": "Kubernetes",
                "description": "Container orchestration",
                "icon": "https://kubernetes.io/images/favicon.png"
            },
            ToolType.PROMETHEUS: {
                "name": "Prometheus",
                "description": "Monitoring and alerting",
                "icon": "https://prometheus.io/assets/favicon.png"
            },
            ToolType.GRAFANA: {
                "name": "Grafana",
                "description": "Metrics visualization and dashboards",
                "icon": "https://grafana.com/static/img/menu/grafana2.svg"
            }
        }
    
    def _load_dashboard_template(self) -> str:
        """Load the dashboard HTML template."""
        try:
            template_path = os.path.join(os.path.dirname(__file__), "dashboard_template.html")
            with open(template_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading dashboard template: {str(e)}")
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Environment Dashboard</title>
            </head>
            <body>
                <h1>Environment Dashboard</h1>
                <p>Environment: {{ENVIRONMENT_NAME}}</p>
                <p>Status: {{ENVIRONMENT_STATUS}}</p>
                <h2>Tools</h2>
                {{TOOL_CARDS}}
                <h2>Credentials</h2>
                {{CREDENTIALS_TABLE}}
            </body>
            </html>
            """
    
    def _load_environments(self):
        """Load existing environments from disk."""
        try:
            environments_file = os.path.join(self.environments_dir, "environments.json")
            if os.path.exists(environments_file):
                with open(environments_file, 'r') as f:
                    self.environments = json.load(f)
                logger.info(f"Loaded {len(self.environments)} environments")
            else:
                logger.info("No environments file found, starting with empty environments")
                self.environments = {}
        except Exception as e:
            logger.error(f"Error loading environments: {str(e)}")
            self.environments = {}
    
    def _save_environments(self):
        """Save environments to disk."""
        try:
            environments_file = os.path.join(self.environments_dir, "environments.json")
            with open(environments_file, 'w') as f:
                json.dump(self.environments, f, indent=2)
            logger.info(f"Saved {len(self.environments)} environments")
        except Exception as e:
            logger.error(f"Error saving environments: {str(e)}")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an onboarding request."""
        action = input_data.get("action", "create_environment")
        
        if action == "create_environment":
            return await self.create_environment(input_data)
        elif action == "get_environment":
            return self.get_environment(input_data.get("environment_id"))
        elif action == "list_environments":
            return self.list_environments(input_data.get("user_id"))
        elif action == "delete_environment":
            return await self.delete_environment(input_data.get("environment_id"))
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }
    
    async def create_environment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new environment with the requested tools."""
        environment_id = str(uuid.uuid4())
        
        # Create environment config
        environment_config = EnvironmentConfig(
            environment_id=environment_id,
            environment_name=input_data.get("environment_name", f"env-{environment_id[:8]}"),
            environment_type=input_data.get("environment_type", EnvironmentType.DEVELOPMENT),
            user_id=input_data.get("user_id", "default_user"),
            tools=input_data.get("tools", [ToolType.ALL]),
            custom_domain=input_data.get("custom_domain"),
            resource_limits=input_data.get("resource_limits", {}),
            description=input_data.get("description", "Automated environment setup"),
            created_at=datetime.utcnow().isoformat(),
            status="creating"
        )
        
        # Save the environment
        self.environments[environment_id] = environment_config.dict()
        self._save_environments()
        
        # Create environment directory
        environment_dir = os.path.join(self.environments_dir, environment_id)
        os.makedirs(environment_dir, exist_ok=True)
        
        # Generate Docker Compose file
        docker_compose_file = os.path.join(environment_dir, "docker-compose.yml")
        docker_compose_content = self._generate_docker_compose(environment_config)
        
        with open(docker_compose_file, 'w') as f:
            f.write(docker_compose_content)
        
        # Generate environment variables file
        env_file = os.path.join(environment_dir, ".env")
        env_vars = self._generate_environment_variables(environment_config)
        
        with open(env_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Create dashboard directory
        dashboard_dir = os.path.join(environment_dir, "dashboard")
        os.makedirs(dashboard_dir, exist_ok=True)
        
        # Generate initial dashboard
        dashboard_file = os.path.join(dashboard_dir, "index.html")
        dashboard_content = self._generate_dashboard(environment_config)
        
        with open(dashboard_file, 'w') as f:
            f.write(dashboard_content)
        
        # Start the environment asynchronously
        asyncio.create_task(self._start_environment(environment_id))
        
        # Return initial response
        return {
            "environment_id": environment_id,
            "status": "creating",
            "message": "Environment creation started. You will receive access details when complete.",
            "ready": False
        }
    
    async def _start_environment(self, environment_id: str) -> None:
        """Start an environment using Docker Compose."""
        if environment_id not in self.environments:
            logging.error(f"Environment {environment_id} not found")
            return

        environment = self.environments[environment_id]
        environment_dir = os.path.join(self.environments_dir, environment_id)
        
        logging.info(f"Starting environment {environment_id} with Docker Compose")
        
        # Create a unique project name based on the environment ID
        project_name = f"env-{environment_id[:8]}"
        
        try:
            if self.host_deployment:
                # For host deployment, we need to create a setup script that will be executed on the host
                host_env_dir = f"/home/satish/infra-automation/data/environments/{environment_id}"
                
                # Create a setup script that will:
                # 1. Create the host directory
                # 2. Copy all necessary files
                # 3. Start the environment with docker-compose
                setup_script_path = os.path.join(environment_dir, "setup_and_start.sh")
                
                with open(setup_script_path, "w") as f:
                    f.write("#!/bin/bash\n\n")
                    f.write(f"# Script to set up and start environment {environment_id}\n\n")
                    
                    # Create host directory
                    f.write(f"mkdir -p {host_env_dir}\n")
                    f.write(f"mkdir -p {host_env_dir}/dashboard\n\n")
                    
                    # Copy docker-compose.yml
                    f.write(f"cat > {host_env_dir}/docker-compose.yml << 'EOL'\n")
                    with open(os.path.join(environment_dir, "docker-compose.yml"), 'r') as dc_file:
                        f.write(dc_file.read())
                    f.write("\nEOL\n\n")
                    
                    # Copy .env file
                    f.write(f"cat > {host_env_dir}/.env << 'EOL'\n")
                    with open(os.path.join(environment_dir, ".env"), 'r') as env_file:
                        f.write(env_file.read())
                    f.write("\nEOL\n\n")
                    
                    # Copy dashboard files
                    dashboard_dir = os.path.join(environment_dir, "dashboard")
                    for filename in os.listdir(dashboard_dir):
                        if os.path.isfile(os.path.join(dashboard_dir, filename)):
                            f.write(f"cat > {host_env_dir}/dashboard/{filename} << 'EOL'\n")
                            with open(os.path.join(dashboard_dir, filename), 'r') as dash_file:
                                f.write(dash_file.read())
                            f.write("\nEOL\n\n")
                    
                    # Modify ports in docker-compose.yml to avoid conflicts
                    port_offset = hash(environment_id) % 100
                    jira_port = 8080 + port_offset
                    gitlab_port = 8929 + port_offset
                    dashboard_port = 8081 + port_offset
                    
                    f.write(f"# Modify ports to avoid conflicts\n")
                    f.write(f"sed -i 's/\"8080:8080\"/\"{jira_port}:8080\"/' {host_env_dir}/docker-compose.yml\n")
                    f.write(f"sed -i 's/\"8929:80\"/\"{gitlab_port}:80\"/' {host_env_dir}/docker-compose.yml\n")
                    f.write(f"sed -i 's/\"80:80\"/\"{dashboard_port}:80\"/' {host_env_dir}/docker-compose.yml\n\n")
                    
                    # Start the environment
                    f.write(f"# Start the environment\n")
                    f.write(f"cd {host_env_dir}\n")
                    f.write(f"docker-compose --project-name {project_name} up -d\n\n")
                    
                    # Update the API with the environment status
                    f.write(f"# Update the environment status\n")
                    f.write(f"curl -X PUT http://localhost:8000/api/onboarding/environments/{environment_id} -H \"Content-Type: application/json\" -d '{{\n")
                    f.write(f"  \"status\": \"running\"\n")
                    f.write(f"}}'\n")
                
                # Make the script executable
                os.chmod(setup_script_path, 0o755)
                
                # Set default tool endpoints with the calculated ports
                port_offset = hash(environment_id) % 100
                jira_port = 8080 + port_offset
                gitlab_port = 8929 + port_offset
                dashboard_port = 8081 + port_offset
                
                tool_endpoints = {}
                tools = environment.get("tools", [])
                host_ip = "localhost"
                
                if "jira" in tools:
                    tool_endpoints["jira"] = f"http://{host_ip}:{jira_port}"
                if "gitlab" in tools:
                    tool_endpoints["gitlab"] = f"http://{host_ip}:{gitlab_port}"
                
                tool_endpoints["dashboard"] = f"http://{host_ip}:{dashboard_port}"
                
                environment["tool_endpoints"] = tool_endpoints
                environment["access_url"] = tool_endpoints["dashboard"]
                
                # Generate credentials for tools
                environment["credentials"] = self._generate_credentials(environment)
                
                # Update the dashboard with actual data
                self._update_dashboard(environment_id)
                
                # Update environment status to indicate manual action needed
                environment["status"] = "prepared"
                environment["message"] = f"Environment prepared. To start, run: docker exec infra-automation_api_1 cat /app/data/environments/{environment_id}/setup_and_start.sh > /tmp/setup.sh && chmod +x /tmp/setup.sh && /tmp/setup.sh"
                
                # Save updated environment information
                self._save_environments()
                
                logging.info(f"Environment {environment_id} prepared successfully")
                logging.info(f"To start the environment, run: docker exec infra-automation_api_1 cat /app/data/environments/{environment_id}/setup_and_start.sh > /tmp/setup.sh && chmod +x /tmp/setup.sh && /tmp/setup.sh")
            else:
                # For container deployment, use docker-compose directly
                docker_compose_bin = "docker-compose"  # Default to PATH-based resolution
                command = [docker_compose_bin, "-f", os.path.join(environment_dir, "docker-compose.yml"), 
                          "--project-name", project_name, "up", "-d"]
                
                logging.info(f"Running command: {' '.join(command)}")
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logging.error(f"Error starting environment {environment_id}: {error_msg}")
                    environment["status"] = "failed"
                    environment["error"] = error_msg
                    self._save_environments()
                    return
                
                # Wait for containers to be ready
                await asyncio.sleep(5)
                
                # Get container information
                docker_compose_bin = "docker-compose"
                command = [docker_compose_bin, "-f", os.path.join(environment_dir, "docker-compose.yml"), 
                          "--project-name", project_name, "ps"]
                
                logging.info(f"Running command to get container info: {' '.join(command)}")
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logging.warning(f"Error getting container info for {environment_id}: {error_msg}")
                
                # Parse container information and update environment
                container_info = stdout.decode() if stdout else ""
                logging.info(f"Container info for {environment_id}: {container_info}")
                
                # Update environment status
                environment["status"] = "running"
                
                # Generate credentials for tools
                environment["credentials"] = self._generate_credentials(environment)
                
                # Update environment with tool endpoints and credentials
                self._update_environment_endpoints(environment, container_info)
                
                # Update the dashboard with actual data
                self._update_dashboard(environment_id)
                
                # Save updated environment information
                self._save_environments()
                
                logging.info(f"Environment {environment_id} started successfully")
        except Exception as e:
            logging.error(f"Error in _start_environment for {environment_id}: {str(e)}")
            environment["status"] = "failed"
            environment["error"] = str(e)
            self._save_environments()
    
    def _set_default_endpoints(self, environment):
        """Set default tool endpoints for an environment."""
        tool_endpoints = {}
        tools = environment.get("tools", [])
        
        # Default to localhost for host
        host_ip = "localhost"
        
        # Use a port offset based on environment ID to avoid conflicts
        port_offset = hash(environment["environment_id"]) % 100
        
        tool_port_map = {
            "jira": 8080 + port_offset,
            "confluence": 8090 + port_offset,
            "gitlab": 8929 + port_offset,
            "jenkins": 8080 + port_offset,
            "nexus": 8081 + port_offset,
            "vault": 8200 + port_offset,
            "grafana": 3000 + port_offset,
            "prometheus": 9090 + port_offset,
            "kubernetes": 8443 + port_offset
        }
        
        for tool in tools:
            if tool in tool_port_map:
                tool_endpoints[tool] = f"http://{host_ip}:{tool_port_map[tool]}"
        
        # Add dashboard endpoint
        tool_endpoints["dashboard"] = f"http://{host_ip}:8080/dashboard"
        
        # Update environment with endpoints and access URL
        environment["tool_endpoints"] = tool_endpoints
        environment["access_url"] = tool_endpoints["dashboard"]
    
    def _update_dashboard(self, environment_id: str):
        """Update the dashboard with actual endpoints and credentials."""
        try:
            environment = self.environments[environment_id]
            environment_dir = os.path.join(self.environments_dir, environment_id)
            dashboard_file = os.path.join(environment_dir, "dashboard", "index.html")
            
            # Generate updated dashboard
            dashboard_content = self._generate_dashboard(EnvironmentConfig(**environment))
            
            with open(dashboard_file, 'w') as f:
                f.write(dashboard_content)
                
            logger.info(f"Updated dashboard for environment {environment_id}")
        except Exception as e:
            logger.error(f"Error updating dashboard for environment {environment_id}: {str(e)}")
    
    def get_environment(self, environment_id: str) -> Dict[str, Any]:
        """Get information about an environment."""
        if not environment_id or environment_id not in self.environments:
            return {
                "status": "error",
                "message": f"Environment {environment_id} not found"
            }
        
        environment = self.environments[environment_id]
        
        return {
            "environment_id": environment_id,
            "status": environment.get("status", "unknown"),
            "environment_name": environment.get("environment_name", ""),
            "environment_type": environment.get("environment_type", ""),
            "created_at": environment.get("created_at", ""),
            "access_url": environment.get("access_url"),
            "tool_endpoints": environment.get("tool_endpoints", {}),
            "ready": environment.get("status") == "running",
            "message": self._get_status_message(environment.get("status", "unknown"))
        }
    
    def list_environments(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """List all environments, optionally filtered by user_id."""
        environments_list = []
        
        for env_id, env in self.environments.items():
            if user_id is None or env.get("user_id") == user_id:
                environments_list.append({
                    "environment_id": env_id,
                    "environment_name": env.get("environment_name", ""),
                    "environment_type": env.get("environment_type", ""),
                    "status": env.get("status", "unknown"),
                    "created_at": env.get("created_at", ""),
                    "access_url": env.get("access_url"),
                    "ready": env.get("status") == "running"
                })
        
        return {
            "environments": environments_list,
            "count": len(environments_list)
        }
    
    async def delete_environment(self, environment_id: str) -> Dict[str, Any]:
        """Delete an environment and all its resources."""
        if environment_id not in self.environments:
            logging.error(f"Environment {environment_id} not found")
            return {
                "status": "error",
                "message": f"Environment {environment_id} not found"
            }
            
        environment_dir = os.path.join(self.environments_dir, environment_id)
        
        try:
            logging.info(f"Stopping environment {environment_id}")
            
            # Create a unique project name based on the environment ID
            project_name = f"env-{environment_id[:8]}"
            
            if self.host_deployment:
                # For host deployment, use docker run with docker-compose
                host_env_dir = f"/home/satish/infra-automation/data/environments/{environment_id}"
                command = ["docker", "run", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", 
                          "-v", f"{host_env_dir}:{host_env_dir}", "docker/compose:latest", 
                          "-f", f"{host_env_dir}/docker-compose.yml", "--project-name", project_name, 
                          "down", "--volumes", "--remove-orphans"]
            else:
                # For container deployment, use docker-compose directly
                docker_compose_bin = "docker-compose"
                command = [docker_compose_bin, "-f", os.path.join(environment_dir, "docker-compose.yml"), 
                          "--project-name", project_name, "down", "--volumes", "--remove-orphans"]
            
            logging.info(f"Running command: {' '.join(command)}")
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logging.error(f"Error stopping environment {environment_id}: {error_msg}")
                # Continue with deletion even if stopping failed
            
            # Remove environment from tracking
            del self.environments[environment_id]
            self._save_environments()
            
            # Optionally, remove environment directory
            # shutil.rmtree(environment_dir, ignore_errors=True)
            
            logging.info(f"Environment {environment_id} deleted successfully")
            return {
                "status": "success",
                "message": f"Environment {environment_id} deleted successfully"
            }
        except Exception as e:
            logging.error(f"Error in delete_environment for {environment_id}: {str(e)}")
            return {
                "status": "error",
                "message": f"Error deleting environment: {str(e)}"
            }
    
    def _generate_docker_compose(self, environment_config: EnvironmentConfig) -> str:
        """Generate a Docker Compose file for the environment."""
        tools = environment_config.tools
        
        # If ALL is specified, include all tools
        if ToolType.ALL in tools:
            tools = [t for t in ToolType if t != ToolType.ALL]
        
        # Start with the version and network definition
        docker_compose = """version: '3.8'

services:
"""
        
        # Add services based on selected tools
        if ToolType.JIRA in tools:
            docker_compose += """  jira:
    image: atlassian/jira-software:latest
    environment:
      - ATL_JDBC_URL=jdbc:postgresql://db:5432/jira
      - ATL_JDBC_USER=jira
      - ATL_JDBC_PASSWORD=${JIRA_DB_PASSWORD}
    ports:
      - "8080:8080"
    volumes:
      - jira-data:/var/atlassian/application-data/jira
    depends_on:
      - db

"""
        
        if ToolType.CONFLUENCE in tools:
            docker_compose += """  confluence:
    image: atlassian/confluence:latest
    environment:
      - ATL_JDBC_URL=jdbc:postgresql://db:5432/confluence
      - ATL_JDBC_USER=confluence
      - ATL_JDBC_PASSWORD=${CONFLUENCE_DB_PASSWORD}
    ports:
      - "8090:8090"
    volumes:
      - confluence-data:/var/atlassian/application-data/confluence
    depends_on:
      - db

"""
        
        if ToolType.GITLAB in tools:
            docker_compose += """  gitlab:
    image: gitlab/gitlab-ce:latest
    environment:
      GITLAB_OMNIBUS_CONFIG: |
        external_url 'http://gitlab.local'
    ports:
      - "8929:80"
      - "2224:22"
    volumes:
      - gitlab-config:/etc/gitlab
      - gitlab-logs:/var/log/gitlab
      - gitlab-data:/var/opt/gitlab

"""
        
        if ToolType.JENKINS in tools:
            docker_compose += """  jenkins:
    image: jenkins/jenkins:lts
    ports:
      - "8088:8080"
    volumes:
      - jenkins-data:/var/jenkins_home

"""
        
        if ToolType.NEXUS in tools:
            docker_compose += """  nexus:
    image: sonatype/nexus3
    ports:
      - "8081:8081"
    volumes:
      - nexus-data:/nexus-data

"""
        
        if ToolType.VAULT in tools:
            docker_compose += """  vault:
    image: hashicorp/vault:latest
    cap_add:
      - IPC_LOCK
    ports:
      - "8200:8200"
    environment:
      - VAULT_DEV_ROOT_TOKEN_ID=${VAULT_ROOT_TOKEN}
    volumes:
      - vault-data:/vault/data

"""
        
        if ToolType.KUBERNETES in tools:
            docker_compose += """  k3s:
    image: rancher/k3s:latest
    command: server --disable traefik
    privileged: true
    ports:
      - "6443:6443"
    volumes:
      - k3s-server:/var/lib/rancher/k3s

"""
        
        if ToolType.PROMETHEUS in tools:
            docker_compose += """  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - prometheus-data:/prometheus

"""
        
        if ToolType.GRAFANA in tools:
            docker_compose += """  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus

"""
        
        # Add database for tools that need it
        if any(t in tools for t in [ToolType.JIRA, ToolType.CONFLUENCE]):
            docker_compose += """  db:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=${DB_ROOT_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

"""
        
        # Add dashboard for the environment
        docker_compose += """  dashboard:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./dashboard:/usr/share/nginx/html
"""
        
        # Add volumes section
        docker_compose += "\nvolumes:\n"
        
        if ToolType.JIRA in tools:
            docker_compose += "  jira-data:\n"
        
        if ToolType.CONFLUENCE in tools:
            docker_compose += "  confluence-data:\n"
        
        if ToolType.GITLAB in tools:
            docker_compose += "  gitlab-config:\n"
            docker_compose += "  gitlab-logs:\n"
            docker_compose += "  gitlab-data:\n"
        
        if ToolType.JENKINS in tools:
            docker_compose += "  jenkins-data:\n"
        
        if ToolType.NEXUS in tools:
            docker_compose += "  nexus-data:\n"
        
        if ToolType.VAULT in tools:
            docker_compose += "  vault-data:\n"
        
        if ToolType.KUBERNETES in tools:
            docker_compose += "  k3s-server:\n"
        
        if ToolType.PROMETHEUS in tools:
            docker_compose += "  prometheus-data:\n"
        
        if ToolType.GRAFANA in tools:
            docker_compose += "  grafana-data:\n"
        
        if any(t in tools for t in [ToolType.JIRA, ToolType.CONFLUENCE]):
            docker_compose += "  postgres-data:\n"
        
        return docker_compose
    
    def _generate_environment_variables(self, environment_config: EnvironmentConfig) -> Dict[str, str]:
        """Generate environment variables for the Docker Compose file."""
        env_vars = {
            "ENVIRONMENT_ID": environment_config.environment_id,
            "ENVIRONMENT_NAME": environment_config.environment_name,
            "DB_ROOT_PASSWORD": f"password_{uuid.uuid4().hex[:8]}",
            "JIRA_DB_PASSWORD": f"jira_password_{uuid.uuid4().hex[:8]}",
            "CONFLUENCE_DB_PASSWORD": f"confluence_password_{uuid.uuid4().hex[:8]}",
            "VAULT_ROOT_TOKEN": f"vault_token_{uuid.uuid4().hex[:8]}"
        }
        
        return env_vars
    
    def _generate_credentials(self, environment):
        """Generate credentials for tools in the environment."""
        tools = environment.get("tools", [])
        credentials = {}
        
        # Default credentials for common tools
        if "jira" in tools:
            credentials["jira"] = {"username": "admin", "password": "admin"}
        
        if "confluence" in tools:
            credentials["confluence"] = {"username": "admin", "password": "admin"}
            
        if "gitlab" in tools:
            credentials["gitlab"] = {"username": "root", "password": "password"}
            
        if "jenkins" in tools:
            credentials["jenkins"] = {
                "username": "admin", 
                "initial_password_file": "/var/jenkins_home/secrets/initialAdminPassword"
            }
            
        if "nexus" in tools:
            credentials["nexus"] = {"username": "admin", "password": "admin123"}
            
        if "vault" in tools:
            credentials["vault"] = {"token": "vault_token"}
            
        if "grafana" in tools:
            credentials["grafana"] = {"username": "admin", "password": "admin"}
            
        return credentials

    def _update_environment_endpoints(self, environment, container_info):
        """Update environment with tool endpoints based on container information."""
        tool_endpoints = {}
        tools = environment.get("tools", [])
        
        # Default to localhost for host
        host_ip = "localhost"
        
        # Parse container information to extract port mappings
        # Format depends on whether we're using docker-compose ps or docker ps
        if self.host_deployment:
            # Docker ps format: NAME,PORTS
            for line in container_info.splitlines():
                if not line.strip():
                    continue
                
                parts = line.split(',', 1)
                if len(parts) < 2:
                    continue
                    
                container_name = parts[0]
                ports_info = parts[1]
                
                # Extract service name from container name (remove project prefix)
                service_name = container_name.split('_')[-1] if '_' in container_name else container_name
                
                # Parse port mappings like "0.0.0.0:8080->8080/tcp"
                for port_mapping in ports_info.split(', '):
                    if "->" in port_mapping:
                        host_port = port_mapping.split("->")[0].split(":")[-1]
                        tool_endpoints[service_name] = f"http://{host_ip}:{host_port}"
        else:
            # Docker-compose ps format (more complex, may need adjustment)
            try:
                # Try to parse as JSON if docker-compose ps --format json was used
                containers = json.loads(container_info)
                for container in containers:
                    service_name = container.get("Service", "")
                    ports = container.get("Ports", "")
                    
                    if service_name and ports:
                        for port_mapping in ports.split(", "):
                            if "->" in port_mapping:
                                host_port = port_mapping.split("->")[0].split(":")[-1]
                                tool_endpoints[service_name] = f"http://{host_ip}:{host_port}"
            except json.JSONDecodeError:
                # Fallback to line parsing for standard docker-compose ps output
                for line in container_info.splitlines()[2:]:  # Skip header lines
                    if not line.strip():
                        continue
                        
                    parts = line.split()
                    if len(parts) >= 4:
                        service_name = parts[0].split('_')[-1]
                        ports_info = ' '.join(parts[3:])
                        
                        if "->" in ports_info:
                            for port_mapping in ports_info.split(", "):
                                if "->" in port_mapping:
                                    host_port = port_mapping.split("->")[0].split(":")[-1]
                                    tool_endpoints[service_name] = f"http://{host_ip}:{host_port}"
        
        # If we couldn't parse port information, use default ports for known tools
        if not tool_endpoints:
            logging.warning(f"Could not parse container info, using default ports")
            port_offset = hash(environment["environment_id"]) % 100
            
            tool_port_map = {
                "jira": 8080 + port_offset,
                "confluence": 8090 + port_offset,
                "gitlab": 8929 + port_offset,
                "jenkins": 8080 + port_offset,
                "nexus": 8081 + port_offset,
                "vault": 8200 + port_offset,
                "grafana": 3000 + port_offset,
                "prometheus": 9090 + port_offset,
                "kubernetes": 8443 + port_offset
            }
            
            for tool in tools:
                if tool in tool_port_map:
                    tool_endpoints[tool] = f"http://{host_ip}:{tool_port_map[tool]}"
        
        # Add dashboard endpoint
        dashboard_port = 8080  # Default dashboard port
        if "dashboard" in tool_endpoints:
            dashboard_port = tool_endpoints["dashboard"].split(":")[-1]
        tool_endpoints["dashboard"] = f"http://{host_ip}:{dashboard_port}/dashboard"
        
        # Update environment with endpoints and access URL
        environment["tool_endpoints"] = tool_endpoints
        environment["access_url"] = tool_endpoints["dashboard"]
        environment["credentials"] = self._generate_credentials(environment)
    
    def _generate_dashboard(self, environment_config: EnvironmentConfig) -> str:
        """Generate a dashboard HTML file for the environment."""
        # Get environment data
        environment_id = environment_config.environment_id
        environment = self.environments.get(environment_id, {})
        
        # Get tool endpoints and credentials
        tool_endpoints = environment.get("tool_endpoints", {})
        credentials = environment.get("credentials", {})
        
        # Generate tool cards
        tool_cards = ""
        for tool in environment_config.tools:
            if tool == ToolType.ALL:
                continue
                
            tool_info = self.tool_info.get(tool, {
                "name": tool.value.capitalize(),
                "description": f"{tool.value} tool",
                "icon": ""
            })
            
            endpoint = tool_endpoints.get(tool.value, "#")
            
            tool_cards += f"""
            <div class="tool-card">
                <div class="tool-header">
                    <img src="{tool_info['icon']}" alt="{tool_info['name']}" class="tool-icon">
                    <h3 class="tool-name">{tool_info['name']}</h3>
                </div>
                <p class="tool-description">{tool_info['description']}</p>
                <a href="{endpoint}" target="_blank" class="tool-link">Open {tool_info['name']}</a>
            </div>
            """
        
        # Generate credentials table
        credentials_table = ""
        for tool_name, creds in credentials.items():
            username = creds.get("username", "N/A")
            password = creds.get("password", creds.get("token", "N/A"))
            
            credentials_table += f"""
            <tr>
                <td>{tool_name.capitalize()}</td>
                <td>{username}</td>
                <td>{password}</td>
            </tr>
            """
        
        # Replace placeholders in template
        dashboard = self.dashboard_template
        dashboard = dashboard.replace("{{ENVIRONMENT_NAME}}", environment_config.environment_name)
        dashboard = dashboard.replace("{{ENVIRONMENT_TYPE}}", environment_config.environment_type)
        dashboard = dashboard.replace("{{ENVIRONMENT_STATUS}}", environment.get("status", "creating"))
        dashboard = dashboard.replace("{{ENVIRONMENT_CREATED_AT}}", environment_config.created_at)
        dashboard = dashboard.replace("{{ENVIRONMENT_ID}}", environment_id)
        dashboard = dashboard.replace("{{TOOL_CARDS}}", tool_cards)
        dashboard = dashboard.replace("{{CREDENTIALS_TABLE}}", credentials_table)
        
        return dashboard
    
    def _get_status_message(self, status: str) -> str:
        """Get a human-readable message for the environment status."""
        status_messages = {
            "creating": "Environment is being created. This may take a few minutes.",
            "starting": "Environment containers are starting up.",
            "running": "Environment is running and ready to use.",
            "failed": "Environment creation failed. Please check the logs.",
            "stopping": "Environment is being stopped.",
            "stopped": "Environment is stopped.",
            "deleting": "Environment is being deleted."
        }
        
        return status_messages.get(status, f"Unknown status: {status}")
    
    async def execute_workflow_step(self, workflow_state: WorkflowState) -> WorkflowState:
        """Execute a workflow step for environment creation."""
        try:
            # Extract environment configuration from workflow state
            environment_config = workflow_state.inputs.get("environment_config", {})
            
            # Create the environment
            result = await self.create_environment(environment_config)
            
            # Update workflow state
            workflow_state.status = "environment_creation_started"
            workflow_state.resource_endpoints = result.get("tool_endpoints", {})
            workflow_state.add_log("onboarding_agent", f"Environment creation started with ID: {result.get('environment_id')}")
            
            return workflow_state
            
        except Exception as e:
            workflow_state.add_error(f"Error in environment creation: {str(e)}")
            return workflow_state 