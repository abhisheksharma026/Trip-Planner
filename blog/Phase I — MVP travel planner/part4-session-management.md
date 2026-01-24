# Building a Production-Grade AI Agent from Scratch - Part 4: Session Management

## Overview

In Part 3, we built our configuration module that handles API keys and model settings. Now, let's create the **Session Manager** - a critical component that enables our agent to remember context across multiple turns of conversation.

Session management is what transforms our agent from a forgetful chatbot into a helpful assistant that can maintain coherent, multi-turn conversations.

## Why Session Management Matters

Without session management, our agent would be:

1. **Forgetful**: Each query is processed independently, no memory of previous interactions
2. **Frustrating**: Users must repeat information in every query
3. **Limited**: Can't handle complex, multi-step conversations
4. **Untrackable**: No way to monitor or debug conversations

With proper session management, our agent becomes:

1. **Context-aware**: Remembers preferences, constraints, and previous recommendations
2. **Conversational**: Handles follow-ups naturally
3. **Multi-turn**: Can handle complex workflows with multiple questions
4. **Observable**: We can track entire conversations for debugging
5. **Scalable**: Supports multiple users with isolated sessions

## Understanding ADK Session Service

Google ADK provides a built-in `InMemorySessionService` that handles:

- Session creation and management
- Message storage and retrieval
- User identification
- Conversation history

However, for production, we need to wrap this with additional functionality:

- Observability tracking (Opik traces)
- Conversation ID generation
- Query counting and tracking
- Graceful cleanup

## Session Manager Architecture

```
┌─────────────────────────────────────────────────┐
│         User Query                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Session Manager              │
│  ┌─────────────────────────────────────┐  │
│  │  InMemorySessionService         │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Current Sessions          │  │  │
│  │  │  ┌─────────────────────┐  │  │
│  │  │  │ user_1 → session_abc  │  │  │
│  │  │  │ user_2 → session_def456 │  │  │
│  │  │  └─────────────────────┘  │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Conversation Tracking      │  │  │
│  │  │  ┌─────────────────────┐  │  │
│  │  │  │ user_1 → conv_a1b2c3  │  │  │
│  │  │  │ user_1 → 2 queries      │  │  │
│  │  │  │ user_2 → conv_d4e5f6g7  │  │  │
│  │  │  └─────────────────────┘  │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Observability (Opik)        │  │  │
│  │  │  ┌─────────────────────┐  │  │
│  │  │  │ user_1 → trace_xyz789  │  │  │
│  │  │  │ user_2 → trace_abc123  │  │  │
│  │  │  └─────────────────────┘  │  │
│  └─────────────────────────────────────┘  │  │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         Trip Planner Runner            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Concierge Agent              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Specialized Agents            │
└──────────────┬──────────────────────┘
```

## Building the Session Manager

Let's create our session manager. Create `trip_planner/core/session_manager.py`:

