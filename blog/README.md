# Building a Production-Grade AI Agent from Scratch

## Overview

This blog documents the Trip Planner codebase as it evolved from a local MVP to a production-minded system.

The goal is practical: show what changed, why it changed, and what tradeoffs were made at each phase.

## Phase I - MVP Travel Planner

Phase I covers the first working version: multi-agent orchestration, session handling, tools, web UI, and observability.

## Phase II - Production Ready

Phase II adds the first operational safeguards: rate limiting, authentication, and containerized deployment.

## Phase III - CI and Hardening

Phase III focuses on safer defaults and merge-time quality gates: cookie hardening, email validation, CI checks, branch protection, logging cleanup, and Redis-backed services.

## Getting Started

Clone the repository and checkout the `v1.0.0` tag:

```bash
git clone https://github.com/abhisheksharma026/trip-planner.git
cd trip-planner
git checkout v1.0.0
```

## Series Structure

### Phase I - MVP Travel Planner

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

### Phase II - Production Ready

| Part | Title | Focus |
|-------|---------|----------|
| 1 | [Rate Limiting](./Phase%20II%20%E2%80%94%20Production%20Ready/part1-rate-limiting.md) | Global, per-IP, and endpoint protection for API budget and abuse prevention |
| 2 | [User Authentication](./Phase%20II%20%E2%80%94%20Production%20Ready/part2-authentication.md) | Email/password auth and session-based user identity |
| 3 | [Docker and Deployment](./Phase%20II%20%E2%80%94%20Production%20Ready/part3-docker-and-deployment.md) | Docker, Makefile workflows, and deployment setup |

### Phase III - CI and Hardening

| Part | Title | Focus |
|-------|---------|----------|
| 1 | [HTTPS-Only Cookies](./Phase%20III%20%E2%80%94%20CI/part1-https-only-cookies.md) | Secure-by-default session cookies with localhost-only override |
| 2 | [Email Validation](./Phase%20III%20%E2%80%94%20CI/part2-email-validation.md) | Defense-in-depth validation and canonical email normalization |
| 3 | [CI and Branch Protection](./Phase%20III%20%E2%80%94%20CI/part3-ci-and-branch-protection.md) | Automated lint/tests and protected merge policy on main |
| 4 | [Logging Standardization](./Phase%20III%20%E2%80%94%20CI/part4-logging-standardization.md) | Request-correlated, structured logs across middleware and core modules |
| 5 | [Redis-Backed Rate Limiting](./Phase%20III%20%E2%80%94%20CI/part5-redis-backed-rate-limiting.md) | Distributed-ready rate limits with fallback and enforced per-user quotas |
| 6 | [Redis-Backed Session Memory](./Phase%20III%20%E2%80%94%20CI/part6-redis-backed-session-memory.md) | Persist and restore conversation memory snapshots across restarts |

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

Start with [Part 1: Project Setup & Architecture](./Phase%20I%20%E2%80%94%20MVP%20travel%20planner/part1-setup-and-architecture.md)
