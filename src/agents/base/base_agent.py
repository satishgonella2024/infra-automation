"""
Base Agent Module for Multi-Agent Infrastructure Automation System

This module defines the BaseAgent class that all specialized agents will inherit from.
It provides common functionality and interfaces for all agents in the system.
"""

import os
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseAgent(ABC):
    """
    Base Agent class that defines the interface and common functionality
    for all specialized agents in the system.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        llm_service: Any,
        vector_db_service: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new agent with a unique ID and specified capabilities.
        
        Args:
            name: The name of the agent
            description: A description of the agent's purpose
            capabilities: List of capabilities this agent provides
            llm_service: Service for language model interactions
            vector_db_service: Optional service for vector database operations
            config: Optional configuration parameters
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.llm_service = llm_service
        self.vector_db_service = vector_db_service
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")
        self.state = "idle"
        self.memory: List[Dict[str, Any]] = []
        self.creation_time = time.time()
        self.last_active_time = self.creation_time
        
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} Agent (ID: {self.id[:8]}, State: {self.state})"
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data and return the result.
        
        Args:
            input_data: The input data to process
            
        Returns:
            The processed result
        """
        pass
    
    async def think(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate thoughts about the input data before taking action.
        
        Args:
            input_data: The input data to think about
            
        Returns:
            Thoughts and analysis about the input
        """
        self.logger.info(f"Agent {self.name} thinking about task: {input_data.get('task_id', 'unknown')}")
        prompt = f"""
        As {self.name}, an AI agent responsible for {self.description}, 
        think through the following task step by step:
        
        {input_data.get('task', 'No task specified')}
        
        Consider:
        1. What information do I need to complete this task?
        2. What are potential challenges or edge cases?
        3. What best practices should I apply?
        4. What is the optimal approach?
        
        Capabilities at my disposal: {', '.join(self.capabilities)}
        """
        
        response = await self.llm_service.generate(prompt)
        self.update_memory({
            "type": "thinking",
            "input": input_data,
            "thoughts": response,
            "timestamp": time.time()
        })
        
        return {"thoughts": response, "agent": self.name}
    
    def update_state(self, new_state: str) -> None:
        """Update the agent's state."""
        self.logger.info(f"Agent {self.name} state change: {self.state} -> {new_state}")
        self.state = new_state
        self.last_active_time = time.time()
    
    def update_memory(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the agent's memory."""
        self.memory.append(entry)
        if self.vector_db_service:
            # If we have a vector DB service, store the memory there as well
            try:
                self.vector_db_service.store(
                    text=str(entry),
                    metadata={
                        "agent_id": self.id,
                        "agent_name": self.name,
                        "entry_type": entry.get("type", "unknown"),
                        "timestamp": entry.get("timestamp", time.time())
                    }
                )
            except Exception as e:
                self.logger.error(f"Failed to store memory in vector DB: {str(e)}")
    
    async def collaborate(
        self, 
        target_agent: 'BaseAgent', 
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Collaborate with another agent on a task.
        
        Args:
            target_agent: The agent to collaborate with
            task: The task to collaborate on
            
        Returns:
            The result of the collaboration
        """
        self.logger.info(f"Agent {self.name} collaborating with {target_agent.name}")
        self.update_state("collaborating")
        
        # Prepare the collaboration context
        collab_context = {
            "task_id": task.get("task_id", str(uuid.uuid4())),
            "initiator_agent": self.name,
            "target_agent": target_agent.name,
            "task": task.get("task", ""),
            "context": {
                "initiator_capabilities": self.capabilities,
                "target_capabilities": target_agent.capabilities,
                **task.get("context", {})
            }
        }
        
        # First, think about how to approach the collaboration
        thoughts = await self.think(collab_context)
        
        # Then, let the target agent process the task
        target_response = await target_agent.process(collab_context)
        
        # Process the combined results
        result = {
            "collaboration_id": collab_context["task_id"],
            "initiator_agent": self.name,
            "target_agent": target_agent.name,
            "initiator_thoughts": thoughts.get("thoughts", ""),
            "target_response": target_response,
            "timestamp": time.time()
        }
        
        self.update_memory({
            "type": "collaboration",
            "collaboration_data": result,
            "timestamp": time.time()
        })
        
        self.update_state("idle")
        return result
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the agent state to a dictionary.
        
        Returns:
            A dictionary representation of the agent
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "state": self.state,
            "creation_time": self.creation_time,
            "last_active_time": self.last_active_time,
            "memory_size": len(self.memory)
        }