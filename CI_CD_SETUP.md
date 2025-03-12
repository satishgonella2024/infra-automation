# CI/CD Pipeline Setup for Infrastructure Automation

This document outlines the setup and usage of the CI/CD pipeline for the Infrastructure Automation project.

## Overview

The CI/CD pipeline automates the following processes:
- Running tests
- Building Docker images
- Deploying to development and production environments

The pipeline is implemented using:
- Jenkins for orchestration
- Docker for containerization
- Kubernetes for deployment
- Docker Compose for local development

## Prerequisites

- Jenkins server with Kubernetes plugin installed
- Kubernetes cluster (for deployment)
- Docker registry (for storing images)
- Docker and Docker Compose (for local development)

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/infra-automation.git
   cd infra-automation
   ```

2. Start the development environment:
   ```bash
   docker-compose up -d
   ```

3. Run tests locally:
   ```bash
   docker-compose run test
   ```

4. Access the API at http://localhost:8000

## Jenkins Pipeline Setup

1. Configure Jenkins credentials:
   - Add Docker registry credentials with ID `docker-registry-credentials`
   - Add Kubernetes config file with ID `kubeconfig`

2. Create a new Jenkins pipeline:
   - Go to Jenkins > New Item > Pipeline
   - Name it "infra-automation-pipeline"
   - Select "Pipeline script from SCM" in the Definition field
   - Set SCM to Git and provide your repository URL
   - Set the Script Path to "Jenkinsfile"
   - Save the pipeline

3. Configure webhook in your Git repository to trigger the pipeline on code changes.

## Pipeline Stages

The pipeline consists of the following stages:

1. **Checkout**: Retrieves the code from the repository
2. **Install Dependencies**: Installs required Python packages
3. **Run Tests**: Executes the test suite with coverage reporting
4. **Build Docker Image**: Creates a Docker image for the application
5. **Push Docker Image**: Pushes the image to the Docker registry (only on main branch)
6. **Deploy to Development**: Deploys to the development environment (only on main branch)
7. **Deploy to Production**: Deploys to production after manual approval (only on main branch)

## Kubernetes Deployment

The application is deployed to Kubernetes using the manifests in the `k8s` directory:

1. Deploy Ollama LLM service:
   ```bash
   kubectl apply -f k8s/ollama-deployment.yaml
   ```

2. Deploy the Infrastructure Automation service:
   ```bash
   kubectl apply -f k8s/deployment.yaml
   ```

## Environment Variables

The following environment variables can be configured:

| Variable | Description | Default |
|----------|-------------|---------|
| LLM_PROVIDER | LLM provider to use | ollama |
| LLM_MODEL | Model name to use | llama2 |
| LLM_API_BASE | Base URL for LLM API | http://ollama-service:11434 |
| CHROMA_DB_PATH | Path for ChromaDB data | /app/chroma_data |
| TESTING | Enable testing mode | 0 |

## Monitoring and Logs

- Access Jenkins build logs through the Jenkins UI
- Access Kubernetes logs using:
  ```bash
  kubectl logs -f deployment/infra-automation
  kubectl logs -f deployment/ollama
  ```

## Troubleshooting

### Common Issues

1. **Tests failing in CI but passing locally**:
   - Check environment variables in the Jenkins pipeline
   - Ensure all dependencies are installed in the CI environment

2. **Docker build failing**:
   - Verify Docker daemon is running in the Jenkins agent
   - Check if the Docker registry is accessible

3. **Kubernetes deployment failing**:
   - Verify kubeconfig is correct
   - Check if the namespace exists
   - Ensure PersistentVolume is available

## Future Improvements

1. **Add Helm Charts**: Replace raw Kubernetes manifests with Helm charts for more flexible deployments
2. **Implement Blue/Green Deployments**: Reduce downtime during deployments
3. **Add Prometheus Monitoring**: Monitor application performance and health
4. **Implement Canary Releases**: Gradually roll out changes to a subset of users 