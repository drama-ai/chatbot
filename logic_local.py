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

def get_tarot_cards():
    major_arcana = [
        "O Louco", "O Mago", "A Sacerdotisa", "A Imperatriz", "O Imperador", 
        "O Hierofante", "Os Enamorados", "O Carro", "A Força", "O Eremita", 
        "A Roda da Fortuna", "A Justiça", "O Enforcado", "A Morte", "A Temperança", 
        "O Diabo", "A Torre", "A Estrela", "A Lua", "O Sol", "O Julgamento", "O Mundo"
    ]
    
    minor_arcana_suits = ["Copas", "Ouros", "Espadas", "Paus"]
    minor_arcana_values = ["Ás", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Valete", "Cavaleiro", "Rainha", "Rei"]
    
    minor_arcana = [f"{value} de {suit}" for suit in minor_arcana_suits for value in minor_arcana_values]
    
    return major_arcana + minor_arcana

def draw_tarot_card():
    cards = get_tarot_cards()
    return random.choice(cards)

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
        final_response = re.sub(r"\(.*?\)", "", final_response, flags=re.DOTALL)  # Remove elementos desnecessários

    # Remove aspas excessivas
    final_response = re.sub(r'\"{2,}', '"', final_response).strip()
    
    # Remove diálogo da Vidente consigo mesma
    final_response = re.sub(r'Vidente:\s*.*?(?=\s*Vidente:|$)', '', final_response, flags=re.DOTALL).strip()

    # Remove mensagens que fazem referência ao funcionamento interno do modelo
    final_response = re.sub(r'Observação:.*', '', final_response, flags=re.DOTALL).strip()

    return [], final_response.strip()

# ----------------------------------
# 5. Streaming Function to Call Ollama’s API
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
    
    # Updated headers to mimic a browser request
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
        yield "Sorry, an error occurred while generating a response."
        return

    partial_response = ""
    try:
        for line in response.iter_lines(decode_unicode=True):
            if line.strip():
                data = json.loads(line)
                partial_response += data.get("response", "")
                _, final_answer = separate_thinking_and_response(partial_response)  # Remove <think> sections
                yield final_answer
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON: {e}")
        yield "Error decoding response from API."