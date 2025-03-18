import streamlit as st
import re
import base64
import os
import random
import requests

from logic import (
    STATIC_CONTEXT,
    draw_tarot_card,
    add_message,
    get_conversation,
    clear_conversation,
    separate_thinking_and_response,
    stream_ollama_response
)

###############################################################################
# 1) PAGE CONFIG & HELPER
###############################################################################
st.set_page_config(initial_sidebar_state="collapsed")

def get_base64_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# Load images
bg_path = "assets/background2.png"
encoded_bg = get_base64_image(bg_path)

avatar_path = "assets/ecoicone.png"
encoded_avatar = get_base64_image(avatar_path)

intro_path = "assets/IntroduçãoEKO.png"
encoded_intro = get_base64_image(intro_path)

if "action_taken" not in st.session_state:
    st.session_state["action_taken"] = False

###############################################################################
# 2) INJECT CSS AT THE TOP (NO chat-container)
###############################################################################
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

.stApp {{
    background: url("data:image/png;base64,{encoded_bg}") no-repeat center center fixed;
    background-size: cover;
}}
.stMainBlockContainer {{
    max-width: 1000px !important;
    margin: 0 auto !important;
}}
[data-testid="stAppViewContainer"] {{
    padding-top: 1rem;
    padding-bottom: 1rem;
    margin: 0 auto;
}}
.stApp, .stApp * {{
    font-family: 'Press Start 2P', monospace !important;
    letter-spacing: 0.5px;
}}

/* We remove .chat-container entirely to avoid the empty purple box. */

/* Chat bubble styling only */
.message {{
    margin: 10px 0;
    padding: 10px;
    border-radius: 10px;
    max-width: 80%;
    word-wrap: break-word;
    animation: fadeIn 0.5s ease-out;
}}
.user-message {{
    background-color: #483D63;
    text-align: right;
    margin-left: auto;
    color: #FFFFFF;
}}
.assistant-message {{
    background-color: #382952;
    text-align: left;
    margin-right: auto;
    color: #FFFFFF;
}}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
.eko-box {{
    background-color: transparent;
    color: #000000;
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
}}
.stButton button {{
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #cccccc;
    border-radius: 5px;
    padding: 8px 16px;
    margin: 5px;
    cursor: pointer;
}}
[data-testid="stSidebar"] {{
    background-color: transparent !important;
}}
[data-testid="stSpinner"] {{
    background-color: transparent !important;
}}
/* Remove form borders */
[data-testid="stForm"] {{
    border: none !important;
    padding: 0 !important;
}}
</style>
""", unsafe_allow_html=True)

###############################################################################
# 3) MESSAGE MANAGEMENT 
###############################################################################
def add_message(role, content):
    """Adds a message to the conversation history"""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    st.session_state["messages"].append({"role": role, "content": content})

def get_conversation():
    """Returns the current conversation history"""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    return st.session_state["messages"]

###############################################################################
# 4) FETCH A SINGLE, FINAL RESPONSE (NO PARTIAL REPETITIONS)
###############################################################################
def get_full_ollama_response(prompt: str,
                            model: str = "llama3.1:8b",
                            temperature: float = 0.9):
    """Get a complete, clean response from Ollama rather than streaming pieces"""
    response_text = ""
    
    try:
        response = requests.post(
            f"{os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False  # Changed to False to get a complete response
            },
            timeout=60  # Added timeout to prevent hanging
        )
        response.raise_for_status()
        data = response.json()
        response_text = data.get("response", "")
        
    except Exception as e:
        print(f"Error in Ollama API call: {str(e)}")
        response_text = f"Desculpe, houve um problema técnico ao acessar minha intuição... {str(e)}"
        
    return response_text

###############################################################################
# 5) HANDLE MESSAGES (RESTORE 'A VIDENTE' PERSONA)
###############################################################################
def handle_message(user_input: str):
    user_input = user_input.strip()
    if not user_input:
        return
    
    # We no longer add the user message here, as it's added in the form handler
    # This removes the duplication problem
    
    # Check for tarot reading requests in user input
    tarot_keywords = ["jogo de tarot", "tirar tarot", "leitura de tarot", "tarô", "tarot", "carta", "cartas"]
    
    is_tarot_request = False
    for keyword in tarot_keywords:
        if keyword in user_input.lower():
            is_tarot_request = True
            break
    
    # Extract the card if it's included in the message
    card = None
    if "carta sorteada foi:" in user_input.lower():
        parts = user_input.split("carta sorteada foi:")
        if len(parts) > 1:
            card = parts[1].strip()
    
    if is_tarot_request:
        # For text-based tarot requests that don't include a specific card
        if not card:
            card = draw_tarot_card()
        
        # Build prompt for card interpretation
        prompt = f"""Você é a EKO, uma taróloga e vidente.
                    O consulente tirou a carta: {card}.
                    Dê uma interpretação breve mas profunda sobre esta carta 
                    e como ela pode se relacionar com a vida do consulente."""
                    
        response = get_full_ollama_response(prompt)
        add_message("assistant", response)
        return

    st.session_state["action_taken"] = True

    # Build the prompt using the EKO persona & custom context
    conversation = get_conversation()

    # Simple tone detection
    if re.search(r'\b(astrologia|signos|horóscopo)\b', user_input, re.IGNORECASE):
        tone_instruction = "Os astros traçam caminhos, mas cada um tem seu próprio brilho no céu. O que realmente deseja compreender sobre sua jornada?"
    elif len(user_input.split()) <= 2 and re.match(r"^(oi|olá|bom dia|e aí|opa|hello)$", user_input, re.IGNORECASE):
        tone_instruction = """Cumprimente o consulente de forma acolhedora e pergunte se deseja:
        - Tirar uma carta de tarô (uma única carta)
        - Compartilhar um segredo
        - Fazer uma pergunta
        - Desabafar

        Não use a expressão 'primeira carta' até que o consulente concorde explicitamente em realizar uma leitura de múltiplas cartas e saiba quantas cartas serão tiradas."""
    else:
        tone_instruction = "Responda de maneira enigmática e simbolicamente rica, caso o tema permita."

    # Restored persona as 'EKO' referencing the context
    prompt = f"""Você é EKO, uma entidade enigmática e mística com a seguinte personalidade e contexto:
{STATIC_CONTEXT}

