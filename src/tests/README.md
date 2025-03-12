# Infrastructure Automation Test Suite

This directory contains automated tests for the Infrastructure Automation service. The tests are designed to verify that all components of the system function correctly and to catch regressions when changes are made to the codebase.

## Test Structure

The test suite is organized as follows:

- `conftest.py`: Contains pytest fixtures used across multiple test files
- `run_tests.py`: A script to run all tests with proper configuration
- `test_api_endpoints.py`: Tests for the FastAPI endpoints
- `test_architecture_agent.py`: Tests for the ArchitectureAgent class
- `test_chroma_service.py`: Tests for the ChromaService class
- `test_llm_service.py`: Tests for the LLMService class

## Running Tests

To run all tests:

```bash
python -m src.tests.run_tests
```

To run a specific test file:

```bash
python -m pytest src/tests/test_api_endpoints.py -v
```

To run a specific test:

```bash
python -m pytest src/tests/test_api_endpoints.py::test_health_check -v
```

## Environment Variables

The test suite uses the following environment variables:

- `TESTING=True`: Indicates that the code is running in a test environment
- `LOG_LEVEL=INFO`: Sets the logging level for tests

## Test Coverage

The test suite covers the following components:

1. API Endpoints:
   - `GET /health`
   - `POST /patterns`
   - `GET /patterns/search`
   - `PUT /patterns/{pattern_id}`
   - `DELETE /patterns/{pattern_id}`
   - `POST /infrastructure/generate`

2. ArchitectureAgent:
   - Pattern review
   - Infrastructure generation
   - Code extraction
   - Findings parsing

3. ChromaService:
   - Pattern addition
   - Pattern search
   - Pattern retrieval
   - Pattern update
   - Pattern deletion

4. LLMService:
   - Completion generation
   - Provider selection
   - Error handling

## Mocking

The tests use mocking to isolate components and avoid external dependencies:

- LLM API calls are mocked to avoid actual API requests
- ChromaDB operations are mocked to avoid database dependencies
- FastAPI endpoints use TestClient for HTTP request simulation

## Troubleshooting

If you encounter permission errors when running tests, ensure that:

1. The `TESTING` environment variable is set to `True`
2. The user running the tests has write permissions to the temporary directories

## Adding New Tests

When adding new tests:

1. Follow the existing patterns for consistency
2. Use appropriate fixtures from `conftest.py`
3. Mock external dependencies
4. Ensure tests are isolated and don't depend on external state
5. Add appropriate assertions to verify behavior 