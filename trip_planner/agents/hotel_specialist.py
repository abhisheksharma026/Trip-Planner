"""
Hotel Specialist Agent - Specialized agent for finding accommodations.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from trip_planner.tools import get_city_coordinates
from trip_planner.config import get_model_name


class HotelSpecialistAgent:
    """Specialized agent that searches for accommodations based on location, budget, dates, and preferences."""
    
    def __init__(self):
        # Create a search agent wrapper to make google_search a callable
        # This ensures all tools are callables (homogeneous tools list)
        search_agent = Agent(
            name="hotel_search_helper",
            model=get_model_name(),
            description="Helper agent for searching hotel information.",
            instruction="Use google_search to find hotel options, prices, and booking information. Always cite sources.",
            tools=[google_search]
        )
        
        # Create a callable wrapper for the search agent
        async def search_hotels(query: str, tool_context=None):
            """
            Search for hotel information using web search.
            
            Args:
                query: The search query for hotels
            """
            agent_tool = AgentTool(agent=search_agent)
            return await agent_tool.run_async(
                args={"request": query},
                tool_context=tool_context
            )
        
        self.agent = Agent(
            name="hotel_specialist",
            model=get_model_name(),
            description="Specialized agent that searches for accommodations based on location, budget, dates, and preferences.",
            instruction="""
            You are the Hotel Specialist, an expert in finding the perfect accommodations.
            
            Your Responsibilities:
            1. Search for hotels using the search_hotels tool based on:
               - Destination city and neighborhood preferences
               - Check-in and check-out dates
               - Budget range
               - User preferences (amenities, star rating, location type)
            
            2. Present hotel options with:
               - Hotel names and addresses
               - Star ratings and guest reviews
               - Price per night and total cost
               - Key amenities (WiFi, breakfast, pool, etc.)
               - Links to booking sites (Booking.com, Hotels.com, etc.)
            
            3. Always cite your sources to build trust.
            
            4. Consider proximity to attractions mentioned in the trip plan.
            
            Return your recommendations in a clear, structured format with prices.
            """,
            tools=[search_hotels, get_city_coordinates]  # Both are now callables
        )
    
    def get_agent(self):
        """Get the underlying ADK Agent instance."""
        return self.agent

