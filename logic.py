import streamlit as st
import requests
from tinydb import TinyDB, Query
import datetime
import json
import re
import uuid
import os
import random

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
def stream_ollama_response(
    prompt: str,
    model: str = "llama3.1:8b",
    temperature: float = 0.7,
    top_p: float = 0.9,
    top_k: int = 40,
    repeat_penalty: float = 1.2,
    num_predict: int = 512
):
    """
    Streams text from the Ollama API using adjustable parameters
    to reduce repetition, control creativity, etc.
    """
    url = st.secrets.get("OLLAMA_PUBLIC_URL", os.getenv("OLLAMA_PUBLIC_URL", "http://127.0.0.1:11434/api/generate"))
    
    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "http://localhost:8501",
        "Referer": "http://localhost:8501/",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "num_predict": num_predict
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Error contacting Ollama API: {e}")
        yield "Desculpe, ocorreu um erro ao gerar uma resposta."
        return

    # Vamos coletar toda a resposta antes de fazer qualquer processamento
    full_response = ""
    try:
        for line in response.iter_lines(decode_unicode=True):
            if line.strip():
                data = json.loads(line)
                delta = data.get("response", "")
                full_response += delta
                
                # Só fazemos yield se o modelo terminou de gerar
                if data.get("done", False):
                    _, clean_response = separate_thinking_and_response(full_response)
                    yield clean_response
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON: {e}")