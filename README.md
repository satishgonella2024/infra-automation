# Infrastructure Automation

This project provides an API service for automating infrastructure generation using LLMs.

## Features

- Generate infrastructure code (Terraform, CloudFormation, etc.) from natural language descriptions
- Analyze existing infrastructure for security, cost, and performance improvements
- Provide recommendations for infrastructure optimization
- Support for multiple cloud providers (AWS, Azure, GCP)

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Ollama (for local LLM support)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/infra-automation.git
   cd infra-automation
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start the services:
   ```bash
   docker-compose up -d
   ```

## Usage

### API Endpoints

- `GET /health`: Check if the API is running
- `POST /infrastructure/generate`: Generate infrastructure code
- `POST /infrastructure/analyze`: Analyze existing infrastructure

### Example

```bash
curl -X POST http://localhost:8000/infrastructure/generate \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create an S3 bucket with versioning enabled",
    "requirements": "The bucket should be secure and have versioning enabled",
    "cloud_provider": "aws",
    "iac_type": "terraform"
  }'
```

## Testing

### Unit Tests

Run the unit tests with:

```bash
pytest src/tests/test_unit.py
```

### Integration Tests

Run the integration tests with:

```bash
./run_integration_tests.sh
```

This script will:
1. Check if Ollama is running and the required model is available
2. Start the API service using Docker Compose
3. Run the integration tests
4. Run the infrastructure generation tests
5. Clean up the services

### Infrastructure Generation Tests

The infrastructure generation tests verify that the API can generate valid infrastructure code for various scenarios. These tests are included in the integration test suite, but can also be run separately:

```bash
python run_tests.py
```

The test runner will execute each test individually and provide a summary of the results. The tests include:

- Basic S3 bucket creation
- EC2 instance with security groups
- EKS cluster with node groups
- VPC with subnets
- RDS database with encryption

### CI/CD Integration

The tests are integrated with GitHub Actions workflows defined in `.github/workflows/test.yml`. The workflow includes:

- Unit tests job
- Integration tests job that sets up Ollama, pulls the required model, and runs the tests

## Development

### Project Structure

```
infra-automation/
├── src/
│   ├── api/
│   ├── infrastructure/
│   ├── llm/
│   ├── tests/
│   └── utils/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Meta AI for Llama 3
- NVIDIA for GPU & CUDA support
- Contributors and maintainers
