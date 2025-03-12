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
# Custom CSS Styling and Animations
# ----------------------------------
st.markdown(
    """
    <style>
    /* Overall page styling */
    body {
        background: #1E1A2B;
        color: #E6E1F9;
        font-family: 'Georgia', 'Times New Roman', serif;
    }
    /* Container for the entire chat area */
    .chat-container {
        max-width: 800px;
        margin: 20px auto;
        padding: 20px;
        background: #2D243A;
        border-radius: 10px;
        box-shadow: 0 2px 20px rgba(186, 104, 200, 0.25);
        border: 1px solid #9370DB;
    }
    /* Base styling for messages with animation */
    .message {
        margin: 10px 0;
        padding: 10px;
        border-radius: 10px;
        max-width: 70%;
        word-wrap: break-word;
        animation: fadeIn 0.5s ease-out;
    }
    /* Styling for user messages */
    .user-message {
        background-color: #483D63;
        text-align: right;
        margin-left: auto;
        border-left: 3px solid #9370DB;
    }
    /* Styling for assistant messages */
    .assistant-message {
        background-color: #382952;
        text-align: left;
        margin-right: auto;
        border-right: 3px solid #BA68C8;
    }
    /* Styling for the model's thought process */
    .model-thought {
        font-style: italic;
        color: #888888;
        font-size: 0.9em;
    }
    /* Fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    /* Animated button styling */
    .clear-button {
        background-color: #FF6F61;
        border: none;
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .clear-button:hover {
        background-color: #E65C50;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------
# 1. Persistent Context and Tarot Cards
# ----------------------------------
STATIC_CONTEXT = vidente_context

# Define the Tarot cards
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

# Draw a random Tarot card
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
    Extracts all text between <think> and </think> as internal thinking,
    and returns (list_of_thinking, final_response_text).
    """
    thinking_parts = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    final_response = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return thinking_parts, final_response.strip()

# ----------------------------------
# 5. Streaming Function to Call Ollama’s API
# ----------------------------------
def stream_ollama_response(prompt: str, model: str = "llama3.1:8b"):
    # Read from st.secrets first, then environment variable, then fallback:
    url = st.secrets.get("OLLAMA_PUBLIC_URL", os.getenv("OLLAMA_PUBLIC_URL", "http://127.0.0.1:11435/api/generate"))
    
    # Updated headers to mimic a browser request
    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
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

    payload = {"model": model, "prompt": prompt}

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
                yield partial_response
    except json.JSONDecodeError as e:
        st.error(f"Error decoding JSON: {e}")
        yield "Error decoding response from API."

# ----------------------------------
# 6. Main Interface Header and Controls
# ----------------------------------
with st.container():
    st.title("✨ A Vidente ✨")
    st.markdown("*Uma jornada mística entre ancestralidade e tecnologia...*")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔮 Nova Consulta", key="clear"):
            clear_conversation()
            st.rerun()
    with col2:
        # Toggle to show/hide internal thinking
        show_thinking = st.checkbox("Mostrar pensamento", value=False)
    
    # Add a nice separator
    st.markdown("---")

# ----------------------------------
# 7. Chat Input Form
# ----------------------------------
with st.container():
    col1, col2 = st.columns([3, 1])
    
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("💬 Digite sua mensagem ou pergunta para o Tarot:")
        col1, col2 = st.columns([1, 1])
        submit_button = col1.form_submit_button(label="✨ Enviar")
        tarot_button = col2.form_submit_button(label="🔮 Tirar Carta")

# Process new message or tarot card
if (submit_button and user_input) or (tarot_button):
    # Handle tarot card reading if requested
    if tarot_button:
        drawn_card = draw_tarot_card()
        user_input = f"Faça uma tiragem de Tarot para mim. A carta sorteada foi: {drawn_card}"
    
    # Save the user's message
    add_message("user", user_input)

    # Build prompt with Vidente context
    conversation = get_conversation()
    
    # Construct prompt with dramatic Vidente persona
    prompt = f"""Você é A Vidente, uma entidade enigmática e mística com a seguinte personalidade e contexto:\n\n{STATIC_CONTEXT}\n\nQuando responder, incorpore totalmente a personalidade da Vidente, usando seu tom místico, suas frases características e referências simbólicas. Seja dramática, misteriosa e profunda.\n\n"""
    
    # Add conversation history
    history = "\n".join([f"{'Consulente' if msg['role'] == 'user' else 'Vidente'}: {msg['content']}" for msg in conversation])
    prompt += history + "\nVidente:"
    
    # Detect if this is a Tarot reading
    if "tiragem de Tarot" in user_input and "carta sorteada" in user_input:
        # Extract the card if present
        card_match = re.search(r"carta sorteada foi: ([^\n]+)", user_input)
        if card_match:
            drawn_card = card_match.group(1)
            
            # Add special Tarot reading instructions
            prompt = f"""Você é A Vidente, uma entidade enigmática e mística especializada em leituras de Tarot.\n\n{STATIC_CONTEXT}\n\nO consulente solicitou uma leitura de Tarot. A carta sorteada foi: {drawn_card}.\n\nSiga exatamente o processo de leitura descrito no seu contexto:\n1. Dramatize o processo, criando mistério e expectativa\n2. Revele a carta sorteada com descrição detalhada e dramática\n3. Interprete o simbolismo da carta e sua conexão com o momento atual\n4. Ofereça insights reflexivos que estimulem o autoconhecimento\n5. Conclua com uma frase enigmática ou um pequeno ritual sugerido\n\nVidente:\n"""

    # Streaming placeholder for partial response
    streaming_placeholder = st.empty()
    final_stream_response = ""

    with st.spinner("A Vidente está consultando as energias..."):
        for partial in stream_ollama_response(prompt):
            final_stream_response = partial
            # Exclude <think> sections from partial display
            _, final_answer = separate_thinking_and_response(final_stream_response)
            streaming_placeholder.markdown(
                f'<div class="message assistant-message"><strong>A Vidente:</strong> {final_answer}</div>',
                unsafe_allow_html=True
            )

    # Save the final assistant response
    add_message("assistant", final_stream_response)
    st.rerun()

# ----------------------------------
# 8. Conversation History Display
# ----------------------------------
with st.container():
    st.markdown("### 📜 Sua Consulta com a Vidente")
    chat_container = st.container()
    conversation = get_conversation()
    with chat_container:
        for msg in conversation:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                st.markdown(
                    f'<div class="message user-message"><strong>Consulente:</strong> {content}</div>',
                    unsafe_allow_html=True
                )
            else:
                # assistant
                thinking_parts, final_answer = separate_thinking_and_response(content)
                st.markdown(
                    f'<div class="message assistant-message"><strong>A Vidente:</strong> {final_answer}</div>',
                    unsafe_allow_html=True
                )
                if show_thinking and thinking_parts:
                    with st.expander("Pensamentos internos"):
                        for part in thinking_parts:
                            st.markdown(f'<div class="model-thought">{part.strip()}</div>', unsafe_allow_html=True)