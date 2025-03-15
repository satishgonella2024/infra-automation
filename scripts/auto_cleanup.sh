#!/bin/bash

# Automatic cleanup script to delete all environments except for the most recent ones
# Usage: ./auto_cleanup.sh [keep_count]

API_URL="http://192.168.5.199:8000/api/onboarding"
KEEP_COUNT=${1:-2}  # Default to keeping 2 environments if not specified

# Restart the API container to refresh its state
echo "Refreshing API state..."
docker restart infra-automation_api_1 > /dev/null
sleep 5  # Wait for API to restart

# Get all environments
echo "Fetching environment data..."
ENVIRONMENTS=$(curl -s "$API_URL/environments" | jq '.environments')

# Count total environments
TOTAL_COUNT=$(echo $ENVIRONMENTS | jq 'length')
echo "Found $TOTAL_COUNT environments"

# If we have fewer environments than we want to keep, exit
if [ $TOTAL_COUNT -le $KEEP_COUNT ]; then
    echo "Only $TOTAL_COUNT environments exist, which is less than or equal to the number to keep ($KEEP_COUNT). No cleanup needed."
    exit 0
fi

# Sort environments by creation date (newest first)
SORTED_ENVIRONMENTS=$(echo $ENVIRONMENTS | jq 'sort_by(.created_at) | reverse')

# Get the IDs of environments to keep
echo "Keeping the $KEEP_COUNT most recent environments:"
KEEP_IDS=()
for i in $(seq 0 $(($KEEP_COUNT-1))); do
    if [ $i -lt $TOTAL_COUNT ]; then
        ENV_ID=$(echo $SORTED_ENVIRONMENTS | jq -r ".[$i].environment_id")
        ENV_NAME=$(echo $SORTED_ENVIRONMENTS | jq -r ".[$i].environment_name")
        KEEP_IDS+=($ENV_ID)
        echo "- $ENV_NAME ($ENV_ID)"
    fi
done

# Get the IDs of environments to delete
echo "Environments to delete:"
DELETE_COUNT=0
for i in $(seq $KEEP_COUNT $(($TOTAL_COUNT-1))); do
    ENV_ID=$(echo $SORTED_ENVIRONMENTS | jq -r ".[$i].environment_id")
    ENV_NAME=$(echo $SORTED_ENVIRONMENTS | jq -r ".[$i].environment_name")
    ENV_STATUS=$(echo $SORTED_ENVIRONMENTS | jq -r ".[$i].status")
    
    # Check if this ID is in the keep list
    KEEP=false
    for keep_id in "${KEEP_IDS[@]}"; do
        if [ "$keep_id" == "$ENV_ID" ]; then
            KEEP=true
            break
        fi
    done
    
    if [ "$KEEP" == "false" ]; then
        echo "- $ENV_NAME ($ENV_ID) - Status: $ENV_STATUS"
        DELETE_COUNT=$((DELETE_COUNT+1))
    fi
done

if [ $DELETE_COUNT -eq 0 ]; then
    echo "No environments to delete."
    exit 0
fi

# Delete environments automatically without confirmation
echo "Deleting $DELETE_COUNT environments automatically..."
for i in $(seq $KEEP_COUNT $(($TOTAL_COUNT-1))); do
    ENV_ID=$(echo $SORTED_ENVIRONMENTS | jq -r ".[$i].environment_id")
    ENV_NAME=$(echo $SORTED_ENVIRONMENTS | jq -r ".[$i].environment_name")
    
    # Check if this ID is in the keep list
    KEEP=false
    for keep_id in "${KEEP_IDS[@]}"; do
        if [ "$keep_id" == "$ENV_ID" ]; then
            KEEP=true
            break
        fi
    done
    
    if [ "$KEEP" == "false" ]; then
        echo "Deleting $ENV_NAME ($ENV_ID)..."
        
        # Stop and remove containers
        echo "Stopping containers..."
        
        # Try to stop containers using docker-compose in the environment directory
        if [ -d "/home/satish/infra-automation/data/environments/$ENV_ID" ]; then
            cd "/home/satish/infra-automation/data/environments/$ENV_ID" && sudo docker-compose down -v
        else
            echo "Environment directory not found, trying to stop containers directly"
        fi
        
        # Check if containers are still running with the env prefix
        env_prefix="env-${ENV_ID:0:8}"
        running_containers=$(docker ps --filter "name=$env_prefix" -q)
        
        if [ ! -z "$running_containers" ]; then
            echo "Found running containers with prefix $env_prefix, stopping them..."
            docker stop $running_containers
            docker rm $running_containers
        fi
        
        # Delete the environment from the API
        response=$(curl -s -X DELETE "$API_URL/environments/$ENV_ID")
        
        echo "Environment $ENV_NAME ($ENV_ID) deleted successfully"
    fi
done

# Restart the API container to refresh its state
echo "Refreshing API state..."
docker restart infra-automation_api_1 > /dev/null
sleep 5  # Wait for API to restart

# Check remaining environments
REMAINING=$(curl -s "$API_URL/environments" | jq '.environments | length')
echo "Cleanup complete. $REMAINING environments remaining." 