```python
"""
Session Manager - Handles conversation sessions and memory.
"""

import os
import uuid
from google.adk.sessions import InMemorySessionService, Session
from typing import Optional, Any

# Try to import Opik for observability
try:
    import opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    opik = None


class SessionManager:
    """Manages user sessions for maintaining conversation context."""
    
    def __init__(self, app_name: str = "trip_planner_concierge"):
        """
        Initialize session manager.
        
        Args:
            app_name: Name of application for session tracking
        """
        # Initialize ADK's in-memory session service
        self.session_service = InMemorySessionService()
        self.app_name = app_name
        
        # Track sessions by user_id
        self.current_sessions = {}  # user_id -> Session mapping
        self.conversation_ids = {}  # user_id -> conversation_id
        self.conversation_queries = {}  # user_id -> list of queries
        self.opik_traces = {}  # user_id -> Opik trace object
        self.opik_client = None
        
        # Initialize Opik client once (if available)
        if OPIK_AVAILABLE:
            try:
                self.opik_client = opik.Opik(
                    project_name=os.environ.get('OPIK_PROJECT_NAME', 'AI Travel Planner')
                )
                print("Opik client initialized")
            except Exception as e:
                print(f"Could not initialize Opik client: {e}")
    
    async def get_or_create_session(self, user_id: str) -> Session:
        """
        Get existing session for user or create a new one.
        Also creates a single Opik trace for entire conversation.
        
        Args:
            user_id: Unique identifier for the user
        
        Returns:
            Session object for the user
        """
        # Check if session already exists
        if user_id not in self.current_sessions:
            # Create new session
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id
            )
            self.current_sessions[user_id] = session
            self.conversation_queries[user_id] = []
            
            # Generate unique conversation ID
            conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
            self.conversation_ids[user_id] = conversation_id
            
            # Create ONE Opik trace for entire conversation
            self._create_conversation_trace(user_id, session.id, conversation_id)
            
            print(f"Created new session for user '{user_id}': {session.id}")
            print(f"Conversation ID: {conversation_id}")
        else:
            # Return existing session
            session = self.current_sessions[user_id]
            print(f"Using existing session for user '{user_id}': {session.id}")
        
        return session
    
    async def create_new_session(self, user_id: str) -> Session:
        """
        Force create a new session for a user (clears previous context).
        Ends previous Opik trace and starts a new one.
        
        Args:
            user_id: Unique identifier for the user
        
        Returns:
            New Session object
        """
        # End previous conversation trace if exists
        self._end_conversation_trace(user_id, "new_session")
        
        # Create new session
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=user_id
        )
        self.current_sessions[user_id] = session
        self.conversation_queries[user_id] = []
        
        # Generate new conversation ID
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        self.conversation_ids[user_id] = conversation_id
        
        # Create new Opik trace
        self._create_conversation_trace(user_id, session.id, conversation_id)
        
        print(f"Created new session for user '{user_id}': {session.id}")
        print(f"New conversation ID: {conversation_id}")
        
        return session
    
    def _create_conversation_trace(self, user_id: str, session_id: str, conversation_id: str):
        """
        Create root Opik trace for a conversation.
        
        This creates a single trace that will contain all queries
        and tool calls for entire conversation.
        """
        if self.opik_client:
            try:
                trace = self.opik_client.trace(
                    name="travel_conversation",
                    input={"conversation_start": True, "user_id": user_id},
                    metadata={
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "session_id": session_id,
                        "app": self.app_name,
                    },
                    tags=["conversation", "trip_planner"]
                )
                self.opik_traces[user_id] = trace
                print(f"Created Opik conversation trace: {trace.id}")
            except Exception as e:
                print(f"Could not create Opik trace: {e}")
    
    def get_conversation_trace(self, user_id: str) -> Any:
        """
        Get Opik trace object for user's conversation.
        
        Args:
            user_id: User identifier
        
        Returns:
            The trace object, or None if not available
        """
        return self.opik_traces.get(user_id)
    
    def create_query_span(self, user_id: str, query: str, query_num: int) -> Any:
        """
        Create a span for a user query within conversation trace.
        
        Each query in a conversation gets its own span, allowing
        us to track individual queries and their tool calls.
        
        Args:
            user_id: User identifier
            query: The user's query
            query_num: Query number in the conversation
        
        Returns:
            The span object, or None if not available
        """
        trace = self.opik_traces.get(user_id)
        if trace:
            try:
                span = trace.span(
                    name=f"user_query_{query_num}",
                    input={"query": query, "query_num": query_num},
                    metadata={"query_num": query_num}
                )
                return span
            except Exception as e:
                print(f"Could not create query span: {e}")
        return None
    
    def get_conversation_id(self, user_id: str) -> str:
        """
        Get the conversation ID for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Conversation ID string
        """
        if user_id not in self.conversation_ids:
            # Generate new conversation ID if not exists
            self.conversation_ids[user_id] = f"conv_{uuid.uuid4().hex[:12]}"
        return self.conversation_ids[user_id]
    
    def add_query_to_conversation(self, user_id: str, query: str, response: str):
        """
        Track a query-response pair in the conversation.
        
        This helps us understand conversation flow and
        provides context for debugging.
        
        Args:
            user_id: User identifier
            query: User's query
            response: Agent's response
        """
        if user_id not in self.conversation_queries:
            self.conversation_queries[user_id] = []
        
        self.conversation_queries[user_id].append({
            "query": query[:200],  # Truncate for storage
            "response": response[:500] if response else "No response"
        })
    
    def get_query_count(self, user_id: str) -> int:
        """
        Get the number of queries in the current conversation.
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of queries (int)
        """
        return len(self.conversation_queries.get(user_id, []))
    
    def _end_conversation_trace(self, user_id: str, reason: str = None):
        """
        End Opik trace for a user.
        
        Args:
            user_id: User identifier
            reason: Optional reason for ending (e.g., "new_session", "satisfied")
        """
        trace = self.opik_traces.get(user_id)
        if trace:
            try:
                queries = self.conversation_queries.get(user_id, [])
                trace.update(
                    output={
                        "conversation_end": True,
                        "reason": reason or "ended",
                        "total_queries": len(queries),
                    }
                )
                trace.end()
                print(f"Ended Opik trace for user '{user_id}'")
            except Exception as e:
                print(f"Could not end Opik trace: {e}")
        
        # Clean up
        if user_id in self.opik_traces:
            del self.opik_traces[user_id]
    
    def get_session_service(self):
        """
        Get the underlying ADK session service.
        
        This is needed by the Runner to execute queries.
        
        Returns:
            InMemorySessionService instance
        """
        return self.session_service
    
    def clear_session(self, user_id: str):
        """
        Clear a user's session from memory.
        
        Args:
            user_id: User identifier
        """
        if user_id in self.current_sessions:
            del self.current_sessions[user_id]
            print(f"Cleared session for user '{user_id}'")
    
    def end_conversation(self, user_id: str, feedback: str = None):
        """
        End the current conversation for a user.
        Called when user is satisfied or wants to start fresh.
        
        Updates and ends Opik trace with feedback.
        
        Args:
            user_id: User identifier
            feedback: Optional feedback (e.g., 'satisfied')
        """
        # Update and end Opik trace with feedback
        trace = self.opik_traces.get(user_id)
        if trace:
            try:
                queries = self.conversation_queries.get(user_id, [])
                trace.update(
                    output={
                        "conversation_end": True,
                        "feedback": feedback or "satisfied",
                        "total_queries": len(queries),
                    },
                    metadata={
                        "feedback": feedback,
                        "total_queries": len(queries)
                    }
                )
                trace.end()
                print(f"Ended Opik trace with feedback: {feedback}")
            except Exception as e:
                print(f"Could not end Opik trace: {e}")
        
        # Clean up all user data
        if user_id in self.opik_traces:
            del self.opik_traces[user_id]
        if user_id in self.conversation_ids:
            del self.conversation_ids[user_id]
        if user_id in self.conversation_queries:
            del self.conversation_queries[user_id]
        
        self.clear_session(user_id)
        print(f"Conversation ended for user '{user_id}' with feedback: {feedback}")
```

