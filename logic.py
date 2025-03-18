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
    """Stream responses from the Ollama API"""
    try:
        # Get base URL from environment variable with fallback
        ollama_base = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')
        
        # Add retries for better reliability
        s = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5)
        s.mount('http://', HTTPAdapter(max_retries=retries))
        s.mount('https://', HTTPAdapter(max_retries=retries))
        
        # Make the API call with a longer timeout
        response = s.post(
            f"{ollama_base}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": True
            },
            stream=True,
            timeout=30  # Increased timeout
        )
        
        response.raise_for_status()
        
        # Process the streaming response
        full_response = ""
        for line in response.iter_lines(decode_unicode=True):
            if line.strip():
                try:
                    data = json.loads(line)
                    full_response += data.get("response", "")
                    
                    # Only yield complete responses
                    if data.get("done", False):
                        # If we have content to return, yield it
                        if full_response.strip():
                            yield full_response
                        else:
                            yield "Os mistérios do universo estão obscuros neste momento..."
                except json.JSONDecodeError:
                    continue
                    
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error to Ollama API: {e}")
        yield "Desculpe, não consegui acessar minha intuição neste momento. Verifique se o servidor Ollama está em execução e acessível."
        
    except requests.exceptions.Timeout as e:
        print(f"Timeout error with Ollama API: {e}")
        yield "As energias estão demorando para alinhar-se. Tente novamente em alguns momentos."
        
    except requests.exceptions.RequestException as e:
        print(f"Error in Ollama API call: {str(e)}")
        yield "Desculpe, houve um problema técnico ao acessar minha intuição... Por favor, tente novamente."
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        yield "Os astros estão em silêncio neste momento. Aguarde um instante e tente novamente..."