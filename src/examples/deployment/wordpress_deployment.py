import asyncio
import logging
from langchain.llms import OpenAI  # You can replace with your preferred LLM

from agents.deployment_agent import DeploymentAgent
from schemas.deployment import (
    DeploymentConfig, ResourceConfig, ServiceConfig, ResourceType, 
    CloudProvider, NetworkConfig, SecurityRule, ResourceTag
)
from schemas.workflow import WorkflowState

async def deploy_wordpress_site():
    """Example function demonstrating the deployment of a WordPress site."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Create an LLM instance (this would depend on your LLM implementation)
    llm = OpenAI(temperature=0)
    
    # Create the deployment agent
    deployment_agent = DeploymentAgent(llm=llm, cloud_provider="aws")
    
    # Create a WordPress deployment configuration
    wp_deployment_config = DeploymentConfig(
        name="wordpress-site",
        description="WordPress site with MySQL database",
        provider=CloudProvider.AWS,
        region="us-east-1",
        network=NetworkConfig(
            vpc_cidr="10.0.0.0/16",
            subnet_cidrs=["10.0.1.0/24", "10.0.2.0/24"],
            security_rules=[
                SecurityRule(
                    protocol="tcp",
                    port_range="80",
                    source="0.0.0.0/0",
                    description="HTTP access"
                ),
                SecurityRule(
                    protocol="tcp",
                    port_range="443",
                    source="0.0.0.0/0",
                    description="HTTPS access"
                ),
                SecurityRule(
                    protocol="tcp",
                    port_range="3306",
                    source="10.0.0.0/16",
                    description="MySQL internal access"
                )
            ]
        ),
        resources=[
            # VPC Resource
            ResourceConfig(
                name="wordpress-vpc",
                type=ResourceType.VPC,
                provider_specific={
                    "enable_dns_support": True,
                    "enable_dns_hostnames": True
                },
                tags=[ResourceTag(key="Environment", value="Production")]
            ),
            
            # Public Subnet
            ResourceConfig(
                name="wordpress-public-subnet",
                type=ResourceType.SUBNET,
                provider_specific={
                    "cidr_block": "10.0.1.0/24",
                    "availability_zone": "us-east-1a",
                    "map_public_ip_on_launch": True
                },
                depends_on=["wordpress-vpc"],
                tags=[ResourceTag(key="Type", value="Public")]
            ),
            
            # Private Subnet
            ResourceConfig(
                name="wordpress-private-subnet",
                type=ResourceType.SUBNET,
                provider_specific={
                    "cidr_block": "10.0.2.0/24",
                    "availability_zone": "us-east-1b",
                    "map_public_ip_on_launch": False
                },
                depends_on=["wordpress-vpc"],
                tags=[ResourceTag(key="Type", value="Private")]
            ),
            
            # Security Group for Web Servers
            ResourceConfig(
                name="wordpress-web-sg",
                type=ResourceType.SECURITY_GROUP,
                provider_specific={
                    "description": "Security group for WordPress web servers",
                    "ingress_rules": [
                        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
                        {"protocol": "tcp", "from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]}
                    ]
                },
                depends_on=["wordpress-vpc"],
                tags=[ResourceTag(key="Component", value="Web")]
            ),
            
            # Security Group for Databases
            ResourceConfig(
                name="wordpress-db-sg",
                type=ResourceType.SECURITY_GROUP,
                provider_specific={
                    "description": "Security group for WordPress database",
                    "ingress_rules": [
                        {"protocol": "tcp", "from_port": 3306, "to_port": 3306, "source_security_group": "wordpress-web-sg"}
                    ]
                },
                depends_on=["wordpress-vpc", "wordpress-web-sg"],
                tags=[ResourceTag(key="Component", value="Database")]
            ),
            
            # MySQL Database
            ResourceConfig(
                name="wordpress-db",
                type=ResourceType.DATABASE,
                provider_specific={
                    "engine": "mysql",
                    "engine_version": "8.0",
                    "instance_class": "db.t3.small",
                    "allocated_storage": 20,
                    "username": "wordpress_user",
                    "password_parameter_name": "/wordpress/db/password", # Stored in Parameter Store
                    "multi_az": False,
                    "storage_encrypted": True
                },
                depends_on=["wordpress-private-subnet", "wordpress-db-sg"],
                tags=[ResourceTag(key="Application", value="WordPress")]
            ),
            
            # EC2 Instance for WordPress
            ResourceConfig(
                name="wordpress-web-server",
                type=ResourceType.VIRTUAL_MACHINE,
                provider_specific={
                    "instance_type": "t3.small",
                    "ami_id": "ami-0c55b159cbfafe1f0",  # Amazon Linux 2 AMI
                    "key_name": "wordpress-key",
                    "user_data": """#!/bin/bash
                        amazon-linux-extras install -y lamp-mariadb10.2-php7.2 php7.2
                        yum install -y httpd mariadb-server
                        systemctl start httpd
                        systemctl enable httpd
                        cd /var/www/html
                        wget https://wordpress.org/latest.tar.gz
                        tar -xzf latest.tar.gz
                        chown -R apache:apache /var/www/html/wordpress
                        cp /var/www/html/wordpress/wp-config-sample.php /var/www/html/wordpress/wp-config.php
                        # Additional configuration would be added here
                    """
                },
                depends_on=["wordpress-public-subnet", "wordpress-web-sg"],
                tags=[ResourceTag(key="Application", value="WordPress")]
            ),
            
            # S3 Bucket for Media Storage
            ResourceConfig(
                name="wordpress-media",
                type=ResourceType.OBJECT_STORAGE,
                provider_specific={
                    "acl": "private",
                    "versioning": True,
                    "lifecycle_rules": [
                        {
                            "enabled": True,
                            "transition": {
                                "days": 30,
                                "storage_class": "STANDARD_IA"
                            }
                        }
                    ]
                },
                tags=[ResourceTag(key="Application", value="WordPress"), ResourceTag(key="Data", value="Media")]
            ),
            
            # Load Balancer
            ResourceConfig(
                name="wordpress-lb",
                type=ResourceType.LOAD_BALANCER,
                provider_specific={
                    "type": "application",
                    "listeners": [
                        {"port": 80, "protocol": "HTTP"},
                        {"port": 443, "protocol": "HTTPS", "certificate_arn": "arn:aws:acm:us-east-1:123456789012:certificate/example"}
                    ],
                    "health_check": {
                        "path": "/",
                        "port": "traffic-port",
                        "protocol": "HTTP",
                        "timeout": 5,
                        "interval": 30,
                        "healthy_threshold": 2,
                        "unhealthy_threshold": 2
                    }
                },
                depends_on=["wordpress-public-subnet", "wordpress-web-sg"],
                tags=[ResourceTag(key="Application", value="WordPress")]
            )
        ],
        services=[
            # WordPress Service
            ServiceConfig(
                name="wordpress",
                type="web_app",
                source="https://github.com/wordpress/wordpress.git",
                environment_variables={
                    "DB_HOST": "${wordpress-db.endpoint}",
                    "DB_NAME": "wordpress",
                    "DB_USER": "wordpress_user",
                    "DB_PASSWORD": "${ssm:/wordpress/db/password}",
                    "S3_BUCKET": "${wordpress-media.name}"
                },
                dependencies=["wordpress-db", "wordpress-web-server", "wordpress-media", "wordpress-lb"],
                scaling={
                    "min_capacity": 1,
                    "max_capacity": 3,
                    "scale_on": "cpu",
                    "target_value": 70
                },
                configuration={
                    "wp_config_settings": {
                        "WP_DEBUG": False,
                        "AUTOMATIC_UPDATER_DISABLED": True,
                        "WP_MEMORY_LIMIT": "128M"
                    }
                }
            )
        ],
        tags=[
            ResourceTag(key="Project", value="WordPress"),
            ResourceTag(key="Environment", value="Production"),
            ResourceTag(key="ManagedBy", value="InfraAutomation")
        ]
    )
    
    # Create a workflow state and add the deployment configuration
    workflow_state = WorkflowState(
        workflow_id="wordpress-deployment-workflow",
        user_id="user123",
        template_id="wordpress-standard",
        status="initialized",
        deployment_config=wp_deployment_config,
        inputs={
            "site_name": "My WordPress Site",
            "admin_email": "admin@example.com"
        }
    )
    
    # Execute the deployment step
    logger.info("Starting deployment workflow")
    updated_workflow_state = await deployment_agent.execute_workflow_step(workflow_state)
    
    # Check the results
    if updated_workflow_state.status == "deployment_completed":
        logger.info("Deployment completed successfully!")
        logger.info(f"WordPress site URL: {updated_workflow_state.resource_endpoints.get('wordpress', 'N/A')}")
        
        # Output all endpoints
        logger.info("Resource endpoints:")
        for name, endpoint in updated_workflow_state.resource_endpoints.items():
            logger.info(f"  - {name}: {endpoint}")
    else:
        logger.error(f"Deployment failed: {updated_workflow_state.errors}")
    
    return updated_workflow_state

# Entry point for running the example
if __name__ == "__main__":
    asyncio.run(deploy_wordpress_site())