## Understanding the Session Manager

### Key Components

#### 1. Session Storage

```python
self.current_sessions = {}  # user_id -> Session
```

Stores active ADK Session objects for each user.

#### 2. Conversation Tracking

```python
self.conversation_ids = {}  # user_id -> conversation_id
self.conversation_queries = {}  # user_id -> list of queries
```

Tracks conversation metadata and query history.

#### 3. Observability

```python
self.opik_traces = {}  # user_id -> Opik trace
self.opik_client = opik.Opik(project_name="AI Travel Planner")
```

Stores Opik trace objects for monitoring and debugging.

### Key Methods

#### `get_or_create_session(user_id)`

```python
if user_id not in self.current_sessions:
    # Create new session
    session = await self.session_service.create_session(...)
    self._create_conversation_trace(user_id, session.id, conversation_id)
else:
    # Return existing session
    session = self.current_sessions[user_id]
```

Gets or creates session with observability trace.

#### `create_query_span(user_id, query, query_num)`

```python
trace = self.opik_traces.get(user_id)
if trace:
    span = trace.span(
        name=f"user_query_{query_num}",
        input={"query": query}
    )
    return span
```

Creates a span for tracking individual queries.

## Testing Session Manager

To test session manager, use the web interface:

1. Start the web server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Ask multiple questions in the chat interface to test session persistence:
   - "I want to plan a trip to Paris in March 2025"
   - "What's the weather like in March?"
   - "What if I increase my budget to $2,000?"

