# Infrastructure Automation Scripts

This directory contains scripts for managing the infrastructure automation platform.

## Environment Management Scripts

### `manage_environment.sh`

This script is used to manage individual environments.

**Usage:**
```bash
./manage_environment.sh delete <environment_id>
```

### `one_click_environment.sh`

This script provides a one-click solution for creating and managing environments.

**Usage:**
```bash
# Create a new environment
./one_click_environment.sh create [environment_name]

# Delete an environment
./one_click_environment.sh delete [environment_id]

# List all environments
./one_click_environment.sh list
```

The script automatically handles port assignments and environment setup.

### `cleanup_environments.sh`

This script cleans up environments, keeping only the most recent ones.

**Usage:**
```bash
# Keep the 2 most recent environments (default)
./cleanup_environments.sh

# Keep a specific number of environments
./cleanup_environments.sh 3
```

### `auto_cleanup.sh`

This is a non-interactive version of the cleanup script that can be run automatically.

**Usage:**
```bash
# Keep the 2 most recent environments (default)
./auto_cleanup.sh

# Keep a specific number of environments
./auto_cleanup.sh 3
```

## API Database Management Scripts

### `reset_api_db.sh`

This script resets the API database, keeping only the most recent environments.

**Usage:**
```bash
# Keep the 2 most recent environments (default)
./reset_api_db.sh

# Keep a specific number of environments
./reset_api_db.sh 3
```

### `auto_reset_api_db.sh`

This is a non-interactive version of the reset script that can be run automatically.

**Usage:**
```bash
# Keep the 2 most recent environments (default)
./auto_reset_api_db.sh

# Keep a specific number of environments
./auto_reset_api_db.sh 3
```

## Cron Job Setup

To automatically clean up environments and reset the API database, you can set up a cron job:

```bash
# Edit the crontab
crontab -e

# Add the following line to run the cleanup script daily at 2 AM
0 2 * * * /home/satish/infra-automation/scripts/auto_cleanup.sh

# Add the following line to reset the API database weekly on Sunday at 3 AM
0 3 * * 0 /home/satish/infra-automation/scripts/auto_reset_api_db.sh
``` 