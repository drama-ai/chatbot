import streamlit as st
import random
import base64
import os

st.set_page_config(
    page_title="E-CO Chat",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_base64_image(image_path: str) -> str:
    """Reads a local image file and returns its Base64-encoded string."""
    if not os.path.exists(image_path):
        return ""
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# 1) Load the background image from the assets folder
bg_path = "assets/background.jpg"  # Adjust this path/filename
encoded_bg = get_base64_image(bg_path)

# 2) Load the avatar image (the E-CO icon) from the assets folder
avatar_path = "assets/ecoicone.png"
encoded_avatar = get_base64_image(avatar_path)

# 3) Prepare the custom CSS. We inject the background image into `.main`.
css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');

/* Force every element to use the pixel font */
html, body, [data-testid="stAppViewContainer"] * {{
  font-family: 'Press Start 2P', monospace !important;
  letter-spacing: 0.5px; /* optional: tweak spacing for readability */
}}

#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
.stDeployButton {{display: none;}}

/* Container styling: narrower (450px) plus a background image */
.main {{
  background: url("data:image/jpg;base64,{encoded_bg}") no-repeat center center;
  background-size: cover; /* or contain, if you prefer */
  border-radius: 20px;
  padding: 0;
  max-width: 450px; 
  margin: 50px auto;
}}

/* Top-left corner text */
.header-left {{
  text-align: left;
  padding: 20px;
  margin: 0;
}}

.header-left h1 {{
  font-size: 2rem;
  margin: 0;
}}

/* Optional black pill below top-left E-CO */
.header-left p {{
  background-color: black;
  color: white;
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 0.7rem;
  margin-top: 5px;
}}

.main-content {{
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}}

/* Big pixel text below the avatar */
.main-title {{
  font-size: 2rem; 
  text-align: center;
  margin-top: 10px;
  margin-bottom: 5px;
}}

.subtitle {{
  font-size: 1rem;
  color: #666;
  text-align: center;
  margin-bottom: 30px;
}}

/* Make the avatar bigger (150px) */
.eco-avatar {{
  width: 150px;
  display: block;
  margin: 0 auto 10px auto;
}}

/* Chat box area: narrower (350px) */
.chat-input-area {{
  background-color: rgba(241,241,241,0.85); /* a bit transparent if desired */
  border-radius: 10px;
  padding: 20px;
  width: 350px; 
  margin: 0 auto;
}}

.fortune-btn {{
  background-color: white;
  color: #333;
  border: 1px solid #ccc;
  border-radius: 20px;
  padding: 8px 15px;
  cursor: pointer;
}}

.search-btn {{
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 15px;
  cursor: pointer;
}}

/* Chat message bubble also narrower (350px) */
.chat-message {{
  background-color: rgba(241,241,241,0.85);
  border-radius: 10px;
  padding: 10px 15px;
  margin-top: 20px;
  width: 350px;
  text-align: left;
  margin-left: auto;
  margin-right: auto;
}}
</style>
"""

st.markdown(css, unsafe_allow_html=True)

def read_fortune():
    fortunes = [
        "Uma jornada inesperada está prestes a começar.",
        "Você encontrará uma oportunidade valiosa em breve.",
        "Um novo relacionamento trará alegria à sua vida.",
        "Confie em sua intuição para tomar a próxima decisão importante.",
        "Um desafio atual se resolverá de maneira surpreendente."
    ]
    return random.choice(fortunes)

def process_user_input(user_input):
    return f"Obrigada por sua mensagem: '{user_input}'. Como posso ajudar?"

st.markdown('<div class="main">', unsafe_allow_html=True)

# Top-left corner header: "E-CO" with optional black pill
st.markdown("""
<div class="header-left">
  <h1>E-CO</h1>
  <p>O que é a E-CO</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# 4) Embed the avatar in the center, if found
if encoded_avatar:
    st.markdown(
        f'<img src="data:image/png;base64,{encoded_avatar}" alt="" class="eco-avatar" />',
        unsafe_allow_html=True
    )
else:
    st.write("⚠️ Avatar não encontrado:", avatar_path)

# Big pixel text under the avatar
st.markdown("<h1 class='main-title'>Oi, eu sou a E-CO</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Vamos traçar novos destinos?</p>", unsafe_allow_html=True)

# Input area
with st.form(key="message_form", clear_on_submit=True):
    st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
    user_input = st.text_area("Mande mensagem para a E-CO...", height=80)
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        fortune_button = st.form_submit_button("♣ Leia sua sorte")
    with col2:
        submit_button = st.form_submit_button("Pesquise :)")

# Show result
if submit_button and user_input.strip():
    response = process_user_input(user_input.strip())
    st.markdown(f"<div class='chat-message'><strong>Assistant:</strong> {response}</div>", unsafe_allow_html=True)

if fortune_button:
    fortune = read_fortune()
    st.markdown(f"<div class='chat-message'><strong>Assistant:</strong> {fortune}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close main-content
st.markdown("</div>", unsafe_allow_html=True)  # close main