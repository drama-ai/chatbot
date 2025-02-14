import streamlit as st
import requests
from tinydb import TinyDB
import datetime
import json
import re
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

def get_conversation():
    """Retrieve all conversation messages sorted by timestamp."""
    messages = messages_table.all()
    return sorted(messages, key=lambda x: x.get("timestamp", ""))

def add_message(role: str, content: str):
    """Add a new message to the conversation log."""
    messages_table.insert({
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.now().isoformat()
    })

def clear_conversation():
    """Clear all messages from the conversation log."""
    messages_table.truncate()

# ----------------------------------
# 3. Helper: Separate Thinking from Final Response
# ----------------------------------
def separate_thinking_and_response(text: str):
    """
    Extracts all text between <think> and </think> tags as internal thinking,
    and returns a tuple: (list_of_thinking, final_response_text)
    """
    thinking_parts = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    # Remove all thinking tokens from the text to produce the final response.
    final_response = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return thinking_parts, final_response.strip()

# ----------------------------------
# 4. Streaming Function to Call Ollama’s API
# ----------------------------------
def stream_ollama_response(prompt: str, model: str = "llama3.1:8b"):
    url = "https://f04f-179-214-115-197.ngrok-free.app/api/generate"  # (Use the current ngrok URL)
    
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
# 5. Main Interface Header and Controls
# ----------------------------------
with st.container():
    st.title("Contextual ChatBot Prototype")
    st.markdown("This chatbot maintains persistent context and streams responses in real time.")
    # Place Clear Conversation button in header (outside the sidebar)
    if st.button("Clear Conversation", key="clear"):
        clear_conversation()
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            st.warning("Please refresh the page.")
    # Toggle to show/hide internal thinking
    show_thinking = st.checkbox("Show internal thinking", value=False)

# ----------------------------------
# 6. Chat Input Form (inside a styled container)
# ----------------------------------
with st.container():
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Your message:")
        submit_button = st.form_submit_button(label="Send")

# Process new message
if submit_button and user_input:
    add_message("user", user_input)
    # Build prompt with static context and conversation history.
    conversation = get_conversation()
    prompt = (
        STATIC_CONTEXT + "\n" +
        "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation]) +
        "\nassistant:"
    )
    
    # Placeholder for streaming response.
    streaming_placeholder = st.empty()
    final_stream_response = ""
    
    with st.spinner("Generating response..."):
        for partial in stream_ollama_response(prompt):
            final_stream_response = partial
            # Extract final answer (excluding internal thinking)
            _, final_answer = separate_thinking_and_response(final_stream_response)
            streaming_placeholder.markdown(
                f'<div class="message assistant-message"><strong>Assistant:</strong> {final_answer}</div>',
                unsafe_allow_html=True
            )
    # Save the final complete assistant response.
    add_message("assistant", final_stream_response)
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

# ----------------------------------
# 7. Conversation History Display
# ----------------------------------
with st.container():
    st.subheader("Conversation History")
    chat_container = st.container()
    conversation = get_conversation()
    with chat_container:
        for msg in conversation:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="message user-message"><strong>User:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                # Separate internal thinking and final answer for assistant messages.
                thinking_parts, final_answer = separate_thinking_and_response(msg["content"])
                st.markdown(
                    f'<div class="message assistant-message"><strong>Assistant:</strong> {final_answer}</div>',
                    unsafe_allow_html=True
                )
                # If the user has opted to see internal thinking and there is any, display it.
                if show_thinking and thinking_parts:
                    with st.expander("Internal model thoughts"):
                        for part in thinking_parts:
                            st.markdown(f'<div class="model-thought">{part.strip()}</div>', unsafe_allow_html=True)