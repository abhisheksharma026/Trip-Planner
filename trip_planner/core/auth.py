"""
Authentication module - SQLite-based user authentication.

This module handles:
- User registration and login with email/password
- Session management with secure cookies
- User tracking for rate limiting

Uses SQLite for persistence - works great with Render's persistent disk.
"""

import os
import hashlib
import secrets
import sqlite3
from datetime import datetime, date
from typing import Optional, Dict, Tuple

from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware


# =============================================================================
# Configuration
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/trip_planner.db")

# Ensure data directory exists
os.makedirs(os.path.dirname(DATABASE_PATH) if os.path.dirname(DATABASE_PATH) else ".", exist_ok=True)


# =============================================================================
# User Model
# =============================================================================

class User(BaseModel):
    """User information."""
    id: str
    email: str
    name: Optional[str] = None
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at
        }


# =============================================================================
# Database Functions
# =============================================================================

from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


# Initialize database on module load
init_db()


# =============================================================================
# Password Utilities
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password with salt using PBKDF2."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash."""
    try:
        salt, hashed = stored_hash.split(':')
        check_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(check_hash.hex(), hashed)
    except (ValueError, AttributeError):
        # ValueError: hash doesn't contain ':'
        # AttributeError: stored_hash is None
        return False


# =============================================================================
# User Management Functions
# =============================================================================

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email."""
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user(email: str, password: str, name: str = None) -> User:
    """Create a new user."""
    user_id = secrets.token_urlsafe(16)
    password_hash = hash_password(password)
    created_at = datetime.now().isoformat()
    display_name = name or email.split('@')[0]

    with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO users (id, email, password_hash, name, created_at) VALUES (?, ?, ?, ?, ?)',
            (user_id, email.lower(), password_hash, display_name, created_at)
        )
        conn.commit()

    return User(
        id=user_id,
        email=email.lower(),
        name=display_name,
        created_at=created_at
    )


def verify_user(email: str, password: str) -> Optional[User]:
    """Verify user credentials."""
    user_data = get_user_by_email(email)
    if not user_data:
        return None
    
    if verify_password(password, user_data.get("password_hash", "")):
        return User(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data.get("name"),
            created_at=user_data.get("created_at", "")
        )
    return None


# =============================================================================
# Authentication Functions
# =============================================================================

def register_user(email: str, password: str, name: str = None) -> Tuple[Optional[User], Optional[str]]:
    """
    Register a new user.
    
    Returns:
        Tuple of (User, None) on success or (None, error_message) on failure
    """
    # Validate password
    if len(password) < 6:
        return None, "Password must be at least 6 characters"
    
    # Check if user exists
    if get_user_by_email(email):
        return None, "An account with this email already exists"
    
    # Create user
    try:
        user = create_user(email, password, name)
        return user, None
    except Exception as e:
        return None, f"Registration failed: {str(e)}"


def login_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    Login a user.
    
    Returns:
        Tuple of (User, None) on success or (None, error_message) on failure
    """
    user = verify_user(email, password)
    if not user:
        return None, "Invalid email or password"
    return user, None


# =============================================================================
# Session Middleware
# =============================================================================

def get_session_middleware():
    """Get session middleware for FastAPI."""
    from starlette.middleware.sessions import SessionMiddleware as SM
    
    class ConfiguredSessionMiddleware(SM):
        def __init__(self, app):
            super().__init__(
                app,
                secret_key=SECRET_KEY,
                session_cookie="trip_planner_session",
                max_age=86400 * 7,  # 7 days
                same_site="lax",
                https_only=False  # Set to True in production with HTTPS
            )
    
    return ConfiguredSessionMiddleware


# =============================================================================
# Session Functions
# =============================================================================

def get_current_user(request) -> Optional[User]:
    """Get the currently authenticated user from session."""
    user_data = request.session.get("user")
    if not user_data:
        return None

    try:
        return User(
            id=user_data.get("id", ""),
            email=user_data.get("email", ""),
            name=user_data.get("name"),
            created_at=user_data.get("created_at", "")
        )
    except (KeyError, TypeError, ValueError):
        # KeyError: Missing required field
        # TypeError: user_data is not a dict
        # ValueError: Pydantic validation error
        return None


def require_user(request) -> User:
    """Require an authenticated user."""
    user = get_current_user(request)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in."
        )
    return user


def set_session_user(request, user: User) -> None:
    """Set user in session."""
    request.session["user"] = user.to_dict()


def logout_user(request) -> None:
    """Clear the user session."""
    request.session.clear()


# =============================================================================
# User Rate Limit Tracking (in-memory, resets on restart)
# =============================================================================

import threading

_user_limits: Dict[str, Dict] = {}
_user_limits_lock = threading.Lock()


def _reset_user_data_if_needed(user_data: Dict, today: date) -> None:
    """Reset user counter if it's a new day."""
    if user_data["reset_date"] != today:
        user_data["count"] = 0
        user_data["reset_date"] = today


def get_user_rate_limit(user_id: str, daily_limit: int = 50) -> Dict:
    """Get rate limit status for a specific user."""
    with _user_limits_lock:
        today = date.today()

        if user_id not in _user_limits:
            _user_limits[user_id] = {"count": 0, "reset_date": today}

        user_data = _user_limits[user_id]
        _reset_user_data_if_needed(user_data, today)

        return {
            "count": user_data["count"],
            "limit": daily_limit,
            "remaining": daily_limit - user_data["count"],
            "reset_date": today.isoformat()
        }


def increment_user_rate_limit(user_id: str, daily_limit: int = 50) -> Tuple[bool, int, int]:
    """Increment rate limit counter for a user."""
    with _user_limits_lock:
        today = date.today()

        if user_id not in _user_limits:
            _user_limits[user_id] = {"count": 0, "reset_date": today}

        user_data = _user_limits[user_id]
        _reset_user_data_if_needed(user_data, today)

        if user_data["count"] >= daily_limit:
            return False, user_data["count"], 0

        user_data["count"] += 1
        return True, user_data["count"], daily_limit - user_data["count"]
