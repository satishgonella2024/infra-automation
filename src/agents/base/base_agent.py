"""
Base Agent Module for Multi-Agent Infrastructure Automation System

This module defines the BaseAgent class that all specialized agents will inherit from.
It provides common functionality and interfaces for all agents in the system.
"""

import os
import time
import uuid
import json
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
        
        # Check for similar past thoughts if vector DB is available
        similar_thoughts = []
        if self.vector_db_service:
            try:
                # Convert task to a string for searching
                task_str = input_data.get('task', str(input_data))
                similar_thoughts = await self.retrieve_similar_memories(
                    query=task_str, 
                    n_results=3,
                    memory_type="thinking"
                )
                
                if similar_thoughts:
                    self.logger.info(f"Found {len(similar_thoughts)} similar past thoughts")
            except Exception as e:
                self.logger.error(f"Error retrieving similar thoughts: {str(e)}")
        
        # Prepare context from similar thoughts
        context = ""
        if similar_thoughts:
            context = "Here are some similar tasks I've thought about before:\n\n"
            for i, memory in enumerate(similar_thoughts):
                thought_data = memory.get("memory", {})
                sim_input = thought_data.get("input", {})
                sim_task = sim_input.get("task", "") if isinstance(sim_input, dict) else ""
                sim_thoughts = thought_data.get("thoughts", "")
                
                if sim_task and sim_thoughts:
                    context += f"Task {i+1}: {sim_task}\n"
                    context += f"Thoughts: {sim_thoughts[:300]}...\n\n"
        
        prompt = f"""
        As {self.name}, an AI agent responsible for {self.description}, 
        think through the following task step by step:
        
        {input_data.get('task', 'No task specified')}
        
        {context}
        
        Consider:
        1. What information do I need to complete this task?
        2. What are potential challenges or edge cases?
        3. What best practices should I apply?
        4. What is the optimal approach?
        
        Capabilities at my disposal: {', '.join(self.capabilities)}
        """
        
        response = await self.llm_service.generate(prompt)
        await self.update_memory({
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
    
    async def update_memory(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the agent's memory."""
        self.memory.append(entry)
        if self.vector_db_service:
            try:
                # Convert complex objects to strings for storage
                memory_text = json.dumps(entry, default=str)
                memory_id = str(uuid.uuid4())
                
                # Store in vector database
                await self.vector_db_service.store_document(
                    collection_name="agent_memories",
                    document_id=memory_id,
                    text=memory_text,
                    metadata={
                        "agent_id": self.id,
                        "agent_name": self.name,
                        "entry_type": entry.get("type", "unknown"),
                        "timestamp": entry.get("timestamp", time.time())
                    }
                )
                self.logger.info(f"Stored memory in vector DB with ID: {memory_id[:8]}")
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
        
        await self.update_memory({
            "type": "collaboration",
            "collaboration_data": result,
            "timestamp": time.time()
        })
        
        self.update_state("idle")
        return result
    
    async def retrieve_similar_memories(
        self, 
        query: str, 
        n_results: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories similar to the given query.
        
        Args:
            query: Text to search for similar memories
            n_results: Maximum number of results to return
            memory_type: Optional filter for memory type
            
        Returns:
            List of similar memories with metadata
        """
        if not self.vector_db_service:
            return []
        
        try:
            # Build the where clause
            where = {"agent_id": self.id}
            if memory_type:
                where["entry_type"] = memory_type
            
            # Query for similar memories
            results = await self.vector_db_service.query_similar(
                collection_name="agent_memories",
                query_text=query,
                n_results=n_results,
                where=where
            )
            
            # Parse the memories
            formatted_results = []
            for result in results:
                try:
                    memory_data = json.loads(result["content"])
                    formatted_results.append({
                        "memory": memory_data,
                        "similarity": result["similarity"],
                        "metadata": result["metadata"]
                    })
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse memory: {result['content']}")
            
            return formatted_results
        except Exception as e:
            self.logger.error(f"Error retrieving memories: {str(e)}")
            return []
    
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
            "memory_size": len(self.memory),
            "has_vector_memory": self.vector_db_service is not None
        }