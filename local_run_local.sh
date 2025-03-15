#!/usr/bin/env bash
set -e

########################################
# 1) Clean up leftover processes
########################################
echo "[local_run_local.sh] Killing leftover processes (ollama)..."
pkill -f ollama || echo "[local_run_local.sh] No existing ollama process found."

echo "[local_run_local.sh] Checking if anything is using port 11434..."
lsof -i :11434 | grep LISTEN && echo "[local_run_local.sh] Port 11434 is in use; attempting to kill..." && lsof -t -i :11434 | xargs sudo kill -9 || echo "[local_run_local.sh] Port 11434 is free."

########################################
# 2) Start Ollama on port 11434
########################################
echo "[local_run_local.sh] Starting Ollama on port 11434..."
# We leave OLLAMA_ORIGINS blank since Nginx will rewrite the Host header.
export OLLAMA_ORIGINS=""
ollama serve &
# Give Ollama a moment to start
sleep 3

########################################
# 3) Start the Streamlit app directly (using app_local.py)
########################################
echo "[local_run_local.sh] Starting Streamlit app..."
streamlit run app_local.py --server.port=8501 --server.address=0.0.0.0