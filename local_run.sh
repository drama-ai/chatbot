#!/usr/bin/env bash
set -e

########################################
# Kill leftover processes that might conflict
########################################
echo "[local_run.sh] Checking and killing any processes using port 11434..."
lsof -ti tcp:11434 | xargs kill -9 2>/dev/null || echo "[local_run.sh] No process using port 11434 found."

echo "[local_run.sh] Killing any existing ngrok processes..."
pkill ngrok 2>/dev/null || echo "[local_run.sh] No ngrok process found."

########################################
# 1) Start Ollama in the background
########################################
echo "[local_run.sh] Starting Ollama on port 11434..."
# Ollama defaults to port 11434, no '-p' flag needed
ollama serve &

########################################
# 2) Start ngrok locally to tunnel port 11434
########################################
echo "[local_run.sh] Starting ngrok to tunnel port 11434..."
ngrok http 11434 --log=stdout --log-format=json > /tmp/ngrok.log 2>&1 &

# Give ngrok time to initialize
sleep 5

########################################
# 3) Grab the public ngrok URL
########################################
TUNNEL_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r .tunnels[0].public_url)
if [ -z "$TUNNEL_URL" ] || [ "$TUNNEL_URL" = "null" ]; then
  echo "[local_run.sh] ERROR: Could not retrieve ngrok tunnel URL!"
  cat /tmp/ngrok.log
  exit 1
fi

echo "[local_run.sh] ngrok public URL: $TUNNEL_URL"

########################################
# 4) Build your Docker image
########################################
echo "[local_run.sh] Building Docker image..."
docker build -t chatbot-ngrok .

########################################
# 5) Run the Docker container, passing the ngrok URL via OLLAMA_PUBLIC_URL
########################################
echo "[local_run.sh] Running Docker container..."
docker run --rm -p 8501:8501 \
  -e OLLAMA_PUBLIC_URL="${TUNNEL_URL}/api/generate" \
  --name chatbot-ngrok \
  chatbot-ngrok