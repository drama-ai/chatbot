# app.py
# This file contains the UI customization for the EKO app.
# It handles the visual styling and layout while importing logic functions from logic.py.

import streamlit as st
from logic import (
    STATIC_CONTEXT,
    draw_tarot_card,
    add_message,
    get_conversation,
    clear_conversation,
    separate_thinking_and_response,
    stream_ollama_response
)
import re
import base64
import os

##########################
# Session State
##########################
if "action_taken" not in st.session_state:
    st.session_state["action_taken"] = False  # Tracks whether user has interacted

##########################
# Helper Functions
##########################
def get_base64_image(image_path: str) -> str:
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

def handle_message(user_input: str):
    """
    Takes the user's text, adds it to the conversation, and streams a response.
    """
    user_input = user_input.strip()
    if not user_input:
        return

    # Mark that user has taken an action
    st.session_state["action_taken"] = True

    # Save user's message
    add_message("user", user_input)
    conversation = get_conversation()

    # Build prompt with Vidente context
    prompt = f"""Você é A Vidente, uma entidade enigmática e mística com a seguinte personalidade e contexto:\n\n{STATIC_CONTEXT}\n\nQuando responder, incorpore totalmente a personalidade da Vidente, usando seu tom místico, suas frases características e referências simbólicas. Seja dramática, misteriosa e profunda.\n\n"""
    history = "\n".join(
        f"{'Consulente' if msg['role'] == 'user' else 'Vidente'}: {msg['content']}"
        for msg in conversation
    )
    prompt += history + "\nVidente:"

    streaming_placeholder = st.empty()
    final_stream_response = ""

    with st.spinner("A Vidente está consultando as energias..."):
        for partial in stream_ollama_response(prompt):
            final_stream_response = partial
            # Separate internal thinking (<think>) from final answer
            _, final_answer = separate_thinking_and_response(final_stream_response)
            streaming_placeholder.markdown(
                f'<div class="message assistant-message"><strong>A Vidente:</strong> {final_answer}</div>',
                unsafe_allow_html=True
            )

    add_message("assistant", final_stream_response)

##########################
# Load Images & Background
##########################
bg_path = "assets/background.jpg"
encoded_bg = get_base64_image(bg_path)

avatar_path = "assets/ecoicone.png"
encoded_avatar = get_base64_image(avatar_path)

