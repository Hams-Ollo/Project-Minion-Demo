# Project Minion: Multi-Agent AI Assistant

## Overview

Project Minion is an advanced multi-agent AI system designed to provide specialized assistance across various domains. It utilizes a network of AI agents (minions) to handle user queries efficiently and accurately.

## Key Components

1. **Orchestrator**: The central component that routes user queries to the appropriate specialized minion.
2. **Specialized Minions**:
   - Cat Minion: Handles all cat-related queries
   - Dog Minion: Handles all dog-related queries
   - Monkey Minion: Handles all monkey-related queries
   - Chat Minion: Handles general queries and conversations

3. **User Interface**: A Streamlit-based web interface for user interaction

## Technology Stack

- Python
- LangChain
- Groq (for AI models)
- Streamlit (for the user interface)

## Project Structure

```
Project-Minion-Demo/
├── .env
├── .gitignore
├── google_config.json
├── LICENSE
├── multi_agent_orchestrator.log
├── README.md
├── requirements.txt
├── docs/
│   ├── git-branching-strategy.md
│   ├── project-architecture-doc.md
│   ├── project-echo-langraph-integration-guide-v2.md
│   └── project_overview.md
└── src/
    ├── __init__.py
    ├── api_client.py
    ├── app.py
    ├── develop.py
    ├── main.py
    ├── multi_agent_orchestrator.log
    ├── multi_minion_orchestrator.log
    ├── config/
    │   └── __init__.py
    ├── minions/
    │   └── __init__.py
    └── orchestrator/
        └── __init__.py
```

## Main Components Explanation

1. **main.py**: The core script that sets up the multi-agent system, including:
   - Importing necessary libraries
   - Setting up logging
   - Initializing AI models for each minion
   - Defining prompt templates for each minion and the orchestrator
   - Implementing the minion orchestrator and invocation functions
   - Setting up the Streamlit user interface

2. **Minions**: Specialized AI agents (Cat, Dog, Monkey, and Chat) that handle domain-specific queries.

3. **Orchestrator**: Routes user queries to the appropriate minion based on the content of the query.

4. **User Interface**: A Streamlit-based web interface that allows users to interact with the multi-agent system, view conversation history, and access additional tools and information.

## Getting Started

1. Clone the repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Set up the necessary environment variables in the `.env` file
4. Run the application: `streamlit run src/main.py`

## Configuration

Ensure that the following environment variables are set in the `.env` file:
- `GROQ_API_KEY`: Your Groq API key for accessing the AI models

## Logging

The system uses Python's logging module to log information, warnings, and errors. Log files are generated in the project root directory:
- `multi_agent_orchestrator.log`
- `multi_minion_orchestrator.log`

## Future Improvements

1. Implement more specialized minions for broader domain coverage
2. Enhance the orchestrator's routing capabilities using more advanced NLP techniques
3. Implement a feedback mechanism for continuous improvement of minion responses
4. Expand the user interface to include more advanced features and visualizations

## Contributing

Please refer to the `git-branching-strategy.md` file in the `docs` folder for information on how to contribute to this project.

## License

This project is licensed under the terms specified in the `LICENSE` file in the project root directory.
