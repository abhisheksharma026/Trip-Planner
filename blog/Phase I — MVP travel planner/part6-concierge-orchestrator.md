# Building a Production-Grade AI Agent from Scratch - Part 6: The Concierge Orchestrator

## Overview

In Part 5, we built our specialized agents (Flight, Hotel, Financial, Research, Safety). Now, let's create the **Concierge Orchestrator** - the root agent that coordinates all specialized agents to provide a seamless user experience.

The Concierge is the brain of our multi-agent system. It's the only agent that users interact with directly. It:

1. **Understands user intent**: Parses user queries and determines what's needed
2. **Delegates to specialists**: Routes requests to appropriate specialized agents
3. **Coordinates workflows**: Manages multi-step processes
4. **Ensures safety**: Checks constraints before making recommendations
5. **Provides explanations**: Explains reasoning behind recommendations

## Concierge Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│         Concierge Orchestrator       │
│  ┌─────────────────────────────────────┐  │
│  │  Intent Understanding              │  │
│  │  - Parse user query                 │  │
│  │  - Extract constraints              │  │
│  │  - Identify needs                   │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Safety First Workflow              │  │
│  │  1. Check constraints               │  │
│  │  2. Validate feasibility            │  │
│  │  3. Get recommendations              │  │
│  │  4. Verify safety                   │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Agent Coordination                 │  │
│  │  - Route to Flight Recommender      │  │
│  │  - Route to Hotel Specialist        │  │
│  │  - Route to Financial Planner       │  │
│  │  - Route to Travel Researcher       │  │
│  │  - Route to Safety Checker          │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Response Generation                │  │
│  │  - Synthesize recommendations       │  │
│  │  - Provide explanations             │  │
│  │  - Offer follow-up options          │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
    │
    ▼
Response to User
```

## Building the Concierge

Let's create the Concierge agent. Create `trip_planner/agents/concierge.py`:

```python
"""
Concierge Agent - Root orchestrator that coordinates all specialized agents.
"""

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from typing import Optional

# Import specialized agents
from trip_planner.agents.flight_recommender import create_flight_recommender
from trip_planner.agents.hotel_specialist import create_hotel_specialist
from trip_planner.agents.financial_planner import create_financial_planner
from trip_planner.agents.travel_researcher import create_travel_researcher
from trip_planner.agents.safety_checker import create_safety_checker

# Import tools
from trip_planner.tools.export import export_itinerary
from google.adk.tools import google_search

