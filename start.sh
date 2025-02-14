#!/usr/bin/env bash
set -e

echo "[start.sh] Starting up..."

########################################
# 1. Load NGROK_AUTH_TOKEN from .env if present
########################################
# Because 'docker run' doesn't automatically read .env files,
# we do it ourselves if the file exists inside the container.
if [ -z "$NGROK_AUTH_TOKEN" ] && [ -f "/app/.env" ]; then
  echo "[start.sh] Reading .env file to load NGROK_AUTH_TOKEN..."
  # This exports variables defined in /app/.env (ignoring commented lines).
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
# 3. Start Ngrok in the background, tunneling host.docker.internal:11434
########################################
echo "[start.sh] Starting ngrok to forward host.docker.internal:11434..."
ngrok http host.docker.internal:11434 --log=stdout --log-format=json > /tmp/ngrok.log 2>&1 &

# Give ngrok time to initialize
sleep 5

########################################
# 4. Retrieve the new public URL from ngrok's local API
########################################
TUNNEL_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r .tunnels[0].public_url)

if [ -z "$TUNNEL_URL" ] || [ "$TUNNEL_URL" = "null" ]; then
  echo "[start.sh] ERROR: Could not retrieve ngrok tunnel URL!"
  cat /tmp/ngrok.log  # Print ngrok logs for debugging
  exit 1
fi

echo "[start.sh] ngrok public URL: $TUNNEL_URL"

########################################
# 5. Export the URL as OLLAMA_PUBLIC_URL
########################################
export OLLAMA_PUBLIC_URL="${TUNNEL_URL}/api/generate"

########################################
# 6. Run Streamlit
########################################
echo "[start.sh] Starting Streamlit..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0