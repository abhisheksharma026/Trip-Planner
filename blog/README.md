# Building a Production-Grade AI Agent from Scratch

## Overview

A comprehensive series on building a production-grade AI agent from scratch using Google's Agent Development Kit (ADK). Each part builds upon the previous one, creating a complete multi-agent system.

## Phase I - MVP Travel Planner

Current implementation is a Minimum Viable Product with multi-agent architecture, session management, custom tools, web interface, and observability.

## Getting Started

Clone the repository and checkout the v1.0.0 tag:

```bash
git clone https://github.com/abhisheksharma026/trip-planner.git
cd trip-planner
git checkout v1.0.0
```

## Series Structure

| Part | Title | Focus |
|-------|---------|----------|
| 1 | [Project Setup & Architecture](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part1-setup-and-architecture.md) | System overview, project structure, and technology stack |
| 2 | [Configuration & Environment](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part2-configuration-and-environment.md) | API keys, model setup, and virtual environment |
| 3 | [Configuration Module](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part3-configuration-module.md) | Building core configuration module |
| 4 | [Session Management](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part4-session-management.md) | Conversation context and memory with Opik integration |
| 5 | [Specialized Agents](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part5-specialized-agents.md) | Flight, Hotel, Financial, Research, and Safety agents |
| 6 | [Concierge Orchestrator](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part6-concierge-orchestrator.md) | Root agent coordination with safety-first workflow |
| 7 | [Custom Tools](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part7-custom-tools.md) | Geolocation, export, and flight search tools |
| 8 | [Web Interface](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part8-web-interface.md) | FastAPI backend with HTML/CSS/JavaScript frontend |
| 9 | [Observability](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part9-observability.md) | Opik integration for tracing and debugging |
| 10 | [Running & Testing](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part10-running-and-testing.md) | End-to-end testing and deployment |

## Prerequisites

- Python 3.10 or higher
- Google API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Basic Python knowledge (functions, classes, async/await)

## Technology Stack

- Google ADK: Agent Development Kit
- Google Generative AI: Gemini 2.5 Flash
- FastAPI: Modern Python web framework
- Opik: Observability platform

## Resources

- [Google ADK Documentation](https://github.com/google/adk)
- [Google AI Documentation](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Opik Documentation](https://www.comet.com/site/products/opik/)

---

**Start with [Part 1: Project Setup & Architecture](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part1-setup-and-architecture.md)**
