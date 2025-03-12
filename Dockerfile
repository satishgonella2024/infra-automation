FROM python:3.10-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code, excluding venv and other large directories
COPY src/ ./src/
COPY configs/ ./configs/
COPY templates/ ./templates/
# Remove the COPY *.py line since there are no Python files in the root directory

# Create necessary directories
RUN mkdir -p data logs

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "src.main", "--mode", "api", "--config", "configs/config.yaml"]