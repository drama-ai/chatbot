#!/usr/bin/env bash
set -e

########################################
# 1) Clean up leftover processes
########################################
echo "[local_run.sh] Killing leftover processes (ollama, nginx, cloudflared)..."
pkill -f ollama || echo "[local_run.sh] No existing ollama process found."
pkill -f nginx || echo "[local_run.sh] No existing nginx process found."
pkill -f cloudflared || echo "[local_run.sh] No existing cloudflared process found."

echo "[local_run.sh] Checking if anything is using port 11434 or 11435..."
lsof -i :11434 | grep LISTEN && echo "[local_run.sh] Port 11434 is in use; attempting to kill..." && lsof -t -i :11434 | xargs sudo kill -9 || echo "[local_run.sh] Port 11434 is free."
lsof -i :11435 | grep LISTEN && echo "[local_run.sh] Port 11435 is in use; attempting to kill..." && lsof -t -i :11435 | xargs sudo kill -9 || echo "[local_run.sh] Port 11435 is free."

########################################
# 2) Start Ollama on port 11434
########################################
echo "[local_run.sh] Starting Ollama on port 11434..."
# We leave OLLAMA_ORIGINS blank since Nginx will rewrite the Host header.
export OLLAMA_ORIGINS=""
ollama serve &
# Give Ollama a moment to start
sleep 3

########################################
# 3) Start system Nginx
########################################
echo "[local_run.sh] Starting (or reloading) system Nginx..."
# This assumes your system Nginx is already configured to proxy from port 11435 to 11434 with:
#   proxy_pass http://127.0.0.1:11434;
#   proxy_set_header Host localhost;
sudo nginx -s reload || sudo nginx

########################################
# 4) Start Cloudflare Tunnel (using your existing configuration)
########################################
echo "[local_run.sh] Starting Cloudflare Tunnel..."
cloudflared tunnel run ollama-tunnel &
# Give Cloudflare Tunnel a moment to initialize
sleep 5

########################################
# 5) Start the Streamlit app directly
########################################
echo "[local_run.sh] Starting Streamlit app..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0