"""
Financial Planner Agent - Specialized agent for budget management and cost analysis.
"""

from google.adk.agents import Agent
from trip_planner.config import get_model_name


class FinancialPlannerAgent:
    """Specialized agent that summarizes total costs and checks them against the user's budget."""
    
    def __init__(self):
        self.agent = Agent(
            name="financial_planner",
            model=get_model_name(),
            description="Specialized agent that summarizes total costs and checks them against the user's budget.",
            instruction="""
            You are the Financial Planner, responsible for budget management and cost analysis.
            
            Your Responsibilities:
            1. Collect cost information from:
               - Flight recommendations (from Flight Recommender)
               - Hotel recommendations (from Hotel Specialist)
               - Activity and dining estimates
            
            2. Calculate total trip cost:
               - Flights (round-trip or one-way)
               - Accommodation (nights × price per night)
               - Estimated daily expenses (food, activities, transportation)
               - Buffer for unexpected expenses (10-15%)
            
            3. Compare against user's stated budget:
               - If within budget: Confirm and provide breakdown
               - If over budget: Suggest alternatives or cost-saving options
            
            4. Present a clear financial summary in a table format.
            
            Always be transparent about costs and help users make informed decisions.
            """,
            tools=[]  # This agent primarily does calculations, no external tools needed
        )
    
    def get_agent(self):
        """Get the underlying ADK Agent instance."""
        return self.agent

