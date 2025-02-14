import streamlit as st
import requests
from tinydb import TinyDB, Query
import datetime
import json
import re
import uuid
import os

from context import static_context

# ----------------------------------
# Custom CSS Styling and Animations
# ----------------------------------
st.markdown(
    """
    <style>
    /* Overall page styling */
    body {
        background: #f5f5f5;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Container for the entire chat area */
    .chat-container {
        max-width: 800px;
        margin: 20px auto;
        padding: 20px;
        background: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
        background-color: #DCF8C6;
        text-align: right;
        margin-left: auto;
    }
    /* Styling for assistant messages */
    .assistant-message {
        background-color: #F1F0F0;
        text-align: left;
        margin-right: auto;
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
# 1. Persistent Context
# ----------------------------------
STATIC_CONTEXT = static_context

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
    # CHANGED: read from st.secrets first, then environment variable, then fallback:
    url = st.secrets.get("OLLAMA_PUBLIC_URL", os.getenv("OLLAMA_PUBLIC_URL", "http://host.docker.internal:11434/api/generate"))

    headers = {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "1",
        "User-Agent": "Mozilla/5.0"
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
    st.title("Contextual ChatBot Prototype")
    st.markdown("Each user gets an independent conversation (ephemeral for them, stored in DB).")
    if st.button("Clear Conversation", key="clear"):
        clear_conversation()
        st.rerun()

    # Toggle to show/hide internal thinking
    show_thinking = st.checkbox("Show internal thinking", value=False)

# ----------------------------------
# 7. Chat Input Form
# ----------------------------------
with st.container():
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message:")
        submit_button = st.form_submit_button(label="Send")

# Process new message
if submit_button and user_input:
    # Save the user's message
    add_message("user", user_input)

    # Build prompt with static context + conversation history
    conversation = get_conversation()
    prompt = (
        STATIC_CONTEXT + "\n" +
        "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation]) +
        "\nassistant:"
    )

    # Streaming placeholder for partial response
    streaming_placeholder = st.empty()
    final_stream_response = ""

    with st.spinner("Generating response..."):
        for partial in stream_ollama_response(prompt):
            final_stream_response = partial
            # Exclude <think> sections from partial display
            _, final_answer = separate_thinking_and_response(final_stream_response)
            streaming_placeholder.markdown(
                f'<div class="message assistant-message"><strong>Assistant:</strong> {final_answer}</div>',
                unsafe_allow_html=True
            )

    # Save the final assistant response
    add_message("assistant", final_stream_response)
    st.rerun()

# ----------------------------------
# 8. Conversation History Display
# ----------------------------------
with st.container():
    st.subheader("Conversation History (This Session)")
    chat_container = st.container()
    conversation = get_conversation()
    with chat_container:
        for msg in conversation:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                st.markdown(
                    f'<div class="message user-message"><strong>User:</strong> {content}</div>',
                    unsafe_allow_html=True
                )
            else:
                # assistant
                thinking_parts, final_answer = separate_thinking_and_response(content)
                st.markdown(
                    f'<div class="message assistant-message"><strong>Assistant:</strong> {final_answer}</div>',
                    unsafe_allow_html=True
                )
                if show_thinking and thinking_parts:
                    with st.expander("Internal model thoughts"):
                        for part in thinking_parts:
                            st.markdown(f'<div class="model-thought">{part.strip()}</div>', unsafe_allow_html=True)