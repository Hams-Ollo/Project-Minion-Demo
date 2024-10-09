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
        logging.FileHandler('multi_agent_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)

# Access environment variables
groq_api_key = os.getenv("GROQ_API_KEY")

# Define chatbot state
class State(TypedDict):
    messages: list[Union[HumanMessage, AIMessage]]

# Initialize models for each agent
cat_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
dog_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
monkey_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
receptionist_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
orchestrator_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")

# Prompt templates
cat_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI assistant who loves to talk about cats."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

dog_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI assistant who loves to talk about dogs."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

monkey_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI assistant who loves to talk about monkeys."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

receptionist_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI receptionist, providing general help and directing users appropriately."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Define orchestrator prompt with more explicit instructions
orchestrator_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are an orchestrator assistant. You need to determine which specialized agent should handle each user query. Here are the rules:
    - The 'cat agent' handles all queries related to cats, kittens, or feline-related information. Example queries include: 'I love cats', 'Tell me about Siamese cats', 'Give me a cat fact'.
    - The 'dog agent' handles all queries related to dogs, puppies, or canine-related information. Example queries include: 'I love dogs', 'What is the best breed of dog?', 'Give me a dog fact'.
    - The 'monkey agent' handles all queries related to monkeys, apes, or primate-related information. Example queries include: 'Tell me about monkeys', 'I love chimpanzees', 'Give me a monkey fact'.
    - The 'receptionist agent' handles any general questions that are not specifically related to cats, dogs, or monkeys, or when the intent is unclear.
    Based on the user query, output the name of the agent that should handle the query: 'cat', 'dog', 'monkey', or 'receptionist'."""),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Function to determine which agent to use
def agent_orchestrator(user_question: str) -> Callable[[State], dict]:
    # Invoke orchestrator LLM to determine routing
    response = orchestrator_model.invoke(orchestrator_prompt.format(input=user_question))
    agent_name = response.content.strip().lower()

    if agent_name == "cat":
        logger.info("Routing to cat agent.")
        return cat_agent
    elif agent_name == "dog":
        logger.info("Routing to dog agent.")
        return dog_agent
    elif agent_name == "monkey":
        logger.info("Routing to monkey agent.")
        return monkey_agent
    else:
        logger.info("Routing to receptionist agent.")
        return receptionist_agent

# Functions representing each agent
def cat_agent(state: State) -> dict:
    return invoke_agent(state, cat_model, cat_prompt, "cat")

def dog_agent(state: State) -> dict:
    return invoke_agent(state, dog_model, dog_prompt, "dog")

def monkey_agent(state: State) -> dict:
    return invoke_agent(state, monkey_model, monkey_prompt, "monkey")

def receptionist_agent(state: State) -> dict:
    return invoke_agent(state, receptionist_model, receptionist_prompt, "receptionist")

# Function to invoke a specific agent
def invoke_agent(state: State, model: ChatGroq, prompt: ChatPromptTemplate, agent_name: str) -> dict:
    messages = state['messages']
    human_input = messages[-1].content if isinstance(messages[-1], HumanMessage) else ""
    
    logger.info(f"\033[94m[{agent_name} agent] Received input: {human_input}\033[0m")
    
    try:
        response = model.invoke(prompt.format(chat_history=messages[:-1], input=human_input))
        
        logger.info(f"\033[92m[{agent_name} agent] Response: {response.content}\033[0m")
        
        if response.content.strip():
            return {"messages": state['messages'] + [AIMessage(content=response.content)]}
        else:
            logger.warning(f"\033[93m[{agent_name} agent] Empty response from agent\033[0m")
            return {"messages": state['messages'] + [AIMessage(content="I'm sorry, I couldn't generate a response. Could you try asking something else?")]}    
    except Exception as e:
        logger.error(f"\033[91m[{agent_name} agent] Error in invoke_agent function: {str(e)}\033[0m", exc_info=True)
        return {"messages": state['messages'] + [AIMessage(content="I apologize, but I encountered an error. Can we try again?")]}    

# Initialize Streamlit app
st.set_page_config(page_title="Project Minion AI Assistant", page_icon="🤖")
st.title("Project Minion AI Assistant 🤖")
st.write("Welcome to Project Minion AI Assistant! This chatbot routes your queries to specialized agents who love to talk about cats, dogs, monkeys, or provide general assistance.")

# Add a sidebar for additional user controls
st.sidebar.title("Chat Settings")
st.sidebar.write("Configure your chat experience here.")
st.sidebar.markdown("---")

# Option to clear the chat history
if st.sidebar.button("Clear Chat History"):
    st.session_state['messages'] = []

# Global state to maintain conversation history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# User input with an improved UI
def user_input_widget():
    st.text_input("Enter your question:", key="user_input", placeholder="Ask me anything about cats, dogs, monkeys, or general topics...")
    return st.session_state.user_input

user_question = user_input_widget()

if st.button("Send") and user_question:
    # Update state with user's question
    st.session_state['messages'].append(HumanMessage(content=user_question))
    
    # Determine which agent should handle the query
    try:
        selected_agent = agent_orchestrator(user_question)
        st.session_state['messages'] = selected_agent({"messages": st.session_state['messages']})['messages']
    except Exception as e:
        logger.error(f"Error in orchestrator or agent: {str(e)}", exc_info=True)
        st.session_state['messages'].append(AIMessage(content="An error occurred while processing your request."))

# Display conversation history in a chat-like format with enhanced UI
for message in st.session_state['messages']:
    if isinstance(message, HumanMessage):
        st.markdown(f"<div style='background-color:#2a2a2a; padding:10px; border-radius:10px; margin-bottom:5px; color: #ffffff;'><strong>You:</strong> {message.content}</div>", unsafe_allow_html=True)
    elif isinstance(message, AIMessage):
        st.markdown(f"<div style='background-color:#3a3a3a; padding:10px; border-radius:10px; margin-bottom:5px; color: #ffffff;'><strong>🤖 Minion AI:</strong> {message.content}</div>", unsafe_allow_html=True)

# Footer section with credits and helpful information
st.sidebar.markdown("---")
st.sidebar.write("**About Project Minion AI**")
st.sidebar.write("Project Minion AI is a multi-agent chatbot that helps answer your questions about cats, dogs, monkeys, and more. Built with Streamlit for an intuitive user experience.")

# Add some styling to enhance the user experience
st.markdown("<style> \n    .reportview-container { \n        background: #1e1e1e;\n    }\n    .sidebar .sidebar-content {\n        background: #1e1e1e;\n    }\n    .stTextInput > div > input {\n        background-color: #333333;\n        color: #ffffff;\n    }\n    .stButton > button {\n        background-color: #4a4a4a;\n        color: #ffffff;\n    }\n</style>", unsafe_allow_html=True)