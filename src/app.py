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
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows you to keep sensitive information (like API keys) secure and easily configurable.
load_dotenv()

# Set up logging for the application
# Logging helps track what is happening during the execution of your program, useful for debugging.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('multi_agent_orchestrator.log')  # Log to a file for later review
    ]
)
logger = logging.getLogger(__name__)

# Access environment variables to get API keys and settings
groq_api_key = os.getenv("GROQ_API_KEY")
langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
langchain_project = os.getenv("LANGCHAIN_PROJECT")

# Define chatbot state
# The State class defines the format for maintaining the conversation history between user and agent.
class State(TypedDict):
    messages: list[Union[HumanMessage, AIMessage]]  # Stores the messages exchanged

# Initialize language models for each agent (cat, dog, monkey, receptionist, orchestrator)
# Each agent has a distinct model that is specialized to answer related questions.
cat_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
dog_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
monkey_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
receptionist_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
orchestrator_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")

# Define prompt templates for each agent
# These prompts are what the agent sees when generating a response, setting the tone and context.
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

# Define orchestrator prompt with explicit instructions
# The orchestrator determines which specialized agent (cat, dog, monkey, or receptionist) should handle each query.
orchestrator_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are an orchestrator assistant. You need to determine which specialized agent should handle each user query. Here are the rules:
    - The 'cat agent' handles all queries related to cats.
    - The 'dog agent' handles all queries related to dogs.
    - The 'monkey agent' handles all queries related to monkeys.
    - The 'receptionist agent' handles any general questions or unclear intent.
    Based on the user query, output the name of the agent that should handle the query: 'cat', 'dog', 'monkey', or 'receptionist'."""),
    HumanMessagePromptTemplate.from_template("{input}")
])

# Function to determine which agent should be used based on the user's question
def agent_orchestrator(user_question: str) -> Callable[[State], dict]:
    # Use the orchestrator model to determine which agent should handle the query
    response = orchestrator_model.invoke(orchestrator_prompt.format(input=user_question))
    agent_name = response.content.strip().lower()  # Get the agent name recommended by the orchestrator

    # Route the user question to the appropriate agent
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
# Each function below is designed to handle the conversation state by invoking the respective agent.
def cat_agent(state: State) -> dict:
    return invoke_agent(state, cat_model, cat_prompt, "cat")

def dog_agent(state: State) -> dict:
    return invoke_agent(state, dog_model, dog_prompt, "dog")

def monkey_agent(state: State) -> dict:
    return invoke_agent(state, monkey_model, monkey_prompt, "monkey")

def receptionist_agent(state: State) -> dict:
    return invoke_agent(state, receptionist_model, receptionist_prompt, "receptionist")

# Function to invoke a specific agent based on the provided model and prompt
# This function standardizes how each agent interacts with the user.
def invoke_agent(state: State, model: ChatGroq, prompt: ChatPromptTemplate, agent_name: str) -> dict:
    # Extract the latest message from the conversation state
    messages = state['messages']
    human_input = messages[-1].content if isinstance(messages[-1], HumanMessage) else ""

    # Log the received input for debugging
    logger.info(f"[{agent_name} agent] Received input: {human_input}")

    try:
        # Use LangSmith tracing to monitor this section of code
        with trace("agent_response"):
            response = model.invoke(prompt.format(chat_history=messages[:-1], input=human_input))
        
        # Log the response generated by the agent
        logger.info(f"[{agent_name} agent] Response: {response.content}")

        # Return the updated conversation state
        if response.content.strip():
            return {"messages": state['messages'] + [AIMessage(content=response.content)]}
        else:
            logger.warning(f"[{agent_name} agent] Empty response from agent")
            return {"messages": state['messages'] + [AIMessage(content="I'm sorry, I couldn't generate a response. Could you try asking something else?")]}    
    except Exception as e:
        # Handle any errors encountered during model invocation
        logger.error(f"[{agent_name} agent] Error in invoke_agent function: {str(e)}", exc_info=True)
        return {"messages": state['messages'] + [AIMessage(content="I apologize, but I encountered an error. Can we try again?")]}    

# Tool/helper function for agents to perform basic tasks
# This example function shows how agents can perform extra tasks, such as fetching random facts.
def basic_task_tool(task: str) -> str:
    if task == "fetch_random_fact":
        facts = [
            "Cats sleep for 12-16 hours a day.",
            "Dogs have a sense of time and can predict future events.",
            "Monkeys are highly social animals and live in troops.",
            "The receptionist is here to help direct your query."
        ]
        return random.choice(facts)
    return "I cannot perform this task."

# Create the state graph and add nodes
# This graph defines the conversation flow and orchestrates how user queries move through different agents.
graph = StateGraph(State)
graph.add_node("orchestrator", lambda state: agent_orchestrator(state['messages'][-1].content)(state))
graph.set_entry_point("orchestrator")  # The starting point for all queries
graph.add_edge("orchestrator", END)  # Marking the orchestrator as leading to an END state

# Compile the state graph into an executable application
# This converts the defined state flow into a callable entity.
app = graph.compile()

# Initialize Flask app for serving the chatbot via a REST API
flask_app = Flask(__name__)

# Global state to maintain the conversation history across different API calls
global_state = {"messages": []}

@flask_app.route('/chat', methods=['POST'])
def chat():
    global global_state

    # Extract the user's question from the incoming request
    data = request.json
    user_question = data.get('userquestion', '')

    try:
        # Invoke the orchestrator with the current state
        with trace("user_interaction"):
            global_state = app.invoke({"messages": global_state["messages"] + [HumanMessage(content=user_question)]})
            ai_message = global_state['messages'][-1].content

        # Log the interaction
        logger.info(f"\nUser: {user_question}\nAI: {ai_message}\n{'-'*50}")
        return jsonify({"response": ai_message})

    except Exception as e:
        # Handle any errors encountered during the endpoint call
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your request."}), 500

# Start the Flask server
# This server will run locally and serve the chatbot on port 5000.
if __name__ == '__main__':
    print("Multi-Agent Chat Server is running. Press Ctrl+C to quit.")
    flask_app.run(debug=True, port=5000, use_reloader=False)
