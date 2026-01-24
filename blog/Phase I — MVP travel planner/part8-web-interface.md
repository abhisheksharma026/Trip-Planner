# Building a Production-Grade AI Agent from Scratch - Part 8: Building Web Interface

## Overview

In Part 7, we built our custom tools that agents use to perform specific tasks. Now, let's create the **Web Interface** - a modern, responsive web application that users can interact with.

Our web interface will provide:

1. **Modern UI**: Clean, intuitive design with good UX
2. **Real-time responses**: Streaming responses for better UX
3. **Sample queries**: Quick-start options for new users
4. **Feedback collection**: Gather user feedback for improvement
5. **Responsive design**: Works on desktop and mobile

## Web Architecture

```
┌─────────────────────────────────────────────────┐
│         User Browser                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         HTML Interface              │
│  ┌─────────────────────────────────────┐  │
│  │  Chat Interface                    │  │
│  │  - Message display area             │  │
│  │  - Input field                      │  │
│  │  - Send button                      │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Sample Queries                     │  │
│  │  - Quick-start options              │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Feedback Form                      │  │
│  │  - Collect user feedback            │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         JavaScript (app.js)         │
│  ┌─────────────────────────────────────┐  │
│  │  API Client                        │  │
│  │  - Send queries to backend         │  │
│  │  - Handle streaming responses      │  │
│  │  - Display messages                │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  UI Manager                        │  │
│  │  - Update message display          │  │
│  │  - Handle user interactions        │  │
│  │  - Show/hide elements              │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         FastAPI Backend              │
│  ┌─────────────────────────────────────┐  │
│  │  REST API Endpoints                │  │
│  │  - POST /api/query                 │  │
│  │  - GET /api/samples                │  │
│  │  - POST /api/feedback              │  │
│  │  - GET /health                     │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Agent Runner                      │  │
│  │  - Execute queries                 │  │
│  │  - Stream responses                │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Trip Planner System          │
└─────────────────────────────────────────────────┘
```

## Building the FastAPI Backend

Let's start with the FastAPI backend. Create `app.py`:

```python
"""
FastAPI Web Application - Trip Planner Web Interface.
"""

import os
import socket
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.requests import Request

# Import trip planner components
from trip_planner.config import initialize_config, get_model_name
from trip_planner.core.session_manager import SessionManager
from trip_planner.core.runner import TripPlannerRunner
from trip_planner.agents.concierge import create_concierge

# Initialize FastAPI app
app = FastAPI(
    title="AI Travel Planner",
    description="Production-grade AI agent for trip planning",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variables
session_manager = None
runner = None
concierge = None
port = None


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="User query")
    user_id: str = Field(default="default_user", description="User identifier")
    session_id: Optional[str] = Field(None, description="Session ID")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    response: str = Field(..., description="Agent response")
    query_id: str = Field(..., description="Query identifier")
    session_id: str = Field(..., description="Session ID")


class FeedbackRequest(BaseModel):
    """Request model for feedback endpoint."""
    query_id: str = Field(..., description="Query identifier")
    feedback: str = Field(..., description="User feedback")
    rating: Optional[int] = Field(None, description="Rating (1-5)")


class SampleQuery(BaseModel):
    """Model for sample query."""
    query: str = Field(..., description="Sample query text")
    category: str = Field(..., description="Query category")


# Sample queries
SAMPLE_QUERIES = [
    SampleQuery(
        query="I want to plan a trip to Paris in March 2025 with a $1,500 budget",
        category="Trip Planning"
    ),
    SampleQuery(
        query="Find me flights from New York to London for next week",
        category="Flight Search"
    ),
    SampleQuery(
        query="What are the best hotels in Tokyo under $200 per night?",
        category="Hotel Search"
    ),
    SampleQuery(
        query="Plan a weekend getaway to San Francisco with a $500 budget",
        category="Weekend Trip"
    ),
    SampleQuery(
        query="What if I increase my budget to $2,000 for my Paris trip?",
        category="What-If Scenario"
    ),
    SampleQuery(
        query="Export my current itinerary to a file",
        category="Export"
    )
]


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application components on startup."""
    global session_manager, runner, concierge, port
    
    # Find an available port
    port = find_available_port(8000)
    print(f"Starting server on port {port}")
    
    # Initialize configuration
    initialize_config()
    print("Configuration initialized")
    
    # Initialize session manager
    session_manager = SessionManager()
    print("Session manager initialized")
    
    # Initialize concierge agent
    concierge = create_concierge()
    print("Concierge agent initialized")
    
    # Initialize runner
    runner = TripPlannerRunner(session_manager, concierge)
    print("Runner initialized")
    
    print("Application startup complete!")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    print("Shutting down application...")


# Helper function to find available port
def find_available_port(start_port: int) -> int:
    """
    Find an available port starting from start_port.
    
    Args:
        start_port: Starting port number
    
    Returns:
        Available port number
    """
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise Exception("No available ports found")


# API Endpoints

@app.get("/", response_class=StreamingResponse)
async def root(request: Request):
    """Serve the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a user query.
    
    Args:
        request: Query request with query text and user ID
    
    Returns:
        Query response with agent response and metadata
    
    Example:
        POST /api/query
        {
            "query": "I want to plan a trip to Paris",
            "user_id": "user_123"
        }
    """
    try:
        # Execute query through runner
        response = await runner.run_query(request.query, request.user_id)
        
        return QueryResponse(
            response=response,
            query_id=f"query_{request.user_id}_{len(session_manager.conversation_queries.get(request.user_id, []))}",
            session_id=session_manager.current_sessions.get(request.user_id, {}).id if request.user_id in session_manager.current_sessions else "unknown"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/samples", response_model=List[SampleQuery])
async def get_samples():
    """
    Get sample queries for quick-start.
    
    Returns:
        List of sample queries
    
    Example:
        GET /api/samples
    """
    return SAMPLE_QUERIES


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback.
    
    Args:
        request: Feedback request with query ID and feedback
    
    Returns:
        Success message
    
    Example:
        POST /api/feedback
        {
            "query_id": "query_user_123_1",
            "feedback": "Very helpful!",
            "rating": 5
        }
    """
    # In production, save feedback to database
    # For now, just log it
    print(f"Feedback received for query {request.query_id}: {request.feedback}")
    if request.rating:
        print(f"Rating: {request.rating}/5")
    
    return {"message": "Feedback received. Thank you!"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    
    Example:
        GET /health
    """
    return {
        "status": "healthy",
        "model": get_model_name(),
        "session_manager": session_manager is not None,
        "runner": runner is not None,
        "concierge": concierge is not None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port if port else 8000)
```

