# src/api/dependencies.py

from ..agents.infra import InfrastructureAgent
from ..agents.architect import ArchitectureAgent

# These would typically be configured at startup and stored in a global state
# For simplicity, we're using globals here
_infrastructure_agent = None
_architecture_agent = None

def set_infrastructure_agent(agent: InfrastructureAgent):
    global _infrastructure_agent
    _infrastructure_agent = agent
    
def get_infrastructure_agent() -> InfrastructureAgent:
    return _infrastructure_agent

def set_architecture_agent(agent: ArchitectureAgent):
    global _architecture_agent
    _architecture_agent = agent
    
def get_architecture_agent() -> ArchitectureAgent:
    return _architecture_agent