4. Check the console output to verify:
   - Session is created for the user
   - Conversation ID is generated
   - Opik trace is created (if OPIK_API_KEY is set)
   - Queries are tracked in the conversation

Expected console output:
```
Starting server on port 8000
Configuration initialized
API Key loaded from environment/.env file
API Key configured successfully!
Opik configured successfully!
Session manager initialized
Opik client initialized
Concierge agent initialized
Runner initialized
Application startup complete!

Created new session for user 'web_user': session_abc123
Conversation ID: conv_a1b2c3d4e5f6
Created Opik conversation trace: trace_xyz789

Using existing session for user 'web_user': session_abc123

Using existing session for user 'web_user': session_abc123
```

5. Verify that the agent remembers context from previous questions in the conversation

## Production Considerations

### 1. Memory Usage

Our current implementation uses in-memory storage. For production, consider:

```python
# For production, replace InMemorySessionService with:
# - Database-backed session service
# - Redis for fast caching
# - Cloud storage for persistence
```

### 2. Session Cleanup

We currently clean up sessions manually. In production:

```python
# Add automatic cleanup
# - Expire sessions after inactivity
# - Limit session duration
# - Clean up old traces
```

### 3. Multi-User Support

Our implementation already supports multiple users:

```python
# Different users get different sessions
session1 = await session_manager.get_or_create_session("user_1")
session2 = await session_manager.get_or_create_session("user_2")
# These are completely independent
```

### 4. Observability

Opik traces help us:
- Debug conversations
- Analyze agent behavior
- Track performance metrics
- Identify patterns in user queries

## Common Issues

### Issue: Session Not Persisted

**Symptoms**:
```
Using existing session for user 'user_1': session_abc123
```

**Solution**: This is expected behavior. Sessions are in-memory and lost on restart. For persistence, implement database-backed sessions.

### Issue: Opik Trace Not Created

**Symptoms**:
```
Query span not created (Opik not available)
```

**Solution**: Check Opik configuration in `.env` file:

```bash
OPIK_API_KEY=your_opik_key
OPIK_PROJECT_NAME=AI Travel Planner
```

## What's Next?

Congratulations! You've built a robust session manager. In Part 5, we'll create our specialized agents - Flight Recommender, Hotel Specialist, and Financial Planner.

## Summary

In this part, we:
- Built a comprehensive session manager
- Implemented conversation context tracking
- Added Opik observability traces
- Supported multi-user sessions
- Implemented query counting and tracking
- Added graceful session cleanup

## Key Takeaways

1. **Session management is critical**: It's what makes agents conversational
2. **Context matters**: Remembering previous turns improves UX
3. **Observability is valuable**: Traces help debug and analyze
4. **Multi-user support**: Each user gets isolated sessions
5. **Graceful cleanup**: Properly end traces and clear data

## Resources

- [Google ADK Sessions](https://github.com/google/adk)
- [Opik Documentation](https://www.comet.com/site/products/opik/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
- [UUID Module](https://docs.python.org/3/library/uuid.html)

---

Continue to Part 5: Specialized Agents