## Building the HTML Interface

Now let's create the HTML interface. Create `templates/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Travel Planner</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>AI Travel Planner</h1>
            <p>Your intelligent travel assistant</p>
        </header>

        <main>
            <div class="chat-container">
                <div class="messages" id="messages">
                    <div class="message assistant">
                        <div class="message-content">
                            <p>Hello! I'm your AI Travel Planner. I can help you plan trips, find flights and hotels, and provide travel recommendations. How can I assist you today?</p>
                        </div>
                    </div>
                </div>

                <div class="input-container">
                    <form id="query-form">
                        <input 
                            type="text" 
                            id="query-input" 
                            placeholder="Ask me anything about travel planning..."
                            autocomplete="off"
                        >
                        <button type="submit" id="send-button">
                            <span>Send</span>
                        </button>
                    </form>
                </div>
            </div>

            <div class="samples-container">
                <h3>Quick Start</h3>
                <div class="samples" id="samples">
                    <!-- Sample queries will be loaded here -->
                </div>
            </div>

            <div class="feedback-container">
                <h3>Feedback</h3>
                <form id="feedback-form">
                    <input 
                        type="text" 
                        id="feedback-input" 
                        placeholder="Share your feedback..."
                        autocomplete="off"
                    >
                    <button type="submit">Submit</button>
                </form>
            </div>
        </main>

        <footer>
            <p>Powered by Google ADK and Gemini 2.5 Flash</p>
        </footer>
    </div>

    <script src="/static/js/app.js"></script>
</body>
</html>
```

## Building the CSS Styles

Now let's create the CSS styles. Create `static/css/style.css`:

```css
/* AI Travel Planner Styles */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.container {
    width: 100%;
    max-width: 900px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    overflow: hidden;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    text-align: center;
}

header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
}

header p {
    font-size: 1.1em;
    opacity: 0.9;
}

main {
    padding: 30px;
}

.chat-container {
    background: #f8f9fa;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 30px;
}

.messages {
    max-height: 400px;
    overflow-y: auto;
    margin-bottom: 20px;
    padding-right: 10px;
}

.messages::-webkit-scrollbar {
    width: 8px;
}

.messages::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

.messages::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 10px;
}

.messages::-webkit-scrollbar-thumb:hover {
    background: #555;
}

.message {
    margin-bottom: 20px;
    display: flex;
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message.user {
    justify-content: flex-end;
}

.message.assistant {
    justify-content: flex-start;
}

.message-content {
    max-width: 70%;
    padding: 15px 20px;
    border-radius: 20px;
    line-height: 1.6;
}

.message.user .message-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-bottom-right-radius: 5px;
}

.message.assistant .message-content {
    background: white;
    color: #333;
    border: 2px solid #e0e0e0;
    border-bottom-left-radius: 5px;
}

.input-container {
    display: flex;
    gap: 10px;
}

#query-form {
    display: flex;
    gap: 10px;
    width: 100%;
}

