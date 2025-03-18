import streamlit as st
import re
import base64
import os
import random

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
""", unsafe_allow_html=True)

###############################################################################
# 3) FETCH A SINGLE, FINAL RESPONSE (NO PARTIAL REPETITIONS)
###############################################################################
def get_full_ollama_response(prompt: str,
                             model: str = "llama3.1:8b",
                             temperature: float = 0.6,
                             top_p: float = 0.85,
                             top_k: int = 50,
                             repeat_penalty: float = 1.3,
                             num_predict: int = 256):
    """Collect all partial chunks from stream_ollama_response into one final string."""
    response_text = ""
    with st.spinner("A Vidente está consultando as energias..."):
        for partial in stream_ollama_response(
            prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            num_predict=num_predict
        ):
            response_text += partial
    return response_text

###############################################################################
# 4) HANDLE MESSAGES (RESTORE 'A VIDENTE' PERSONA)
###############################################################################
def handle_message(user_input: str):
    user_input = user_input.strip()
    if not user_input:
        return

    # --- Tarot Game Handling ---
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

    if "jogo de tarot" in user_input.lower():
        st.session_state["tarot_game"] = {"step": 1, "cards": []}
        card = draw_tarot_card()
        st.session_state["tarot_game"]["cards"].append(card)
        add_message("assistant", f"Primeira carta: {card}. Deseja que tire a segunda carta? Responda 'sim' para continuar.")
        return
    # --- End Tarot Game Handling ---

    st.session_state["action_taken"] = True
    add_message("user", user_input)

    # Build the prompt using the old 'A Vidente' persona & custom context
    conversation = get_conversation()

    # Simple tone detection
    if re.search(r'\b(astrologia|signos|horóscopo)\b', user_input, re.IGNORECASE):
        tone_instruction = "Os astros traçam caminhos, mas cada um tem seu próprio brilho no céu. O que realmente deseja compreender sobre sua jornada?"
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

    # Restored persona as 'A Vidente' referencing the context
    prompt = f"""Você é A Vidente, uma entidade enigmática e mística com a seguinte personalidade e contexto:
{STATIC_CONTEXT}

{tone_instruction}
Evite repetir instruções ou lembretes sobre sua própria conduta na resposta.

"""

    # Add conversation history
    history = "\n".join(
        f"{'Consulente' if msg['role'] == 'user' else 'A Vidente'}: {msg['content']}"
        for msg in conversation
    )
    prompt += history + "\nA Vidente:"

    # Get final text (no partial repeated lines)
    final_response = get_full_ollama_response(prompt)

    # Clean up
    _, final_answer = separate_thinking_and_response(final_response)
    final_answer = final_answer.replace('"', '')
    final_answer = re.sub(r'\(.*?\)', '', final_answer)
    if "A Vidente:" in final_answer:
        final_answer = final_answer.split("A Vidente:")[1].strip()
    final_answer = re.sub(r'Observação:.*', '', final_answer, flags=re.DOTALL).strip()

    # Save assistant's final response
    add_message("assistant", final_answer)

###############################################################################
# 5) SIDEBAR
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
            st.experimental_rerun()

###############################################################################
# 6) TOP CONTAINER
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
# 7) FORM FOR USER INPUT
###############################################################################
with st.form("message_form", clear_on_submit=True):
    user_input = st.text_input("Mande sua pergunta para a Vidente...", key="user_input")
    col1, col2 = st.columns([1, 1])
    with col1:
        submitted = st.form_submit_button("Enviar")
    with col2:
        tarot_clicked = st.form_submit_button("Tirar Tarot")

if submitted and user_input.strip():
    handle_message(user_input)

if tarot_clicked:
    drawn_card = draw_tarot_card()
    handle_message(f"Faça uma tiragem de Tarot para mim. A carta sorteada foi: {drawn_card}")

###############################################################################
# 8) DISPLAY MESSAGES (WITHOUT chat-container)
###############################################################################
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
            f'<div class="message assistant-message"><strong>A Vidente:</strong> {final_answer}</div>',
            unsafe_allow_html=True
        )