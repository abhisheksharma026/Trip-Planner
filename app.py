"""
FastAPI web application for the AI Trip Planner.
"""

import os
import sys
import socket
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from trip_planner.config import setup_api_key, setup_opik
from trip_planner.core.session_manager import SessionManager
from trip_planner.core.runner import TripPlannerRunner
from trip_planner.core.rate_limiter import (
    limiter,
    global_limiter,
    check_global_limit,
    get_global_status,
    RATE_LIMIT_PER_MINUTE,
    anonymous_limiter,
    get_client_identifier,
)
from trip_planner.core.auth import (
    get_session_middleware,
    get_current_user,
    require_user,
    register_user,
    login_user,
    logout_user,
    set_session_user,
    get_user_rate_limit,
    increment_user_rate_limit,
    User,
)

# Import middleware
from trip_planner.middleware import (
    validate_content_type,
    add_security_headers,
    log_requests,
    add_request_id,
)

# =============================================================================
# Constants
# =============================================================================

LOCALHOST_ORIGINS = [
    "http://localhost:5000",
    "http://localhost:5001",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5001",
]

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

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure session middleware (required for OAuth)
app.add_middleware(get_session_middleware())

# Configure CORS
# In production, set ALLOWED_ORIGINS to your domain(s), e.g., "https://yourapp.onrender.com,https://yourapp.com"
# Security note: allow_credentials=True requires specific origins, not wildcard
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not allowed_origins or allowed_origins == [""]:
    # Default: allow local development only with credentials
    allowed_origins = LOCALHOST_ORIGINS
    allow_credentials = True
    print("[INFO] CORS: Using local development origins only")
elif "*" in allowed_origins:
    # Wildcard mode: disable credentials for security
    allowed_origins = ["*"]
    allow_credentials = False
    print("[WARNING] CORS: Wildcard origins detected - credentials disabled")
else:
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


# =============================================================================
# Custom Middleware
# =============================================================================
# Middleware execution order (outer to inner):
# Request → [Request ID] → [Content-Type] → [Security Headers] → [Logging] → Route Handler
# Response ← [Request ID] ← [Content-Type] ← [Security Headers] ← [Logging] ← Route Handler

app.middleware("http")(add_request_id)
app.middleware("http")(validate_content_type)
app.middleware("http")(add_security_headers)
app.middleware("http")(log_requests)


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


# =============================================================================
# Helper Functions
# =============================================================================

def build_rate_limit_headers(is_authenticated: bool, anon_remaining: int) -> Dict[str, str]:
    """Build rate limit headers for API responses."""
    status = get_global_status()
    return {
        "X-RateLimit-Limit": str(status["limit"]),
        "X-RateLimit-Remaining": str(status["remaining"]),
        "X-RateLimit-Reset": status["reset_date"],
        "X-RateLimit-Used": str(status["count"]),
        "X-Anonymous-Remaining": str(anon_remaining) if not is_authenticated else "unlimited",
        "X-Authenticated": str(is_authenticated).lower()
    }


# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/query", response_model=QueryResponse)
@limiter.limit(f"{RATE_LIMIT_PER_MINUTE}/minute")
async def handle_query(request: Request, query_request: QueryRequest):
    """
    Handle user queries.
    
    Rate limited to RATE_LIMIT_PER_MINUTE requests per minute per IP.
    Also checks global daily limit (200 calls/day by default).
    Anonymous users get 5 free queries before login is required.
    """
    # Check if user is authenticated
    current_user = get_current_user(request)
    is_authenticated = current_user is not None
    
    # For anonymous users, check the 5-query limit
    if not is_authenticated:
        client_id = get_client_identifier(request)
        allowed, anon_count, anon_remaining = anonymous_limiter.check_and_increment(client_id)
        if not allowed:
            raise HTTPException(
                status_code=401,
                detail="You've used all 5 free queries! Please log in to continue planning your trip. It's free and only takes a moment."
            )
    
    # Check global daily limit first
    allowed, count, remaining = check_global_limit()
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Daily API limit exceeded. Please try again tomorrow."
        )
    
    if not runner:
        raise HTTPException(status_code=503, detail="Trip planner not initialized")

    query = query_request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        response, session = await runner.run_query(
            query=query,
            user_id=query_request.user_id,
            create_new_session=query_request.new_session
        )

        # Ensure response is a string
        if response is None:
            response = "I received your message but couldn't generate a response. Please try again."
        elif not isinstance(response, str):
            response = str(response)

        # Build response with rate limit headers
        query_response = QueryResponse(
            success=True,
            response=response,
            session_id=session.id if session else None
        )

        return JSONResponse(
            content=query_response.model_dump(),
            headers=build_rate_limit_headers(is_authenticated, anon_remaining)
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
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
        logger.info(
            f"Feedback received: {request.feedback} from user {request.user_id} (session: {request.session_id})"
        )

        if runner and request.feedback == "satisfied":
            runner.end_conversation(request.user_id, request.feedback)
            logger.info(f"Conversation ended for user {request.user_id}")

        return FeedbackResponse(
            success=True,
            message="Feedback recorded and conversation ended"
        )
    except Exception as e:
        logger.error(f"Error handling feedback: {e}")
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


@app.get("/api/rate-limit-status")
async def rate_limit_status(request: Request):
    """
    Get current rate limit status.
    
    Returns the number of API calls made today and remaining quota.
    For authenticated users, returns their personal limit.
    """
    user = get_current_user(request)
    if user:
        # Authenticated users get per-user limits
        user_status = get_user_rate_limit(f"user:{user.id}")
        return {
            **user_status,
            "user": user.email,
            "authenticated": True
        }
    else:
        # Anonymous users see global limit
        return {
            **get_global_status(),
            "user": None,
            "authenticated": False
        }


# =============================================================================
# Authentication Routes
# =============================================================================

class LoginRequest(BaseModel):
    """Login request model."""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RegisterRequest(BaseModel):
    """Registration request model."""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    name: Optional[str] = Field(None, description="User name")


class AuthResponse(BaseModel):
    """Authentication response model."""
    success: bool
    user: Optional[dict] = None
    error: Optional[str] = None


@app.get("/api/user")
async def get_user(request: Request):
    """Get current authenticated user."""
    user = get_current_user(request)
    if user:
        return {
            "authenticated": True,
            "user": user.to_dict()
        }
    return {
        "authenticated": False,
        "user": None
    }


@app.post("/api/register", response_model=AuthResponse)
async def api_register(request: Request, data: RegisterRequest):
    """Register a new user."""
    user, error = register_user(data.email, data.password, data.name)
    
    if error:
        return AuthResponse(success=False, error=error)
    
    # Auto-login after registration
    set_session_user(request, user)
    
    return AuthResponse(
        success=True,
        user=user.to_dict()
    )


@app.post("/api/login", response_model=AuthResponse)
async def api_login(request: Request, data: LoginRequest):
    """Login with email and password."""
    user, error = login_user(data.email, data.password)
    
    if error:
        return AuthResponse(success=False, error=error)
    
    set_session_user(request, user)
    
    return AuthResponse(
        success=True,
        user=user.to_dict()
    )


@app.post("/api/logout")
async def api_logout(request: Request):
    """Log out the current user."""
    logout_user(request)
    return {"success": True, "message": "Logged out successfully"}


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