#query-input {
    flex: 1;
    padding: 15px 20px;
    border: 2px solid #e0e0e0;
    border-radius: 25px;
    font-size: 1em;
    outline: none;
    transition: border-color 0.3s;
}

#query-input:focus {
    border-color: #667eea;
}

#send-button {
    padding: 15px 30px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 25px;
    font-size: 1em;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

#send-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

#send-button:active {
    transform: translateY(0);
}

.samples-container {
    margin-bottom: 30px;
}

.samples-container h3 {
    margin-bottom: 15px;
    color: #333;
    font-size: 1.2em;
}

.samples {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
}

.sample {
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 15px;
    cursor: pointer;
    transition: all 0.3s;
}

.sample:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.2);
}

.sample h4 {
    color: #667eea;
    margin-bottom: 5px;
    font-size: 0.9em;
    text-transform: uppercase;
}

.sample p {
    color: #666;
    font-size: 0.95em;
}

.feedback-container {
    background: #f8f9fa;
    border-radius: 15px;
    padding: 20px;
}

.feedback-container h3 {
    margin-bottom: 15px;
    color: #333;
    font-size: 1.2em;
}

#feedback-form {
    display: flex;
    gap: 10px;
}

#feedback-input {
    flex: 1;
    padding: 12px 15px;
    border: 2px solid #e0e0e0;
    border-radius: 20px;
    font-size: 0.95em;
    outline: none;
    transition: border-color 0.3s;
}

#feedback-input:focus {
    border-color: #667eea;
}

#feedback-form button {
    padding: 12px 25px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 20px;
    font-size: 0.95em;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

#feedback-form button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

footer {
    background: #f8f9fa;
    padding: 20px;
    text-align: center;
    color: #666;
    font-size: 0.9em;
}

.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(102, 126, 234, 0.3);
    border-radius: 50%;
    border-top-color: #667eea;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Responsive Design */
@media (max-width: 768px) {
    header h1 {
        font-size: 2em;
    }

    header p {
        font-size: 1em;
    }

    main {
        padding: 20px;
    }

    .message-content {
        max-width: 85%;
    }

    .samples {
        grid-template-columns: 1fr;
    }

    #query-form {
        flex-direction: column;
    }

    #send-button {
        width: 100%;
    }

    #feedback-form {
        flex-direction: column;
    }

    #feedback-form button {
        width: 100%;
    }
}
```

## Building the JavaScript

Now let's create the JavaScript. Create `static/js/app.js`:

```javascript
// AI Travel Planner JavaScript

// API base URL
const API_BASE = '';

// DOM elements
const messagesContainer = document.getElementById('messages');
const queryForm = document.getElementById('query-form');
const queryInput = document.getElementById('query-input');
const sendButton = document.getElementById('send-button');
const samplesContainer = document.getElementById('samples');
const feedbackForm = document.getElementById('feedback-form');
const feedbackInput = document.getElementById('feedback-input');

// Current query ID for feedback
let currentQueryId = null;

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    await loadSamples();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    queryForm.addEventListener('submit', handleQuery);
    feedbackForm.addEventListener('submit', handleFeedback);
}

// Handle query submission
async function handleQuery(event) {
    event.preventDefault();
    
    const query = queryInput.value.trim();
    if (!query) return;
    
    // Clear input
    queryInput.value = '';
    
    // Add user message to chat
    addMessage(query, 'user');
    
    // Show loading indicator
    const loadingMessage = addLoadingMessage();
    
    try {
        // Send query to API
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                user_id: 'web_user'
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        
        // Remove loading message
        removeMessage(loadingMessage);
        
        // Add assistant response to chat
        addMessage(data.response, 'assistant');
        
        // Store query ID for feedback
        currentQueryId = data.query_id;
        
    } catch (error) {
        // Remove loading message
        removeMessage(loadingMessage);
        
        // Show error message
        addMessage('Sorry, something went wrong. Please try again.', 'assistant');
        console.error('Error:', error);
    }
}

