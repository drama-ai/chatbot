# Use a slim Python base image (ARM-compatible for Apple Silicon)
FROM python:3.9-slim

# Create a working directory inside the container
WORKDIR /app

# Copy in your requirements
COPY requirements.txt /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . /app

# Expose the Streamlit port
EXPOSE 8501

# By default, run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]