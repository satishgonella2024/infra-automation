#!/bin/bash
# Script to run integration tests for the Infrastructure Automation service

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Infrastructure Automation Integration Tests ===${NC}"

# Set environment variables
export API_URL=http://localhost:8000
export OLLAMA_URL=http://localhost:11434

# Check if Ollama is running
echo -e "${YELLOW}Checking if Ollama is running...${NC}"
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}Starting Ollama...${NC}"
    # Set Ollama to listen on all interfaces
    OLLAMA_HOST=0.0.0.0:11434 ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to start
    echo -e "${YELLOW}Waiting for Ollama to start...${NC}"
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/version > /dev/null; then
            echo -e "${GREEN}✓ Ollama started successfully${NC}"
            break
        fi
        
        if [ $i -eq 10 ]; then
            echo -e "${RED}✗ Failed to start Ollama${NC}"
            exit 1
        fi
        
        sleep 2
    done
fi

# Check if the llama3 model is available
echo -e "${YELLOW}Checking if llama3 model is available...${NC}"
if curl -s http://localhost:11434/api/tags | grep -q "llama3"; then
    echo -e "${GREEN}✓ llama3 model is available${NC}"
else
    echo -e "${YELLOW}Pulling llama3 model...${NC}"
    ollama pull llama3
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to pull llama3 model${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ llama3 model pulled successfully${NC}"
fi

# Start the services with Docker Compose
echo -e "${YELLOW}Starting services with Docker Compose...${NC}"
docker-compose down
docker-compose up -d

# Wait for the API service to start
echo -e "${YELLOW}Waiting for API service to start...${NC}"
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ API service started successfully${NC}"
        break
    fi
    
    if [ $i -eq 10 ]; then
        echo -e "${RED}✗ Failed to start API service${NC}"
        docker-compose logs api
        docker-compose down
        exit 1
    fi
    
    sleep 2
done

# Run the integration tests
echo -e "${YELLOW}Running integration tests...${NC}"
python run_tests.py

# Store the exit code
exit_code=$?

# Run the infrastructure generation tests
echo -e "${YELLOW}Running infrastructure generation tests...${NC}"
./test_infra_generation.py
INFRA_GEN_EXIT_CODE=$?

# Store the combined exit code
if [ $exit_code -eq 0 ] && [ $INFRA_GEN_EXIT_CODE -eq 0 ]; then
    EXIT_CODE=0
else
    EXIT_CODE=1
fi

# Stop the services
echo -e "${YELLOW}Stopping services...${NC}"
docker-compose down

# Exit with the test result
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed${NC}"
fi

exit $EXIT_CODE 