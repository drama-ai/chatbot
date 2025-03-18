#!/usr/bin/env bash
set -e

echo "[start.sh] Starting up..."
echo "[start.sh] OLLAMA_PUBLIC_URL: $OLLAMA_PUBLIC_URL"

########################################
# 1. Load NGROK_AUTH_TOKEN from .env if present
########################################
if [ -z "$NGROK_AUTH_TOKEN" ] && [ -f "/app/.env" ]; then
  echo "[start.sh] Reading .env file to load NGROK_AUTH_TOKEN..."
  export $(grep -v '^#' /app/.env | xargs)
fi

########################################
# 2. If we have a token, run 'ngrok authtoken' (v2 syntax)
########################################
if [ -n "$NGROK_AUTH_TOKEN" ]; then
  echo "[start.sh] Adding ngrok authtoken (v2 syntax)"
  ngrok authtoken "$NGROK_AUTH_TOKEN"
fi

########################################
# 3. If OLLAMA_PUBLIC_URL is not provided, start ngrok inside the container
########################################
if [ -z "$OLLAMA_PUBLIC_URL" ]; then
  echo "[start.sh] OLLAMA_PUBLIC_URL not set. Starting ngrok to forward host.docker.internal:11434..."
  ngrok http host.docker.internal:11434 --log=stdout --log-format=json > /tmp/ngrok.log 2>&1 &
  
  # Give ngrok time to initialize
  sleep 5
  
  TUNNEL_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r .tunnels[0].public_url)
  
  if [ -z "$TUNNEL_URL" ] || [ "$TUNNEL_URL" = "null" ]; then
    echo "[start.sh] ERROR: Could not retrieve ngrok tunnel URL!"
    cat /tmp/ngrok.log
    exit 1
  fi
  
  echo "[start.sh] ngrok public URL: $TUNNEL_URL"
  export OLLAMA_PUBLIC_URL="${TUNNEL_URL}/api/generate"
  echo "[start.sh] OLLAMA_PUBLIC_URL set to: $OLLAMA_PUBLIC_URL"
else
  echo "[start.sh] Using provided OLLAMA_PUBLIC_URL: $OLLAMA_PUBLIC_URL"
fi

########################################
# 4. Set Ollama to listen on all interfaces to bypass VPN restrictions
########################################
export OLLAMA_HOST="0.0.0.0:11434"

########################################
# 5. Run Streamlit
########################################
echo "[start.sh] Starting Streamlit..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0