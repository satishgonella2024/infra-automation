#!/bin/bash
# Script to check and ensure the required Ollama model is available

MODEL_NAME="llama3"
echo "Checking if $MODEL_NAME is available in Ollama..."

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
  echo "Ollama is not running. Starting Ollama..."
  ollama serve &
  sleep 5  # Give it time to start
fi

# Check if the model exists
if ! ollama list | grep -q "$MODEL_NAME"; then
  echo "$MODEL_NAME model not found. Pulling it now..."
  ollama pull $MODEL_NAME
  echo "$MODEL_NAME model pulled successfully."
else
  echo "$MODEL_NAME model is already available."
fi

echo "Ollama setup complete with $MODEL_NAME model."