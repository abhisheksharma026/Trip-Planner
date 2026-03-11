# AI Trip Planner Agent

A modular multi-agent system for intelligent trip planning built with Google ADK (Agent Development Kit).

## Architecture

```
Client (Web/CLI)
      │
      ▼
FastAPI App (`app.py`)
  ├─ Middleware: request-id, security headers, content-type, request logging
  ├─ Auth + Session cookies (secure-by-default, localhost-only override)
  ├─ Rate limits: per-IP (SlowAPI), global daily, anonymous/user daily quotas
  ├─ Admin debug endpoint (`/api/admin/debug/redis`) metadata-only
  │
  ▼
TripPlannerRunner + SessionManager
  ├─ ADK InMemorySessionService runtime
  ├─ Optional Redis snapshot persistence for conversation memory
  └─ Opik traces/spans (optional)
  │
  ▼
Concierge Agent (root orchestrator)
  ├─ Flight Recommender
  ├─ Hotel Specialist
  ├─ Financial Planner
  └─ Tools: geolocation, Amadeus flights, itinerary export

Persistence/Infra
  ├─ SQLite: users/auth records
  ├─ Redis (optional): rate limits + session-memory snapshots
  └─ Structured logging with request correlation
```

## Project Structure

```
Trip Planner/
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI lint + tests
├── trip_planner/              # Main package
│   ├── __init__.py
│   ├── config.py              # Centralized application config
│   ├── logging_utils.py       # Structured logging + request-id context
│   ├── agents/                # Agent modules
│   │   ├── __init__.py
│   │   ├── concierge.py       # Root orchestrator
│   │   ├── flight_recommender.py
│   │   ├── hotel_specialist.py
│   │   └── financial_planner.py
│   ├── middleware/            # HTTP middleware
│   │   ├── request_id.py
│   │   ├── request_logging.py
│   │   ├── security_headers.py
│   │   └── content_type.py
│   ├── tools/                 # Custom tools
│   │   ├── __init__.py
│   │   ├── geolocation.py     # City to coordinates
│   │   ├── amadeus_flights.py # Real flight search
│   │   └── export.py          # Itinerary export
│   └── core/                  # Core functionality
│       ├── __init__.py
│       ├── session_manager.py  # Session handling
│       ├── runner.py          # Query execution
│       ├── rate_limiter.py    # Rate limiting
│       ├── auth.py            # User authentication
│       ├── redis_client.py    # Shared Redis client helper
│       └── redis_debug.py     # Safe Redis metadata inspector
├── app.py                     # FastAPI web application
├── main.py                    # CLI application entry point
├── tests/                     # Security/unit/integration tests
├── templates/                 # HTML templates
│   └── index.html            # Web app frontend
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css         # Stylesheet
│   └── js/
│       └── app.js            # Frontend JavaScript
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose
├── Makefile                   # Development commands
├── render.yaml                # Render deployment
├── requirements.txt           # Dependencies
├── blog/                      # Build log / implementation walkthrough
└── README.md                  # This file
```

## Features

- **Multi-Agent System**: Specialized agents for flights, hotels, and finances
- **Custom Tools**: Geolocation, real flight search (Amadeus), and export capabilities
- **Conversational Memory**: Session-based context retention
- **Redis Session Snapshots (Optional)**: Persist and restore conversation memory across app restarts
- **Budget Management**: Financial analysis and cost tracking
- **Real-time Search**: Google Search integration for live prices
- **Request-Correlated Logging**: Structured logs with request ID propagation
- **Modular Design**: Clean separation of responsibilities
- **Production Hardening**: Secure cookies, email validation, CI checks, branch protection

## Production Features

### Rate Limiting
- **Global limit**: 200 API calls/day (configurable)
- **Per-IP limit**: 100 calls/hour, 20 calls/minute
- **Anonymous users**: 5 free queries before login required
- **Authenticated users**: 50 calls/day per user

### User Authentication
- Email/password registration
- Email validation + canonical normalization
- Secure password hashing (PBKDF2-SHA256)
- SQLite database for persistence
- Session-based authentication with secure-by-default cookies

### Redis-Backed Services (Optional)
- Distributed counters for rate limiting across app instances
- Conversation-memory snapshot persistence with TTL
- Admin-only metadata debug endpoint: `GET /api/admin/debug/redis`

### CI and Merge Controls
- GitHub Actions workflow for lint + tests
- Required status checks on `main`
- Minimum 1 approving PR review
- `enforce_admins=true` enabled

### Docker Support
- Containerized deployment
- Persistent volume for database
- Health checks
- Docker Compose for local development

## Prerequisites

- **Python 3.10 or higher** (required for MCP/ADK dependencies)
- **uv** (recommended) or pip for package management
- **Docker** (optional, for containerized deployment)

## Quick Start

