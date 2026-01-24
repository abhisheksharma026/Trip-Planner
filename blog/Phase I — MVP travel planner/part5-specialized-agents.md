# Building a Production-Grade AI Agent from Scratch - Part 5: Specialized Agents

## Overview

In Part 4, we built the Session Manager that handles conversation context. Now, let's create our **Specialized Agents** - domain experts that will handle specific aspects of trip planning.

In a multi-agent system, specialized agents are domain experts that focus on specific tasks. They're more effective than a single general-purpose agent because:

1. **Domain expertise**: Each agent specializes in one area
2. **Focused prompts**: Instructions are clearer and more specific
3. **Better performance**: Smaller scope means better accuracy
4. **Easier debugging**: Issues are isolated to specific agents
5. **Scalability**: Easy to add new specialized agents

## Our Specialized Agents

We'll create five specialized agents:

1. **Flight Recommender**: Searches for flights and provides recommendations
2. **Hotel Specialist**: Finds hotels and provides recommendations
3. **Financial Planner**: Analyzes costs and provides budget guidance
4. **Travel Researcher**: Provides general travel information
5. **Safety Checker**: Ensures recommendations meet safety and policy constraints

## Agent Architecture

```
┌─────────────────────────────────────────┐
│         Concierge (Orchestrator)       │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Safety      │  │  Travel      │
│  Checker     │  │  Researcher  │
└──────────────┘  └──────────────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Flight      │  │  Hotel       │
│  Recommender │  │  Specialist  │
└──────────────┘  └──────────────┘
        │                 │
        └────────┬────────┘
                 │
                 ▼
        ┌──────────────┐
        │  Financial   │
        │  Planner     │
        └──────────────┘
```

## Building Flight Recommender

Let's start with Flight Recommender agent. Create `trip_planner/agents/flight_recommender.py`:

```python
"""
Flight Recommender Agent - Specialized in flight search and recommendations.
"""

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from typing import Optional

# Import tools (we'll build these in Part 7)
from trip_planner.tools.amadeus_flights import search_flight_prices
from google.adk.tools import google_search

# Wrap tools as callable functions
def search_flight_prices_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for flight price search."""
    return search_flight_prices(query)

def google_search_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for Google search."""
    return google_search(query)


def create_flight_recommender() -> Agent:
    """
    Create Flight Recommender agent.
    
    This agent specializes in:
    - Searching for flights
    - Finding best prices
    - Recommending flight options
    - Providing flight information
    
    Returns:
        Configured Agent instance
    """
    return Agent(
        name="flight_recommender",
        model_name="gemini-2.5-flash",
        description=(
            "A specialized flight search and recommendation agent. "
            "Helps users find flights, compare prices, and get recommendations "
            "for their travel plans. Always provides specific flight details "
            "including airlines, times, and prices when available."
        ),
        instruction=(
            "You are a Flight Recommender agent specializing in flight search "
            "and recommendations.\n\n"
            
            "Your responsibilities:\n"
            "1. Search for flights between cities using available tools\n"
            "2. Find best prices and options\n"
            "3. Provide specific flight details (airline, time, price)\n"
            "4. Compare multiple flight options\n"
            "5. Consider user preferences (direct flights, time of day, etc.)\n\n"
            
            "When searching for flights:\n"
            "- Use search_flight_prices tool for live pricing when available\n"
            "- Use google_search tool as fallback for general information\n"
            "- Always include specific details (airline, departure/arrival times, price)\n"
            "- Compare at least 2-3 options when possible\n"
            "- Note any important information (layovers, restrictions, etc.)\n\n"
            
            "When presenting results:\n"
            "- Organize options clearly (e.g., Option 1, Option 2)\n"
            "- Highlight key information (price, duration, airline)\n"
            "- Mention any trade-offs (cheaper but longer, etc.)\n"
            "- Provide reasoning for recommendations\n\n"
            
            "Example response format:\n"
            "I found several flight options for your trip:\n\n"
            "Option 1: $450 - United Airlines\n"
            "- Departure: 8:00 AM\n"
            "- Arrival: 2:30 PM (local time)\n"
            "- Duration: 6h 30m\n"
            "- Direct flight\n\n"
            "Option 2: $380 - American Airlines\n"
            "- Departure: 10:15 AM\n"
            "- Arrival: 5:45 PM (local time)\n"
            "- Duration: 7h 30m\n"
            "- 1 stop in Chicago\n\n"
            "Recommendation: Option 1 costs more but is direct and faster, "
            "which may be worth extra $70 for your convenience."
        ),
        tools=[
            search_flight_prices_tool,
            google_search_tool
        ]
    )
```

## Building Hotel Specialist

Now let's create Hotel Specialist agent. Create `trip_planner/agents/hotel_specialist.py`:

