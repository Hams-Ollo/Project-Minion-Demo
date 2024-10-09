# Import necessary libraries
import os
import logging
from typing import TypedDict, Union, Callable
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langgraph.graph import StateGraph, END
import random
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('multi_minion_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)

# Access environment variables
groq_api_key = os.getenv("GROQ_API_KEY")

# Define chatbot state
class State(TypedDict):
    messages: list[Union[HumanMessage, AIMessage]]

# Initialize models for each minion
cat_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
dog_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
monkey_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
receptionist_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
orchestrator_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")

# Prompt templates
cat_minion_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI assistant who loves to talk about cats."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

dog_minion_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI assistant who loves to talk about dogs."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

monkey_minion_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI assistant who loves to talk about monkeys."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

chat_minion_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are an advanced, friendly AI assistant named Chat Minion, designed to provide exceptional conversational experiences and general assistance. Your primary goals are:

1. Engage in natural, context-aware conversations
2. Provide accurate and helpful information on a wide range of topics
3. Offer personalized assistance based on user preferences and conversation history
4. Guide users to specialized minions (Cat, Dog, or Monkey) when appropriate
5. Maintain a positive and supportive tone throughout the interaction

Key features:
- Contextual understanding: Analyze the entire conversation history to provide relevant responses
- Personalization: Remember user preferences and adapt your communication style accordingly
- Proactive assistance: Anticipate user needs and offer suggestions or follow-up questions
- Emotional intelligence: Recognize and respond appropriately to user emotions
- Clear communication: Use concise language and break down complex information when needed
- Honesty: Admit when you don't know something or when a specialized minion might be better suited to help

Remember to:
- Ask clarifying questions when needed
- Provide step-by-step explanations for complex topics
- Offer analogies or examples to illustrate concepts
- Summarize key points at the end of longer explanations
- Suggest relevant resources for further learning
- Maintain a friendly and engaging tone throughout the conversation

If a query is specifically about cats, dogs, or monkeys, politely suggest consulting the respective specialized minion for more detailed information."""),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Define orchestrator prompt with more explicit instructions
orchestrator_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are the AI orchestrator assistant for this multi-minion framework. You need to determine which specialized minion should handle each user query. Here are the rules:
    - The 'cat minion' handles all queries related to cats, kittens, or feline-related information. Example queries include: 'I love cats', 'Tell me about Siamese cats', 'Give me a cat fact'.
    - The 'dog minion' handles all queries related to dogs, puppies, or canine-related information. Example queries include: 'I love dogs', 'What is the best breed of dog?', 'Give me a dog fact'.
    - The 'monkey minion' handles all queries related to monkeys, apes, or primate-related information. Example queries include: 'Tell me about monkeys', 'I love chimpanzees', 'Give me a monkey fact'.
    - The 'chat minion' handles any general questions or chat conversation that is not specifically related to cats, dogs, or monkeys, or when the user intent remains unclear.
    Based on the user query, output the name of the minion that should handle the query: 'cat minion', 'dog minion', 'monkey minion', or 'chat minion'."""),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Function to determine which minion to use
def minion_orchestrator(user_question: str) -> Callable[[State], dict]:
    # Invoke orchestrator LLM to determine routing
    response = orchestrator_model.invoke(orchestrator_prompt.format(input=user_question))
    minion_name = response.content.strip().lower()

    if minion_name == "cat minion":
        logger.info("Routing to cat minion.")
        return cat_minion
    elif minion_name == "dog minion":
        logger.info("Routing to dog minion.")
        return dog_minion
    elif minion_name == "monkey minion":
        logger.info("Routing to monkey minion.")
        return monkey_minion
    else:
        logger.info("Routing to chat minion.")
        return chat_minion

# Functions representing each minion
def cat_minion(state: State) -> dict:
    return invoke_minion(state, cat_model, cat_minion_prompt, "cat minion")

def dog_minion(state: State) -> dict:
    return invoke_minion(state, dog_model, dog_minion_prompt, "dog minion")

def monkey_minion(state: State) -> dict:
    return invoke_minion(state, monkey_model, monkey_minion_prompt, "monkey minion")

def chat_minion(state: State) -> dict:
    return invoke_minion(state, receptionist_model, chat_minion_prompt, "chat minion")

