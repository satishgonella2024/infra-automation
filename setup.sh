#!/bin/bash
# Multi-Agent Infrastructure Automation System - Environment Setup Script

echo "Setting up development environment for Multi-Agent Infrastructure System..."

# Update and install basic dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git docker.io docker-compose curl wget

# Setup Python virtual environment
mkdir -p ~/infra-automation
cd ~/infra-automation
python3 -m venv venv
source venv/bin/activate

# Install required Python packages
pip install fastapi uvicorn langchain openai pydantic python-dotenv pytest flask requests numpy pandas scipy matplotlib transformers torch tqdm

# Infrastructure as Code tools
sudo apt install -y terraform ansible
pip install ansible-lint

# Install Node.js for the frontend
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g yarn

# Setup Ollama for local LLM
curl -fsSL https://ollama.com/install.sh | sh
# Pull a default model (e.g., llama2)
ollama pull llama2

# Create project structure
mkdir -p ~/infra-automation/src/{agents,models,services,utils,api,tests}
mkdir -p ~/infra-automation/src/agents/{base,infra,security,architect}
mkdir -p ~/infra-automation/src/services/{llm,vector_db,code_gen,simulation}
mkdir -p ~/infra-automation/templates/{terraform,ansible,jenkins}
mkdir -p ~/infra-automation/ui
mkdir -p ~/infra-automation/configs

# Create a default configuration file
cat > ~/infra-automation/configs/config.yaml << EOL
system:
  name: "Multi-Agent Infrastructure Automation"
  version: "0.1.0"
  
llm:
  provider: "ollama"
  model: "llama2"
  api_base: "http://localhost:11434/api"

agents:
  max_concurrent: 5
  timeout_seconds: 300

infrastructure:
  templates_path: "templates"
  supported_tools:
    - "terraform"
    - "ansible"
    - "jenkins"
EOL

# Create a simple README
cat > ~/infra-automation/README.md << EOL
# Multi-Agent Infrastructure Automation System

A system that uses specialized AI agents to automate infrastructure provisioning, 
security review, architecture optimization, and more.

## Features

- Multi-Agent Architecture
- Infrastructure as Code Generation
- Digital Twin Visualization
- Vector Database Learning
- Simulation Engine

## Setup

Run \`source venv/bin/activate\` to activate the virtual environment.
EOL

echo "Development environment setup complete!"
echo "To get started, navigate to ~/infra-automation and activate the virtual environment:"
echo "cd ~/infra-automation && source venv/bin/activate"