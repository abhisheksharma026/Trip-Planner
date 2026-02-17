# Building a Production-Grade AI Agent from Scratch - Phase II Part 2: User Authentication

## Overview

In Part 1, we added rate limiting to protect our API budget. Now we need to answer a critical question: **How do we track usage per user?**

Without authentication, rate limiting is based on IP addresses, which has problems:
- Multiple users behind the same IP (office, VPN) share the same limit
- A single user can bypass limits by switching IPs
- We can't offer personalized quotas

The solution: **Email/password authentication**.

## Why Simple Auth?

| Approach | Pros | Cons |
|----------|------|------|
| **Email/Password** | No external setup required | Need to manage passwords |
| Google OAuth | No password management | Requires Google Cloud setup |
| Magic Links | Passwordless | Requires email service |

We chose email/password because it works immediately without any external configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                         │
│                                                                 │
│  1. User clicks "Login" button                                 │
│  2. Modal shows login/register form                            │
│  3. User enters email + password                               │
│  4. Server validates credentials                               │
│  5. Session created with user ID                               │
│  6. User is now authenticated                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation

### Step 1: Create Auth Module

Create `trip_planner/core/auth.py`:

```python
"""
Authentication module - Simple email/password authentication.
"""

import os
import hashlib
import secrets
import json
from pydantic import BaseModel

# User storage (JSON file for simplicity)
USERS_FILE = "data/users.json"

class User(BaseModel):
    id: str
    email: str
    name: str = None

def hash_password(password: str) -> str:
    """Hash a password with salt."""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}:{hashed.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against stored hash."""
    salt, hashed = stored_hash.split(':')
    check_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return secrets.compare_digest(check_hash.hex(), hashed)

def register_user(email: str, password: str, name: str = None):
    """Register a new user."""
    user_id = secrets.token_urlsafe(16)
    # Store user in JSON file
    # Return User object

def login_user(email: str, password: str):
    """Login a user."""
    # Verify credentials
    # Return User object or error
```

### Step 2: Add Auth Routes

Update `app.py`:

```python
from trip_planner.core.auth import (
    register_user, login_user, logout_user, 
    get_current_user, set_session_user
)

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = None

@app.post("/api/register")
async def api_register(request: Request, data: RegisterRequest):
    user, error = register_user(data.email, data.password, data.name)
    if error:
        return {"success": False, "error": error}
    set_session_user(request, user)
    return {"success": True, "user": user.to_dict()}

@app.post("/api/login")
async def api_login(request: Request, data: LoginRequest):
    user, error = login_user(data.email, data.password)
    if error:
        return {"success": False, "error": error}
    set_session_user(request, user)
    return {"success": True, "user": user.to_dict()}

@app.post("/api/logout")
async def api_logout(request: Request):
    logout_user(request)
    return {"success": True}
```

### Step 3: Add Login Modal to Frontend

Add to `templates/index.html`:

```html
<!-- Login Modal -->
<div id="loginModal" class="modal">
    <div class="modal-content">
        <form id="authForm">
            <input type="email" id="email" placeholder="Email" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <p>Don't have an account? <a href="#" id="switchToRegister">Register</a></p>
    </div>
</div>
```

### Step 4: Add JavaScript Auth Manager

Add to `static/js/app.js`:

```javascript
class AuthManager {
    async checkAuthStatus() {
        const response = await fetch('/api/user');
        const data = await response.json();
        if (data.authenticated) {
            this.user = data.user;
            this.showUserInfo();
        } else {
            this.showLoginButton();
        }
    }
    
    async login(email, password) {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        return response.json();
    }
    
    async register(email, password, name) {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password, name})
        });
        return response.json();
    }
}
```

## How It Works

### User Registration

1. User clicks "Login" → Modal opens
2. User clicks "Register" link
3. Enters email, password, and optional name
4. Server creates user account with hashed password
5. User is automatically logged in

### User Login

1. User enters email and password
2. Server verifies credentials against stored hash
3. Session is created with user ID
4. User is redirected back to app

### Per-User Rate Limiting

```python
@app.post("/api/query")
async def handle_query(request: Request, data: QueryRequest):
    user = get_current_user(request)
    
    if user:
        # Authenticated: use per-user limit
        allowed, count, remaining = increment_user_rate_limit(f"user:{user.id}")
    else:
        # Anonymous: use global limit
        allowed, count, remaining = check_global_limit()
    
    if not allowed:
        raise HTTPException(429, "Rate limit exceeded")
```

## Files Changed

| File | Change |
|------|--------|
| `trip_planner/core/auth.py` | NEW - Email/password auth module |
| `app.py` | MODIFIED - Added auth routes |
| `templates/index.html` | MODIFIED - Added login modal |
| `static/js/app.js` | MODIFIED - Added AuthManager class |
| `static/css/style.css` | MODIFIED - Added modal styles |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/register` | POST | Register new user |
| `/api/login` | POST | Login with email/password |
| `/api/logout` | POST | Logout current user |
| `/api/user` | GET | Get current user info |

## Testing

```bash
# Register a new user
curl -X POST http://localhost:5000/api/register \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "secret123"}'

# Login
curl -X POST http://localhost:5000/api/login \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com", "password": "secret123"}'

# Check current user
curl http://localhost:5000/api/user
```

## Summary

In this part, we implemented:

1. **Email/password authentication** - Simple registration and login
2. **Session management** - Cookie-based sessions
3. **Per-user rate limiting** - Each user gets their own quota
4. **Login modal** - Clean UI for authentication

### Key Takeaway

Authentication enables per-user rate limiting, which is essential for fair usage. Email/password auth works immediately without any external service setup.

## Next Steps

In Part 3, we'll add Docker containerization for consistent deployment.
