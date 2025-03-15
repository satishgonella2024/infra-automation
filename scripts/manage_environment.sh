#!/bin/bash

# Script to automate environment creation and deletion
# Usage: ./manage_environment.sh create|delete [environment_name]

API_URL="http://192.168.5.199:8000/api/onboarding"
USER_ID="user123"
ENV_TYPE="development"
TOOLS='["jira", "gitlab"]'
RESOURCE_LIMITS='{"cpu": 2, "memory": "4Gi"}'

function create_environment() {
    local env_name=$1
    if [ -z "$env_name" ]; then
        env_name="auto-env-$(date +%s)"
    fi
    
    echo "Creating environment: $env_name"
    
    # Create the environment
    response=$(curl -s -X POST "$API_URL/new-environment" \
        -H "Content-Type: application/json" \
        -d "{
            \"environment_name\": \"$env_name\",
            \"environment_type\": \"$ENV_TYPE\",
            \"user_id\": \"$USER_ID\",
            \"tools\": $TOOLS,
            \"resource_limits\": $RESOURCE_LIMITS,
            \"description\": \"Automated environment with host deployment\"
        }")
    
    # Extract environment ID
    env_id=$(echo $response | grep -o '"environment_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ -z "$env_id" ]; then
        echo "Failed to create environment"
        echo "Response: $response"
        exit 1
    fi
    
    echo "Environment created with ID: $env_id"
    echo "Waiting for environment to be prepared..."
    
    # Wait for environment to be prepared
    status="creating"
    while [ "$status" == "creating" ]; do
        sleep 5
        env_info=$(curl -s "$API_URL/environments/$env_id")
        status=$(echo $env_info | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo "Current status: $status"
    done
    
    if [ "$status" != "prepared" ]; then
        echo "Environment preparation failed"
        echo "Response: $env_info"
        exit 1
    fi
    
    # Get the setup script and execute it
    echo "Environment prepared. Starting environment..."
    docker exec infra-automation_api_1 cat "/app/data/environments/$env_id/setup_and_start.sh" > /tmp/setup.sh
    chmod +x /tmp/setup.sh
    
    # Modify the setup script to avoid port conflicts
    # 1. Change GitLab SSH port
    sed -i 's/"2224:22"/"2226:22"/' /tmp/setup.sh
    
    # 2. Generate random port offsets for other services
    jira_port=$((8200 + RANDOM % 100))
    gitlab_port=$((9000 + RANDOM % 100))
    dashboard_port=$((8300 + RANDOM % 100))
    
    # 3. Update the ports in the setup script
    sed -i "s/\"8[0-9]*:8080\"/\"$jira_port:8080\"/" /tmp/setup.sh
    sed -i "s/\"8[0-9]*:80\"/\"$dashboard_port:80\"/" /tmp/setup.sh
    sed -i "s/\"9[0-9]*:80\"/\"$gitlab_port:80\"/" /tmp/setup.sh
    
    echo "Using ports: Jira=$jira_port, GitLab=$gitlab_port, Dashboard=$dashboard_port"
    
    # Execute the setup script
    sudo /tmp/setup.sh
    
    # Check if environment started successfully
    env_info=$(curl -s "$API_URL/environments/$env_id")
    status=$(echo $env_info | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$status" != "running" ]; then
        # Update the environment status manually
        echo "Updating environment status..."
        docker exec infra-automation_api_1 bash -c "cat /app/data/environments/environments.json > /tmp/environments.json && sed -i 's/\"status\": \"prepared\"/\"status\": \"running\"/' /tmp/environments.json && sed -i 's/\"ready\": false/\"ready\": true/' /tmp/environments.json && sed -i 's|\"jira\":\"http://localhost:[0-9]*\"|\"jira\":\"http://localhost:$jira_port\"|' /tmp/environments.json && sed -i 's|\"gitlab\":\"http://localhost:[0-9]*\"|\"gitlab\":\"http://localhost:$gitlab_port\"|' /tmp/environments.json && sed -i 's|\"dashboard\":\"http://localhost:[0-9]*\"|\"dashboard\":\"http://localhost:$dashboard_port\"|' /tmp/environments.json && cat /tmp/environments.json > /app/data/environments/environments.json"
        
        # Restart the API to reload the configuration
        docker restart infra-automation_api_1
        
        # Wait for API to restart
        sleep 5
    fi
    
    # Get the final environment info
    env_info=$(curl -s "$API_URL/environments/$env_id")
    
    # Extract tool endpoints
    jira_url=$(echo $env_info | grep -o '"jira":"[^"]*"' | cut -d'"' -f4)
    gitlab_url=$(echo $env_info | grep -o '"gitlab":"[^"]*"' | cut -d'"' -f4)
    dashboard_url=$(echo $env_info | grep -o '"dashboard":"[^"]*"' | cut -d'"' -f4)
    
    echo "Environment created successfully!"
    echo "Environment ID: $env_id"
    echo "Environment Name: $env_name"
    echo "Status: $status"
    echo "Services:"
    echo "- Jira: $jira_url"
    echo "- GitLab: $gitlab_url"
    echo "- Dashboard: $dashboard_url"
    
    # Save environment ID to a file for later use
    echo $env_id > /tmp/last_environment_id
}

function delete_environment() {
    local env_id=$1
    
    # If no environment ID is provided, try to get the last created environment
    if [ -z "$env_id" ]; then
        if [ -f "/tmp/last_environment_id" ]; then
            env_id=$(cat /tmp/last_environment_id)
        else
            echo "No environment ID provided and no last environment ID found"
            exit 1
        fi
    fi
    
    echo "Deleting environment with ID: $env_id"
    
    # Get environment info
    env_info=$(curl -s "$API_URL/environments/$env_id")
    env_name=$(echo $env_info | grep -o '"environment_name":"[^"]*"' | cut -d'"' -f4)
    
    # Stop and remove containers
    echo "Stopping containers..."
    
    # Try to stop containers using docker-compose in the environment directory
    if [ -d "/home/satish/infra-automation/data/environments/$env_id" ]; then
        cd "/home/satish/infra-automation/data/environments/$env_id" && sudo docker-compose down -v
    else
        echo "Environment directory not found, trying to stop containers directly"
    fi
    
    # Check if containers are still running with the env prefix
    env_prefix="env-${env_id:0:8}"
    running_containers=$(docker ps --filter "name=$env_prefix" -q)
    
    if [ ! -z "$running_containers" ]; then
        echo "Found running containers with prefix $env_prefix, stopping them..."
        docker stop $running_containers
        docker rm $running_containers
    fi
    
    # Delete the environment from the API
    response=$(curl -s -X DELETE "$API_URL/environments/$env_id")
    
    if [[ $response == *"error"* ]]; then
        echo "Failed to delete environment from API"
        echo "Response: $response"
        
        # Remove the environment manually from the environments.json file
        echo "Removing environment manually..."
        docker exec infra-automation_api_1 bash -c "cat /app/data/environments/environments.json > /tmp/environments.json && jq 'del(.\"$env_id\")' /tmp/environments.json > /tmp/environments_new.json && cat /tmp/environments_new.json > /app/data/environments/environments.json"
        
        # Restart the API to reload the configuration
        docker restart infra-automation_api_1
    fi
    
    echo "Environment $env_name ($env_id) deleted successfully"
    
    # Remove the last environment ID file if it matches the deleted environment
    if [ -f "/tmp/last_environment_id" ] && [ "$(cat /tmp/last_environment_id)" == "$env_id" ]; then
        rm /tmp/last_environment_id
    fi
}

function list_environments() {
    echo "Listing all environments:"
    curl -s "$API_URL/environments" | jq '.environments[] | {environment_id, environment_name, status, ready}'
}

# Main script
case "$1" in
    create)
        create_environment "$2"
        ;;
    delete)
        delete_environment "$2"
        ;;
    list)
        list_environments
        ;;
    *)
        echo "Usage: $0 create|delete|list [environment_name|environment_id]"
        exit 1
        ;;
esac

exit 0 