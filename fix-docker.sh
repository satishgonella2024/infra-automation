#!/bin/bash
# Fix script for Multi-Agent Infrastructure Automation System

echo "Fixing Docker setup issues..."

# Update Dockerfile to fix GPG issue
cat > Dockerfile << 'EOL'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    gnupg \
    lsb-release \
    software-properties-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/templates

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "src.main", "--mode", "api", "--config", "configs/config.yaml"]
EOL

echo "Updated Dockerfile to fix GPG issues"

# Create __init__.py files for Python modules
echo "Creating __init__.py files for Python packages"
find src -type d -exec touch {}/__init__.py \;

# Update docker-compose.yml
cat > docker-compose.yml << 'EOL'
version: '3.8'

services:
  # Core API service
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
      - ./data:/app/data
    environment:
      - LLM_PROVIDER=ollama
      - LLM_MODEL=llama2
      - LLM_API_BASE=http://ollama:11434/api
    depends_on:
      - ollama
      - vector-db
    command: ["python", "-m", "src.main", "--mode", "api", "--config", "configs/config.yaml"]
    networks:
      - infra-network
    restart: unless-stopped

  # Ollama LLM service
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ./ollama-models:/root/.ollama
    networks:
      - infra-network
    restart: unless-stopped
    # GPU configuration - Option 1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    # GPU configuration - Option 2 (uncomment if Option 1 doesn't work)
    # environment:
    #   - NVIDIA_VISIBLE_DEVICES=all
    # runtime: nvidia

  # Vector database for agent memory
  vector-db:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./vector-db-data:/qdrant/storage
    networks:
      - infra-network
    restart: unless-stopped

networks:
  infra-network:
    driver: bridge
EOL

echo "Updated docker-compose.yml with improved GPU configuration"

# Create a basic UI placeholder
mkdir -p ui
cat > ui/Dockerfile << 'EOL'
FROM node:18-slim

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
EOL

echo "Created UI placeholder"

# Ensure all Python scripts are properly formatted
for file in src/agents/base/base_agent.py src/agents/infra/infrastructure_agent.py src/services/llm/llm_service.py src/api/server.py src/main.py src/utils/template_utils.py; do
  if [ -f "$file" ]; then
    echo "Checking script: $file"
    # Simple validation: check if file can be parsed by Python
    python3 -m py_compile "$file" 2>/dev/null
    if [ $? -ne 0 ]; then
      echo "Warning: $file may have syntax errors. Please review it."
    else
      echo "$file looks ok."
    fi
  else
    echo "Warning: $file not found. Make sure all required code files are in place."
  fi
done

echo "Fixed Docker setup. Try running docker-compose up --build now."
