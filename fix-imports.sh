#!/bin/bash
# Script to fix Python import issues by updating __init__.py files

echo "Fixing import issues in __init__.py files..."

# Fix LLMService import
echo "Creating/updating src/services/llm/__init__.py"
echo "from .llm_service import LLMService" > src/services/llm/__init__.py

# Fix InfrastructureAgent import
echo "Creating/updating src/agents/infra/__init__.py"
echo "from .infrastructure_agent import InfrastructureAgent" > src/agents/infra/__init__.py

# Fix BaseAgent import
echo "Creating/updating src/agents/base/__init__.py"
echo "from .base_agent import BaseAgent" > src/agents/base/__init__.py

# Create/update other potential __init__.py files
echo "Creating/updating other module __init__.py files"
mkdir -p src/api && touch src/api/__init__.py
mkdir -p src/utils && touch src/utils/__init__.py

# Ensure __init__.py exists in all directories
echo "Ensuring all directories have __init__.py files"
find src -type d -exec touch {}/__init__.py \;

echo "Import fixes complete!"
