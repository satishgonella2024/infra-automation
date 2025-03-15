#!/bin/bash

# Script to reset the API database
# Usage: ./reset_api_db.sh [keep_count]

API_URL="http://192.168.5.199:8000/api/onboarding"
KEEP_COUNT=${1:-2}  # Default to keeping 2 environments if not specified

echo "This script will reset the API database, keeping only the $KEEP_COUNT most recent environments."
echo "WARNING: This will remove all environment records from the API database."
read -p "Are you sure you want to continue? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Reset cancelled."
    exit 0
fi

# Get all environments
echo "Fetching environment data..."
ENVIRONMENTS=$(curl -s "$API_URL/environments" | jq '.environments')

# Count total environments
TOTAL_COUNT=$(echo $ENVIRONMENTS | jq 'length')
echo "Found $TOTAL_COUNT environments in the API database."

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

# Stop the API container
echo "Stopping API container..."
docker stop infra-automation_api_1

# Backup the current databases
echo "Backing up current databases..."
BACKUP_DIR="/home/satish/infra-automation/data/backups"
mkdir -p $BACKUP_DIR
BACKUP_TIME=$(date +%Y%m%d_%H%M%S)

# Backup main database
MAIN_DB_BACKUP="$BACKUP_DIR/api_db_backup_$BACKUP_TIME.json"
docker cp infra-automation_api_1:/app/data/db.json $MAIN_DB_BACKUP 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Main database backed up to $MAIN_DB_BACKUP"
else
    echo "Warning: Could not backup main database, it may not exist yet."
    echo "{\"environments\": []}" > $MAIN_DB_BACKUP
fi

# Backup environments database
ENV_DB_BACKUP="$BACKUP_DIR/environments_db_backup_$BACKUP_TIME.json"
docker cp infra-automation_api_1:/app/data/environments/environments.json $ENV_DB_BACKUP 2>/dev/null
if [ $? -eq 0 ]; then
    echo "Environments database backed up to $ENV_DB_BACKUP"
else
    echo "Warning: Could not backup environments database, it may not exist yet."
    echo "{}" > $ENV_DB_BACKUP
fi

# Create a new main database with only the environments to keep
echo "Creating new main database with only the environments to keep..."
TMP_MAIN_DB="/tmp/new_main_db.json"
echo "{\"environments\": []}" > $TMP_MAIN_DB

# Create a new environments database with only the environments to keep
echo "Creating new environments database with only the environments to keep..."
TMP_ENV_DB="/tmp/new_env_db.json"
echo "{}" > $TMP_ENV_DB

# Add the environments to keep to the new databases
for keep_id in "${KEEP_IDS[@]}"; do
    # Add to main database
    ENV_DATA=$(echo $ENVIRONMENTS | jq ".[] | select(.environment_id == \"$keep_id\")")
    if [ ! -z "$ENV_DATA" ]; then
        # Add the environment to the new main database
        jq --argjson env "$ENV_DATA" '.environments += [$env]' $TMP_MAIN_DB > $TMP_MAIN_DB.tmp
        mv $TMP_MAIN_DB.tmp $TMP_MAIN_DB
        
        # Add to environments database
        ENV_DETAIL=$(cat $ENV_DB_BACKUP | jq ".\"$keep_id\"")
        if [ ! -z "$ENV_DETAIL" ] && [ "$ENV_DETAIL" != "null" ]; then
            # Add the environment to the new environments database
            jq --arg id "$keep_id" --argjson env "$ENV_DETAIL" '. + {($id): $env}' $TMP_ENV_DB > $TMP_ENV_DB.tmp
            mv $TMP_ENV_DB.tmp $TMP_ENV_DB
        fi
    fi
done

# Create environments directory if it doesn't exist
docker exec infra-automation_api_1 mkdir -p /app/data/environments

# Copy the new databases to the API container
echo "Copying new databases to API container..."
docker cp $TMP_MAIN_DB infra-automation_api_1:/app/data/db.json
docker cp $TMP_ENV_DB infra-automation_api_1:/app/data/environments/environments.json

# Start the API container
echo "Starting API container..."
docker start infra-automation_api_1
echo "Waiting for API to start..."
sleep 10

# Check the environments
echo "Checking environments after reset..."
REMAINING=$(curl -s "$API_URL/environments" | jq '.environments | length')
echo "Reset complete. $REMAINING environments remaining in the API database."

# Clean up
rm $TMP_MAIN_DB $TMP_ENV_DB
echo "Temporary files cleaned up." 