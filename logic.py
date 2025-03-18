import streamlit as st
import requests
from requests.adapters import Retry, HTTPAdapter
from tinydb import TinyDB, Query
import datetime
import json
import re
import uuid
import os
import random
import time
import socket

from context import vidente_context

# ----------------------------------
# 1. Persistent Context and Tarot Cards
# ----------------------------------
STATIC_CONTEXT = vidente_context

cartas_tarot = {
    1: {"nome": "O Mago"},
    2: {"nome": "A Sacerdotisa"},
    3: {"nome": "A Imperatriz"},
    4: {"nome": "O Imperador"},
    5: {"nome": "O Hierofante"},
    6: {"nome": "Os Enamorados"},
    7: {"nome": "O Carro"},
    8: {"nome": "A Força"},
    9: {"nome": "O Eremita"},
    10: {"nome": "A Roda da Fortuna"},
    11: {"nome": "A Justiça"},
    12: {"nome": "O Enforcado"},
    13: {"nome": "A Morte"},
    14: {"nome": "A Temperança"},
    15: {"nome": "O Diabo"},
    16: {"nome": "A Torre"},
    17: {"nome": "A Estrela"},
    18: {"nome": "A Lua"},
    19: {"nome": "O Sol"},
    20: {"nome": "O Julgamento"},
    21: {"nome": "O Mundo"},
    22: {"nome": "O Louco"},
    # Paus
    23: {"nome": "Ás de Paus"},
    24: {"nome": "Dois de Paus"},
    25: {"nome": "Três de Paus"},
    26: {"nome": "Quatro de Paus"},
    27: {"nome": "Cinco de Paus"},
    28: {"nome": "Seis de Paus"},
    29: {"nome": "Sete de Paus"},
    30: {"nome": "Oito de Paus"},
    31: {"nome": "Nove de Paus"},
    32: {"nome": "Dez de Paus"},
    33: {"nome": "Valete de Paus"},
    34: {"nome": "Cavaleiro de Paus"},
    35: {"nome": "Rainha de Paus"},
    36: {"nome": "Rei de Paus"},
    # Espadas
    37: {"nome": "Ás de Espadas"},
    38: {"nome": "Dois de Espadas"},
    39: {"nome": "Três de Espadas"},
    40: {"nome": "Quatro de Espadas"},
    41: {"nome": "Cinco de Espadas"},
    42: {"nome": "Seis de Espadas"},
    43: {"nome": "Sete de Espadas"},
    44: {"nome": "Oito de Espadas"},
    45: {"nome": "Nove de Espadas"},
    46: {"nome": "Dez de Espadas"},
    47: {"nome": "Valete de Espadas"},
    48: {"nome": "Cavaleiro de Espadas"},
    49: {"nome": "Rainha de Espadas"},
    50: {"nome": "Rei de Espadas"},
    # Copas
    51: {"nome": "Ás de Copas"},
    52: {"nome": "Dois de Copas"},
    53: {"nome": "Três de Copas"},
    54: {"nome": "Quatro de Copas"},
    55: {"nome": "Cinco de Copas"},
    56: {"nome": "Seis de Copas"},
    57: {"nome": "Sete de Copas"},
    58: {"nome": "Oito de Copas"},
    59: {"nome": "Nove de Copas"},
    60: {"nome": "Dez de Copas"},
    61: {"nome": "Valete de Copas"},
    62: {"nome": "Cavaleiro de Copas"},
    63: {"nome": "Rainha de Copas"},
    64: {"nome": "Rei de Copas"},
    # Ouros
    65: {"nome": "Ás de Ouros"},
    66: {"nome": "Dois de Ouros"},
    67: {"nome": "Três de Ouros"},
    68: {"nome": "Quatro de Ouros"},
    69: {"nome": "Cinco de Ouros"},
    70: {"nome": "Seis de Ouros"},
    71: {"nome": "Sete de Ouros"},
    72: {"nome": "Oito de Ouros"},
    73: {"nome": "Nove de Ouros"},
    74: {"nome": "Dez de Ouros"},
    75: {"nome": "Valete de Ouros"},
    76: {"nome": "Cavaleiro de Ouros"},
    77: {"nome": "Rainha de Ouros"},
    78: {"nome": "Rei de Ouros"}
}

def get_tarot_cards():
    return cartas_tarot

def draw_tarot_card():
    card_number = random.randint(1, 78)
    return cartas_tarot[card_number]["nome"]

# ----------------------------------
# 2. TinyDB: Set Up the Conversation DB
# ----------------------------------
db = TinyDB("db.json")
messages_table = db.table("messages")
MsgQuery = Query()

# ----------------------------------
# Session ID Utilities
# ----------------------------------
def get_or_create_session_id():
    """
    Create or retrieve a unique session ID for the current user's session.
    Each user/browser session gets its own ID, ensuring separate chat histories.
    """
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())
    return st.session_state["session_id"]

# ----------------------------------
# 3. Database Helpers
# ----------------------------------
def add_message(role: str, content: str):
    """Insert a message for this session into the DB."""
    session_id = get_or_create_session_id()
    messages_table.insert({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.now().isoformat()
    })

def get_conversation():
    """Retrieve all messages for the current session, sorted by timestamp."""
    session_id = get_or_create_session_id()
    msgs = messages_table.search(MsgQuery.session_id == session_id)
    return sorted(msgs, key=lambda x: x.get("timestamp", ""))

def clear_conversation():
    """Remove all messages for the current session."""
    session_id = get_or_create_session_id()
    messages_table.remove(MsgQuery.session_id == session_id)

