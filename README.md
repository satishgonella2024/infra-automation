# Multi-Agent Infrastructure Automation System

A system that uses specialized AI agents to automate infrastructure provisioning, security review, architecture optimization, and more.

## Features

- Multi-Agent Architecture
- Infrastructure as Code Generation
- Digital Twin Visualization
- Vector Database Learning
- Simulation Engine

## Setup

1. Run `./setup.sh` to set up the development environment
2. Run `source venv/bin/activate` to activate the virtual environment
3. Start the system with `python -m src.main --mode api`

## Components

- Base Agent Framework
- Infrastructure Generation Agent
- LLM Service Integration
- API Server
- Template Utilities

Make sure to set up Ollama (if not already done by the setup script):

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the llama2 model
ollama pull llama2

