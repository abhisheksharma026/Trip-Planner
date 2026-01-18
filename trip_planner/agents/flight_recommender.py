"""
Flight Recommender Agent - Specialized agent for finding flight options.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from trip_planner.tools import get_city_coordinates, search_flight_prices
from trip_planner.config import get_model_name


class FlightRecommenderAgent:
    """Specialized agent focused solely on finding and recommending flight options."""
    
    def __init__(self):
        # Create a search agent wrapper to make google_search a callable
        # This ensures all tools are callables (homogeneous tools list)
        search_agent = Agent(
            name="flight_search_helper",
            model=get_model_name(),
            description="Helper agent for searching flight information.",
            instruction="Use google_search to find flight options, prices, and booking information. Always cite sources.",
            tools=[google_search]
        )
        
        # Create a callable wrapper for the search agent
        async def search_flights(query: str, tool_context=None):
            """
            Search for flight information using web search.
            
            Args:
                query: The search query for flights
            """
            agent_tool = AgentTool(agent=search_agent)
            return await agent_tool.run_async(
                args={"request": query},
                tool_context=tool_context
            )
        
        self.agent = Agent(
            name="flight_recommender",
            model=get_model_name(),
            description="Specialized agent focused solely on finding and recommending flight options based on origin, destination, dates, and preferences.",
            instruction="""
            You are the Flight Recommender, a specialist in finding the best flight options.
            
            Your Responsibilities:
            1. Search for flight options using the search_flights tool based on:
               - Origin and destination cities
               - Departure and return dates
               - Budget constraints
               - User preferences (direct flights, airline preferences, layover tolerance)
            
            2. When exact dates are provided, ALWAYS call `search_flight_prices` to fetch live-priced options.
               - Use date_flex_days (default 2) to surface a flex option (±N days)
               - Compare exact-date best vs. flex best and state the price delta (e.g., "$120 cheaper if you leave Tuesday instead of Monday")
               - Provide airline, flight number, duration, and stop count
               - Use web search (`search_flights`) only as a fallback or for qualitative context

            3. Present flight options with:
               - Airline names and flight numbers
               - Departure and arrival times
               - Duration and layover information
               - Live prices (from Amadeus when available)
               - Links to booking sites or guidance on where to book
            
            3. Always cite your sources (Expedia, Kayak, Google Flights, etc.)
            
            4. If the user mentions disliking long layovers, remember this preference.
            
            Return your recommendations in a clear, structured format with prices.
            """,
            tools=[search_flight_prices, search_flights, get_city_coordinates]  # All callables
        )
    
    def get_agent(self):
        """Get the underlying ADK Agent instance."""
        return self.agent

