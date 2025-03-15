from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from src.models.onboarding_agent import OnboardingAgent

router = APIRouter()

@router.put("/environments/{environment_id}")
async def update_environment(
    environment_id: str,
    update_data: dict,
    onboarding_agent: OnboardingAgent = Depends(get_onboarding_agent)
):
    """Update an environment's status or configuration."""
    if environment_id not in onboarding_agent.environments:
        raise HTTPException(status_code=404, detail=f"Environment {environment_id} not found")
    
    # Update the environment with the provided data
    environment = onboarding_agent.environments[environment_id]
    
    for key, value in update_data.items():
        if key in environment:
            environment[key] = value
    
    # Save the updated environments
    onboarding_agent._save_environments()
    
    # Return the updated environment
    return onboarding_agent.get_environment(environment_id) 