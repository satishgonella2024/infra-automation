FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for ChromaDB data
RUN mkdir -p /app/chroma_data && chmod 777 /app/chroma_data

# Set environment variables
ENV PYTHONPATH=/app
ENV LLM_PROVIDER=ollama
ENV LLM_MODEL=llama3
ENV LLM_API_BASE=http://ollama:11434
ENV CHROMA_DB_PATH=/app/chroma_data

# Expose the API port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.api.server"]