# ----------------------------------
# 4. Separate Thinking from Final Response
# ----------------------------------
def separate_thinking_and_response(text: str):
    """
    Remove qualquer conteúdo dentro das tags <think>...</think> e descrições excessivas quando a resposta não exige isso.
    """
    final_response = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    
    # Remove floreios quando a resposta for simples
    if not re.search(r"(tarot|destino|futuro|existência|energia|forças)", text, re.IGNORECASE):
        final_response = re.sub(r"\(.*?\)", "", final_response, flags=re.DOTALL)

    # Remove aspas excessivas
    final_response = re.sub(r'\"{2,}', '"', final_response).strip()
    
    # Remove diálogo da EKO consigo mesma
    final_response = re.sub(r'Eko:\s*.*?(?=\s*Eko:|$)', '', final_response, flags=re.DOTALL).strip()
    
    # Remove mensagens que fazem referência ao funcionamento interno do modelo
    final_response = re.sub(r'Observação:.*', '', final_response, flags=re.DOTALL).strip()
    
    # Remove qualquer texto anterior a "EKO:" ou "A Vidente:"
    if "EKO:" in final_response:
        final_response = final_response.split("EKO:")[-1].strip()
    elif "Eko:" in final_response:
        final_response = final_response.split("Eko:")[-1].strip()
    elif "A Vidente:" in final_response:
        final_response = final_response.split("A Vidente:")[-1].strip()
    
    # Certifique-se de que referências a "Vidente" são substituídas por "EKO"
    final_response = re.sub(r'\b(A Vidente|Vidente)\b', 'EKO', final_response)
    
    return [], final_response.strip()

# ----------------------------------
# 5. Streaming Function to Call Ollama's API
# ----------------------------------
def stream_ollama_response(prompt, model="llama3.1:8b", temperature=0.9):
    """Stream response from Ollama API with improved reliability for VPN scenarios"""
    try:
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
        
        # Try different Ollama endpoints - prioritize direct IP which works better with VPNs
        ollama_endpoints = []
        
        # Try environment variables first
        if os.environ.get("OLLAMA_PUBLIC_URL"):
            ollama_endpoints.append(os.environ.get("OLLAMA_PUBLIC_URL").rstrip('/'))
        
        if os.environ.get("OLLAMA_API_BASE"):
            ollama_endpoints.append(os.environ.get("OLLAMA_API_BASE").rstrip('/'))
        
        # Add fallback endpoints - prioritize direct IP over localhost names
        ollama_endpoints.extend([
            "http://127.0.0.1:11434",  # Direct IP address works better with VPNs
            "http://0.0.0.0:11434",    # Bind address if OLLAMA_HOST is set
            "http://localhost:11434",
            "http://host.docker.internal:11434"
        ])
        
        # Try each endpoint
        for ollama_base in ollama_endpoints:
            try:
                # Ensure properly formatted URL by removing trailing slashes and adding /api/
                base_url = ollama_base.rstrip('/')
                
                # Print the exact URL being used
                api_url = f"{base_url}/api/generate"
                print(f"Attempting to stream response from Ollama at: {api_url}")
                
                response = s.post(
                    api_url,
                    json={
                        "model": model,
                        "prompt": prompt,
                        "temperature": temperature,
                        "stream": True
                    },
                    stream=True,
                    timeout=45  # Increased timeout for VPN conditions
                )
                
                print(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"Streaming from {api_url} with status {response.status_code}")
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                            except json.JSONDecodeError as e:
                                print(f"Error decoding JSON: {e}, line: {line}")
                                continue
                    
                    # If we successfully completed streaming, exit the function
                    return
                else:
                    # Print response details to help debug
                    print(f"Response from {api_url}: Status {response.status_code}")
                    try:
                        error_content = response.text
                        print(f"Error content: {error_content[:200]}...")
                    except:
                        print("Could not read error content")
                
            except Exception as endpoint_error:
                print(f"Error with endpoint {ollama_base}: {str(endpoint_error)}")
                continue
        
        # If we reach here, all endpoints failed
        yield "\n\n⚠️ Não foi possível conectar ao servidor Ollama. Verifique sua conexão ou tente novamente mais tarde."
            
    except Exception as e:
        error_details = f"Error streaming from Ollama: {str(e)}"
        print(error_details)
        yield "\n\n⚠️ Erro ao conectar com o servidor. Tente novamente mais tarde ou consulte o administrador do sistema."

# Create a custom DNS resolver function to help with VPN DNS issues
original_getaddrinfo = socket.getaddrinfo

def patched_getaddrinfo(*args, **kwargs):
    """
    Custom DNS resolver that helps with VPN DNS issues by trying multiple resolution methods
    """
    # Get the hostname from args (standard socket.getaddrinfo format)
    hostname = args[0]
    
    # Known Ollama hostnames that might need special handling
    ollama_hosts = ["localhost", "127.0.0.1", "host.docker.internal"]
    
    # If this is an Ollama host, try to bypass VPN DNS restrictions
    if hostname in ollama_hosts or (isinstance(hostname, str) and "ollama" in hostname.lower()):
        try:
            # First try normal resolution
            return original_getaddrinfo(*args, **kwargs)
        except socket.gaierror:
            # If it fails and this is localhost, force the IP
            if hostname == "localhost":
                # Force localhost to resolve to 127.0.0.1
                print(f"DNS resolution failed for {hostname}, forcing to 127.0.0.1")
                # Create a result similar to what getaddrinfo would return
                return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('127.0.0.1', args[1]))]
            # For other Ollama hosts, let the original exception propagate
            raise
    else:
        # For non-Ollama hosts, use normal resolution
        return original_getaddrinfo(*args, **kwargs)

# Replace the DNS resolver with our custom version
socket.getaddrinfo = patched_getaddrinfo