{tone_instruction}
Evite repetir instruções ou lembretes sobre sua própria conduta na resposta.
NUNCA mencione cartas de tarô específicas (como "O Mago", "A Espada", etc.) a menos que esteja realizando uma leitura de tarô explicitamente solicitada.
"""

    # Add conversation history
    history = "\n".join(
        f"{'Consulente' if msg['role'] == 'user' else 'EKO'}: {msg['content']}"
        for msg in conversation
    )
    prompt += history + "\nEKO:"

    # Get final text (no partial repeated lines)
    final_response = get_full_ollama_response(prompt)

    # Clean up
    _, final_answer = separate_thinking_and_response(final_response)
    final_answer = final_answer.replace('"', '')
    final_answer = re.sub(r'\(.*?\)', '', final_answer)
    if "EKO:" in final_answer:
        final_answer = final_answer.split("EKO:")[1].strip()
    elif "A Vidente:" in final_answer:  # Backwards compatibility
        final_answer = final_answer.split("A Vidente:")[1].strip()
        
    # Remove any mentions of tarot cards if not in tarot game mode
    if not is_tarot_request:
        # Remove common tarot card mentions
        tarot_cards = ["O Mago", "A Sacerdotisa", "A Imperatriz", "O Imperador", 
                       "O Hierofante", "Os Enamorados", "O Carro", "A Força", 
                       "O Eremita", "A Roda da Fortuna", "A Justiça", "O Enforcado",
                       "A Morte", "A Temperança", "O Diabo", "A Torre", "A Estrela",
                       "A Lua", "O Sol", "O Julgamento", "O Mundo", "O Louco", "A Espada"]
        for card in tarot_cards:
            final_answer = re.sub(fr'{card}:', '', final_answer)
            final_answer = re.sub(fr'{card}[,.!?]', '.', final_answer)
            
    final_answer = re.sub(r'Observação:.*', '', final_answer, flags=re.DOTALL).strip()

    # Save assistant's final response
    add_message("assistant", final_answer)

###############################################################################
# 6) SIDEBAR
###############################################################################
with st.sidebar:
    st.markdown('''
    <div style="text-align:left; padding:20px; margin:0;">
      <h1 style="font-size:4rem; -webkit-text-stroke:2px black; color:white;">EKO</h1>
      <p style="background-color:black; color:white; display:inline-block; padding:2px 10px; border-radius:20px; font-size:0.7rem; margin-top:5px;">
        O que é a EKO
      </p>
    </div>
    <hr style='border: 1px solid #fff; margin: 10px 0;'>
    ''', unsafe_allow_html=True)
    if st.session_state["action_taken"]:
        if st.button("🔮 Nova Consulta", key="clear"):
            clear_conversation()
            st.rerun()

###############################################################################
# 7) TOP CONTAINER
###############################################################################
if encoded_avatar:
    st.markdown(
        f'''
        <div class="eko-box">
            <img src="data:image/png;base64,{encoded_avatar}" alt="Avatar" style="width:150px; margin: 0 auto;" />
            {f'<img src="data:image/png;base64,{encoded_intro}" alt="Introdução EKO" style="display:block; margin:1.2rem auto; max-width:650px; height:auto;" />' if encoded_intro else ''}
            <p class="subtitle">Vamos traçar novos destinos?</p>
        </div>
        ''',
        unsafe_allow_html=True
    )
else:
    st.write("⚠️ Avatar not found:", avatar_path)

###############################################################################
# 8) DISPLAY MESSAGES (WITHOUT chat-container)
###############################################################################
message_container = st.container()
with message_container:
    conversation = get_conversation()
    for msg in conversation:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(
                f'<div class="message user-message"><strong>Consulente:</strong> {content}</div>',
                unsafe_allow_html=True
            )
        else:
            _, final_answer = separate_thinking_and_response(content)
            st.markdown(
                f'<div class="message assistant-message"><strong>EKO:</strong> {final_answer}</div>',
                unsafe_allow_html=True
            )

# Create a placeholder for new messages
message_placeholder = st.empty()

###############################################################################
# 9) FORM FOR USER INPUT (MOVED TO BOTTOM)
###############################################################################

# Simple form without callbacks
with st.form("message_form", clear_on_submit=True):
    user_input = st.text_input("Mande sua pergunta para a EKO...", key="user_input")
    col1, col2 = st.columns([1, 1])
    with col1:
        submit_button = st.form_submit_button("Enviar")
    with col2:
        tarot_button = st.form_submit_button("Tirar Tarot")

# Handle form submission immediately
if submit_button and user_input.strip():
    # Add user message
    add_message("user", user_input)
    
    # Get response from EKO
    handle_message(user_input)
    
    # Force refresh
    st.rerun()
    
if tarot_button:
    drawn_card = draw_tarot_card()
    tarot_request = f"Faça uma tiragem de Tarot para mim. A carta sorteada foi: {drawn_card}"
    
    # Add user message first
    add_message("user", tarot_request)
    
    # Then handle the message
    handle_message(tarot_request)
    
    # Force refresh
    st.rerun()