### Option 1: Using uv (Recommended - Faster)

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver.

1. **Install uv:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd "Trip Planner"
   
   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. **Set your API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```
   
   Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey)

4. **Run the application:**
   ```bash
   uv run python app.py     # Web app
   uv run python main.py    # CLI app
   ```

### Option 2: Using pip

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Set your API key:**
   
   **Option A: Create a `.env` file (Recommended):**
   ```bash
   cp .env.example .env
   # Edit .env and add your GOOGLE_API_KEY
   ```
   
   **Option B: Set environment variable:**
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```
   
   Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey)

3. **Run the application:**
   ```bash
   ./run.sh          # Web app (default)
   ./run.sh web      # Web app explicitly
   ./run.sh cli      # CLI application
   ```

See [SETUP.md](SETUP.md) for detailed instructions.

### Option 3: Using Docker

1. **Start Docker Desktop**

2. **Build and run:**
   ```bash
   make run-docker
   # or
   docker compose up --build
   ```

3. **Open your browser:**
   ```
   http://localhost:5000
   ```

### Option 4: Using Makefile

```bash
make help          # Show all available commands
make install       # Install dependencies
make run           # Run on port 5000
make run-dev       # Run with auto-reload on port 8000
make run-docker    # Run in Docker
```

## Web Application

The project includes a modern web interface for easy interaction.

### Running the Web App

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   python -m uvicorn app:app --host 0.0.0.0 --port 5000
   ```

3. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Web App Features

- **Interactive Chat Interface**: Real-time conversation with the AI agent
- **Sample Queries**: Click on sample queries to see expected formats
- **Session Management**: Start new sessions to clear conversation history
- **User Authentication**: Register/login for extended usage
- **Rate Limit Feedback**: Visual warnings when approaching limits
- **Modern UI**: Beautiful, responsive design that works on all devices

### Admin Redis Debug Endpoint

For operational debugging, the API exposes:

- `GET /api/admin/debug/redis`

Access rules:

- endpoint must be enabled in config (`ADMIN_DEBUG_ENABLED=True`)
- caller must be authenticated
- caller must be allowlisted (`ADMIN_DEBUG_ALLOWED_EMAILS` or `ADMIN_DEBUG_ALLOWED_USER_IDS`)

Response is metadata-only (counts, TTLs, key summaries). It does not expose full session event payloads.

### Sample Queries in the Web App

The web interface includes sample queries demonstrating:

1. **Complete Trip Planning**: Full end-to-end trip planning with all details
2. **Vague Request**: How the agent handles incomplete information
3. **Hotel Search**: Specific hotel search with preferences
4. **Flight Search**: Flight search with budget and preferences
5. **Budget Analysis**: Financial planning and cost breakdown

## Usage Examples

### Example 1: Complete Trip Planning

```
You: Hi! I want to plan a trip to Paris, France. I'm traveling from San Francisco on March 15, 2025 and returning on March 22, 2025. My budget is $3000 total. I prefer direct flights and hate long layovers.

[Agent finds flights, hotels, and analyzes budget]

You: Great! Now can you find me some hotel options? I'd like to stay in a central location, preferably near the Eiffel Tower area. Budget is around $150 per night.

[Agent finds hotels]

You: Perfect! Can you analyze the total costs and make sure everything fits within my $3000 budget?

[Agent provides financial analysis]
```

### Example 2: Vague Request

```
You: I want to go somewhere warm next week.

[Agent asks clarifying questions about budget, duration, preferences]
```

### Example 3: Memory Test

```
You: I want to plan a trip to Tokyo. I really hate long layovers, so please find direct flights if possible.

[Agent finds flights without long layovers]

You: Can you also check flights for my return trip?

