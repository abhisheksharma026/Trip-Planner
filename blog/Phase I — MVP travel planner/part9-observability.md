# Building a Production-Grade AI Agent from Scratch - Part 9: Adding Observability with Opik

## Overview

In Part 8, we built our web interface with FastAPI, HTML, CSS, and JavaScript. Now, let's add **Observability with Opik** - a powerful tool for tracking, debugging, and understanding how our AI agents behave.

Observability is critical for production AI systems because:

1. **Debugging**: Understand what went wrong when issues occur
2. **Performance**: Track response times and resource usage
3. **Quality**: Monitor agent behavior over time
4. **Improvement**: Identify patterns and areas for optimization
5. **Compliance**: Track and audit agent decisions

## What is Opik?

Opik is an observability platform specifically designed for AI applications. It provides:

- **Traces**: Track entire conversations and workflows
- **Spans**: Break down operations into individual steps
- **Metrics**: Collect performance data
- **Metadata**: Store additional context
- **Visualization**: View traces and spans in a dashboard

## Observability Architecture

```
┌─────────────────────────────────────────────────┐
│         User Query                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Session Manager              │
│  ┌─────────────────────────────────────┐  │
│  │  Create Conversation Trace         │  │
│  │  - User ID                         │  │
│  │  - Session ID                      │  │
│  │  - Conversation ID                 │  │
│  │  - Metadata                        │  │
│  └─────────────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Trip Planner Runner          │
│  ┌─────────────────────────────────────┐  │
│  │  Create Query Span                │  │
│  │  - Query text                     │  │
│  │  - Query number                   │  │
│  │  - Metadata                       │  │
│  └─────────────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Concierge Agent              │
│  ┌─────────────────────────────────────┐  │
│  │  Create Tool Call Spans           │  │
│  │  - Flight search                  │  │
│  │  - Hotel search                   │  │
│  │  - Financial analysis             │  │
│  │  - Safety checks                  │  │
│  └─────────────────────────────────────┘  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Opik Dashboard               │
│  ┌─────────────────────────────────────┐  │
│  │  View Traces                      │  │
│  │  - Search by user                 │  │
│  │  - Filter by date                 │  │
│  │  - View metadata                  │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  View Spans                       │  │
│  │  - Query spans                    │  │
│  │  - Tool call spans                │  │
│  │  - Timing information             │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Analyze Performance              │  │
│  │  - Response times                 │  │
│  │  - Error rates                    │  │
│  │  - Success rates                  │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Understanding Traces and Spans

### Traces

A **trace** represents an entire conversation or workflow. It contains:

- **Name**: Descriptive name (e.g., "travel_conversation")
- **Input**: Initial input data
- **Output**: Final output data
- **Metadata**: Additional context
- **Spans**: Child operations

Example trace structure:

```python
{
    "name": "travel_conversation",
    "input": {
        "conversation_start": True,
        "user_id": "user_123"
    },
    "output": {
        "conversation_end": True,
        "total_queries": 5
    },
    "metadata": {
        "conversation_id": "conv_abc123",
        "user_id": "user_123",
        "session_id": "session_xyz789"
    },
    "spans": [
        # Query spans go here
    ]
}
```

### Spans

A **span** represents a single operation within a trace. It contains:

- **Name**: Descriptive name (e.g., "user_query_1")
- **Input**: Input data for the operation
- **Output**: Output data from the operation
- **Metadata**: Additional context
- **Timing**: Start and end times

Example span structure:

```python
{
    "name": "user_query_1",
    "input": {
        "query": "I want to plan a trip to Paris",
        "query_num": 1
    },
    "output": {
        "response": "Great! I can help you plan a trip to Paris..."
    },
    "metadata": {
        "query_num": 1,
        "agent": "concierge"
    }
}
```

## Opik Integration in Session Manager

We already integrated Opik into our Session Manager in Part 4. Let's review the key components:

### 1. Opik Client Initialization

```python
# In trip_planner/core/session_manager.py

try:
    import opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    opik = None

class SessionManager:
    def __init__(self, app_name: str = "trip_planner_concierge"):
        # ... other initialization
        
        # Initialize Opik client
        if OPIK_AVAILABLE:
            try:
                self.opik_client = opik.Opik(
                    project_name=os.environ.get('OPIK_PROJECT_NAME', 'AI Travel Planner')
                )
                print("Opik client initialized")
            except Exception as e:
                print(f"Could not initialize Opik client: {e}")
