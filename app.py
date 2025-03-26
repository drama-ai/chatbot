import os
import re
import json
import time
import random
import requests
from requests.adapters import Retry, HTTPAdapter
import streamlit as st
import base64

from logic import (
    STATIC_CONTEXT,
    draw_tarot_card,
    add_message,
    get_conversation,
    clear_conversation,
    separate_thinking_and_response,
    stream_ollama_response,
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

# Load banner image for the bottom
banner_path = "assets/regua_de_logos-EKO_Prancheta1.png"
encoded_banner = get_base64_image(banner_path)

if "action_taken" not in st.session_state:
    st.session_state["action_taken"] = False

###############################################################################
# 2) INJECT CSS AT THE TOP (NO chat-container)
###############################################################################
st.markdown(
    f"""
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

/* Fix text input field alignment */
div[data-testid="stChatInput"] {{
    display: flex !important;
    align-items: center !important;
}}

div[data-testid="stChatInput"] input {{
    padding: 12px !important;
    margin: 12px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

}}

/* Fix submit button alignment */
div[data-testid="stChatInput"] button {{
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    margin: 0 !important;
    height: 42px !important;
    width: 42px !important;
}}

/* Target the SVG icon inside the button */
div[data-testid="stChatInput"] button svg {{
    display: block !important;
    margin: auto !important;
}}
</style>
""",
    unsafe_allow_html=True,
)


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
def get_full_ollama_response(
    prompt: str, model: str = "llama3.1:8b", temperature: float = 0.9
):
    """Get a complete response from Ollama API with VPN-aware connection handling"""
    try:
        # Create a session with retries
        s = requests.Session()
        retries = requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        s.mount("http://", requests.adapters.HTTPAdapter(max_retries=retries))
        s.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))

        # Try different Ollama endpoints
        ollama_endpoints = []

        # Try environment variables first - handle pre-formatted URLs correctly
        if os.environ.get("OLLAMA_PUBLIC_URL"):
            public_url = os.environ.get("OLLAMA_PUBLIC_URL")
            # Check if URL already contains the API path to avoid duplication
            if "/api/generate" in public_url:
                ollama_endpoints.append(public_url)  # Use complete URL as-is
            else:
                ollama_endpoints.append(
                    public_url.rstrip("/")
                )  # Normalize for later path appending

        if os.environ.get("OLLAMA_API_BASE"):
            api_base = os.environ.get("OLLAMA_API_BASE")
            # Check if URL already contains the API path
            if "/api/generate" in api_base:
                ollama_endpoints.append(api_base)  # Use complete URL as-is
            else:
                ollama_endpoints.append(
                    api_base.rstrip("/")
                )  # Normalize for later path appending

        # Add fallback endpoints
        ollama_endpoints.extend(
            [
                "http://127.0.0.1:11434",  # Direct IP address works better with VPNs
                "http://0.0.0.0:11434",  # Bind address if OLLAMA_HOST is set
                "http://localhost:11434",
                "http://host.docker.internal:11434",
            ]
        )

        # Try each endpoint
        for ollama_base in ollama_endpoints:
            try:
                # Properly construct the API URL without duplication
                api_url = ollama_base
                if not api_url.endswith("/api/generate"):
                    api_url = f"{ollama_base.rstrip('/')}/api/generate"

                print(f"Sending full response request to Ollama at: {api_url}")
                response = s.post(
                    api_url,
                    json={
                        "model": model,
                        "prompt": prompt,
                        "temperature": temperature,
                        "stream": False,
                    },
                    timeout=45,  # Increased timeout for VPN conditions
                )

                print(f"Response status code: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "")
                else:
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
        return "⚠️ Não foi possível conectar ao servidor Ollama. Verifique sua conexão ou tente novamente mais tarde."

    except Exception as e:
        error_message = f"Error getting full response from Ollama: {str(e)}"
        print(error_message)
        return "⚠️ Erro ao conectar com o servidor. Tente novamente mais tarde ou consulte o administrador do sistema."


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
    tarot_keywords = [
        "jogo de tarot",
        "tirar tarot",
        "leitura de tarot",
        "tarô",
        "tarot",
        "carta",
        "cartas",
    ]

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
    if re.search(r"\b(astrologia|signos|horóscopo)\b", user_input, re.IGNORECASE):
        tone_instruction = "Os astros traçam caminhos, mas cada um tem seu próprio brilho no céu. O que realmente deseja compreender sobre sua jornada?"
    elif len(user_input.split()) <= 2 and re.match(
        r"^(oi|olá|bom dia|e aí|opa|hello)$", user_input, re.IGNORECASE
    ):
        tone_instruction = """Cumprimente o consulente de forma acolhedora e pergunte se deseja:
        - Tirar uma carta de tarô (uma única carta)
        - Compartilhar um segredo
        - Fazer uma pergunta
        - Desabafar

        Não use a expressão 'primeira carta' até que o consulente concorde explicitamente em realizar uma leitura de múltiplas cartas e saiba quantas cartas serão tiradas."""
    else:
        tone_instruction = (
            "Responda de maneira enigmática e simbolicamente rica, caso o tema permita."
        )

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
    final_answer = final_answer.replace('"', "")
    final_answer = re.sub(r"\(.*?\)", "", final_answer)
    if "EKO:" in final_answer:
        final_answer = final_answer.split("EKO:")[1].strip()
    elif "A Vidente:" in final_answer:  # Backwards compatibility
        final_answer = final_answer.split("A Vidente:")[1].strip()

    # Remove any mentions of tarot cards if not in tarot game mode
    if not is_tarot_request:
        # Remove common tarot card mentions
        tarot_cards = [
            "O Mago",
            "A Sacerdotisa",
            "A Imperatriz",
            "O Imperador",
            "O Hierofante",
            "Os Enamorados",
            "O Carro",
            "A Força",
            "O Eremita",
            "A Roda da Fortuna",
            "A Justiça",
            "O Enforcado",
            "A Morte",
            "A Temperança",
            "O Diabo",
            "A Torre",
            "A Estrela",
            "A Lua",
            "O Sol",
            "O Julgamento",
            "O Mundo",
            "O Louco",
            "A Espada",
        ]
        for card in tarot_cards:
            final_answer = re.sub(rf"{card}:", "", final_answer)
            final_answer = re.sub(rf"{card}[,.!?]", ".", final_answer)

    final_answer = re.sub(r"Observação:.*", "", final_answer, flags=re.DOTALL).strip()

    # Save assistant's final response
    add_message("assistant", final_answer)


###############################################################################
# 6) MAIN APPLICATION
###############################################################################
def main():
    # Set the background image
    st.markdown(
        f"""
    <style>
    .stApp {{
        background: url("data:image/png;base64,{encoded_bg}") no-repeat center center fixed;
        background-size: cover;
    }}
    
    /* Hide "Press Enter" text */
    .stTextInput div small {{
        display: none;
    }}
    
    /* Only adjust spacing to fix the gap */
    .block-container {{
        padding-top: 1rem;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Fixed header area that won't scroll
    header_container = st.container()
    with header_container:
        if encoded_avatar:
            st.markdown(
                f"""
                <div class="eko-box">
                    <img src="data:image/png;base64,{encoded_avatar}" alt="Avatar" style="width:150px; margin: 0 auto;" />
                    {f'<img src="data:image/png;base64,{encoded_intro}" alt="Introdução EKO" class="intro-img"/>' if encoded_intro else ''}
                    <p class="subtitle">Vamos traçar novos destinos?</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.write("⚠️ Avatar not found:", avatar_path)

    # Initialize conversation if needed
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Get the conversation
    conversation = get_conversation()

    # Only show the message container if there are messages
    if len(conversation) > 0:
        # Create scrollable message container with fixed height
        message_container = st.container(height=400, border=False)
        with message_container:
            # Create a placeholder for JavaScript injection
            js_placeholder = st.empty()

            for msg in conversation:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div class="message user-message"><strong>Consulente:</strong> {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    _, final_answer = separate_thinking_and_response(msg["content"])
                    st.markdown(
                        f'<div class="message assistant-message"><strong>EKO:</strong> {final_answer}</div>',
                        unsafe_allow_html=True,
                    )

            # Add JavaScript for auto-scrolling to the bottom of the message container
            js_placeholder.markdown(
                """
            <script>
                // Function to scroll all scrollable containers to the bottom
                function scrollToBottom() {
                    const containers = window.parent.document.querySelectorAll('[data-testid="stVerticalBlock"]');
                    containers.forEach(container => {
                        if (container.scrollHeight > container.clientHeight) {
                            container.scrollTop = container.scrollHeight;
                        }
                    });
                }
                
                // Call immediately and after delays to ensure it works
                scrollToBottom();
                setTimeout(scrollToBottom, 200);
                setTimeout(scrollToBottom, 500);
            </script>
            """,
                unsafe_allow_html=True,
            )

    # Fixed footer area for input
    footer_container = st.container()
    with footer_container:
        # Create a placeholder for the spinner/loading message
        spinner_placeholder = st.empty()

        # Using st.chat_input instead of form for a cleaner chat experience
        user_input = st.chat_input("Fale com a EKO...", key="user_input")

        # Center the Tarot button at the bottom with proper spacing
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing

        # Simplify approach - just use a regular Streamlit button with custom styling
        st.markdown(
            """
        <style>
        /* Style the Tarot button */
.intro-img {
    display: block !important;
    margin: 1.2rem auto !important;
    max-width: 650px !important;
    height: auto !important;
}

        @media (max-width: 1000px) {
    .intro-img {
        max-width: 280px !important;
    }
    /* Slightly decrease font size for all elements on mobile */
    .stApp, .stApp * {
        font-size: .98em !important;
    }
    /* Ensure chat input and buttons remain readable */
    .stButton > button {
        font-size: 16px !important;
        padding: 8px !important;
        margin: 5px !important;
    }
    /* Ensure messages are readable */
    .message {
        font-size: 0.97em !important;
    }
    /* Add margin to the top of content */
    .block-container {
        margin-top: 15px !important;
    }
    /* Make the Tarot button smaller on mobile using the exact class name */
    div.stVerticalBlock button#tarot_btn, 
    div.stHorizontalBlock button#tarot_btn {
        width: 120px !important;
        padding: 4px !important;
        font-size: 10px !important;
    }
    
    /* Style for the submit button in text input field */
    div[data-testid="stChatInput"] button {
        width: 36px !important;
        height: 36px !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: 1 !important;
        font-size: 10px !important;
    }
    
    div[data-testid="stChatInput"] button svg {
        display: block !important;
        margin: auto !important;
    }
    /* Decrease space between elements */
    div.stVerticalBlock,
    div.stHorizontalBlock {
        margin-top: -5px !important;
        margin-bottom: 5px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
        }
        .stButton > button {
            background-color: #4E386F !important;
            color: white !important;
            border: none !important;
            padding: 10px !important;
            text-align: center !important;
            text-decoration: none !important;
            font-size: 16px !important;
            margin: 4px auto !important;
            cursor: pointer !important;
            border-radius: 8px !important;
            white-space: nowrap !important;
            display: block !important;
            width: 200px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        
        /* Center the button container */
        div.row-widget.stButton {
            text-align: center !important;
            margin-bottom: 15px !important;
            width: 100% !important;
            display: flex !important;
            justify-content: center !important;
        }
        
        /* Ensure proper centering for Tarot button */
        button#tarot_btn {
            margin: 0 auto !important;
            width: 200px !important;
            display: block !important;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Remove the column-based approach and use a single centered container
        tarot_container = st.container()
        with tarot_container:
            tarot_button = st.button("Tirar Tarot", key="tarot_btn")

        # Handle user text input
        if user_input and user_input.strip():
            st.session_state["action_taken"] = True
            add_message("user", user_input)

            # Show spinner in the placeholder
            with spinner_placeholder.container():
                with st.spinner("EKO está consultando os astros..."):
                    handle_message(user_input)

            st.rerun()

        # Handle tarot button click
        if tarot_button:
            st.session_state["action_taken"] = True
            drawn_card = draw_tarot_card()
            tarot_request = f"A carta sorteada foi: {drawn_card}"

            # Add user message first
            add_message("user", tarot_request)

            # Show spinner in the placeholder
            with spinner_placeholder.container():
                with st.spinner("EKO está interpretando a carta..."):
                    handle_message(tarot_request)

            st.rerun()

    # Add banner at the bottom (fixed position)
    if encoded_banner:
        st.markdown(
            f"""
            <style>
            .footer-banner {{                
                position: fixed;
                bottom: -150px;
                left: -17px;
                width: 100%;
                text-align: center;
                z-index: 999;
                display: flex;
                justify-content: center;
                padding-bottom: -20px;
            }}
            .banner-image {{                
                max-width: 460px;
                height: auto;
                transform: translateX(32px); /* Shift to the right to match screenshot */
            }}
            @media (max-width: 768px) {{
                .banner-image {{
                    max-width: 300px;
                }}
            }}
            </style>
            <div class="footer-banner">
                <img src="data:image/png;base64,{encoded_banner}" alt="Partners" class="banner-image" />
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
