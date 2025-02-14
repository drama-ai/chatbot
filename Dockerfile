# Dockerfile
FROM python:3.9-slim

# 1) Install needed system packages
RUN apt-get update && apt-get install -y \
    wget curl jq \
 && rm -rf /var/lib/apt/lists/*

# 2) Create and switch to /app
WORKDIR /app

# 3) Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 4) Install ngrok v3
RUN wget -O /tmp/ngrok.tgz https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz \
    && tar -C /usr/local/bin -xzf /tmp/ngrok.tgz

# 5) Copy the rest of your code into /app
COPY . /app

# 6) Make start.sh executable
RUN chmod +x /app/start.sh

# 7) Expose Streamlit’s default port
EXPOSE 8501

# 8) Default command: run the startup script
CMD ["/app/start.sh"]