

from flask import Flask, request, jsonify
import os
from typing import TypedDict, Union, Callable
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langgraph.graph import StateGraph, END
import logging
from langsmith import trace
import random
from googleapiclient.discovery import build
from google.oauth2 import service_account
import requests

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
langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
langchain_project = os.getenv("LANGCHAIN_PROJECT")

os.environ["WEATHER_API_KEY"] = "<INSERT_YOUR_WEATHER_API_KEY_HERE>"

# Google API credentials setup
GOOGLE_CREDENTIALS_PATH = '<INSERT_PATH_TO_YOUR_GOOGLE_CREDENTIALS_JSON>'

# Define chatbot state
class State(TypedDict):
    messages: list[Union[HumanMessage, AIMessage]]

# Initialize models for each agent
cat_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
dog_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
monkey_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
receptionist_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
orchestrator_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
email_manager_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
scheduling_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
research_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
knowledge_base_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")

# Prompt templates for each agent
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

email_manager_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are an email manager assistant who can send and organize emails."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

scheduling_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a scheduling assistant who helps users manage events in their calendar."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

research_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a research assistant who can gather information from the web, such as the weather."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

knowledge_base_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You help manage the user's knowledge base, including note taking, categorization, and linking."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Google API setup
def setup_gmail_service():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH, scopes=['https://www.googleapis.com/auth/gmail.send']
    )
    service = build('gmail', 'v1', credentials=creds)
    return service

def setup_calendar_service():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDENTIALS_PATH, scopes=['https://www.googleapis.com/auth/calendar']
    )
    service = build('calendar', 'v3', credentials=creds)
    return service

gmail_service = setup_gmail_service()
calendar_service = setup_calendar_service()

# Helper functions
def send_email(recipient, subject, message_body):
    # Code to send an email via Gmail API
    pass

def create_event(event_data):
    # Code to create a calendar event using Google Calendar API
    pass

def get_weather(zip_code: str):
    api_key = os.getenv("WEATHER_API_KEY")
    response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?zip={zip_code}&appid={api_key}")
    if response.status_code == 200:
        weather_data = response.json()
        return f"The current weather is {weather_data['weather'][0]['description']} with a temperature of {weather_data['main']['temp']}K."
    else:
        return "I couldn't fetch the weather data. Please try again later."

def save_note_to_obsidian(note_title: str, note_content: str):
    with open(f"obsidian_notes/{note_title}.md", 'w') as note_file:
        note_file.write(note_content)

def get_note_from_obsidian(note_title: str) -> str:
    try:
        with open(f"obsidian_notes/{note_title}.md", 'r') as note_file:
            return note_file.read()
    except FileNotFoundError:
        return "Note not found."

# Define orchestrator prompt with more explicit instructions
orchestrator_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""
    You are an orchestrator assistant. You need to determine which specialized agent should handle each user query. Here are the rules:
    - The 'generic fallback minion' handles general queries.
    - The 'email manager minion' handles email-related queries.
    - The 'scheduling assistant minion' handles event or reminder-related queries.
    - The 'research minion' handles weather and simple information gathering.
    - The 'knowledge base minion' manages information and notes.
    Based on the user query, output the name of the agent that should handle the query: 'generic fallback', 'email manager', 'scheduling assistant', 'research', 'knowledge base', or other.
    """),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Function to determine which agent to use
def agent_orchestrator(user_question: str) -> Callable[[State], dict]:
    response = orchestrator_model.invoke(orchestrator_prompt.format(input=user_question))
    agent_name = response.content.strip().lower()

    if agent_name == "generic fallback":
        return generic_fallback_minion
    elif agent_name == "email manager":
        return email_manager_minion
    elif agent_name == "scheduling assistant":
        return scheduling_minion
    elif agent_name == "research":
        return research_minion
    elif agent_name == "knowledge base":
        return knowledge_base_minion
    else:
        return generic_fallback_minion

# Functions for each minion
def email_manager_minion(state: State) -> dict:
    user_input = state['messages'][-1].content
    if "send email" in user_input.lower():
        # Extract email details from user input
        send_email("recipient@example.com", "Subject", "This is a test message.")
        return {"messages": state['messages'] + [AIMessage(content="Email sent successfully!")]}    
    else:
        return invoke_agent(state, email_manager_model, email_manager_prompt, "email_manager")

def scheduling_minion(state: State) -> dict:
    user_input = state['messages'][-1].content
    if "schedule event" in user_input.lower():
        # Extract event details from user input
        create_event({"summary": "Meeting", "start": "2024-10-06T09:00:00-07:00", "end": "2024-10-06T10:00:00-07:00"})
        return {"messages": state['messages'] + [AIMessage(content="Event scheduled successfully!")]}    
    else:
        return invoke_agent(state, scheduling_model, scheduling_prompt, "scheduling")

def research_minion(state: State) -> dict:
    user_input = state['messages'][-1].content
    if "weather" in user_input.lower():
        zip_code = "94103"  # Example ZIP code, extract actual code from user input
        weather_info = get_weather(zip_code)
        return {"messages": state['messages'] + [AIMessage(content=weather_info)]}
    return invoke_agent(state, research_model, research_prompt, "research")

def knowledge_base_minion(state: State) -> dict:
    return invoke_agent(state, knowledge_base_model, knowledge_base_prompt, "knowledge_base")

def generic_fallback_minion(state: State) -> dict:
    return invoke_agent(state, receptionist_model, receptionist_prompt, "receptionist")

# Function to invoke a specific agent
def invoke_agent(state: State, model: ChatGroq, prompt: ChatPromptTemplate, agent_name: str) -> dict:
    messages = state['messages']
    human_input = messages[-1].content if isinstance(messages[-1], HumanMessage) else ""
    
    logger.info(f"\033[94m[{agent_name} agent] Received input: {human_input}\033[0m")
    
    try:
        with trace("agent_response"):
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

# Create the state graph and add nodes
graph = StateGraph(State)
graph.add_node("orchestrator", lambda state: agent_orchestrator(state['messages'][-1].content)(state))
graph.set_entry_point("orchestrator")
graph.add_edge("orchestrator", END)

# Compile the graph
app = graph.compile()

# Initialize Flask app
flask_app = Flask(__name__)

# Global state to maintain conversation history
global_state = {"messages": []}

@flask_app.route('/chat', methods=['POST'])
def chat():
    global global_state
    
    data = request.json
    user_question = data.get('userquestion', '')
    
    try:
        with trace("user_interaction"):
            global_state = app.invoke({"messages": global_state["messages"] + [HumanMessage(content=user_question)]})
            ai_message = global_state['messages'][-1].content
        
        logger.info(f"\nUser: {user_question}\nAI: {ai_message}\n{'-'*50}")
        return jsonify({"response": ai_message})
    
    except Exception as e:
        logger.error(f"\033[91mError in chat endpoint: {str(e)}\033[0m", exc_info=True)
        return jsonify({"error": "An error occurred while processing your request."}), 500

if __name__ == '__main__':
    print("Multi-Agent Chat Server is running. Press Ctrl+C to quit.")
    flask_app.run(debug=True, port=5000, use_reloader=False)