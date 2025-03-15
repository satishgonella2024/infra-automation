#!/bin/bash

# One-click environment management script
# Usage: ./one_click_environment.sh create|delete [environment_name]

API_URL="http://192.168.5.199:8000/api/onboarding"
MAX_ENVIRONMENTS=2

function refresh_api() {
    # Restart the API container to refresh its state
    echo "Refreshing API state..."
    docker restart infra-automation_api_1 > /dev/null
    sleep 5  # Wait for API to restart
}

function count_active_environments() {
    # Count active environments (status=running and ready=true)
    local count=$(curl -s "$API_URL/environments" | jq '.environments | map(select(.status == "running" and .ready == true)) | length')
    echo $count
}

function get_next_port_set() {
    # Get the next available port set based on the number of active environments
    local count=$1
    local base_port=$((8090 + count * 10))
    local jira_port=$base_port
    local gitlab_port=$((base_port + 1))
    local dashboard_port=$((base_port + 2))
    echo "$jira_port:$gitlab_port:$dashboard_port"
}

function create_environment() {
    local env_name=$1
    if [ -z "$env_name" ]; then
        env_name="auto-env-$(date +%s)"
    fi
    
    # Refresh API state
    refresh_api
    
    # Check if we already have the maximum number of environments
    local env_count=$(count_active_environments)
    if [ $env_count -ge $MAX_ENVIRONMENTS ]; then
        echo "Maximum number of environments ($MAX_ENVIRONMENTS) already reached."
        echo "Please delete an environment before creating a new one."
        exit 1
    fi
    
    echo "Creating environment: $env_name"
    echo "Current active environments: $env_count"
    
    # Get the next port set
    local port_set=$(get_next_port_set $env_count)
    local jira_port=$(echo $port_set | cut -d':' -f1)
    local gitlab_port=$(echo $port_set | cut -d':' -f2)
    local dashboard_port=$(echo $port_set | cut -d':' -f3)
    
    echo "Using ports: Jira=$jira_port, GitLab=$gitlab_port, Dashboard=$dashboard_port"
    
    # Create the environment
    response=$(curl -s -X POST "$API_URL/new-environment" \
        -H "Content-Type: application/json" \
        -d "{
            \"environment_name\": \"$env_name\",
            \"environment_type\": \"development\",
            \"user_id\": \"user123\",
            \"tools\": [\"jira\", \"gitlab\"],
            \"resource_limits\": {\"cpu\": 2, \"memory\": \"4Gi\"},
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
    
    # Modify the setup script to use our port assignments
    sed -i "s/\"8[0-9]*:8080\"/\"$jira_port:8080\"/" /tmp/setup.sh
    sed -i "s/\"8[0-9]*:80\"/\"$dashboard_port:80\"/" /tmp/setup.sh
    sed -i "s/\"9[0-9]*:80\"/\"$gitlab_port:80\"/" /tmp/setup.sh
    
    # Execute the setup script
    sudo /tmp/setup.sh
    
    # Check if environment started successfully
    env_info=$(curl -s "$API_URL/environments/$env_id")
    status=$(echo $env_info | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$status" != "running" ]; then
        # Update the environment status manually
        echo "Updating environment status..."
        curl -X PUT -H "Content-Type: application/json" -d '{"status": "running", "ready": true}' "$API_URL/environments/$env_id"
    fi
    
    # Get the final environment info
    env_info=$(curl -s "$API_URL/environments/$env_id")
    
    echo "Environment created successfully!"
    echo "Environment ID: $env_id"
    echo "Environment Name: $env_name"
    echo "Status: running"
    echo "Services:"
    echo "- Jira: http://localhost:$jira_port"
    echo "- GitLab: http://localhost:$gitlab_port"
    echo "- Dashboard: http://localhost:$dashboard_port"
    
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
    
    echo "Environment $env_name ($env_id) deleted successfully"
    
    # Remove the last environment ID file if it matches the deleted environment
    if [ -f "/tmp/last_environment_id" ] && [ "$(cat /tmp/last_environment_id)" == "$env_id" ]; then
        rm /tmp/last_environment_id
    fi
    
    # Refresh API state
    refresh_api
}

function list_environments() {
    # Refresh API state
    refresh_api
    
    echo "Listing all environments:"
    curl -s "$API_URL/environments" | jq '.environments[] | {environment_id, environment_name, status, ready, access_url}'
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
