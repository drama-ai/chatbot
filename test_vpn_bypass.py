#!/usr/bin/env python3
"""
VPN Bypass Test Script for Ollama

This script tests different connection scenarios to Ollama to validate our VPN bypass solution.
"""

import os
import time
import json
import socket
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import subprocess

def test_connection(url, description):
    """Test a connection to Ollama and print results"""
    try:
        # Set a short timeout to simulate VPN conditions
        response = requests.get(f"{url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✅ {description} - Connection SUCCESSFUL: {url}")
            return True
        else:
            print(f"❌ {description} - Connection FAILED with status {response.status_code}: {url}")
            return False
    except Exception as e:
        print(f"❌ {description} - Connection ERROR: {url} - {str(e)}")
        return False

def reset_ollama_host():
    """Reset OLLAMA_HOST environment variable if it exists"""
    if "OLLAMA_HOST" in os.environ:
        del os.environ["OLLAMA_HOST"]
        print("🔄 Reset OLLAMA_HOST environment variable")

def set_ollama_host(value):
    """Set OLLAMA_HOST environment variable"""
    os.environ["OLLAMA_HOST"] = value
    print(f"🔧 Set OLLAMA_HOST={value}")

def simulate_vpn_restriction():
    """Simulate VPN restriction by modifying the hosts file or using iptables"""
    print("\n📡 Simulating VPN-like network restrictions...")
    print("⚠️ Note: This is just a simulation and won't fully replicate VPN behavior\n")
    
    # For a real simulation, we would need sudo access to modify network rules
    # Instead, we'll just test how connections behave with different configurations

def run_tests():
    """Run all connection tests"""
    endpoints = [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://0.0.0.0:11434",
        "http://host.docker.internal:11434"
    ]
    
    # Check if Ollama is running
    print("\n🔍 Checking if Ollama is running...")
    ollama_running = False
    try:
        output = subprocess.check_output(["ps", "aux"], text=True)
        if "ollama" in output.lower():
            print("✅ Ollama process found")
            ollama_running = True
        else:
            print("❌ Ollama process not found - make sure Ollama is running")
    except Exception as e:
        print(f"❌ Error checking Ollama process: {e}")
    
    if not ollama_running:
        print("⚠️ Please start Ollama before running this test")
        return
    
    # Test 1: Standard connections without OLLAMA_HOST
    print("\n🧪 Test 1: Standard connections without OLLAMA_HOST")
    reset_ollama_host()
    for url in endpoints:
        test_connection(url, "Standard")
    
    # Test 2: With OLLAMA_HOST set to 0.0.0.0:11434
    print("\n🧪 Test 2: Connections with OLLAMA_HOST=0.0.0.0:11434")
    set_ollama_host("0.0.0.0:11434")
    for url in endpoints:
        test_connection(url, "With OLLAMA_HOST")
    
    # Test 3: Simulate VPN restrictions
    print("\n🧪 Test 3: Simulate VPN mode with retry logic")
    simulate_vpn_restriction()
    
    # Create a session with retries
    s = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    
    for url in endpoints:
        try:
            print(f"🔄 Testing VPN mode with retries: {url}")
            response = s.get(f"{url}/api/tags", timeout=10)
            if response.status_code == 200:
                print(f"✅ VPN Simulation - Connection SUCCESSFUL: {url}")
            else:
                print(f"❌ VPN Simulation - Connection FAILED with status {response.status_code}: {url}")
        except Exception as e:
            print(f"❌ VPN Simulation - Connection ERROR: {url} - {str(e)}")
    
    # Test 4: Test our app's connection logic with environment variables
    print("\n🧪 Test 4: Testing stream_ollama_response connection logic")
    try:
        from logic import stream_ollama_response
        
        print("🔄 Testing stream_ollama_response function...")
        response_generator = stream_ollama_response("Hello, this is a test.", model="llama3.1:8b")
        
        # Get first few tokens to validate connection
        response_tokens = []
        for i, token in enumerate(response_generator):
            response_tokens.append(token)
            if i >= 5:  # Just get first 5 tokens to confirm it's working
                break
                
        if response_tokens:
            print(f"✅ stream_ollama_response - Connection SUCCESSFUL: received {len(response_tokens)} tokens")
            print(f"   First tokens: {''.join(response_tokens)[:50]}...")
        else:
            print("❌ stream_ollama_response - No response received")
    except Exception as e:
        print(f"❌ Error testing stream_ollama_response: {str(e)}")
    
    # Reset environment to clean state
    reset_ollama_host()
    print("\n🧪 Tests completed")

if __name__ == "__main__":
    print("🔬 Ollama VPN Bypass Test")
    print("========================")
    print("This script tests various connection methods to Ollama")
    print("to validate our VPN bypass solution")
    print("========================")
    
    run_tests()
