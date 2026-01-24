# AI Trip Planner Agent

A modular multi-agent system for intelligent trip planning built with Google ADK (Agent Development Kit).

## Architecture

```
                    ┌─────────────────────────┐
                    │   Concierge (Root)      │
                    │   - Greets user         │
                    │   - Delegates tasks     │
                    │   - Coordinates flow    │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Flight          │ │ Hotel        │ │ Financial    │
    │ Recommender     │ │ Specialist   │ │ Planner      │
    └─────────────────┘ └──────────────┘ └──────────────┘
```

## Project Structure

```
Trip Planner/
├── trip_planner/              # Main package
│   ├── __init__.py
│   ├── config.py              # Configuration and API setup
│   ├── agents/                # Agent modules
│   │   ├── __init__.py
│   │   ├── concierge.py       # Root orchestrator
│   │   ├── flight_recommender.py
│   │   ├── hotel_specialist.py
│   │   └── financial_planner.py
│   ├── tools/                 # Custom tools
│   │   ├── __init__.py
│   │   ├── geolocation.py     # City to coordinates
│   │   └── export.py          # Itinerary export
│   └── core/                  # Core functionality
│       ├── __init__.py
│       ├── session_manager.py  # Session handling
│       └── runner.py          # Query execution
├── app.py                     # Flask web application
├── main.py                    # CLI application entry point
├── templates/                 # HTML templates
│   └── index.html            # Web app frontend
├── static/                    # Static assets
│   ├── css/
│   │   └── style.css         # Stylesheet
│   └── js/
│       └── app.js            # Frontend JavaScript
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Features

- **Multi-Agent System**: Specialized agents for flights, hotels, and finances
- **Custom Tools**: Geolocation and export capabilities
- **Conversational Memory**: Session-based context retention
- **Budget Management**: Financial analysis and cost tracking
- **Real-time Search**: Google Search integration for live prices
- **Modular Design**: Clean separation of responsibilities

## Prerequisites

- **Python 3.10 or higher** (required for MCP/ADK dependencies)
- Bash shell (macOS/Linux) or Command Prompt/PowerShell (Windows)

## Quick Start

### Automated Setup (Recommended)

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Set your API key:**
   
   **Option 1: Create a `.env` file (Recommended):**
   ```bash
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```
   
   **Option 2: Set environment variable:**
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```
   
   Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey)

3. **Run the application:**
   ```bash
   ./run.sh          # Web app (default)
   ./run.sh web      # Web app explicitly
   ./run.sh cli       # CLI application
   ```

See [SETUP.md](SETUP.md) for detailed instructions.

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install google-adk google-generativeai flask flask-cors
```

### 2. Get API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Generate an API key
3. Set it as an environment variable:

**Mac/Linux:**
```bash
export GOOGLE_API_KEY=your_api_key_here
```

**Windows:**
```bash
setx GOOGLE_API_KEY "your_api_key_here"
```

Or the application will prompt you to enter it when you run it.

### 3. Run the Application

**Web Application (Recommended):**
```bash
python app.py
```
Then open http://localhost:5000 in your browser.

**CLI Application:**
```bash
# Interactive Mode
python main.py

# Single Query Mode
python main.py "I want to plan a trip to Paris next month"
```

## Web Application

The project includes a modern web interface for easy interaction.

### Running the Web App

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Flask server**:
   ```bash
   python app.py
   ```

3. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

### Web App Features

- **Interactive Chat Interface**: Real-time conversation with the AI agent
- **Sample Queries**: Click on sample queries to see expected formats
- **Session Management**: Start new sessions to clear conversation history
- **Modern UI**: Beautiful, responsive design that works on all devices

### Sample Queries in the Web App

The web interface includes 5 sample queries demonstrating:

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
- Model configuration
- Environment setup

### `trip_planner/agents/`
- **concierge.py**: Root orchestrator that coordinates all agents
- **flight_recommender.py**: Specialized flight search agent
- **hotel_specialist.py**: Specialized hotel search agent
- **financial_planner.py**: Budget analysis agent

### `trip_planner/tools/`
- **geolocation.py**: City name to coordinates conversion
- **export.py**: Itinerary export to markdown files

### `trip_planner/core/`
- **session_manager.py**: Manages conversation sessions and memory
- **runner.py**: Executes queries and handles agent interactions

## Production Enhancements

To make this production-ready, consider:

1. **Real API Integrations**:
   - Replace mock geolocation with Google Maps Geocoding API
   - Integrate Google Docs/Sheets API for export
   - Add flight/hotel booking APIs (Amadeus, Booking.com)

2. **Persistence**:
   - Replace InMemorySessionService with database-backed sessions
   - Add user authentication
   - Store trip history

3. **Additional Features**:
   - Activity/attraction recommendations
   - Weather integration
   - Travel document reminders
   - Multi-user support

4. **Web Interface**:
   - Use ADK's web UI: `adk run --agent trip_planner_concierge`
   - Or build a custom web interface

## Testing

The application includes built-in testing capabilities. You can test various scenarios:

1. **Complete trip planning flow**: Full end-to-end planning
2. **Vague requests**: Agent asks clarifying questions
3. **Memory**: Agent remembers preferences across conversation
4. **Export**: Itinerary export functionality

## License

This project is for educational purposes.

## Support

For issues or questions, refer to:
- [Google ADK Documentation](https://github.com/google/adk)
- [Google AI Studio](https://aistudio.google.com/)

---

**Happy Trip Planning!**

