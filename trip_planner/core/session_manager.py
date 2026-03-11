"""
Session Manager - Handles conversation sessions and memory.
"""

import os
import uuid
import json
from google.adk.sessions import InMemorySessionService, Session
from google.adk.events import Event
from typing import Optional, Any
from trip_planner.config import get_session_memory_settings
from trip_planner.core.redis_client import get_redis_client
from trip_planner.logging_utils import get_logger

logger = get_logger(__name__)

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
        self.session_memory_settings = get_session_memory_settings()
        self.session_memory_backend = self.session_memory_settings["backend"]
        self.session_memory_key_prefix = self.session_memory_settings["key_prefix"]
        self.session_memory_ttl_seconds = int(self.session_memory_settings["ttl_seconds"])
        self.session_memory_redis = (
            get_redis_client(self.session_memory_settings["redis_url"])
            if self.session_memory_backend == "redis"
            else None
        )
        logger.info(
            "Conversation memory backend initialized: %s",
            "redis" if self.session_memory_redis is not None else "memory",
        )
        
        # Initialize Opik client once
        if OPIK_AVAILABLE:
            try:
                self.opik_client = opik.Opik(
                    project_name=os.environ.get('OPIK_PROJECT_NAME', 'AI Travel Planner')
                )
                logger.info("Opik client initialized.")
            except Exception as e:
                logger.warning("Could not initialize Opik client: %s", e)

    def _session_memory_key(self, user_id: str) -> str:
        """Build Redis key for persisted conversation memory."""
        return f"{self.session_memory_key_prefix}:session_memory:{self.app_name}:{user_id}"

    async def _restore_from_persistent_memory(self, user_id: str) -> Optional[Session]:
        """Restore session + conversation metadata from Redis if available."""
        if self.session_memory_redis is None:
            return None

        key = self._session_memory_key(user_id)
        try:
            payload_raw = self.session_memory_redis.get(key)
            if not payload_raw:
                return None
            payload = json.loads(payload_raw)
        except Exception as exc:
            logger.warning("Failed to load persisted conversation memory for '%s': %s", user_id, exc)
            return None

        session_data = payload.get("session")
        if not isinstance(session_data, dict):
            return None

        session_id = session_data.get("id")
        state = session_data.get("state") or {}
        events = session_data.get("events") or []

        restored_session = None
        if session_id:
            try:
                restored_session = await self.session_service.get_session(
                    app_name=self.app_name,
                    user_id=user_id,
                    session_id=session_id,
                )
            except Exception:
                restored_session = None

        if restored_session is None:
            restored_session = await self.session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                state=state,
                session_id=session_id,
            )
            for event_data in events:
                try:
                    event_obj = Event.model_validate(event_data)
                    self.session_service.append_event(restored_session, event_obj)
                except Exception as exc:
                    logger.warning("Skipping invalid persisted event during restore: %s", exc)

        self.current_sessions[user_id] = restored_session
        self.conversation_ids[user_id] = payload.get("conversation_id") or f"conv_{uuid.uuid4().hex[:12]}"
        self.conversation_queries[user_id] = payload.get("conversation_queries") or []
        self._create_conversation_trace(user_id, restored_session.id, self.conversation_ids[user_id])
        logger.info("Restored conversation memory from Redis for user '%s' (session=%s).", user_id, restored_session.id)
        return restored_session

    async def persist_user_memory(self, user_id: str, session: Optional[Session] = None) -> None:
        """Persist current session + conversation metadata to Redis."""
        if self.session_memory_redis is None:
            return

        session_obj = session or self.current_sessions.get(user_id)
        if session_obj is None:
            return

        try:
            latest_session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_obj.id,
            )
            session_to_store = latest_session or session_obj
            payload = {
                "session": session_to_store.model_dump(mode="json"),
                "conversation_id": self.conversation_ids.get(user_id),
                "conversation_queries": self.conversation_queries.get(user_id, []),
            }
            self.session_memory_redis.set(
                self._session_memory_key(user_id),
                json.dumps(payload),
                ex=self.session_memory_ttl_seconds,
            )
        except Exception as exc:
            logger.warning("Failed to persist conversation memory for '%s': %s", user_id, exc)

    def clear_persisted_memory(self, user_id: str) -> None:
        """Remove persisted conversation memory from Redis."""
        if self.session_memory_redis is None:
            return
        try:
            self.session_memory_redis.delete(self._session_memory_key(user_id))
        except Exception as exc:
            logger.warning("Failed to clear persisted conversation memory for '%s': %s", user_id, exc)
    
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
            restored_session = await self._restore_from_persistent_memory(user_id)
            if restored_session is not None:
                return restored_session

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
            await self.persist_user_memory(user_id, session)
            
            logger.info("Created new session for user '%s': %s", user_id, session.id)
            logger.info("Conversation ID: %s", conversation_id)
        else:
            session = self.current_sessions[user_id]
            logger.info("Using existing session for user '%s': %s", user_id, session.id)
        
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
        await self.persist_user_memory(user_id, session)
        
        logger.info("Created new session for user '%s': %s", user_id, session.id)
        logger.info("New conversation ID: %s", conversation_id)
        
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
                logger.info("Created Opik conversation trace: %s", trace.id)
            except Exception as e:
                logger.warning("Could not create Opik trace: %s", e)
    
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
                logger.warning("Could not create query span: %s", e)
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
                logger.info("Ended Opik trace for user '%s'", user_id)
            except Exception as e:
                logger.warning("Could not end Opik trace: %s", e)
        
        # Clean up
        if user_id in self.opik_traces:
            del self.opik_traces[user_id]
    
    def get_session_service(self):
        """Get the underlying session service."""
        return self.session_service
    
    def clear_session(self, user_id: str, clear_persistent: bool = False):
        """Clear a user's session from memory and optionally persistent storage."""
        if user_id in self.current_sessions:
            del self.current_sessions[user_id]
            logger.info("Cleared session for user '%s'", user_id)
        if clear_persistent:
            self.clear_persisted_memory(user_id)
    
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
                logger.info("Ended Opik trace with feedback: %s", feedback)
            except Exception as e:
                logger.warning("Could not end Opik trace: %s", e)
        
        # Clean up all user data
        if user_id in self.opik_traces:
            del self.opik_traces[user_id]
        if user_id in self.conversation_ids:
            del self.conversation_ids[user_id]
        if user_id in self.conversation_queries:
            del self.conversation_queries[user_id]
        
        self.clear_session(user_id, clear_persistent=True)
        logger.info("Conversation ended for user '%s' with feedback: %s", user_id, feedback)
