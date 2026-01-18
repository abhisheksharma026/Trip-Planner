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
        Initialize the session manager.
        
        Args:
            app_name: Name of the application for session tracking
        """
        self.session_service = InMemorySessionService()
        self.app_name = app_name
        self.current_sessions = {}  # user_id -> Session mapping
        self.conversation_ids = {}  # user_id -> conversation_id
        self.conversation_queries = {}  # user_id -> list of queries
        self.opik_traces = {}  # user_id -> Opik trace object
        self.opik_client = None
        
        # Initialize Opik client once
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
        Also creates a single Opik trace for the entire conversation.
        
        Args:
            user_id: Unique identifier for the user
        
        Returns:
            Session object for the user
        """
        if user_id not in self.current_sessions:
            session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id
            )
            self.current_sessions[user_id] = session
            self.conversation_queries[user_id] = []
            
            # Generate conversation ID
            conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
            self.conversation_ids[user_id] = conversation_id
            
            # Create ONE Opik trace for the entire conversation
            self._create_conversation_trace(user_id, session.id, conversation_id)
            
            print(f"Created new session for user '{user_id}': {session.id}")
            print(f"Conversation ID: {conversation_id}")
        else:
            session = self.current_sessions[user_id]
            print(f"Using existing session for user '{user_id}': {session.id}")
        
        return session
    
    async def create_new_session(self, user_id: str) -> Session:
        """
        Force create a new session for a user (clears previous context).
        Ends the previous Opik trace and starts a new one.
        
        Args:
            user_id: Unique identifier for the user
        
        Returns:
            New Session object
        """
        # End the previous conversation trace if exists
        self._end_conversation_trace(user_id, "new_session")
        
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
        """Create the root Opik trace for a conversation."""
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
        """Get the Opik trace object for the user's conversation."""
        return self.opik_traces.get(user_id)
    
    def create_query_span(self, user_id: str, query: str, query_num: int) -> Any:
        """
        Create a span for a user query within the conversation trace.
        
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
        """Get the conversation ID."""
        if user_id not in self.conversation_ids:
            self.conversation_ids[user_id] = f"conv_{uuid.uuid4().hex[:12]}"
        return self.conversation_ids[user_id]
    
    def add_query_to_conversation(self, user_id: str, query: str, response: str):
        """Track a query-response pair in the conversation."""
        if user_id not in self.conversation_queries:
            self.conversation_queries[user_id] = []
        self.conversation_queries[user_id].append({
            "query": query[:200],
            "response": response[:500] if response else "No response"
        })
    
    def get_query_count(self, user_id: str) -> int:
        """Get the number of queries in current conversation."""
        return len(self.conversation_queries.get(user_id, []))
    
    def _end_conversation_trace(self, user_id: str, reason: str = None):
        """End the Opik trace for the user."""
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
        """Get the underlying session service."""
        return self.session_service
    
    def clear_session(self, user_id: str):
        """Clear a user's session from memory."""
        if user_id in self.current_sessions:
            del self.current_sessions[user_id]
            print(f"Cleared session for user '{user_id}'")
    
    def end_conversation(self, user_id: str, feedback: str = None):
        """
        End the current conversation for a user (called when user is satisfied).
        Ends the Opik trace with feedback.
        
        Args:
            user_id: User identifier
            feedback: Optional feedback (e.g., 'satisfied')
        """
        # Update and end the Opik trace with feedback
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
