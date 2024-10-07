# Project Minion/ Echo Multi-Agent PoC Developer Guide

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overview of Multi-Agent PoC](#2-overview-of-multi-agent-poc)
3. [Components Breakdown](#3-components-breakdown)
   - 3.1 [Environment Setup](#31-environment-setup)
   - 3.2 [Logging Configuration](#32-logging-configuration)
   - 3.3 [Agent Initialization](#33-agent-initialization)
   - 3.4 [Prompt Templates](#34-prompt-templates)
   - 3.5 [Orchestrator Logic](#35-orchestrator-logic)
   - 3.6 [Agent Functions](#36-agent-functions)
   - 3.7 [Helper Tools](#37-helper-tools)
   - 3.8 [StateGraph Setup](#38-stategraph-setup)
   - 3.9 [Flask API Integration](#39-flask-api-integration)
4. [State Management and Orchestration](#4-state-management-and-orchestration)
5. [Enhancements and Next Steps](#5-enhancements-and-next-steps)

## 1. Introduction

The Project Echo Multi-Agent Proof of Concept (PoC) aims to demonstrate a multi-agent system that dynamically routes user queries to the appropriate agent based on the context of the query. This PoC uses LangGraph as the backbone for managing the workflow between agents. The orchestrator is key to determining which specialized agent should handle a query, ensuring modularity and flexibility.

The goal of this guide is to provide a detailed breakdown of the code, enabling our team to understand each component and how they all fit together to form a functional multi-agent system. This PoC will eventually be enhanced and integrated with our current agent workflows and tool functions.

## 2. Overview of Multi-Agent PoC

The PoC contains an orchestrator and several specialized "minion" agents (nodes). The orchestrator routes the user queries to the correct minion based on their content. Each agent has its own unique function and handles a specific type of user query. For example:

- **Cat Agent**: Handles queries related to cats.
- **Dog Agent**: Handles queries about dogs.
- **Monkey Agent**: Manages monkey-related queries.
- **Receptionist Agent**: Handles general questions and unclear intents.

The main objectives are:

1. Demonstrate how the **orchestrator** directs queries to different agents using the **LangGraph StateGraph**.
2. Showcase **state management** in a multi-agent context, ensuring correct interaction across agents.
3. Use a **Flask API** to expose this multi-agent chatbot as an endpoint for user interaction.

## 3. Components Breakdown

### 3.1 Environment Setup

The script loads environment variables from a `.env` file using `dotenv`. These variables are used for keeping sensitive information like API keys secure and making configurations easily adjustable.

```python
load_dotenv()
```

- **Key Environment Variables**:
  - `GROQ_API_KEY`, `LANGCHAIN_API_KEY`, and other configurations are accessed from the environment for secure access.

### 3.2 Logging Configuration

The logging setup helps with debugging by tracking application behavior and potential errors.

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('multi_agent_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)
```

- **Log Handlers**:
  - Console logging (for real-time monitoring).
  - File logging (to keep a persistent log of operations).

### 3.3 Agent Initialization

Each specialized agent (cat, dog, monkey, receptionist, orchestrator) is initialized with the `ChatGroq` model. Each agent has a specific purpose, and its language model is tuned to understand its particular topic.

```python
cat_model = ChatGroq(temperature=0.7, model_name="llama3-groq-70b-8192-tool-use-preview")
```

- **Agent Specialization**: Each model is assigned to different agents to handle domain-specific questions effectively.

### 3.4 Prompt Templates

Prompt templates define the context for each agent's response generation. Each agent has a distinct prompt that sets the expectations for its interactions.

```python
cat_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are a friendly AI assistant who loves to talk about cats."),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}")
])
```

- **System Message**: Sets the context and personality of the agent.
- **MessagesPlaceholder**: Maintains the conversation history to allow contextual responses.
- **Human Message Template**: Represents the latest user input.

### 3.5 Orchestrator Logic

The **orchestrator** uses a dedicated language model to determine which agent should handle a user query. It ensures that the correct agent is selected based on the topic of the user's question.

```python
def agent_orchestrator(user_question: str) -> Callable[[State], dict]:
    response = orchestrator_model.invoke(orchestrator_prompt.format(input=user_question))
    agent_name = response.content.strip().lower()
    
    if agent_name == "cat":
        return cat_agent
    elif agent_name == "dog":
        return dog_agent
    elif agent_name == "monkey":
        return monkey_agent
    else:
        return receptionist_agent
```

- **Routing Logic**: Maps the response from the orchestrator model to the appropriate agent function.
- **Logging**: Each routing decision is logged for visibility and debugging.

### 3.6 Agent Functions

Each agent function processes the incoming state (messages) and interacts with its respective model to generate a response. Each function uses the shared `invoke_agent` utility for standardized processing.

```python
def cat_agent(state: State) -> dict:
    return invoke_agent(state, cat_model, cat_prompt, "cat")
```

- **Invoke Agent Function**: Handles extracting messages, invoking the model, logging, and returning an updated state.
- **Error Handling**: Manages any issues in generating responses gracefully.

### 3.7 Helper Tools

A helper function (`basic_task_tool`) is provided to perform simple tasks, such as fetching random facts. This could be expanded to integrate more complex tools or workflows.

```python
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
```

### 3.8 StateGraph Setup

The **StateGraph** orchestrates the overall conversation, managing how state transitions occur between agents. This is key to maintaining a cohesive flow between agents and ensuring the correct agent processes each query.

```python
graph = StateGraph(State)
graph.add_node("orchestrator", lambda state: agent_orchestrator(state['messages'][-1].content)(state))
graph.set_entry_point("orchestrator")
graph.add_edge("orchestrator", END)
```

- **Nodes and Edges**:
  - **Node Addition**: Adds the orchestrator as the starting point.
  - **Edges**: Defines how the orchestrator connects to the end state after routing the query.

### 3.9 Flask API Integration

The Flask API is used to expose the multi-agent system through an HTTP interface, allowing users to interact with the chatbot via simple HTTP requests.

```python
flask_app = Flask(__name__)

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
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while processing your request."}), 500
```

- **State Management**: Maintains a `global_state` variable that keeps the conversation history intact across API calls.
- **API Endpoint**: `/chat` accepts user queries as POST requests, routes them through the orchestrator, and returns the appropriate response.

## 4. State Management and Orchestration

State management is crucial to ensure continuity and coherence in a multi-agent conversation. The **StateGraph** is used to track the current state and transitions effectively across different nodes. Each query is routed to an agent, which then returns an updated state containing the response.

- **Shared State**: A `global_state` variable is maintained to track the entire conversation, allowing agents to use the history to generate contextually aware responses.
- **Orchestrator as State Manager**: The orchestrator is the gatekeeper of which agent interacts with the user, leveraging the state to make context-sensitive decisions.

## 5. Enhancements and Next Steps

Once this PoC is validated, here are the next steps to enhance and integrate this workflow:

1. **Expand Agent Capabilities**:
   - Introduce new agents that handle more specific tasks.
   - Add helper functions to enhance agent capabilities.

2. **Refine StateGraph**:
   - Improve the state management strategy to handle more complex workflows and transitions.

3. **LangGraph Integration with Current Tools**:
   - Incorporate existing tools and functions developed for other projects, making use of a broader set of APIs and capabilities.

4. **Testing and Validation**:
   - Implement unit tests for agents and orchestrator functions.
   - Validate state transitions and agent routing for various scenarios.

By following this guide, developers can walk through each aspect of the multi-agent workflow in the PoC, understand the orchestrator's role, and see how different agents are connected within the LangGraph framework. This comprehensive understanding will make it easier to extend this framework and integrate it into larger, more sophisticated systems.

---

"The key to growth is the introduction of higher dimensions of consciousness into our awareness." - Lao Tzu. Let Project Echo's orchestrated agents become the embodiment of higher collaboration and intelligent workflows.
