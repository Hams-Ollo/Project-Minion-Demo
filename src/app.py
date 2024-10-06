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
langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
langchain_project = os.getenv("LANGCHAIN_PROJECT")


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

# Tool/helper function for agents to perform basic tasks
def basic_task_tool(task: str) -> str:
    if task == "fetch_random_fact":
        facts = [
            "Cats sleep for 12-16 hours a day.",
            "Dogs have a sense of time and can predict future events.",
            "Monkeys are highly social animals and live in troops.",
            "The receptionist is here to help direct your query."]
        return random.choice(facts)
    return "I cannot perform this task."

# Update each agent to perform a basic task
def invoke_agent_with_task(state: State, model: ChatGroq, prompt: ChatPromptTemplate, agent_name: str) -> dict:
    messages = state['messages']
    human_input = messages[-1].content if isinstance(messages[-1], HumanMessage) else ""
    
    logger.info(f"\033[94m[{agent_name} agent] Received input: {human_input}\033[0m")
    
    # Example of invoking a basic tool/helper function
    if "random fact" in human_input.lower():
        fact = basic_task_tool("fetch_random_fact")
        logger.info(f"\033[96m[{agent_name} agent] Providing random fact: {fact}\033[0m")
        return {"messages": state['messages'] + [AIMessage(content=fact)]}
    
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