FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    linux-headers-generic \
    procps \
    gcc \
    curl \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Install Docker Compose
RUN curl -L "https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# Add separate section for optional GPU monitoring tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add - \
    && distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
    && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list > /etc/apt/sources.list.d/nvidia-docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nvidia-container-toolkit-base || true \
    && rm -rf /var/lib/apt/lists/*

# Install psutil first
RUN pip install --no-cache-dir psutil>=5.9.0

# Create data directory with proper permissions early
RUN mkdir -p /app/data /app/chroma_data /app/data/environments && \
    chmod -R 777 /app/data && \
    chmod -R 777 /app/chroma_data && \
    chmod -R 777 /app/data/environments

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure permissions are set after copying files
RUN chmod -R 777 /app/data && \
    chmod -R 777 /app/chroma_data && \
    chmod -R 777 /app/data/environments

# Set environment variables
ENV PYTHONPATH=/app
ENV LLM_PROVIDER=ollama
ENV LLM_MODEL=llama3
ENV LLM_API_BASE=http://ollama:11434
ENV CHROMA_DB_PATH=/app/chroma_data
ENV HOST_DEPLOYMENT=true

# Expose the API port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.api.server"]