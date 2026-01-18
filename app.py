"""
FastAPI web application for the AI Trip Planner.
"""

import os
import sys
import socket
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from trip_planner.config import setup_api_key, setup_opik
from trip_planner.core.session_manager import SessionManager
from trip_planner.core.runner import TripPlannerRunner

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global components
session_manager: Optional[SessionManager] = None
runner: Optional[TripPlannerRunner] = None


def initialize_components() -> bool:
    """Initialize the trip planner components."""
    global session_manager, runner

    try:
        setup_api_key()
        setup_opik()

        session_manager = SessionManager()
        runner = TripPlannerRunner(session_manager)

        print("Trip Planner initialized successfully!")
        return True
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    if not initialize_components():
        print("Warning: Trip Planner failed to initialize")
    yield
    # Shutdown
    print("Shutting down Trip Planner...")


# Create FastAPI app with lifespan
app = FastAPI(
    title="AI Trip Planner",
    description="AI-powered multi-agent trip planning assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Setup templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# Pydantic models for request/response validation
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User's travel query")
    user_id: str = Field(default="web_user", description="User identifier")
    new_session: bool = Field(default=False, description="Create a new session")


class QueryResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    session_id: Optional[str] = None
    error: Optional[str] = None


class FeedbackRequest(BaseModel):
    user_id: str = Field(default="unknown", description="User identifier")
    session_id: str = Field(default="unknown", description="Session identifier")
    feedback: str = Field(default="unknown", description="User feedback")


class FeedbackResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    initialized: bool


class SampleQuery(BaseModel):
    title: str
    query: str
    description: str


class SamplesResponse(BaseModel):
    success: bool
    samples: list[SampleQuery]


# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """Handle user queries."""
    if not runner:
        raise HTTPException(status_code=503, detail="Trip planner not initialized")

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        response, session = await runner.run_query(
            query=query,
            user_id=request.user_id,
            create_new_session=request.new_session
        )

        # Ensure response is a string
        if response is None:
            response = "I received your message but couldn't generate a response. Please try again."
        elif not isinstance(response, str):
            response = str(response)

        return QueryResponse(
            success=True,
            response=response,
            session_id=session.id if session else None
        )

    except Exception as e:
        return QueryResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/samples", response_model=SamplesResponse)
async def get_sample_queries():
    """Get sample queries for the user."""
    samples = [
        SampleQuery(
            title="Complete Trip Planning",
            query="Hi! I want to plan a trip to Paris, France. I'm traveling from San Francisco on June 15, 2026 and returning on June 22, 2026. My budget is $3000 total. I prefer direct flights and hate long layovers.",
            description="Plan a complete trip with flights, hotels, and budget analysis"
        ),
        SampleQuery(
            title="Vague Request",
            query="I want to go somewhere warm next week.",
            description="See how the agent asks clarifying questions"
        ),
        SampleQuery(
            title="Hotel Search",
            query="Find me hotels in Tokyo for July 10-17, 2026. I'd like something central, around $200 per night, with a gym and breakfast included.",
            description="Search for hotels with specific preferences"
        ),
        SampleQuery(
            title="Flight Search",
            query="I need flights from New York to London departing on September 1, 2026 and returning September 10, 2026. My budget is $800 and I prefer non-stop flights.",
            description="Find flights matching your preferences and budget"
        ),
        SampleQuery(
            title="Budget Analysis",
            query="I've found flights for $600 and hotels for $150/night for 5 nights. Can you analyze if this fits my $2000 budget and suggest activities?",
            description="Get a complete budget breakdown and recommendations"
        ),
        SampleQuery(
            title="Activities & Attractions",
            query="I'm visiting Paris for 5 days. Can you suggest must-see attractions, free activities, and budget-friendly experiences? I'm particularly interested in museums, historical sites, and local experiences.",
            description="Get recommendations for activities, attractions, and local experiences"
        ),
        SampleQuery(
            title="What-If Scenarios",
            query="What if I increase my budget by $500? How would that change my options?",
            description="Explore alternative scenarios and compare options (budget, dates, preferences)"
        )
    ]

    return SamplesResponse(success=True, samples=samples)


@app.post("/api/feedback", response_model=FeedbackResponse)
async def handle_feedback(request: FeedbackRequest):
    """Handle user feedback (satisfaction) and end the conversation."""
    try:
        print(f"Feedback received: {request.feedback} from user {request.user_id} (session: {request.session_id})")

        if runner and request.feedback == "satisfied":
            runner.end_conversation(request.user_id, request.feedback)
            print(f"Conversation ended for user {request.user_id}")

        return FeedbackResponse(
            success=True,
            message="Feedback recorded and conversation ended"
        )
    except Exception as e:
        print(f"Error handling feedback: {e}")
        return FeedbackResponse(
            success=False,
            error=str(e)
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        initialized=runner is not None
    )


@app.get("/test")
async def test():
    """Simple test endpoint to verify server is working."""
    return {
        "message": "Server is working!",
        "template_folder": os.path.join(BASE_DIR, "templates"),
        "static_folder": os.path.join(BASE_DIR, "static"),
        "template_exists": os.path.exists(os.path.join(BASE_DIR, "templates", "index.html")),
        "runner_initialized": runner is not None
    }


def find_free_port(start_port: int = 5000, max_attempts: int = 10) -> Optional[int]:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    return None


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(("127.0.0.1", port))
        return result == 0


if __name__ == "__main__":
    # Find available port
    default_port = int(os.environ.get("PORT", 5000))
    port = default_port

    if is_port_in_use(port):
        print(f"Port {port} is already in use. Finding an available port...")
        free_port = find_free_port(port + 1)
        if free_port:
            port = free_port
            print(f"Using port {port} instead")
        else:
            print("Could not find an available port. Please free up a port or set PORT environment variable.")
            sys.exit(1)

    print("AI Trip Planner Web Application (FastAPI)")
    print(f"Server starting on http://localhost:{port}")
    print(f"API docs available at http://localhost:{port}/docs")

    if port != default_port:
        print(f"Note: Port {default_port} was in use, using {port} instead")

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        log_level="info"
    )
