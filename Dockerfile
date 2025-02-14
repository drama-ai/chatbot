# Use a slim Python 3.9 base (works on Apple Silicon via Docker buildx if needed)
FROM python:3.9-slim

# Update system packages and install needed tools
RUN apt-get update && apt-get install -y \
    wget curl jq \
 && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ngrok (Linux AMD64). For Apple Silicon cross-compile, see notes below.
RUN wget -O /tmp/ngrok.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz \
    && tar -C /usr/local/bin -xzf /tmp/ngrok.tgz

# Copy remaining project files
COPY . /app

# Make start.sh executable
RUN chmod +x /app/start.sh

# Expose Streamlit's default port
EXPOSE 8501

# Default command: run our startup script
CMD ["/app/start.sh"]