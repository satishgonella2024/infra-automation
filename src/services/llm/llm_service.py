"""
LLM Service Module for Multi-Agent Infrastructure Automation System

This module defines the LLMService class that handles interactions with 
various language models including local Ollama models and remote APIs.
"""

import os
import json
import aiohttp
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union

class LLMService:
    """
    Service for interacting with language models, including local Ollama
    and remote API-based models.
    """
    
    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama2",
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new LLMService.
        
        Args:
            provider: LLM provider ("ollama", "openai", "anthropic", etc.)
            model: Model name to use
            api_base: Base URL for API requests
            api_key: API key for authenticated providers
            config: Additional configuration parameters
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.config = config or {}
        
        # Configure logging
        self.logger = logging.getLogger(f"service.llm.{self.provider}")
        self.logger.info(f"Initialized LLM service with provider: {self.provider}, model: {self.model}")
        
        # Set up API base URL based on provider
        if api_base:
            # Remove /api suffix if present, as it's added in the specific methods
            self.api_base = api_base.rstrip("/api")
        elif self.provider == "ollama":
            self.api_base = "http://localhost:11434"
        elif self.provider == "openai":
            self.api_base = "https://api.openai.com/v1"
        elif self.provider == "anthropic":
            self.api_base = "https://api.anthropic.com"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.logger.info(f"Using API base URL: {self.api_base}")
    
    async def generate(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text completion from the language model.
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system prompt (for models that support it)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text completion
        """
        if self.provider == "ollama":
            return await self._generate_ollama(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == "anthropic":
            return await self._generate_anthropic(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider for generation: {self.provider}")
    
    async def _generate_ollama(
        self, 
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate text using local Ollama model."""
        self.logger.info(f"Generating with Ollama model: {self.model}")
        
        request_url = f"{self.api_base}/api/generate"
        self.logger.info(f"Making request to: {request_url}")
        
        # Prepare the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(request_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Ollama API error: {error_text}")
                        return f"Error: Ollama API returned status {response.status}"
                    
                    response_data = await response.json()
                    return response_data.get("response", "")
        except Exception as e:
            self.logger.error(f"Error calling Ollama API: {str(e)}")
            return f"Error: {str(e)}"
    
    async def _generate_openai(
        self, 
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate text using OpenAI API."""
        self.logger.info(f"Generating with OpenAI model: {self.model}")
        
        if not self.api_key:
            return "Error: OpenAI API key not provided"
        
        request_url = f"{self.api_base}/chat/completions"
        
        # Prepare the request payload
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(request_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI API error: {error_text}")
                        return f"Error: OpenAI API returned status {response.status}"
                    
                    response_data = await response.json()
                    return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {str(e)}")
            return f"Error: {str(e)}"
    
    async def _generate_anthropic(
        self, 
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate text using Anthropic API."""
        self.logger.info(f"Generating with Anthropic model: {self.model}")
        
        if not self.api_key:
            return "Error: Anthropic API key not provided"
        
        request_url = f"{self.api_base}/v1/messages"
        
        # Prepare the request payload
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(request_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Anthropic API error: {error_text}")
                        return f"Error: Anthropic API returned status {response.status}"
                    
                    response_data = await response.json()
                    return response_data["content"][0]["text"]
        except Exception as e:
            self.logger.error(f"Error calling Anthropic API: {str(e)}")
            return f"Error: {str(e)}"
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if self.provider == "openai":
            return await self._embed_openai(text)
        elif self.provider == "ollama":
            return await self._embed_ollama(text)
        else:
            raise ValueError(f"Embedding not supported for provider: {self.provider}")
    
    async def _embed_openai(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI API."""
        self.logger.info("Generating embeddings with OpenAI")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        request_url = f"{self.api_base}/embeddings"
        
        payload = {
            "model": "text-embedding-ada-002",  # Default embedding model
            "input": text
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(request_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"OpenAI API error: {error_text}")
                        raise ValueError(f"OpenAI API returned status {response.status}")
                    
                    response_data = await response.json()
                    return response_data["data"][0]["embedding"]
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API for embeddings: {str(e)}")
            raise
    
    async def _embed_ollama(self, text: str) -> List[float]:
        """Generate embeddings using Ollama."""
        self.logger.info(f"Generating embeddings with Ollama model: {self.model}")
        
        request_url = f"{self.api_base}/embeddings"
        
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(request_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Ollama API error: {error_text}")
                        raise ValueError(f"Ollama API returned status {response.status}")
                    
                    response_data = await response.json()
                    return response_data.get("embedding", [])
        except Exception as e:
            self.logger.error(f"Error calling Ollama API for embeddings: {str(e)}")
            raise