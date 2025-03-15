# Infrastructure Automation Platform - Product Requirements Document (PRD)

## 1. Executive Summary

The Infrastructure Automation Platform is designed to streamline the creation, management, and cleanup of development environments. It provides a centralized system for provisioning infrastructure resources, managing their lifecycle, and ensuring efficient resource utilization through automated cleanup processes.

## 2. Vision

To create a self-service platform that enables developers to quickly provision standardized development environments with minimal manual intervention, while ensuring efficient resource utilization through automated lifecycle management.

## 3. Target Users

- **Developers**: Need quick access to development environments
- **DevOps Engineers**: Manage the platform and infrastructure resources
- **System Administrators**: Monitor resource usage and system health
- **Project Managers**: Track environment usage for projects

## 4. Current System Overview

The platform consists of:

1. **API Service**: RESTful API for environment management
2. **Database**: JSON-based storage for environment metadata
3. **Container Orchestration**: Docker-based deployment of environments
4. **Automation Scripts**: Shell scripts for environment lifecycle management

## 5. Core Features

### 5.1 Environment Provisioning

- **One-Click Environment Creation**: Simplified interface for creating new environments
- **Standardized Templates**: Pre-configured environment templates
- **Resource Allocation**: Automatic port assignment and resource allocation
- **Status Tracking**: Real-time status updates during provisioning

### 5.2 Environment Management

- **Environment Listing**: View all provisioned environments
- **Status Monitoring**: Track the status of each environment
- **Access Management**: Manage access to environments
- **Resource Monitoring**: Track resource usage of environments

### 5.3 Automated Cleanup

- **Environment Retention Policies**: Keep only the most recent environments
- **Scheduled Cleanup**: Automatic cleanup of old environments
- **Database Synchronization**: Keep the API database in sync with actual environments
- **Backup Management**: Create backups before cleanup operations

## 6. Technical Requirements

### 6.1 API Service

- **RESTful API**: Provide endpoints for environment management
- **Authentication**: Secure access to API endpoints
- **Rate Limiting**: Prevent abuse of API endpoints
- **Error Handling**: Proper error responses and logging

### 6.2 Database

- **Schema Design**: Efficient storage of environment metadata
- **Backup and Recovery**: Regular backups of database
- **Data Integrity**: Ensure consistency between database and actual environments
- **Performance**: Optimize for quick reads and writes

### 6.3 Container Orchestration

- **Docker Integration**: Use Docker for container management
- **Resource Limits**: Enforce CPU and memory limits
- **Networking**: Manage port assignments and network isolation
- **Volume Management**: Handle persistent storage for environments

### 6.4 Automation Scripts

- **Environment Creation**: Scripts for creating new environments
- **Environment Cleanup**: Scripts for cleaning up old environments
- **Database Reset**: Scripts for resetting the API database
- **Scheduled Execution**: Support for cron-based scheduling

## 7. Implementation Status

### 7.1 Completed Features

- ✅ One-click environment creation script
- ✅ Environment cleanup script (interactive and non-interactive)
- ✅ API database reset script (interactive and non-interactive)
- ✅ Automatic port assignment
- ✅ Environment status tracking
- ✅ Backup creation before operations

### 7.2 In Progress Features

- 🔄 User authentication and authorization
- 🔄 Resource usage monitoring
- 🔄 Enhanced error handling and recovery
- 🔄 Web-based management interface

### 7.3 Planned Features

- 📅 Multi-user support with role-based access control
- 📅 Integration with CI/CD pipelines
- 📅 Advanced resource scheduling and optimization
- 📅 Metrics and analytics dashboard

## 8. Automation Scripts

### 8.1 Environment Management

| Script | Purpose | Status |
|--------|---------|--------|
| `manage_environment.sh` | Manage individual environments | ✅ Completed |
| `one_click_environment.sh` | One-click solution for environment creation | ✅ Completed |
| `cleanup_environments.sh` | Clean up old environments (interactive) | ✅ Completed |
| `auto_cleanup.sh` | Clean up old environments (non-interactive) | ✅ Completed |

### 8.2 Database Management

| Script | Purpose | Status |
|--------|---------|--------|
| `reset_api_db.sh` | Reset API database (interactive) | ✅ Completed |
| `auto_reset_api_db.sh` | Reset API database (non-interactive) | ✅ Completed |

## 9. Maintenance and Operations

### 9.1 Scheduled Tasks

- **Daily Cleanup**: Run `auto_cleanup.sh` daily at 2 AM to remove old environments
- **Weekly Database Reset**: Run `auto_reset_api_db.sh` weekly on Sunday at 3 AM to reset the API database

### 9.2 Monitoring

- Monitor API container health
- Track environment creation and deletion events
- Monitor resource usage across all environments
- Alert on failures or resource constraints

### 9.3 Backup Strategy

- Database backups before any reset operation
- Regular backups of environment configurations
- Retention policy for backups

## 10. Success Metrics

- **Provisioning Time**: Time to create a new environment (target: < 5 minutes)
- **Resource Utilization**: Percentage of allocated resources actually used
- **Cleanup Efficiency**: Number of environments automatically cleaned up
- **System Uptime**: Availability of the platform (target: 99.9%)
- **User Satisfaction**: Feedback from developers using the platform

## 11. Future Roadmap

### Short-term (1-3 months)

- Implement web-based management interface
- Add user authentication and authorization
- Enhance error handling and recovery mechanisms
- Implement resource usage monitoring

### Medium-term (3-6 months)

- Add support for multiple environment types
- Implement role-based access control
- Integrate with CI/CD pipelines
- Develop metrics and analytics dashboard

### Long-term (6+ months)

- Support for multi-cloud deployments
- Implement advanced resource scheduling
- Add predictive scaling based on usage patterns
- Develop self-healing capabilities

## 12. Appendix

### API Endpoints

- `GET /api/onboarding/environments`: List all environments
- `GET /api/onboarding/environments/{id}`: Get environment details
- `POST /api/onboarding/new-environment`: Create a new environment
- `PUT /api/onboarding/environments/{id}`: Update environment status
- `DELETE /api/onboarding/environments/{id}`: Delete an environment

### Environment Lifecycle

1. **Creation**: Environment is created with status "creating"
2. **Preparation**: Environment is prepared with status "prepared"
3. **Running**: Environment is started with status "running" and ready=true
4. **Deletion**: Environment is deleted

### Resource Allocation

- Each environment is allocated a set of ports:
  - Jira: Base port (e.g., 8090)
  - GitLab: Base port + 1 (e.g., 8091)
  - Dashboard: Base port + 2 (e.g., 8092)
- Port allocation is based on the number of active environments 