# Project Echo: LangGraph Integration Guide for Developers and Orchestrator

## Table of Contents
1. [Introduction](#introduction)
2. [Project Overview](#project-overview)
3. [Developer Guide: Migrating to LangGraph Agents](#developer-guide-migrating-to-langgraph-agents)
4. [Orchestrator Guide: Setting Up the Multi-Agent System](#orchestrator-guide-setting-up-the-multi-agent-system)
5. [Integration and Testing](#integration-and-testing)
6. [Optimization and Deployment](#optimization-and-deployment)

## 1. Introduction

This guide outlines the process of integrating the existing Project Echo chatbot components into a LangGraph-based multi-agent system. It is divided into two main sections: one for individual developers to migrate their code to LangGraph agent nodes, and another for the orchestrator to set up the overall multi-agent system.

## 2. Project Overview

- Repository: Azure DevOps
- Main working branch: `develop`
- Individual feature branches: `feature/onboarding_agent`, `feature/scheduling_assistant`, etc.

## 3. Developer Guide: Migrating to LangGraph Agents

### 3.1. Prepare Your Environment

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your_agent_name_langraph
pip install langgraph langchain openai python-dotenv
```

### 3.2. Analyze Your Current Code

- Identify the main functionality of your agent
- List all dependencies and helper functions
- Note any state information your agent needs to maintain

### 3.3. Create LangGraph Agent Structure

In your agent's directory (e.g., `project_echo/agents/your_agent_name/`):

1. Create `langraph_agent.py`:

```python
from langgraph.graph import Node
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ...utils import your_helper_functions

def create_your_agent_node():
    llm = ChatOpenAI()
    prompt = ChatPromptTemplate.from_template(
        "Your agent-specific prompt template here"
    )
    
    def your_agent_function(state):
        # Your agent's core logic here
        # Use state to get input and store output
        return {"your_output_key": "your_output_value"}
    
    return Node(your_agent_function)

# If your agent needs multiple nodes, create additional functions here
```

2. Update `__init__.py` to export your new LangGraph node:

```python
from .langraph_agent import create_your_agent_node
```

### 3.4. Migrate Your Logic

- Move your core agent logic into the `your_agent_function`
- Adapt your code to work with the `state` parameter for input and output
- Ensure all necessary data is passed through the state

### 3.5. Handle Dependencies

- Move helper functions to `project_echo/utils/` if they're not already there
- Update imports in your agent file

### 3.6. Document Your Agent

In your agent's directory, create or update `README.md`:

```markdown
# Your Agent Name

## Description
Brief description of your agent's purpose and functionality.

## Input
Describe the input your agent expects from the state.

## Output
Describe the output your agent adds to the state.

## Dependencies
List any specific dependencies or setup required for your agent.
```

### 3.7. Create Unit Tests

In `tests/test_agents/test_your_agent_name.py`:

```python
from project_echo.agents.your_agent_name import create_your_agent_node

def test_your_agent():
    node = create_your_agent_node()
    test_state = {"input_key": "test_input"}
    result = node.run(test_state)
    assert "your_output_key" in result
    # Add more specific tests
```

### 3.8. Commit Your Changes

```bash
git add .
git commit -m "Migrate YourAgentName to LangGraph node"
git push origin feature/your_agent_name_langraph
```

## 4. Orchestrator Guide: Setting Up the Multi-Agent System

### 4.1. Create the Graph Structure

In `project_echo/graph/`:

1. Create `state.py`:

```python
from pydantic import BaseModel, Field

class ChatbotState(BaseModel):
    user_input: str = Field(default="")
    # Add fields for each agent's input/output
    
    def update_state(self, key, value):
        setattr(self, key, value)
```

2. Create `nodes.py`:

```python
from project_echo.agents.agent1 import create_agent1_node
from project_echo.agents.agent2 import create_agent2_node
# Import all other agent nodes

def get_all_nodes():
    return {
        "agent1": create_agent1_node(),
        "agent2": create_agent2_node(),
        # Add all other agents
    }
```

3. Create `edges.py`:

```python
def define_edges(graph):
    graph.add_edge("user_input", "agent1")
    graph.add_edge("agent1", "agent2")
    # Define the flow between all agents
```

### 4.2. Implement the Main Workflow

In `project_echo/orchestrator/main_workflow.py`:

```python
from langgraph.graph import StateGraph
from ..graph.state import ChatbotState
from ..graph.nodes import get_all_nodes
from ..graph.edges import define_edges

def create_workflow():
    graph = StateGraph(ChatbotState)
    
    # Add all nodes
    nodes = get_all_nodes()
    for name, node in nodes.items():
        graph.add_node(name, node)
    
    # Define edges
    define_edges(graph)
    
    # Set entry point
    graph.set_entry_point("user_input")
    
    return graph.compile()
```

### 4.3. Update Main Application

Update `project_echo/main.py`:

```python
from orchestrator.main_workflow import create_workflow

def main():
    workflow = create_workflow()
    final_state = workflow.invoke({"user_input": "User query here"})
    print(final_state)

if __name__ == "__main__":
    main()
```

## 5. Integration and Testing

### 5.1. Integrate Agent Branches

As each developer completes their agent migration:

1. Review and merge their pull request into `develop`
2. Update `graph/nodes.py` to include the new agent
3. Update `graph/edges.py` to incorporate the new agent into the workflow
4. Update `graph/state.py` if the new agent requires additional state fields

### 5.2. System Integration Testing

Create integration tests in `tests/test_integration/`:

```python
from project_echo.orchestrator.main_workflow import create_workflow

def test_full_workflow():
    workflow = create_workflow()
    initial_state = {"user_input": "Test query"}
    final_state = workflow.invoke(initial_state)
    
    # Assert expected outcomes
    assert "final_response" in final_state
    # Add more specific assertions
```

## 6. Optimization and Deployment

### 6.1. Performance Optimization

- Use LangSmith for tracing and identifying bottlenecks
- Implement caching for frequently accessed data
- Consider async operations for I/O-bound tasks

### 6.2. Deployment

- Update CI/CD pipelines in Azure DevOps
- Ensure all environment variables are set correctly
- Consider containerization for consistent deployment

---

This guide provides a framework for both individual developers to migrate their agents and for you, as the orchestrator, to set up the overall multi-agent system. Adapt the steps as needed based on your specific project requirements and existing codebase structure.