# Function to invoke a specific minion
def invoke_minion(state: State, model: ChatGroq, prompt: ChatPromptTemplate, minion_name: str) -> dict:
    messages = state['messages']
    human_input = messages[-1].content if isinstance(messages[-1], HumanMessage) else ""
    
    logger.info(f"\033[94m[{minion_name}] Received input: {human_input}\033[0m")
    
    try:
        response = model.invoke(prompt.format(chat_history=messages[:-1], input=human_input))
        
        logger.info(f"\033[92m[{minion_name}] Response: {response.content}\033[0m")
        
        if response.content.strip():
            return {"messages": state['messages'] + [AIMessage(content=response.content)]}
        else:
            logger.warning(f"\033[93m[{minion_name}] Empty response from minion\033[0m")
            return {"messages": state['messages'] + [AIMessage(content="I'm sorry, I couldn't generate a response. Could you try asking something else?")]}    
    except Exception as e:
        logger.error(f"\033[91m[{minion_name}] Error in invoke_minion function: {str(e)}\033[0m", exc_info=True)
        return {"messages": state['messages'] + [AIMessage(content="I apologize, but I encountered an error. Can we try again?")]}    

import streamlit as st
from langchain.schema import HumanMessage, AIMessage
import logging

# Initialize Streamlit app
st.set_page_config(page_title="Project Minion", page_icon="🤖")
st.title("Project Minion's AI Assistant 🤖")
st.write("Welcome to Project Minion! This AI Assistant routes your queries to specialized minion agents to assist with answering queries or performing specific functional tasks.")

# Add a sidebar for additional user controls
st.sidebar.title("Multi-Agent Actions 🤖")

# Minion Menu Section
st.sidebar.subheader("Menu")
if st.sidebar.button("Clear Chat"):
    st.session_state['messages'] = []
if st.sidebar.button("Run Diagnostics"):
    st.session_state['messages'].append(AIMessage(content="Running diagnostics on all minions..."))
if st.sidebar.button("View Logs"):
    st.session_state['messages'].append(AIMessage(content="Here are the latest logs."))

# Minion Actions Section
st.sidebar.markdown("---")
st.sidebar.button("Minions", key="minions_button")

# Available Minion Tools Dropdown
st.sidebar.subheader("Available Minion Tools:")
selected_tool = st.sidebar.selectbox(
    "Select a minion tool:",
    ["Knowledge Management Tool", "Dashboard Viewer Tool", "Technical Support Tool"]
)
st.sidebar.write(f"Selected tool: {selected_tool}")

# Global state to maintain conversation history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Function to handle sending queries
def send_query():
    user_question = st.session_state.user_input
    if user_question:
        # Update state with user's question
        st.session_state['messages'].append(HumanMessage(content=user_question))
        
        # Determine which minion should handle the query
        try:
            selected_minion = minion_orchestrator(user_question)
            st.session_state['messages'] = selected_minion({"messages": st.session_state['messages']})['messages']
        except Exception as e:
            logger.error(f"Error in orchestrator or minion: {str(e)}", exc_info=True)
            st.session_state['messages'].append(AIMessage(content="An error occurred while processing your request."))
        
        # Reset the input field
        st.session_state.user_input = ""

# Display conversation history in a chat-like format with enhanced UI
for message in st.session_state['messages']:
    if isinstance(message, HumanMessage):
        st.markdown(f"<div style='background-color:#2a2a2a; padding:10px; border-radius:10px; margin-bottom:5px; color: #ffffff;'><strong>You:</strong> {message.content}</div>", unsafe_allow_html=True)
    elif isinstance(message, AIMessage):
        st.markdown(f"<div style='background-color:#3a3a3a; padding:10px; border-radius:10px; margin-bottom:5px; color: #ffffff;'><strong>🤖 Minion AI:</strong> {message.content}</div>", unsafe_allow_html=True)

# User input with an improved UI
def user_input_widget():
    return st.text_input("Enter your query:", key="user_input", placeholder="Ask me anything...", on_change=send_query)

# Display the user input widget below the chat history
user_input_widget()

# Footer section with credits and helpful information
st.sidebar.markdown("---")
st.sidebar.write("**About Project Minion AI**")
st.sidebar.write("Project Minion is a multi-minion AI solution that aids the user in their tasks using its network of specialized minion agents.")

# Add some styling to enhance the user experience
st.markdown("<style> \n    .reportview-container { \n        background: #1e1e1e;\n    }\n    .sidebar .sidebar-content {\n        background: #1e1e1e;\n    }\n    .stTextInput > div > input {\n        background-color: #333333;\n        color: #ffffff;\n    }\n    .stButton > button {\n        background-color: #4a4a4a;\n        color: #ffffff;\n}</style>", unsafe_allow_html=True)