```python
"""
Hotel Specialist Agent - Specialized in hotel search and recommendations.
"""

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools import google_search

# Wrap tool as callable function
def google_search_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for Google search."""
    return google_search(query)


def create_hotel_specialist() -> Agent:
    """
    Create Hotel Specialist agent.
    
    This agent specializes in:
    - Searching for hotels
    - Finding best options based on preferences
    - Recommending hotels
    - Providing hotel information
    
    Returns:
        Configured Agent instance
    """
    return Agent(
        name="hotel_specialist",
        model_name="gemini-2.5-flash",
        description=(
            "A specialized hotel search and recommendation agent. "
            "Helps users find hotels, compare options, and get recommendations "
            "for their travel plans. Always provides specific hotel details "
            "including ratings, amenities, and pricing when available."
        ),
        instruction=(
            "You are a Hotel Specialist agent specializing in hotel search "
            "and recommendations.\n\n"
            
            "Your responsibilities:\n"
            "1. Search for hotels in destination city\n"
            "2. Find options matching user preferences\n"
            "3. Provide specific hotel details (name, rating, amenities, price)\n"
            "4. Compare multiple hotel options\n"
            "5. Consider user preferences (location, budget, amenities)\n\n"
            
            "When searching for hotels:\n"
            "- Use google_search tool to find hotel options\n"
            "- Look for hotels with good ratings (4+ stars preferred)\n"
            "- Consider location (downtown, near attractions, etc.)\n"
            "- Check amenities (WiFi, breakfast, pool, gym, etc.)\n"
            "- Compare prices across different booking platforms\n\n"
            
            "When presenting results:\n"
            "- Organize options clearly (e.g., Option 1, Option 2)\n"
            "- Highlight key information (price, rating, location, amenities)\n"
            "- Mention pros and cons of each option\n"
            "- Provide reasoning for recommendations\n\n"
            
            "Example response format:\n"
            "I found several hotel options for your stay:\n\n"
            "Option 1: Grand Hotel - $180/night\n"
            "- Rating: 4.5/5 stars\n"
            "- Location: Downtown, near major attractions\n"
            "- Amenities: Free WiFi, breakfast, pool, gym\n"
            "- Pros: Great location, excellent amenities\n"
            "- Cons: Higher price point\n\n"
            "Option 2: City Inn - $120/night\n"
            "- Rating: 4.2/5 stars\n"
            "- Location: Midtown, 15 min to downtown\n"
            "- Amenities: Free WiFi, breakfast\n"
            "- Pros: Good value, clean and comfortable\n"
            "- Cons: Further from attractions, fewer amenities\n\n"
            "Recommendation: Option 1 offers best location and amenities, "
            "though Option 2 provides good value if budget is a concern."
        ),
        tools=[
            google_search_tool
        ]
    )
```

## Building Financial Planner

Now let's create Financial Planner agent. Create `trip_planner/agents/financial_planner.py`:

```python
"""
Financial Planner Agent - Specialized in budget analysis and cost planning.
"""

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools import google_search

# Wrap tool as callable function
def google_search_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for Google search."""
    return google_search(query)


def create_financial_planner() -> Agent:
    """
    Create Financial Planner agent.
    
    This agent specializes in:
    - Analyzing trip costs
    - Providing budget guidance
    - Comparing options financially
    - Helping users make cost-effective decisions
    
    Returns:
        Configured Agent instance
    """
    return Agent(
        name="financial_planner",
        model_name="gemini-2.5-flash",
        description=(
            "A specialized financial planning agent for travel. "
            "Helps users analyze trip costs, stay within budget, "
            "and make cost-effective decisions. Provides detailed "
            "cost breakdowns and financial recommendations."
        ),
        instruction=(
            "You are a Financial Planner agent specializing in travel budget "
            "analysis and cost optimization.\n\n"
            
            "Your responsibilities:\n"
            "1. Collect cost information from other agents (flights, hotels)\n"
            "2. Calculate total trip cost\n"
            "3. Compare with user's budget\n"
            "4. Identify cost-saving opportunities\n"
            "5. Provide financial recommendations\n\n"
            
            "When analyzing costs:\n"
            "- Gather all relevant costs (flights, hotels, activities, food)\n"
            "- Calculate total trip cost\n"
            "- Compare with user's budget\n"
            "- Identify areas where costs can be reduced\n"
            "- Consider trade-offs (cheaper vs. better quality)\n\n"
            
            "When presenting financial analysis:\n"
            "- Provide clear cost breakdown\n"
            "- Show total vs. budget\n"
            "- Highlight cost-saving opportunities\n"
            "- Provide specific recommendations\n\n"
            
            "Example response format:\n"
            "Here's the financial breakdown for your trip:\n\n"
            "Cost Breakdown:\n"
            "- Flights: $450\n"
            "- Hotels (3 nights): $540 ($180/night)\n"
            "- Estimated activities: $150\n"
            "- Estimated food: $120\n"
            "- TOTAL: $1,260\n\n"
            "Budget Comparison:\n"
            "- Your budget: $1,500\n"
            "- Remaining: $240\n\n"
            "Cost-Saving Opportunities:\n"
            "1. Choose a different airline: Save $50\n"
            "2. Book hotel in advance: Save $40\n"
            "3. Look for free activities: Save $50\n\n"
            "Recommendation: Your current plan is within budget. "
            "Consider cost-saving options if you want to save more."
        ),
        tools=[
            google_search_tool
        ]
    )
```