```

### 2. Creating Conversation Traces

```python
def _create_conversation_trace(self, user_id: str, session_id: str, conversation_id: str):
    """
    Create root Opik trace for a conversation.
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
```

### 3. Creating Query Spans

```python
def create_query_span(self, user_id: str, query: str, query_num: int) -> Any:
    """
    Create a span for a user query within conversation trace.
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
```

### 4. Ending Conversation Traces

```python
def _end_conversation_trace(self, user_id: str, reason: str = None):
    """
    End Opik trace for a user.
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
```

## Opik Integration in Runner

Let's update the Runner to use Opik spans. Update `trip_planner/core/runner.py`:

```python
"""
Trip Planner Runner - Executes queries and manages query-response flow.
"""

import os
from typing import Optional

from trip_planner.core.session_manager import SessionManager
from trip_planner.agents.concierge import create_concierge
from google.adk.agents import Agent


class TripPlannerRunner:
    """Executes queries against the concierge agent."""
    
    def __init__(
        self,
        session_manager: SessionManager,
        concierge: Agent
    ):
        """
        Initialize the runner.
        
        Args:
            session_manager: Session manager instance
            concierge: Concierge agent instance
        """
        self.session_manager = session_manager
        self.concierge = concierge
    
    async def run_query(
        self,
        query: str,
        user_id: str = "default_user"
    ) -> str:
        """
        Execute a query and return the response.
        
        Args:
            query: User query text
            user_id: User identifier
        
        Returns:
            Agent response text
        """
        # Get or create session
        session = await self.session_manager.get_or_create_session(user_id)
        
        # Get query number
        query_num = self.session_manager.get_query_count(user_id) + 1
        
        # Create Opik query span
        query_span = self.session_manager.create_query_span(user_id, query, query_num)
        
        try:
            # Execute query
            response = await self._execute_query(session, query)
            
            # Track query in conversation
            self.session_manager.add_query_to_conversation(user_id, query, response)
            
            # Update span with output
            if query_span:
                try:
                    query_span.update(
                        output={
                            "response": response,
                            "success": True
                        }
                    )
                except Exception as e:
                    print(f"Could not update query span: {e}")
            
            return response
            
        except Exception as e:
            # Update span with error
            if query_span:
                try:
                    query_span.update(
                        output={
                            "error": str(e),
                            "success": False
                        }
                    )
                except Exception as update_error:
                    print(f"Could not update query span with error: {update_error}")
            
            raise e
    
    async def _execute_query(self, session, query: str) -> str:
        """
        Execute query against concierge agent.
        
        Args:
            session: ADK session object
            query: User query text
        
        Returns:
            Agent response text
        """
        # Execute query using ADK's run_query method
        # This is where the actual agent execution happens
        from google.adk import run_query as adk_run_query
        
        result = await adk_run_query(
            agent=self.concierge,
            query=query,
            session=session
        )
        
        return result
    
    async def run_interactive(self, user_id: str = "default_user"):
        """
        Run in interactive mode (CLI).
        
        Args:
            user_id: User identifier
        """
        print("AI Travel Planner - Interactive Mode")
        print("Type 'exit' or 'quit' to end the conversation")
        print("-" * 50)
        
        while True:
            try:
                # Get user input
                query = input("\nYou: ").strip()
                
                # Check for exit
                if query.lower() in ['exit', 'quit']:
                    print("Ending conversation. Goodbye!")
                    self.session_manager.end_conversation(user_id, "user_exit")
                    break
                
                # Check for new conversation
                if query.lower() == 'new':
                    print("Starting new conversation...")
                    await self.session_manager.create_new_session(user_id)
                    continue
                
                # Execute query
                response = await self.run_query(query, user_id)
                
                # Display response
                print(f"\nAssistant: {response}")
                
            except KeyboardInterrupt:
                print("\n\nEnding conversation. Goodbye!")
                self.session_manager.end_conversation(user_id, "user_interrupt")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again.")
```

## Setting Up Opik

### 1. Install Opik

```bash
pip install opik
```

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Opik Configuration
OPIK_API_KEY=your_opik_api_key_here
OPIK_PROJECT_NAME=AI Travel Planner
OPIK_WORKSPACE=your_workspace_name
```

### 3. Initialize Opik Project

```bash
# Create a new project in Opik dashboard
# Or use existing project
```

## Testing Opik Integration

To test Opik integration, use the web interface:

1. Start the web server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Ask a question in the chat interface, for example:
   - "I want to plan a trip to Paris in March 2025"

4. Check your Opik dashboard to view the traces and spans:
   - Navigate to your Opik dashboard
   - Look for the "travel_conversation" trace
   - Click on the trace to see the query spans
   - Verify that the trace contains the correct metadata (user_id, session_id, conversation_id)

Expected behavior:
- A conversation trace is created when the first query is sent
- A query span is created for each query
- The trace contains metadata including user_id, session_id, and conversation_id
- The query spans contain the query text and response
- The trace is ended when the conversation ends (e.g., when the user closes the browser or after a timeout)

## Viewing Traces in Opik Dashboard

### 1. Navigate to Opik Dashboard

Open your browser and navigate to your Opik dashboard.

### 2. View Traces

You'll see a list of traces with:

- **Trace Name**: e.g., "travel_conversation"
- **User ID**: e.g., "test_user"
- **Conversation ID**: e.g., "conv_def456"
- **Timestamp**: When the conversation started
- **Duration**: How long the conversation lasted
- **Total Queries**: Number of queries in the conversation

### 3. View Trace Details

Click on a trace to see:

- **Input**: Initial conversation data
- **Output**: Final conversation data
- **Metadata**: Additional context (user_id, session_id, etc.)
- **Spans**: All query spans in the conversation

### 4. View Query Spans

Click on a query span to see:

- **Query**: The user's query text
- **Response**: The agent's response
- **Timing**: How long the query took
- **Metadata**: Query number, agent used, etc.

### 5. Search and Filter

Use the search and filter options to:

- Search by user ID
- Filter by date range
- Filter by tags
- Filter by metadata

## Observability Best Practices

### 1. Meaningful Names

```python
# Good
trace = self.opik_client.trace(
    name="travel_conversation",
    # ...
)

span = trace.span(
    name=f"user_query_{query_num}",
    # ...
)

# Bad
trace = self.opik_client.trace(
    name="trace_1",
    # ...
)
```

### 2. Rich Metadata

```python
# Good
trace = self.opik_client.trace(
    name="travel_conversation",
    metadata={
        "conversation_id": conversation_id,
        "user_id": user_id,
        "session_id": session_id,
        "app": self.app_name,
        "destination": "Paris",
        "budget": 1500,
        "dates": "2025-03-15 to 2025-03-18"
    }
)

# Bad
trace = self.opik_client.trace(
    name="travel_conversation",
    metadata={}
)
```

### 3. Input/Output Tracking

```python
# Good
span = trace.span(
    name=f"user_query_{query_num}",
    input={
        "query": query,
        "query_num": query_num,
        "user_id": user_id
    },
    output={
        "response": response,
        "success": True,
        "response_length": len(response)
    }
)

# Bad
span = trace.span(
    name=f"user_query_{query_num}",
    input={},
    output={}
)
```

### 4. Error Handling

```python
try:
    # Execute operation
    result = await some_operation()
    
    # Update span with success
    span.update(
        output={"result": result, "success": True}
    )
except Exception as e:
    # Update span with error
    span.update(
        output={"error": str(e), "success": False}
    )
    raise e
```

### 5. Proper Span Lifecycle

```python
# Create span
span = trace.span(name="operation")

try:
    # Do work
    result = do_work()
    
    # Update span
    span.update(output={"result": result})
    
finally:
    # End span
    span.end()
```

## Production Considerations

### 1. Sampling

```python
# Sample only a percentage of traces
import random

if random.random() < 0.1:  # 10% sampling
    trace = self.opik_client.trace(...)
```

### 2. Rate Limiting

```python
# Limit trace creation rate
from ratelimit import limits

@limits(calls=100, period=60)
def create_trace(...):
    return self.opik_client.trace(...)
```

### 3. Async Error Handling

```python
# Handle Opik errors gracefully
try:
    trace = self.opik_client.trace(...)
except Exception as e:
    print(f"Could not create Opik trace: {e}")
    # Continue without Opik
```

### 4. Data Privacy

```python
# Sanitize sensitive data before sending to Opik
import re

def sanitize_query(query):
    # Remove emails, phone numbers, etc.
    query = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', query)
    query = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', query)
    return query
```

## Common Issues

### Issue: Opik Not Available

**Symptoms**:
```
Could not initialize Opik client: ...
```

**Solution**: Check your `OPIK_API_KEY` environment variable.

### Issue: Trace Not Created

**Symptoms**:
```
Opik trace not created
```

**Solution**: Ensure Opik client is initialized and API key is valid.

### Issue: Span Not Updated

**Symptoms**:
```
Could not update query span: ...
```

**Solution**: Ensure span is created before updating, and handle errors gracefully.

## What's Next?

Congratulations! You've added observability with Opik. In Part 10, we'll run and test our complete agent.

## Summary

In this part, we:
- Integrated Opik observability into our system
- Created conversation traces for entire workflows
- Created query spans for individual operations
- Updated Runner to use Opik spans
- Set up Opik configuration
- Created test scripts to verify functionality
- Learned observability best practices
- Discussed production considerations

## Key Takeaways

1. **Observability is critical**: Essential for debugging and monitoring
2. **Traces track workflows**: Entire conversations in one place
3. **Spans track operations**: Individual steps within workflows
4. **Rich metadata helps**: More context = better debugging
5. **Error handling matters**: Opik errors shouldn't break the system

## Resources

- [Opik Documentation](https://www.comet.com/site/products/opik/)
- [Observability Best Practices](https://www.comet.com/site/docs/opik/)
- [Distributed Tracing](https://opentelemetry.io/docs/concepts/observability-primer/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

---

Continue to Part 10: Running and Testing Agent