# Wrap tools as callable functions
def export_itinerary_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for itinerary export."""
    return export_itinerary(query)

def google_search_tool(query: str, context: ToolContext) -> str:
    """Tool wrapper for Google search."""
    return google_search(query)


def create_concierge() -> Agent:
    """
    Create the Concierge agent - root orchestrator.
    
    This agent:
    - Coordinates all specialized agents
    - Manages safety-first workflow
    - Handles what-if scenarios
    - Provides explanations and reasoning
    - Ensures all recommendations meet constraints
    
    Returns:
        Configured Agent instance
    """
    return Agent(
        name="concierge",
        model_name="gemini-2.5-flash",
        description=(
            "A helpful travel concierge agent that coordinates specialized "
            "agents to help users plan trips. Follows a safety-first approach, "
            "checking constraints before making recommendations. Provides "
            "clear explanations and reasoning for all recommendations."
        ),
        instruction=(
            "You are a helpful travel concierge agent that coordinates "
            "specialized agents to help users plan their trips.\n\n"
            
            "Your approach:\n"
            "1. Always follow a safety-first workflow\n"
            "2. Check constraints before making recommendations\n"
            "3. Provide clear explanations and reasoning\n"
            "4. Handle what-if scenarios gracefully\n"
            "5. Offer helpful follow-up options\n\n"
            
            "Safety-First Workflow:\n"
            "When a user asks for recommendations:\n"
            "1. First, check their constraints (budget, dates, preferences)\n"
            "2. Validate that constraints are reasonable and feasible\n"
            "3. Get recommendations from specialized agents\n"
            "4. Verify recommendations meet all constraints\n"
            "5. Only then present recommendations to the user\n\n"
            
            "Constraint Checking:\n"
            "Always check:\n"
            "- Budget: Is it reasonable for the trip?\n"
            "- Dates: Are they valid and feasible?\n"
            "- Preferences: Are they clear and achievable?\n"
            "- Location: Is it safe and accessible?\n\n"
            
            "When constraints are unclear:\n"
            "Ask clarifying questions:\n"
            "- What's your budget for this trip?\n"
            "- When are you planning to travel?\n"
            "- How many people will be traveling?\n"
            "- What type of experience are you looking for?\n"
            "- Any specific preferences or requirements?\n\n"
            
            "When constraints are violated:\n"
            "Politely explain the issue:\n"
            "- Your budget of $500 for a week in Paris may not be realistic\n"
            "- March 15-18, 2025 is only 3 days, not a week\n"
            "- Direct flights to your destination may not be available\n"
            "Then suggest alternatives:\n"
            "- Consider increasing your budget to $1,000\n"
            "- Extend your dates to March 15-22\n"
            "- Consider connecting flights which are often cheaper\n\n"
            
            "Getting Recommendations:\n"
            "After validating constraints:\n"
            "1. Route to Flight Recommender for flight options\n"
            "2. Route to Hotel Specialist for hotel options\n"
            "3. Route to Travel Researcher for destination information\n"
            "4. Route to Financial Planner for cost analysis\n"
            "5. Route to Safety Checker to verify recommendations\n\n"
            
            "Presenting Recommendations:\n"
            "Always provide:\n"
            "- Clear, organized options\n"
            "- Specific details (prices, times, ratings)\n"
            "- Reasoning behind recommendations\n"
            "- Trade-offs between options\n"
            "- Total cost breakdown\n\n"
            
            "Example response format:\n"
            "Based on your constraints (budget: $1,500, dates: March 15-18, 2025), "
            "I've found some great options:\n\n"
            "Flight Options:\n"
            "Option 1: $450 - United Airlines, Direct, 6h 30m\n"
            "Option 2: $380 - American Airlines, 1 stop, 7h 30m\n\n"
            "Hotel Options:\n"
            "Option 1: $180/night - Grand Hotel, 4.5 stars, Downtown\n"
            "Option 2: $120/night - City Inn, 4.2 stars, Midtown\n\n"
            "Total Cost:\n"
            "- Flights: $450\n"
            "- Hotels (3 nights): $540\n"
            "- Estimated activities: $150\n"
            "- Estimated food: $120\n"
            "- TOTAL: $1,260 (within your $1,500 budget)\n\n"
            "Recommendation:\n"
            "I recommend Option 1 for flights (direct is worth the extra $70) "
            "and Option 1 for hotels (excellent location and amenities). "
            "This gives you a great experience while staying within budget.\n\n"
            "Would you like me to:\n"
            "- Adjust any of these options?\n"
            "- Get more information about any option?\n"
            "- Export this itinerary?\n"
            "- Help with anything else?\n\n"
            
            "What-If Scenarios:\n"
            "When users ask what-if questions:\n"
            "- What if I increase my budget to $2,000?\n"
            "- What if I travel in April instead of March?\n"
            "- What if I want a direct flight only?\n"
            "Always:\n"
            "- Acknowledge the change\n"
            "- Re-check constraints\n"
            "- Get new recommendations\n"
            "- Compare with previous options\n"
            "- Explain the impact of the change\n\n"
            
            "Example what-if response:\n"
            "If you increase your budget to $2,000:\n\n"
            "New Options:\n"
            "- Flights: $550 (business class upgrade available)\n"
            "- Hotels: $250/night (luxury hotel option)\n"
            "- Activities: $250 (premium experiences)\n"
            "- Food: $180 (fine dining options)\n"
            "- NEW TOTAL: $1,730\n\n"
            "Comparison:\n"
            "- Previous total: $1,260\n"
            "- New total: $1,730\n"
            "- Difference: +$470\n\n"
            "With the higher budget, you get:\n"
            "- Better flight options (business class)\n"
            "- Luxury hotel with spa and amenities\n"
            "- Premium activities and experiences\n"
            "- Fine dining options\n\n"
            "Would you like to proceed with these options, or would you prefer "
            "to stick with the original recommendations?\n\n"
            
            "Exporting Itineraries:\n"
            "When users want to save their itinerary:\n"
            "- Use the export_itinerary tool\n"
            "- Provide the file location\n"
            "- Confirm what was saved\n\n"
            
            "Example export response:\n"
            "I've exported your itinerary to: itineraries/trip_paris_march_2025.md\n\n"
            "The file includes:\n"
            "- Flight details\n"
            "- Hotel information\n"
            "- Cost breakdown\n"
            "- Activity suggestions\n"
            "- Travel tips\n\n"
            "You can open this file to review or share your itinerary.\n\n"
            
            "General Guidelines:\n"
            "- Always be helpful and polite\n"
            "- Provide clear, organized responses\n"
            "- Explain your reasoning\n"
            "- Offer follow-up options\n"
            "- Be proactive in suggesting next steps\n"
            "- Handle errors gracefully\n"
            "- Ask clarifying questions when needed\n"
            "- Never make up information\n"
            "- Use tools to get accurate information\n"
        ),
        sub_agents=[
            create_flight_recommender(),
            create_hotel_specialist(),
            create_financial_planner(),
            create_travel_researcher(),
            create_safety_checker()
        ],
        tools=[
            export_itinerary_tool,
            google_search_tool
        ]
    )
```

## Understanding the Concierge

### Key Components

#### 1. Sub-Agent Coordination

```python
sub_agents=[
    create_flight_recommender(),
    create_hotel_specialist(),
    create_financial_planner(),
    create_travel_researcher(),
    create_safety_checker()
]
```

The Concierge has access to all specialized agents and can route requests to them.

#### 2. Safety-First Workflow

```python
"1. First, check their constraints (budget, dates, preferences)\n"
"2. Validate that constraints are reasonable and feasible\n"
"3. Get recommendations from specialized agents\n"
"4. Verify recommendations meet all constraints\n"
"5. Only then present recommendations to the user\n"
```

Ensures all recommendations are safe and appropriate before presenting to users.

#### 3. What-If Scenarios

```python
"When users ask what-if questions:\n"
"- What if I increase my budget to $2,000?\n"
"- What if I travel in April instead of March?\n"
```

Handles hypothetical questions by recalculating with new constraints.

#### 4. Clear Explanations

```python
"Always provide:\n"
"- Clear, organized options\n"
"- Specific details (prices, times, ratings)\n"
"- Reasoning behind recommendations\n"
"- Trade-offs between options\n"
"- Total cost breakdown\n"
```

Provides transparency and helps users understand recommendations.

## Testing the Concierge

Let's create a test to verify the Concierge works:

```python
# test_concierge.py
"""
Test concierge agent functionality.
"""

import asyncio
from trip_planner.agents.concierge import create_concierge

async def test_concierge():
    print("=" * 60)
    print("Testing Concierge Agent")
    print("=" * 60)
    
    # Test 1: Create Concierge
    print("\n1. Creating Concierge agent...")
    concierge = create_concierge()
    print(f"   Name: {concierge.name}")
    print(f"   Model: {concierge.model_name}")
    print(f"   Sub-agents: {len(concierge.sub_agents)}")
    print(f"   Tools: {len(concierge.tools)}")
    print(f"   ✓ Concierge created")
    
    # Test 2: Verify sub-agents
    print("\n2. Verifying sub-agents...")
    for i, sub_agent in enumerate(concierge.sub_agents, 1):
        print(f"   {i}. {sub_agent.name}")
    print(f"   ✓ All {len(concierge.sub_agents)} sub-agents loaded")
    
    # Test 3: Verify tools
    print("\n3. Verifying tools...")
    print(f"   Tools available: {len(concierge.tools)}")
    print(f"   ✓ Tools loaded")
    
    print("\n" + "=" * 60)
    print("Concierge agent created successfully!")
    print("=" * 60)
    print("\nThe Concierge is ready to coordinate all specialized agents")
    print("and provide a seamless trip planning experience.")

if __name__ == "__main__":
    asyncio.run(test_concierge())
```

Run the test:

```bash
python test_concierge.py
```

Expected output:

```
============================================================
Testing Concierge Agent
============================================================

1. Creating Concierge agent...
   Name: concierge
   Model: gemini-2.5-flash
   Sub-agents: 5
   Tools: 2
   ✓ Concierge created

2. Verifying sub-agents...
   1. flight_recommender
   2. hotel_specialist
   3. financial_planner
   4. travel_researcher
   5. safety_checker
   ✓ All 5 sub-agents loaded

3. Verifying tools...
   Tools available: 2
   ✓ Tools loaded

============================================================
Concierge agent created successfully!
============================================================

The Concierge is ready to coordinate all specialized agents
and provide a seamless trip planning experience.
```

## Concierge Workflow Examples

### Example 1: Simple Trip Request

```
User: "I want to plan a trip to Paris in March 2025 with a $1,500 budget"

Concierge:
1. Parses intent: Trip planning to Paris, March 2025, $1,500 budget
2. Checks constraints: Budget reasonable, dates valid
3. Routes to Flight Recommender: Gets flight options
4. Routes to Hotel Specialist: Gets hotel options
5. Routes to Financial Planner: Calculates total cost
6. Routes to Safety Checker: Verifies all constraints met
7. Presents recommendations with explanations
```

### Example 2: What-If Scenario

```
User: "What if I increase my budget to $2,000?"

Concierge:
1. Acknowledges change: Budget increased to $2,000
2. Re-checks constraints: New budget reasonable
3. Gets new recommendations with higher budget
4. Compares with previous options
5. Explains impact: Better hotels, more activities
6. Presents new options with comparison
```

### Example 3: Constraint Violation

```
User: "I want to plan a week in Paris with a $500 budget"

Concierge:
1. Checks constraints: Budget too low for Paris
2. Identifies issue: $500 not realistic for week in Paris
3. Explains problem politely
4. Suggests alternatives:
   - Increase budget to $1,000-$1,500
   - Consider shorter trip
   - Consider cheaper destination
5. Offers to help with alternatives
```

## Production Considerations

### 1. Error Handling

```python
# Add error handling in instructions
"If an error occurs:\n"
"- Acknowledge the error\n"
"- Explain what happened\n"
"- Offer to try again\n"
"- Suggest alternative approaches\n"
```

### 2. Rate Limiting

```python
# Implement rate limiting for sub-agent calls
from ratelimit import limits

@limits(calls=10, period=60)
async def call_sub_agent(agent, query):
    # ... implementation
```

### 3. Caching

```python
# Cache frequent queries
from functools import lru_cache

@lru_cache(maxsize=50)
def get_cached_recommendations(query_hash):
    # ... implementation
```

### 4. Logging

```python
# Add comprehensive logging
import logging

logger = logging.getLogger(__name__)

def log_concierge_action(action, details):
    logger.info(f"Concierge: {action}", extra=details)
```

## Common Issues

### Issue: Concierge Not Routing

**Symptoms**:
```
Concierge doesn't call sub-agents
```

**Solution**: Check instructions and ensure routing logic is clear.

### Issue: Safety Checks Failing

**Symptoms**:
```
All recommendations rejected as unsafe
```

**Solution**: Review safety checker logic and adjust constraints.

## What's Next?

Congratulations! You've built the Concierge Orchestrator. In Part 7, we'll create the custom tools that our agents use.

## Summary

In this part, we:
- Built the Concierge orchestrator agent
- Implemented safety-first workflow
- Added what-if scenario handling
- Provided clear explanations and reasoning
- Created test scripts to verify functionality
- Learned coordination patterns
- Discussed production considerations

## Key Takeaways

1. **Coordination is key**: The Concierge orchestrates all specialized agents
2. **Safety first**: Always check constraints before presenting recommendations
3. **Clear explanations**: Users need to understand reasoning
4. **What-if scenarios**: Handle hypothetical questions gracefully
5. **Proactive suggestions**: Offer helpful follow-up options

## Resources

- [Google ADK Agents](https://github.com/google/adk)
- [Multi-Agent Coordination](https://arxiv.org/abs/2308.03262)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Orchestrator Pattern](https://www.enterpriseintegrationpatterns.com/patterns/messaging/Orchestrator.html)

---

Continue to Part 7: Creating Custom Tools