[Agent remembers the "no long layovers" preference]
```

## Commands

- Type your query normally to interact with the agent
- Type `new` to start a fresh session (clears memory)
- Type `quit` or `exit` to end the session

## Module Responsibilities

### `trip_planner/config.py`
- API key configuration
- model selection + observability setup
- session cookie/rate-limit/session-memory/admin-debug settings

### `trip_planner/agents/`
- **concierge.py**: Root orchestrator that coordinates all agents
- **flight_recommender.py**: Specialized flight search agent
- **hotel_specialist.py**: Specialized hotel search agent
- **financial_planner.py**: Budget analysis agent

### `trip_planner/tools/`
- **geolocation.py**: City name to coordinates conversion
- **amadeus_flights.py**: Real flight search via Amadeus API
- **export.py**: Itinerary export to markdown files

### `trip_planner/core/`
- **session_manager.py**: Manages conversation sessions and memory
- **runner.py**: Executes queries and handles agent interactions
- **rate_limiter.py**: Multi-level rate limiting (Redis-backed with fallback)
- **auth.py**: User authentication, session middleware, per-user quotas
- **redis_client.py**: Shared Redis connectivity helper
- **redis_debug.py**: Safe metadata extraction for admin Redis debug endpoint

### `trip_planner/middleware/`
- **request_id.py**: request correlation ID propagation
- **request_logging.py**: structured request completion/error logs
- **security_headers.py**: HTTP hardening headers
- **content_type.py**: request content-type validation

### `trip_planner/logging_utils.py`
- centralized logging setup
- request ID context injection across logs

## Deployment

### Deploy to Render (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up (free tier available)

3. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will detect `render.yaml`

4. **Set Environment Variables**
   - In Render dashboard, set `GOOGLE_API_KEY`

5. **Deploy**
   - Click "Create Web Service"
   - Get your public URL!

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `SECRET_KEY` | Session secret | Auto-generated |
| `DAILY_API_LIMIT` | Global daily limit | 200 |
| `ANONYMOUS_FREE_LIMIT` | Free queries for anonymous | 5 |
| `DATABASE_PATH` | SQLite database path | data/trip_planner.db |
| `RATE_LIMIT_BACKEND` | `memory` or `redis` backend | `memory` |
| `RATE_LIMIT_REDIS_URL` | Redis URL for rate-limits | `redis://localhost:6379/0` |
| `SESSION_MEMORY_BACKEND` | `memory` or `redis` for conversation snapshots | `memory` |
| `SESSION_MEMORY_REDIS_URL` | Redis URL for session-memory snapshots | `redis://localhost:6379/0` |

Most operational toggles are now config-first in `trip_planner/config.py` for MVP simplicity.

## Testing

The application includes built-in testing capabilities. You can test various scenarios:

1. **Complete trip planning flow**: Full end-to-end planning
2. **Vague requests**: Agent asks clarifying questions
3. **Memory**: Agent remembers preferences across conversation
4. **Export**: Itinerary export functionality
5. **Rate limiting**: Test with multiple requests
6. **Authentication**: Register, login, logout flows

## Blog Series

This project is documented in a blog series:

### Phase I - MVP Travel Planner
- [Part 1: Setup and Architecture](blog/Phase%20I%20—%20MVP%20travel%20planner/part1-setup-and-architecture.md)
- [Part 2: Configuration and Environment](blog/Phase%20I%20—%20MVP%20travel%20planner/part2-configuration-and-environment.md)
- [Part 3: Configuration Module](blog/Phase%20I%20—%20MVP%20travel%20planner/part3-configuration-module.md)
- [Part 4: Session Management](blog/Phase%20I%20—%20MVP%20travel%20planner/part4-session-management.md)
- [Part 5: Specialized Agents](blog/Phase%20I%20—%20MVP%20travel%20planner/part5-specialized-agents.md)
- [Part 6: Concierge Orchestrator](blog/Phase%20I%20—%20MVP%20travel%20planner/part6-concierge-orchestrator.md)
- [Part 7: Custom Tools](blog/Phase%20I%20—%20MVP%20travel%20planner/part7-custom-tools.md)
- [Part 8: Web Interface](blog/Phase%20I%20—%20MVP%20travel%20planner/part8-web-interface.md)
- [Part 9: Observability](blog/Phase%20I%20—%20MVP%20travel%20planner/part9-observability.md)
- [Part 10: Running and Testing](blog/Phase%20I%20—%20MVP%20travel%20planner/part10-running-and-testing.md)

### Phase II - Production Ready
- [Part 1: Rate Limiting](blog/Phase%20II%20—%20Production%20Ready/part1-rate-limiting.md)
- [Part 2: Authentication](blog/Phase%20II%20—%20Production%20Ready/part2-authentication.md)
- [Part 3: Docker and Deployment](blog/Phase%20II%20—%20Production%20Ready/part3-docker-and-deployment.md)

### Phase III - CI and Hardening
- [Part 1: HTTPS-Only Cookies](blog/Phase%20III%20—%20CI/part1-https-only-cookies.md)
- [Part 2: Email Validation](blog/Phase%20III%20—%20CI/part2-email-validation.md)
- [Part 3: CI and Branch Protection](blog/Phase%20III%20—%20CI/part3-ci-and-branch-protection.md)
- [Part 4: Logging Standardization](blog/Phase%20III%20—%20CI/part4-logging-standardization.md)
- [Part 5: Redis-Backed Rate Limiting](blog/Phase%20III%20—%20CI/part5-redis-backed-rate-limiting.md)
- [Part 6: Redis-Backed Session Memory](blog/Phase%20III%20—%20CI/part6-redis-backed-session-memory.md)

## License

This project is for educational purposes.

## Support

For issues or questions, refer to:
- [Google ADK Documentation](https://github.com/google/adk)
- [Google AI Studio](https://aistudio.google.com/)

---

**Happy Trip Planning!**