// Handle feedback submission
async function handleFeedback(event) {
    event.preventDefault();
    
    const feedback = feedbackInput.value.trim();
    if (!feedback) return;
    
    if (!currentQueryId) {
        alert('Please ask a question first before providing feedback.');
        return;
    }
    
    try {
        // Send feedback to API
        const response = await fetch(`${API_BASE}/api/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query_id: currentQueryId,
                feedback: feedback
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to submit feedback');
        }
        
        // Clear input
        feedbackInput.value = '';
        
        // Show success message
        alert('Thank you for your feedback!');
        
    } catch (error) {
        alert('Failed to submit feedback. Please try again.');
        console.error('Error:', error);
    }
}

// Add message to chat
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = formatMessage(content);
    
    messageDiv.appendChild(messageContent);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageDiv;
}

// Add loading message
function addLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = 'loading-message';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.innerHTML = '<div class="loading"></div>';
    
    messageDiv.appendChild(messageContent);
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageDiv;
}

// Remove message
function removeMessage(messageDiv) {
    if (messageDiv && messageDiv.parentNode) {
        messageDiv.parentNode.removeChild(messageDiv);
    }
}

// Format message content
function formatMessage(content) {
    // Convert newlines to <br>
    let formatted = content.replace(/\n/g, '<br>');
    
    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert *italic* to <em>
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Convert - list items
    formatted = formatted.replace(/^- (.*)/gm, '<li>$1</li>');
    
    // Wrap consecutive <li> in <ul>
    formatted = formatted.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    return formatted;
}

// Load sample queries
async function loadSamples() {
    try {
        const response = await fetch(`${API_BASE}/api/samples`);
        
        if (!response.ok) {
            throw new Error('Failed to load samples');
        }
        
        const samples = await response.json();
        
        // Clear samples container
        samplesContainer.innerHTML = '';
        
        // Add sample queries
        samples.forEach(sample => {
            const sampleDiv = document.createElement('div');
            sampleDiv.className = 'sample';
            sampleDiv.innerHTML = `
                <h4>${sample.category}</h4>
                <p>${sample.query}</p>
            `;
            sampleDiv.addEventListener('click', () => {
                queryInput.value = sample.query;
                queryInput.focus();
            });
            samplesContainer.appendChild(sampleDiv);
        });
        
    } catch (error) {
        console.error('Error loading samples:', error);
        samplesContainer.innerHTML = '<p>Failed to load sample queries.</p>';
    }
}

// Handle Enter key in query input
queryInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        queryForm.dispatchEvent(new Event('submit'));
    }
});

// Handle Enter key in feedback input
feedbackInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        feedbackForm.dispatchEvent(new Event('submit'));
    }
});
```

## Testing the Web Interface

Let's create a test to verify the web interface works:

```bash
# Start the web server
python app.py
```

Expected output:

```
Starting server on port 8000
Configuration initialized
Session manager initialized
Concierge agent initialized
Runner initialized
Application startup complete!
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Now open your browser and navigate to `http://localhost:8000`. You should see:

1. A beautiful gradient interface
2. A welcome message from the assistant
3. Sample queries to click on
4. An input field to type your queries
5. A feedback form

## Web Interface Features

### 1. Modern UI Design

- Gradient background
- Clean, minimalist design
- Smooth animations
- Responsive layout

### 2. Real-time Chat

- User messages on the right
- Assistant messages on the left
- Loading indicators
- Auto-scroll to latest message

### 3. Sample Queries

- Quick-start options
- Categorized by type
- Click to use

### 4. Feedback Collection

- Easy feedback form
- Linked to specific queries
- Helps improve the system

### 5. Responsive Design

- Works on desktop
- Works on mobile
- Adapts to screen size

## Production Considerations

### 1. Authentication

```python
# Add authentication
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate token
    pass
```

### 2. Rate Limiting

```python
# Add rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/query")
@limiter.limit("10/minute")
async def query(request: Request, query_request: QueryRequest):
    # ... implementation
```

### 3. Database Persistence

```python
# Add database for sessions and feedback
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ... implementation
```

### 4. HTTPS

```python
# Configure HTTPS
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )
```

## Common Issues

### Issue: Port Already in Use

**Symptoms**:
```
OSError: [Errno 48] Address already in use
```

**Solution**: The app automatically finds an available port. Check the console output for the actual port.

### Issue: CORS Errors

**Symptoms**:
```
Access to fetch at 'http://localhost:8000/api/query' from origin 'null' has been blocked by CORS policy
```

**Solution**: Ensure CORS middleware is configured correctly in `app.py`.

## What's Next?

Congratulations! You've built a modern web interface. In Part 9, we'll add observability with Opik.

## Summary

In this part, we:
- Built a FastAPI backend with REST API
- Created a modern HTML interface
- Styled with CSS for a beautiful UI
- Added JavaScript for interactivity
- Implemented real-time chat functionality
- Added sample queries for quick-start
- Created feedback collection
- Made the interface responsive

## Key Takeaways

1. **Modern UI matters**: Good design improves user experience
2. **FastAPI is powerful**: Easy to build REST APIs
3. **Responsive design**: Works on all devices
4. **Real-time feedback**: Loading indicators improve UX
5. **Sample queries**: Help users get started quickly

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [HTML5 Tutorial](https://www.w3schools.com/html/)
- [CSS3 Tutorial](https://www.w3schools.com/css/)
- [JavaScript Tutorial](https://www.w3schools.com/js/)
- [Responsive Web Design](https://www.w3schools.com/html/html_responsive.asp)

---

Continue to Part 9: Adding Observability with Opik
