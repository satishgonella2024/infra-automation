# test_deployment_integration.py
import asyncio
from src.agents.deployment.deployment_agent import DeploymentAgent
from src.models.deployment import DeploymentConfig, CloudProvider
from src.models.workflow import WorkflowState
from src.services.llm.llm_service import get_llm

async def test_deployment_integration():
    # Get LLM from your service
    llm = get_llm()
    
    # Create deployment agent
    deployment_agent = DeploymentAgent(llm=llm)
    
    # Create a simple test deployment config
    test_config = DeploymentConfig(
        name="test-deployment",
        provider=CloudProvider.AWS,
        region="us-east-1",
        # Add other required fields...
    )
    
    # Create workflow state
    workflow_state = WorkflowState(
        workflow_id="test-workflow",
        user_id="test-user",
        status="initialized",
        deployment_config=test_config
    )
    
    # Execute deployment
    result = await deployment_agent.execute_workflow_step(workflow_state)
    
    print(f"Deployment result: {result.status}")
    print(f"Endpoints: {result.resource_endpoints}")

if __name__ == "__main__":
    asyncio.run(test_deployment_integration())