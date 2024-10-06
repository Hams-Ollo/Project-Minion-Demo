# Project Echo

## Overview

Project Echo is a sophisticated multi-agent AI system designed to assist field personnel in various aspects of their work, from customer interactions to product support. The system leverages LangGraph for creating a flexible and powerful multi-agent architecture.

## Table of Contents

1. [Features](#features)
2. [System Architecture](#system-architecture)
3. [Agents](#agents)
4. [Getting Started](#getting-started)
5. [Development](#development)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Contributing](#contributing)
9. [License](#license)

## Features

- Multi-agent system for comprehensive field support
- Natural language processing for user interactions
- Integrated scheduling and task management
- Product information and support
- Customer relationship management
- Onboarding assistance for new team members
- LangGraph-based architecture for flexible agent interactions

## System Architecture

Project Echo is built on a LangGraph framework, allowing for dynamic interactions between multiple specialized agents. The system uses a state-based approach to manage information flow and decision-making processes.

Key components:
- LangGraph for agent orchestration
- LangChain for natural language processing
- Vector databases for efficient information retrieval
- Azure DevOps for CI/CD and project management

## Agents

1. **Product Chatbot**: Handles product-related inquiries
2. **Scheduling Assistant**: Manages scheduling and time-related tasks
3. **Customer Agent**: Provides customer history and sentiment analysis
4. **Sales Agent**: Offers cross-sell/up-sell opportunities
5. **Onboarding Assistant**: Helps new team members with the onboarding process

## Getting Started

### Prerequisites

- Python 3.8+
- Azure DevOps account
- OpenAI API key

### Installation

1. Clone the repository:
   ```
   git clone https://dev.azure.com/your-org/project-echo.git
   cd project-echo
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

## Development

We use a Git Flow-inspired branching strategy:

- `main`: Production-ready code
- `develop`: Main development branch
- `feature/*`: For new features or agents
- `bugfix/*`: For bug fixes
- `release/*`: For release candidates

To start working on a new feature:

```
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

## Testing

Run the test suite:

```
pytest
```

For integration tests:

```
pytest tests/integration
```

## Deployment

Deployment is managed through Azure DevOps pipelines. See `azure-pipelines.yml` for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