##########################
# CSS Styling
##########################
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    
    /* Overall app background */
    .stApp {{
        background: url("data:image/jpg;base64,{encoded_bg}") no-repeat center center fixed;
        background-size: cover;
    }}

    /* Força uma largura maior no bloco principal do Streamlit */
    .stMainBlockContainer {{
        max-width: 1000px !important;
        margin: 0 auto !important; /* ADICIONADO: centraliza o conteúdo */
    }}

    /*
     * REMOVIDO/ALTERADO: removemos o display:flex que impedia a rolagem.
     * Caso queira manter algum espaçamento, ajuste padding-top/bottom.
     */
    [data-testid="stAppViewContainer"] {{
        padding-top: 1rem;
        padding-bottom: 1rem;
        /* display: flex;
           justify-content: center;
           align-items: flex-start; */
        margin: 0 auto;
    }}

    /* Global font/color overrides */
    .stApp, .stApp * {{
        font-family: 'Press Start 2P', monospace !important;
        letter-spacing: 0.5px;
    }}

    /* Container para toda a área de chat */
    .chat-container {{
        max-width: 1000px;
        margin: 20px auto;
        padding: 20px;
        background: #2D243A;
        border-radius: 10px;
        box-shadow: 0 2px 20px rgba(186, 104, 200, 0.25);
        border: 1rem solid black;
    }}

    /* Mensagens do chat */
    .message {{
        margin: 10px 0;
        padding: 10px;
        border-radius: 10px;
        max-width: 70%;
        word-wrap: break-word;
        animation: fadeIn 0.5s ease-out;
    }}
    .user-message {{
        background-color: #483D63;
        text-align: right;
        margin-left: auto;
        border-left: 3px solid #9370DB;
        color: #FFFFFF; /* ADICIONADO para melhor contraste */
    }}
    .assistant-message {{
        background-color: #382952;
        text-align: left;
        margin-right: auto;
        border-right: 3px solid #BA68C8;
        color: #FFFFFF; /* ADICIONADO para melhor contraste */
    }}
    .model-thought {{
        font-style: italic;
        color: #888888;
        font-size: 0.9em;
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .clear-button {{
        background-color: #FF6F61;
        border: none;
        color: white;
        padding: 8px 16px;
        font-size: 14px;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }}
    .clear-button:hover {{
        background-color: #E65C50;
    }}

    /* Top-left corner badge (placed in the sidebar) */
    .header-left {{
        text-align: left;
        padding: 20px;
        margin: 0;
    }}
    .header-left h1 {{
        font-size: 4rem;
        margin: 0;
        -webkit-text-stroke: 2px black;
        color: white;
    }}
    .header-left p {{
        background-color: black;
        color: white;
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.7rem;
        margin-top: 5px;
    }}

    /* Info icon with tooltip */
    .info-icon {{
        display: inline-block;
        position: relative;
        font-size: 1.2rem;
        cursor: help;
        margin-left: 10px;
    }}
    .info-icon .tooltip-text {{
        visibility: hidden;
        width: 280px;
        background-color: rgba(0, 0, 0, 0.8);
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -140px;
        font-size: 0.7rem;
    }}
    .info-icon:hover .tooltip-text {{
        visibility: visible;
    }}

    /* Position the 'Nova Consulta' button top-right of main content */
    .top-right {{
        position: absolute;
        top: 20px;
        right: 20px;
    }}

    /* Container for the 'Oi, eu sou a EKO' block: light gray background and black text */
    .eko-box {{
        background-color: #EEEEEE;
        color: #000000;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        max-width: 1000px;
        margin-left: auto;
        margin-right: auto;
    }}
    .eko-box hr {{
        border: 1px solid #000000;
        width: 80%;
        margin: 10px auto;
    }}

    /* Buttons: set text color to black for better contrast on white */
    .stButton button {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #cccccc;
        border-radius: 5px;
        padding: 8px 16px;
        margin: 5px;
        cursor: pointer;
    }}

    /* Make the sidebar background 100% transparent */
    [data-testid="stSidebar"] {{
        background-color: transparent !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

##########################
# Sidebar Column
##########################
with st.sidebar:
    st.markdown(
        '''
        <div class="header-left">
          <h1>EKO</h1>
          <p>O que é a EKO</p>
        </div>
        ''',
        unsafe_allow_html=True
    )
    st.markdown("<hr style='border: 1px solid #fff; margin: 10px 0;'>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="
            padding: 20px; 
            font-family: 'Press Start 2P', monospace; 
            color: black; 
            text-shadow: 
                -1px -1px 0 #fff, 
                 1px -1px 0 #fff, 
                -1px  1px 0 #fff, 
                 1px  1px 0 #fff;
        ">
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="margin-bottom: 10px;">• nova consulta</li>
                <li style="margin-bottom: 10px;">• configurações</li>
                <li style="margin-bottom: 10px;">• entre em contato</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )

##########################
# Wrap ALL main content inside .chat-container
##########################

#
# 1) Nova Consulta Button (only if user has interacted)
#
if st.session_state["action_taken"]:
    col1, col2 = st.columns([9,1])
    with col2:
        if st.button("🔮 Nova Consulta", key="clear"):
            clear_conversation()
            st.experimental_rerun()

st.markdown("---")

#
# 2) EKO Box: Avatar + Title + Subtitle
#
if encoded_avatar:
    st.markdown(
        f'''
        <div class="eko-box">
            <img src="data:image/png;base64,{encoded_avatar}" alt="Avatar" style="width:150px; margin: 0 auto;" />
            <hr />
            <h1 class="main-title">✨Oi, eu sou a EKO✨</h1>
            <p class="subtitle">Vamos traçar novos destinos?</p>
        </div>
        ''',
        unsafe_allow_html=True
    )
else:
    st.write("⚠️ Avatar not found:", avatar_path)

#
# 3) Info Icon + Input + Buttons
#
st.markdown(
    """
    <div style="text-align:center; margin-bottom: 20px;">
      <span class="info-icon">ℹ️
        <span class="tooltip-text">
          você pode falar diretamente com o oráculo, tirar tarot, ou ler a sua sorte. 
          como posso te ajudar hoje?
        </span>
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)

user_input = st.text_input("Mande sua pergunta para a EKO...")

colA, colB, colC = st.columns([1,1,1])
with colA:
    if st.button("Enviar"):
        st.session_state["action_taken"] = True
        handle_message(user_input)
with colB:
    if st.button("🔮 Tirar Tarot"):
        st.session_state["action_taken"] = True
        drawn_card = draw_tarot_card()
        handle_message(f"Faça uma tiragem de Tarot para mim. A carta sorteada foi: {drawn_card}")
with colC:
    if st.button("leia sua sorte"):
        st.session_state["action_taken"] = True
        handle_message("Leia minha sorte, por favor!")

#
# 4) Conversation History
#
st.markdown("### 📜 Sua Consulta com a Vidente")
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
        # assistant
        thinking_parts, final_answer = separate_thinking_and_response(content)
        st.markdown(
            f'<div class="message assistant-message"><strong>A Vidente:</strong> {final_answer}</div>',
            unsafe_allow_html=True
        )

#
# Finally, close the chat-container
#
st.markdown('</div>', unsafe_allow_html=True)