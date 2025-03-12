# Infrastructure Automation with GPU-Accelerated LLM

A sophisticated infrastructure automation platform leveraging GPU-accelerated LLM (Llama 3 8B) to generate, validate, and manage cloud infrastructure with a focus on security and compliance.

## System Architecture

### Core Components

- **GPU-Accelerated LLM Service**
  - Model: Meta-Llama-3-8B-Instruct (8.03B parameters)
  - Quantization: Q4_0 (4.33 GiB)
  - Context Length: 8192 tokens
  - Batch Size: 512
  - GPU Layers: All 33 layers offloaded

- **Memory Management**
  - Model Buffer: 4155.99 MiB
  - KV Cache: 1024.00 MiB
  - Compute Buffer: 560.00 MiB
  - Total GPU Usage: ~6GB of 16GB

- **API Layer**
  - Framework: GIN
  - Response Times: 2.5s - 18.3s
  - Parallel Processing: 4 concurrent requests

### Performance Characteristics

- **GPU Utilization**
  - Peak: 75%
  - Temperature Range: 34-47°C
  - Power Usage: 7W-193W (320W capacity)
  - Memory Usage: 6048 MiB / 16376 MiB

- **Model Configuration**
  - Embedding Length: 4096
  - Feed Forward Length: 14336
  - Attention Heads: 32 (8 KV heads)
  - GQA: 4
  - RoPE Base: 500000.0

## Requirements

- NVIDIA GPU with Compute Capability 8.9+
- CUDA 12.4+
- 16GB+ GPU Memory
- Docker & Docker Compose
- Python 3.8+

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/infra-automation.git
   cd infra-automation
   ```

2. Set up the environment:
   ```bash
   ./setup.sh
   ```

3. Configure environment variables:
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

- `POST /api/generate`
  ```json
  {
    "task": "Create an AWS EKS cluster",
    "cloud_provider": "aws",
    "iac_type": "terraform"
  }
  ```

### Example Requests

1. Generate EKS Cluster:
   ```bash
   curl -X POST http://localhost:8000/api/generate \
     -H "Content-Type: application/json" \
     -d '{"task": "Create a highly available EKS cluster", "cloud_provider": "aws", "iac_type": "terraform"}'
   ```

2. Generate RDS Aurora Cluster:
   ```bash
   curl -X POST http://localhost:8000/api/generate \
     -H "Content-Type: application/json" \
     -d '{"task": "Create an Aurora PostgreSQL cluster with 2 read replicas", "cloud_provider": "aws", "iac_type": "terraform"}'
   ```

## Development

### Project Structure

```
infra-automation/
├── src/
│   ├── agents/          # Multi-agent system components
│   ├── services/        # Core services (LLM, Vector DB)
│   ├── models/          # Data models and schemas
│   └── utils/           # Helper utilities
├── configs/             # Configuration files
├── tests/               # Test suites
└── docker/             # Docker configurations
```

### Running Tests

```bash
python -m pytest tests/
```

## Performance Monitoring

Monitor GPU usage:
```bash
nvidia-smi -l 1
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Meta AI for Llama 3
- NVIDIA for GPU & CUDA support
- Contributors and maintainers
