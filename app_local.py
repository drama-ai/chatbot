import streamlit as st
from logic_local import (
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
import random  # Adicionado para permitir o uso de random

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

def draw_tarot_card():
    card_number = random.randint(1, 78)
    return cartas_tarot[card_number]["nome"]

def handle_message(user_input: str):
    """
    Takes the user's text, adds it to the conversation, and streams a single response.
    """
    user_input = user_input.strip()
    if not user_input:
        return

    # --- Tarot Game Handling ---
    # If a tarot game is already in progress, handle the response
    if "tarot_game" in st.session_state:
        if user_input.lower() == "sim":
            step = st.session_state["tarot_game"]["step"]
            if step == 1:
                card = draw_tarot_card()
                st.session_state["tarot_game"]["cards"].append(card)
                st.session_state["tarot_game"]["step"] = 2
                add_message("assistant", f"Segunda carta: {card}. Deseja que tire a terceira carta? Responda 'sim' para continuar.")
                return
            elif step == 2:
                card = draw_tarot_card()
                st.session_state["tarot_game"]["cards"].append(card)
                all_cards = st.session_state["tarot_game"]["cards"]
                add_message("assistant", f"Terceira carta: {card}. Jogo concluído! Suas cartas foram: {', '.join(all_cards)}.")
                del st.session_state["tarot_game"]
                return
        else:
            add_message("assistant", "Entendido. O jogo de tarot foi encerrado.")
            del st.session_state["tarot_game"]
            return

    # If the user is starting a tarot game
    if "jogo de tarot" in user_input.lower():
        st.session_state["tarot_game"] = {"step": 1, "cards": []}
        card = draw_tarot_card()
        st.session_state["tarot_game"]["cards"].append(card)
        add_message("assistant", f"Primeira carta: {card}. Deseja que tire a segunda carta? Responda 'sim' para continuar.")
        return

    # --- End Tarot Game Handling ---

    # Mark that user has taken an action
    st.session_state["action_taken"] = True

    # Save user's message to DB
    add_message("user", user_input)
    conversation = get_conversation()

    # Verificar se a pergunta está relacionada a astrologia, signos ou horóscopo
    if re.search(r'\b(astrologia|signos|horóscopo)\b', user_input, re.IGNORECASE):
        tone_instruction = "Os astros traçam caminhos, mas cada um tem seu próprio brilho no céu. O que realmente deseja compreender sobre sua jornada?"
    # Avaliar a complexidade da entrada para saudações curtas
    elif len(user_input.split()) <= 2 and re.match(r"^(oi|olá|bom dia|e aí|opa|hello)$", user_input, re.IGNORECASE):
        tone_instruction = """Cumprimente o consulente de forma acolhedora e pergunte se deseja:
        - Tirar uma carta de tarô (uma única carta)
        - Fazer uma leitura com várias cartas (por exemplo, 3 cartas)
        - Compartilhar um segredo
        - Fazer uma pergunta
        - Desabafar

        Não use a expressão 'primeira carta' até que o consulente concorde explicitamente em realizar uma leitura de múltiplas cartas e saiba quantas cartas serão tiradas."""
    else:
        tone_instruction = "Responda de maneira enigmática e simbolicamente rica, caso o tema permita."

    # Build prompt with Vidente context including tone instruction
    prompt = f"""Você é Eko, uma entidade enigmática e mística com a seguinte personalidade e contexto:\n\n{STATIC_CONTEXT}\n\n
    {tone_instruction}
    Evite repetir instruções ou lembretes sobre sua própria conduta na resposta.\n\n"""
    history = "\n".join(
        f"{'Consulente' if msg['role'] == 'user' else 'Eko'}: {msg['content']}"
        for msg in conversation
    )
    prompt += history + "\nEko:"

    final_stream_response = ""

    # Show a spinner while generating the response
    with st.spinner("Eko estou consultando as energias..."):
        # Stream from Ollama, but do not display partial text to avoid duplication
        for partial in stream_ollama_response(
            prompt,
            model="llama3.1:8b",
            temperature=0.6,  # A bit higher for more creative responses
            top_p=0.85,
            top_k=50,
            repeat_penalty=1.3,
            num_predict=256
        ):
            final_stream_response = partial
            
    # Process the final response to filter out unwanted text
    _, final_answer = separate_thinking_and_response(final_stream_response)

    # Remove unnecessary quotes
    final_answer = final_answer.replace('"', '')

    # Filter out scene directions if not needed
    final_answer = re.sub(r'\(.*?\)', '', final_answer)

    # Check to avoid Eko falando para mim mesma
    if "Eko:" in final_answer:
        final_answer = final_answer.split("Eko:")[1].strip()

    # Remove qualquer referência ao funcionamento do modelo
    final_answer = re.sub(r'Observação:.*', '', final_answer, flags=re.DOTALL).strip()

    # Save the assistant's final response
    add_message("assistant", final_answer)

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
        margin: 0 auto !important;
    }}

    [data-testid="stAppViewContainer"] {{
        padding-top: 1rem;
        padding-bottom: 1rem;
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
        color: #FFFFFF;
    }}
    .assistant-message {{
        background-color: #382952;
        text-align: left;
        margin-right: auto;
        border-right: 3px solid #BA68C8;
        color: #FFFFFF;
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

    /* Container for the 'Oi, eu sou a EKO' block */
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

    /* --- Spinner Overrides --- */
    [data-testid="stSpinner"] {{
        background-color: transparent !important;
    }}

    [data-testid="stSpinner"] .stSpinner {{
        background-color: rgba(0, 0, 0, 0.4) !important;
        color: #ffffff !important;
        border: 2px solid #BA68C8 !important;
        border-radius: 10px;
        padding: 20px;
    }}

    [data-testid="stSpinner"] .stSpinner > div > div {{
        border-color: #BA68C8 transparent transparent transparent !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

##########################
# Sidebar with model parameter controls
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
    # Horizontal divider
    st.markdown("<hr style='border: 1px solid #fff; margin: 10px 0;'>", unsafe_allow_html=True)

    # 'Nova Consulta' button moved to the sidebar
    if st.session_state["action_taken"]:
        if st.button("🔮 Nova Consulta", key="clear"):
            clear_conversation()
            st.experimental_rerun()

    # Model Parameter Controls
    st.session_state["temperature"] = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    st.session_state["top_p"] = st.slider("Top P", 0.0, 1.0, 0.9, 0.05)
    st.session_state["top_k"] = st.slider("Top K", 1, 100, 40, 1)
    st.session_state["repeat_penalty"] = st.slider("Repeat Penalty", 1.0, 2.0, 1.2, 0.1)
    st.session_state["num_predict"] = st.slider("Max Tokens (num_predict)", 64, 1024, 512, 32)

##########################
# Main Content
##########################

st.markdown("---")

#
# 1) EKO Box: Avatar + Title + Subtitle
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
# 2) Conversation History
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
            f'<div class="message assistant-message"><strong>Eko:</strong> {final_answer}</div>',
            unsafe_allow_html=True
        )

#
# 3) Info Icon + Input + Buttons at the bottom
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

def submit_message():
    if st.session_state.get('user_input', '').strip():
        st.session_state['action_taken'] = True
        handle_message(st.session_state['user_input'])
        st.session_state['user_input'] = ''

user_input = st.text_input("Mande sua pergunta para a EKO...", key="user_input", on_change=submit_message)

colA, colB, colC = st.columns([1,1,1])
with colA:
    if st.button("Enviar"):
        submit_message()
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
# Done
#
st.markdown('</div>', unsafe_allow_html=True)