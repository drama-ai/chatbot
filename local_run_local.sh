#!/usr/bin/env bash
set -e

########################################
# 1) Clean up leftover processes
########################################
echo "[local_run_local.sh] Killing leftover processes (ollama)..."
pkill -f ollama || echo "[local_run_local.sh] No existing ollama process found."

########################################
# 2) Check if port 11434 is in use
########################################
echo "[local_run_local.sh] Checking if anything is using port 11434..."
lsof -i :11434 | grep LISTEN && echo "[local_run_local.sh] Port 11434 is in use; attempting to kill..." && lsof -t -i :11434 | xargs sudo kill -9 || echo "[local_run_local.sh] Port 11434 is free."

########################################
# 3) Start Ollama on port 11434
########################################
echo "[local_run_local.sh] Starting Ollama on port 11434..."
ollama serve &

# Give Ollama a moment to start
sleep 3

########################################
# 4) Start the Streamlit app
########################################
echo "[local_run_local.sh] Starting Streamlit app..."
streamlit run app_local.py --server.port=8501 --server.address=0.0.0.0