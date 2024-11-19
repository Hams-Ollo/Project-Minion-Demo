import streamlit as st
import requests
import json
from typing import List
import time

# Configure the page
st.set_page_config(
    page_title="Project Minion Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
    <style>
    /* Dark theme modifications */
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    
    .stTextInput > div > div > input {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    .user-message {
        background-color: #2c3e50;
        color: #ffffff;
        border: 1px solid #34495e;
    }
    
    .bot-message {
        background-color: #1e272e;
        color: #ffffff;
        border: 1px solid #2c3e50;
    }
    
    .message-content {
        margin-top: 0.5rem;
    }
    
    /* Sidebar modifications */
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    
    /* Button modifications */
    .stButton>button {
        background-color: #2c3e50;
        color: #ffffff;
        border: 1px solid #34495e;
    }
    
    .stButton>button:hover {
        background-color: #34495e;
        color: #ffffff;
        border: 1px solid #445566;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for messages if it doesn't exist
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Title and description
st.title("🤖 Project Minion Chat")
st.markdown("""
    Welcome to Project Minion! This AI Assistant uses specialized agents to help answer 
    your questions about cats, dogs, monkeys, or general topics.
""")

# Sidebar configuration
with st.sidebar:
    st.header("Settings")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.experimental_rerun()
    
    st.markdown("---")
    st.markdown("""
    ### Available Agents 🤖
    - 🐱 Cat Agent
    - 🐕 Dog Agent
    - 🐒 Monkey Agent
    - 👋 Receptionist Agent
    """)

# Main chat interface
def display_chat_message(message: dict, is_user: bool):
    with st.container():
        if is_user:
            st.markdown(f"""
                <div class="chat-message user-message">
                    <div><strong>You</strong> 💬</div>
                    <div class="message-content">{message}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message bot-message">
                    <div><strong>Minion AI</strong> 🤖</div>
                    <div class="message-content">{message}</div>
                </div>
            """, unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    display_chat_message(
        message['content'],
        message['is_user']
    )

# Chat input
user_input = st.chat_input("Type your message here...")

if user_input:
    # Display user message
    display_chat_message(user_input, True)
    st.session_state.messages.append({"content": user_input, "is_user": True})
    
    # Send request to backend
    try:
        response = requests.post(
            "http://localhost:5000/chat",
            json={"userquestion": user_input},
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()['response']
            display_chat_message(ai_response, False)
            st.session_state.messages.append({"content": ai_response, "is_user": False})
        else:
            st.error("Failed to get response from the server. Please try again.")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ by Project Minion Team")