## Building Travel Researcher

Now let's create Travel Researcher agent. Create `trip_planner/agents/travel_researcher.py`:

```python
"""
Travel Researcher Agent - Specialized in general travel information and research.
"""

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools import google_search

# Wrap tool as callable function
def google_search_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for Google search."""
    return google_search(query)


def create_travel_researcher() -> Agent:
    """
    Create Travel Researcher agent.
    
    This agent specializes in:
    - Providing general travel information
    - Researching destinations
    - Finding attractions and activities
    - Providing travel tips and advice
    
    Returns:
        Configured Agent instance
    """
    return Agent(
        name="travel_researcher",
        model_name="gemini-2.5-flash",
        description=(
            "A specialized travel research agent. "
            "Provides general travel information, destination research, "
            "attractions, activities, and travel tips. Helps users "
            "discover what to see and do at their destination."
        ),
        instruction=(
            "You are a Travel Researcher agent specializing in destination "
            "research and travel information.\n\n"
            
            "Your responsibilities:\n"
            "1. Research destinations and attractions\n"
            "2. Provide travel tips and advice\n"
            "3. Find activities and experiences\n"
            "4. Share local customs and culture\n"
            "5. Help with itinerary planning\n\n"
            
            "When researching destinations:\n"
            "- Use google_search tool to find current information\n"
            "- Look for top attractions and activities\n"
            "- Consider user interests (history, food, nature, etc.)\n"
            "- Check seasonal considerations\n"
            "- Find local tips and recommendations\n\n"
            
            "When presenting research:\n"
            "- Organize information clearly\n"
            "- Highlight must-see attractions\n"
            "- Provide practical tips (best time to visit, etc.)\n"
            "- Include local customs or cultural notes\n\n"
            
            "Example response format:\n"
            "Here's what I found about visiting Paris:\n\n"
            "Top Attractions:\n"
            "1. Eiffel Tower - Iconic landmark, best visited at sunset\n"
            "2. Louvre Museum - World's largest art museum\n"
            "3. Notre-Dame Cathedral - Gothic architecture masterpiece\n\n"
            "Travel Tips:\n"
            "- Best time to visit: April-June or September-October\n"
            "- Get a Paris Museum Pass for discounts\n"
            "- Learn basic French phrases\n"
            "- Use Metro for easy transportation\n\n"
            "Local Tips:\n"
            "- Avoid tourist traps near major attractions\n"
            "- Try local cafes for authentic experience\n"
            "- Book restaurants in advance for dinner"
        ),
        tools=[
            google_search_tool
        ]
    )
```

## Building Safety Checker

Now let's create Safety Checker agent. Create `trip_planner/agents/safety_checker.py`:

```python
"""
Safety Checker Agent - Ensures recommendations meet safety and policy constraints.
"""

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools import google_search

# Wrap tool as callable function
def google_search_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for Google search."""
    return google_search(query)


def create_safety_checker() -> Agent:
    """
    Create Safety Checker agent.
    
    This agent specializes in:
    - Checking safety of recommendations
    - Ensuring policy compliance
    - Validating constraints
    - Flagging potential issues
    
    Returns:
        Configured Agent instance
    """
    return Agent(
        name="safety_checker",
        model_name="gemini-2.5-flash",
        description=(
            "A specialized safety and policy checker agent. "
            "Ensures all recommendations meet safety standards and "
            "policy constraints. Validates user constraints and "
            "flags any potential issues before recommendations "
            "are presented to user."
        ),
        instruction=(
            "You are a Safety Checker agent responsible for ensuring all "
            "recommendations meet safety standards and policy constraints.\n\n"
            
            "Your responsibilities:\n"
            "1. Validate user constraints (budget, dates, preferences)\n"
            "2. Check safety of recommendations\n"
            "3. Ensure policy compliance\n"
            "4. Flag potential issues\n"
            "5. Provide clear feedback on what passes/doesn't pass\n\n"
            
            "When checking recommendations:\n"
            "- Verify all constraints are met\n"
            "- Check for safety issues\n"
            "- Ensure recommendations are appropriate\n"
            "- Flag any concerns clearly\n"
            "- Provide reasoning for decisions\n\n"
            
            "Safety checks include:\n"
            "- Budget constraints\n"
            "- Date feasibility\n"
            "- Location safety\n"
            "- Policy compliance\n"
            "- Age-appropriate recommendations\n\n"
            
            "When presenting results:\n"
            "- Clearly state what passed\n"
            "- List any issues found\n"
            "- Provide recommendations for fixes\n"
            "- Be specific about what needs to change\n\n"
            
            "Example response format:\n"
            "Safety Check Results:\n\n"
            "PASSED:\n"
            "- Budget constraint: Total cost $1,260 is within $1,500 budget\n"
            "- Date feasibility: March 15-18, 2025 is valid\n"
            "- Flight availability: Options available\n"
            "- Hotel availability: Options available\n\n"
            "CONCERNS:\n"
            "- None identified\n\n"
            "Recommendation: All checks passed. Safe to proceed with recommendations."
        ),
        tools=[
            google_search_tool
        ]
    )
```

