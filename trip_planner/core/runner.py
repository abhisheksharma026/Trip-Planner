"""
Trip Planner Runner - Executes queries against the concierge agent.
"""

import asyncio
import os
from typing import Optional, Tuple, Any
from google.adk.runners import Runner
from google.adk.sessions import Session
from google.genai.types import Content, Part
from trip_planner.agents.concierge import ConciergeAgent
from trip_planner.core.session_manager import SessionManager

# Try to import Opik for observability
try:
    import opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    opik = None


# Global variable to store current query span for tool calls
_current_query_span = None


def get_current_query_span():
    """Get the current query span for tool calls to use."""
    global _current_query_span
    return _current_query_span


def set_current_query_span(span):
    """Set the current query span."""
    global _current_query_span
    _current_query_span = span


class TripPlannerRunner:
    """Runs queries against the trip planner concierge agent."""
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize the trip planner runner.
        
        Args:
            session_manager: SessionManager instance for handling sessions
        """
        self.concierge = ConciergeAgent()
        self.session_manager = session_manager
        self.runner = Runner(
            agent=self.concierge.get_agent(),
            session_service=session_manager.get_session_service(),
            app_name=self.concierge.get_agent().name
        )
    
    async def run_query(
        self,
        query: str,
        user_id: str = "default_user",
        create_new_session: bool = False
    ) -> Tuple[str, Session]:
        """
        Run a query against the trip planner agent.
        Creates a span under the conversation trace for this query.
        
        Args:
            query: User's query or request
            user_id: Unique identifier for the user
            create_new_session: If True, creates a new session (clears memory)
        
        Returns:
            Tuple of (response_text, session)
        """
        # Get or create session (this also creates the Opik trace if new)
        if create_new_session:
            session = await self.session_manager.create_new_session(user_id)
        else:
            session = await self.session_manager.get_or_create_session(user_id)
        
        # Skip tracing for "New session" dummy queries
        is_dummy_query = query.strip().lower() in ['new session', 'new_session']
        
        # Get query number
        query_num = self.session_manager.get_query_count(user_id) + 1
        conversation_id = self.session_manager.get_conversation_id(user_id)
        
        print(f"\nUser Query #{query_num}: '{query}'")
        print(f"Conversation ID: {conversation_id}")
        print("=" * 60)
        
        # Create a span for this query under the conversation trace (skip for dummy queries)
        query_span = None
        if not is_dummy_query:
            query_span = self.session_manager.create_query_span(user_id, query, query_num)
            # Set the global query span so tool calls can create child spans
            set_current_query_span(query_span)
        
        try:
            # Run the agent query
            final_response = await self._run_agent_query(query, user_id, session)
            
            # Update and end the query span (only if it was created)
            if query_span:
                try:
                    query_span.update(output={"response": final_response[:2000] if final_response else "No response"})
                    query_span.end()
                except Exception as e:
                    print(f"Could not update query span: {e}")
        finally:
            # Clear the global span
            set_current_query_span(None)
        
        # Track this query-response in the conversation (skip for dummy queries)
        if not is_dummy_query:
            self.session_manager.add_query_to_conversation(user_id, query, final_response)
        
        print("=" * 60)
        print("Response:")
        print(final_response)
        print("=" * 60 + "\n")
        
        return final_response, session
    
    async def _run_agent_query(self, query: str, user_id: str, session: Session) -> str:
        """
        Run the actual agent query and collect the response.
        """
        final_response = ""
        all_text_parts = []
        
        try:
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=Content(parts=[Part(text=query)], role="user")
            ):
                # Collect all text parts from events
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            all_text_parts.append(part.text)
                
                # Also check final response
                if event.is_final_response():
                    # Extract text from all text parts in final response
                    text_parts = []
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                    
                    if text_parts:
                        final_response = "\n".join(text_parts)
                    elif all_text_parts:
                        # Use collected text parts if final response has no text
                        final_response = "\n".join(all_text_parts)
                    else:
                        # If no text parts, try to get string representation
                        final_response = str(event.content) if event.content else "Response received but no text content found."
        
        except Exception as e:
            final_response = f"An error occurred: {e}"
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: use collected text if final_response is still empty
        if not final_response and all_text_parts:
            final_response = "\n".join(all_text_parts)
        
        # Ensure we always return something
        if not final_response or not final_response.strip():
            final_response = "I received your message but couldn't generate a response. Please try again."
        
        return final_response
    
    def end_conversation(self, user_id: str, feedback: str = None):
        """
        End the conversation for a user (called when satisfied).
        
        Args:
            user_id: User identifier
            feedback: Optional feedback
        """
        self.session_manager.end_conversation(user_id, feedback)
    
    async def run_interactive(self, user_id: str = "default_user"):
        """
        Run an interactive session with the trip planner.
        
        Args:
            user_id: Unique identifier for the user
        """
        print("\n" + "=" * 60)
        print("AI Trip Planner - Interactive Mode")
        print("=" * 60)
        print("Type 'quit', 'exit', or 'new' (to start fresh) to end the session.\n")
        
        session = await self.session_manager.get_or_create_session(user_id)
        
        while True:
            try:
                query = input("\nYou: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['quit', 'exit', 'q']:
                    self.end_conversation(user_id, "quit")
                    print("\nGoodbye! Happy travels!")
                    break
                
                if query.lower() == 'new':
                    session = await self.session_manager.create_new_session(user_id)
                    print("Started a new session. Previous context cleared.\n")
                    continue
                
                # Run the query
                response, session = await self.run_query(query, user_id)
                
            except KeyboardInterrupt:
                self.end_conversation(user_id, "interrupted")
                print("\n\nGoodbye! Happy travels!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