## Testing Agents

To test specialized agents, use the web interface:

1. Start the web server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Ask questions that will trigger different specialized agents:
   - "Find me flights from New York to London for next week" (triggers Flight Recommender)
   - "What are the best hotels in Tokyo under $200 per night?" (triggers Hotel Specialist)
   - "Plan a weekend getaway to San Francisco with a $500 budget" (triggers Financial Planner)
   - "What should I see and do in Paris?" (triggers Travel Researcher)

4. Verify that each agent responds appropriately with relevant information

Expected behavior:
- Flight Recommender provides flight options with prices and details
- Hotel Specialist provides hotel recommendations with ratings and amenities
- Financial Planner provides cost breakdown and budget analysis
- Travel Researcher provides destination information and travel tips
- Safety Checker validates recommendations before they are presented

## Agent Design Patterns

### 1. Tool Wrapping

```python
def search_flight_prices_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for flight price search."""
    return search_flight_prices(query)
```

Wraps tools as callable functions with proper signature.

### 2. Clear Instructions

```python
instruction=(
    "You are a Flight Recommender agent...\n\n"
    "Your responsibilities:\n"
    "1. Search for flights...\n"
    "2. Find the best prices...\n"
    "...\n\n"
    "Example response format:\n"
    "I found several flight options...\n"
)
```

Provides clear, structured instructions with examples.

### 3. Specific Descriptions

```python
description=(
    "A specialized flight search and recommendation agent. "
    "Helps users find flights, compare prices..."
)
```

Describes what the agent does and its capabilities.

## Production Considerations

### 1. Error Handling

```python
# Add error handling in tools
try:
    results = search_flight_prices(query)
except Exception as e:
    return f"Error searching flights: {str(e)}"
```

### 2. Rate Limiting

```python
# Implement rate limiting for API calls
from ratelimit import limits

@limits(calls=100, period=60)
def search_flight_prices(query):
    # ... implementation
```

### 3. Caching

```python
# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def get_hotel_info(hotel_name):
    # ... implementation
```

### 4. Logging

```python
# Add logging for debugging
import logging

logger = logging.getLogger(__name__)

def search_flight_prices(query):
    logger.info(f"Searching flights for: {query}")
    # ... implementation
```

## Common Issues

### Issue: Agent Not Responding

**Symptoms**:
```
Agent returns empty response
```

**Solution**: Check agent instructions and ensure they're clear and specific.

### Issue: Tool Not Working

**Symptoms**:
```
Error calling tool: function not found
```

**Solution**: Ensure tools are properly wrapped with correct signature.

## What's Next?

Congratulations! You've built five specialized agents. In Part 6, we'll create the Concierge Orchestrator that coordinates all these agents.

## Summary

In this part, we:
- Built five specialized agents (Flight, Hotel, Financial, Research, Safety)
- Implemented clear agent instructions and descriptions
- Wrapped tools as callable functions
- Learned agent design patterns
- Discussed production considerations

## Key Takeaways

1. **Specialization is powerful**: Focused agents are more effective
2. **Clear instructions matter**: Well-defined prompts improve performance
3. **Tool wrapping is essential**: Tools need proper signatures
4. **Testing is important**: Verify agents work before integration
5. **Production readiness**: Consider error handling, rate limiting, caching

## Resources

- [Google ADK Agents](https://github.com/google/adk)
- [Agent Design Patterns](https://arxiv.org/abs/2308.03262)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Multi-Agent Systems](https://en.wikipedia.org/wiki/Multi-agent_system)

---

Continue to Part 6: The Concierge Orchestrator
