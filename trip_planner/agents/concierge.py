"""
Concierge Agent - Root orchestrator that coordinates all specialized agents.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from trip_planner.tools import export_itinerary_to_doc
from trip_planner.config import get_model_name
from .flight_recommender import FlightRecommenderAgent
from .hotel_specialist import HotelSpecialistAgent
from .financial_planner import FinancialPlannerAgent

# Try to import Opik for tool call tracing
try:
    import opik
    OPIK_AVAILABLE = True
except ImportError:
    OPIK_AVAILABLE = False
    opik = None


def get_query_span():
    """Get the current query span from the runner module."""
    try:
        from trip_planner.core.runner import get_current_query_span
        return get_current_query_span()
    except (ImportError, AttributeError, RuntimeError):
        return None


def create_tool_span(name: str, input_data: dict):
    """Create a child span for a tool call under the current query span."""
    query_span = get_query_span()
    if query_span:
        try:
            return query_span.span(name=name, input=input_data)
        except Exception as e:
            print(f"Could not create tool span: {e}")
    return None


class ConciergeAgent:
    """Professional travel concierge that orchestrates trip planning by delegating to specialized agents."""
    
    def __init__(self):
        # Initialize specialized agents
        self.flight_recommender = FlightRecommenderAgent()
        self.hotel_specialist = HotelSpecialistAgent()
        self.financial_planner = FinancialPlannerAgent()
        
        # Create research agent for general travel information (wraps google_search)
        # This ensures all tools are callables, not mixing with Tool objects
        # Store the agent directly since Agent() returns an LlmAgent
        self.research_agent = Agent(
            name="travel_researcher",
            model=get_model_name(),
            description="Specialist for general travel information and web searches.",
            instruction="""You are a travel researcher specializing in finding general travel information.
            
            Your Responsibilities:
            1. Search for travel-related information using Google Search:
               - Weather conditions and forecasts
               - Local events and festivals
               - Visa requirements and travel documents
               - Cultural information and customs
               - Transportation options
               - Safety and travel advisories
            
            2. Present information clearly with sources cited.
            
            3. Focus on practical, actionable information for travelers.
            """,
            tools=[google_search]
        )
        
        # Create safety check agent for hard constraints
        self.safety_agent = Agent(
            name="travel_safety_checker",
            model=get_model_name(),
            description="Specialist for checking travel safety constraints and requirements.",
            instruction="""You are a travel safety specialist responsible for identifying HARD CONSTRAINTS that could prevent or endanger travel.
            
            Your CRITICAL Responsibilities:
            1. **Visa Requirements**: 
               - Check if the destination requires a visa for the traveler's nationality
               - Identify visa application requirements and processing times
               - Warn if visa cannot be obtained in time for travel dates
               - Example warning: "WARNING: This destination requires a visa for your nationality. Processing time is typically 2-4 weeks."
            
            2. **Travel Advisories**:
               - Check official government travel advisories (US State Department, UK FCO, etc.)
               - Identify Level 3 (Reconsider Travel) or Level 4 (Do Not Travel) warnings
               - Check for specific security concerns, health warnings, or natural disasters
               - Example warning: "WARNING: [Country] has a Level 3 travel advisory due to [reason]. Reconsider travel."
            
            3. **Weather Extremes**:
               - Check for extreme weather conditions during travel dates
               - Identify hurricane seasons, monsoon seasons, extreme heat/cold
               - Check for natural disaster risks (floods, earthquakes, wildfires)
               - Example warning: "WARNING: Travel dates fall during [hurricane/monsoon] season. High risk of weather disruptions."
            
            4. **Political Instability**:
               - Check for ongoing conflicts, civil unrest, or political instability
               - Identify areas with active travel restrictions
               - Check for border closures or entry restrictions
               - Example warning: "WARNING: [Country] is experiencing political instability. Exercise extreme caution."
            
            Your Response Format:
            - If NO hard constraints found: "No hard constraints identified. Travel appears feasible."
            - If constraints found: List each constraint with clear warnings
            - Always cite sources (government websites, official advisories)
            - Be direct and clear - safety is paramount
            - If multiple constraints exist, list all of them
            
            Search Strategy:
            - Use specific queries like: "[Country] visa requirements for [Nationality]"
            - Use queries like: "[Country] travel advisory [Current Year]"
            - Use queries like: "[Country] [Month] weather extreme conditions"
            - Use queries like: "[Country] political situation travel safety [Current Year]"
            """,
            tools=[google_search]
        )
        
        # Create standalone tool functions that capture self via closure
        # These must be proper callables, not bound methods
        async def call_flight_recommender(
            origin: str,
            destination: str,
            departure_date: str,
            return_date: str = None,
            budget: str = None,
            preferences: str = None,
            tool_context: ToolContext = None
        ) -> str:
            """
            Use this tool to find flight options. Call this when the user needs flight recommendations.
            
            Args:
                origin: Departure city
                destination: Destination city
                departure_date: Departure date (e.g., '2025-03-15' or 'next week')
                return_date: Return date if round trip (optional)
                budget: Budget constraint (e.g., 'under $500', 'economy')
                preferences: User preferences (e.g., 'no long layovers', 'prefer direct flights')
            """
            return await self._call_flight_recommender(
                origin, destination, departure_date, return_date, budget, preferences, tool_context
            )
        
        async def call_hotel_specialist(
            destination: str,
            check_in: str,
            check_out: str,
            budget: str = None,
            preferences: str = None,
            tool_context: ToolContext = None
        ) -> str:
            """
            Use this tool to find hotel accommodations. Call this when the user needs hotel recommendations.
            
            Args:
                destination: Destination city
                check_in: Check-in date
                check_out: Check-out date
                budget: Budget constraint (e.g., 'under $150 per night')
                preferences: User preferences (e.g., 'downtown location', 'pool and gym')
            """
            return await self._call_hotel_specialist(
                destination, check_in, check_out, budget, preferences, tool_context
            )
        
        async def call_financial_planner(
            user_budget: str,
            tool_context: ToolContext = None
        ) -> str:
            """
            Use this tool to analyze costs and check against budget. Call this after gathering flight and hotel information.
            
            Args:
                user_budget: The user's total budget for the trip
            """
            return await self._call_financial_planner(user_budget, tool_context)
        
        async def call_travel_researcher(
            query: str,
            tool_context: ToolContext = None
        ) -> str:
            """
            Use this tool to search for general travel information (weather, events, visa requirements, cultural info).
            
            Args:
                query: The search query or question to research
            """
            return await self._call_travel_researcher(query, tool_context)
        
        async def check_travel_safety(
            destination: str,
            travel_dates: str = None,
            traveler_nationality: str = None,
            tool_context: ToolContext = None
        ) -> str:
            """
            Use this tool to check for hard travel constraints BEFORE making recommendations.
            Checks visa requirements, travel advisories, weather extremes, and political instability.
            
            Args:
                destination: Destination country/city
                travel_dates: Travel dates (optional, for weather checks)
                traveler_nationality: Traveler's nationality/passport country (optional, for visa checks)
            """
            return await self._check_travel_safety(destination, travel_dates, traveler_nationality, tool_context)
        
        # Create the concierge agent with standalone functions as tools
        # All tools must be callables (no mixing with Tool objects)
        self.agent = Agent(
            name="trip_planner_concierge",
            model=get_model_name(),
            description="Professional travel concierge that orchestrates trip planning by delegating to specialized agents.",
            instruction="""
            You are a professional travel concierge and the main interface for trip planning.
            
            Your Mission:
            Help users plan complete trips by gathering information and delegating to specialists.
            Act as a decision assistant, not just a recommender - help users explore "what-if" scenarios.
            
            Your Workflow:
            1. **Greet and Gather Information**:
               - Start by warmly greeting the user
               - Ask for: destination, travel dates, budget, and any preferences
               - If nationality/passport country is not mentioned, ask for it (needed for visa checks)
               - Remember user preferences throughout the conversation (e.g., "I hate long layovers")
               - Store key details: original budget, dates, preferences, nationality, and recommendations
            
            2. **SAFETY FIRST - Check Hard Constraints** (CRITICAL STEP):
               - BEFORE making any recommendations, ALWAYS use `check_travel_safety` to check for:
                 * Visa requirements for the traveler's nationality
                 * Travel advisories (Level 3/4 warnings)
                 * Weather extremes during travel dates
                 * Political instability or security concerns
               - If hard constraints are found:
                 * Display warnings prominently at the TOP of your response
                 * Use bold text for warnings
                 * Example: "**WARNING**: This destination requires a visa for your nationality."
                 * Do NOT proceed with flight/hotel recommendations if travel is unsafe
                 * Advise the user on how to address the constraint (e.g., "Apply for visa at least 4 weeks in advance")
               - If no hard constraints: Proceed with normal planning workflow
            
            3. **Delegate to Specialists** (only after safety checks pass):
               - Use `call_flight_recommender` to find flight options
               - Use `call_hotel_specialist` to find accommodations
               - Use `call_financial_planner` to analyze costs against budget
               - Use `call_travel_researcher` to find general travel information (weather, events, cultural info)
            
            3. **Coordinate and Present with Reasoning**:
               - Combine recommendations from all specialists
               - **ALWAYS explain WHY you made each recommendation** - this makes you feel intelligent, not random
               - Present a cohesive trip plan with clear reasoning
               - Use structured format: "I recommended [Destination/Choice] because:" followed by bullet points
               - Include relevant factors in your reasoning:
                 * Flight availability (e.g., "Direct flights available", "Best price for your dates")
                 * Weather conditions (e.g., "Average March temperature ~18°C", "Perfect weather for outdoor activities")
                 * Budget fit (e.g., "Fits your $2,500 budget", "Leaves $300 for activities")
                 * Attractions/features (e.g., "Strong food & cultural scene", "World-class museums", "Beautiful beaches")
                 * Safety considerations (e.g., "No travel advisories", "Safe for solo travelers")
                 * User preferences match (e.g., "Matches your preference for direct flights", "No long layovers as requested")
                 * Value proposition (e.g., "Best value for money", "Premium experience within budget")
               - Example format:
                 
                 "I recommended Barcelona because:
                 • Direct flights available from your origin
                 • Average March temperature ~18°C - perfect for sightseeing
                 • Fits your $2,500 budget with room for activities
                 • Strong food & cultural scene matching your interests
                 • No visa required for your nationality
                 • Safe destination with no travel advisories"
               
               - For multiple options, explain why each is recommended
               - Ask if the user wants to export the itinerary
            
            4. **Handle Follow-ups and What-If Scenarios**:
               - Remember previous conversation context and original plan details
               - When users ask "what-if" questions, you are a DECISION ASSISTANT:
                 
                 **What-If Budget Changes** (e.g., "What if I increase my budget by $500?"):
                 - Recall the original budget and current plan
                 - Calculate the new budget amount
                 - Re-run financial analysis with the new budget
                 - Compare: What new options become available? What can be upgraded?
                 - Present side-by-side comparison: Original vs. New Scenario
                 - Highlight benefits and trade-offs
                 
                 **What-If Date Changes** (e.g., "What if I travel one week later?"):
                 - Recall original travel dates
                 - Calculate the new dates
                 - Re-check flights and hotels for the new dates
                 - Compare: Price differences, availability, weather changes
                 - Present side-by-side comparison: Original vs. New Dates
                 - Highlight advantages (e.g., better prices, events) and disadvantages
                 
                 **What-If Preference Changes** (e.g., "What if I allow one layover?"):
                 - Recall original preferences (e.g., "no layovers", "direct flights only")
                 - Understand the new preference
                 - Re-search flights with the new preference
                 - Compare: Price differences, flight duration, convenience
                 - Present side-by-side comparison: Original vs. New Preference
                 - Highlight cost savings vs. convenience trade-offs
                 
                 **General What-If Approach**:
                 - Always start by acknowledging the scenario: "Let me explore that scenario for you..."
                 - Re-run relevant searches with modified parameters
                 - Present a clear comparison table or structured comparison
                 - Use headers like "Original Plan" vs. "What-If Scenario"
                 - Quantify differences (e.g., "$200 savings", "2 hours longer travel time")
                 - Provide a recommendation with reasoning: "Based on this comparison, I recommend [option] because:"
                   * List specific reasons why the recommended option is better
                   * Highlight key advantages and trade-offs
                 - Ask if they want to proceed with the new scenario
            
            5. **Adapt Recommendations**:
               - Adapt recommendations based on feedback
               - Answer questions about the trip plan
               - Remember all modifications and comparisons made
            
            Important Guidelines:
            - **SAFETY IS PARAMOUNT**: Always check safety constraints BEFORE making recommendations
            - If hard constraints are found, display warnings prominently and do not proceed with unsafe recommendations
            - **ALWAYS EXPLAIN YOUR REASONING**: Every recommendation must include a "Why" explanation
              * Never just list options - always explain why you chose them
              * Use structured bullet points for clarity
              * Make the reasoning specific and data-driven (mention temperatures, prices, flight types, etc.)
              * This makes you feel intelligent and thoughtful, not random
            - Always be friendly and professional
            - Remember user preferences and original plan details throughout the conversation
            - When handling what-if scenarios, be thorough and compare systematically
            - Cite sources when presenting recommendations
            - If the user says "I want to go somewhere warm next week", ask clarifying questions about:
              * Approximate budget
              * Preferred travel style (relaxing, adventurous, etc.)
              * Duration of trip
              * Nationality/passport country (for visa checks)
            - When suggesting destinations, ALWAYS explain why:
              * "I'm recommending [Destination] because it matches your criteria: [specific reasons]"
            - Present information in a clear, organized markdown format
            - Use comparison tables or structured comparisons for what-if scenarios
            - Quantify all differences (costs, time, features) when comparing scenarios
            - Format safety warnings clearly:
              * Use **bold text** for warning headers
              * Place warnings at the top of responses
              * Provide actionable advice on how to address constraints
            - Format recommendation explanations clearly:
              * Use "I recommended [X] because:" as a header
              * Use bullet points (•) for each reason
              * Be specific with numbers, dates, and facts
              * Connect each reason to user's stated preferences or constraints
            """,
            tools=[
                check_travel_safety,  # Safety checks FIRST - must be before recommendations
                call_flight_recommender,
                call_hotel_specialist,
                call_financial_planner,
                call_travel_researcher,  # Wrapped google_search in an agent
                export_itinerary_to_doc
            ]
        )
    
    async def _call_flight_recommender(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str = None,
        budget: str = None,
        preferences: str = None,
        tool_context: ToolContext = None
    ) -> str:
        print("--- TOOL CALL: call_flight_recommender ---")
        
        query = f"Find flights from {origin} to {destination}"
        if departure_date:
            query += f" departing {departure_date}"
        if return_date:
            query += f" returning {return_date}"
        if budget:
            query += f" within budget {budget}"
        if preferences:
            query += f". Preferences: {preferences}"
        
        # Create a tool span as child of the query span
        tool_span = create_tool_span("call_flight_recommender", {
            "origin": origin, "destination": destination,
            "departure_date": departure_date, "return_date": return_date,
            "budget": budget, "preferences": preferences,
            "search_query": query
        })
        
        try:
            agent_tool = AgentTool(agent=self.flight_recommender.get_agent())
            result = await agent_tool.run_async(
                args={"request": query},
                tool_context=tool_context
            )
            
            # Update and end the tool span
            if tool_span:
                tool_span.update(output={"result": str(result)[:1500] if result else "No result"})
                tool_span.end()
        except Exception as e:
            if tool_span:
                tool_span.update(output={"error": str(e)})
                tool_span.end()
            raise
        
        # Store flight info in context for financial planner
        if tool_context:
            tool_context.state["flight_info"] = result
        
        return result
    
    async def _call_hotel_specialist(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        budget: str = None,
        preferences: str = None,
        tool_context: ToolContext = None
    ) -> str:
        print("--- TOOL CALL: call_hotel_specialist ---")
        
        query = f"Find hotels in {destination}"
        if check_in and check_out:
            query += f" from {check_in} to {check_out}"
        if budget:
            query += f" within budget {budget}"
        if preferences:
            query += f". Preferences: {preferences}"
        
        # Create a tool span as child of the query span
        tool_span = create_tool_span("call_hotel_specialist", {
            "destination": destination, "check_in": check_in, "check_out": check_out,
            "budget": budget, "preferences": preferences,
            "search_query": query
        })
        
        try:
            agent_tool = AgentTool(agent=self.hotel_specialist.get_agent())
            result = await agent_tool.run_async(
                args={"request": query},
                tool_context=tool_context
            )
            
            # Update and end the tool span
            if tool_span:
                tool_span.update(output={"result": str(result)[:1500] if result else "No result"})
                tool_span.end()
        except Exception as e:
            if tool_span:
                tool_span.update(output={"error": str(e)})
                tool_span.end()
            raise
        
        # Store hotel info in context for financial planner
        if tool_context:
            tool_context.state["hotel_info"] = result
        
        return result
    
    async def _call_financial_planner(
        self,
        user_budget: str,
        tool_context: ToolContext = None
    ) -> str:
        print("--- TOOL CALL: call_financial_planner ---")
        
        # Gather information from context
        flight_info = tool_context.state.get("flight_info", "No flight information available.") if tool_context else "No flight information available."
        hotel_info = tool_context.state.get("hotel_info", "No hotel information available.") if tool_context else "No hotel information available."
        
        query = f"""
        Analyze the total cost of this trip and compare it to the user's budget of {user_budget}.
        
        Flight Information:
        {flight_info}
        
        Hotel Information:
        {hotel_info}
        
        Please provide:
        1. Total estimated cost breakdown
        2. Comparison to the stated budget
        3. Recommendations if over budget
        """
        
        # Create a tool span as child of the query span
        tool_span = create_tool_span("call_financial_planner", {
            "user_budget": user_budget,
            "has_flight_info": flight_info != "No flight information available.",
            "has_hotel_info": hotel_info != "No hotel information available."
        })
        
        try:
            agent_tool = AgentTool(agent=self.financial_planner.get_agent())
            result = await agent_tool.run_async(
                args={"request": query},
                tool_context=tool_context
            )
            
            if tool_span:
                tool_span.update(output={"result": str(result)[:1500] if result else "No result"})
                tool_span.end()
        except Exception as e:
            if tool_span:
                tool_span.update(output={"error": str(e)})
                tool_span.end()
            raise
        
        return result
    
    async def _call_travel_researcher(
        self,
        query: str,
        tool_context: ToolContext = None
    ) -> str:
        """
        Internal method to call the travel researcher agent.
        
        Args:
            query: The search query or question to research
            tool_context: The tool context for state management
        """
        print(f"--- TOOL CALL: call_travel_researcher (Query: {query}) ---")
        
        # Create a tool span as child of the query span
        tool_span = create_tool_span("call_travel_researcher", {"research_query": query})
        
        try:
            agent_tool = AgentTool(agent=self.research_agent)
            result = await agent_tool.run_async(
                args={"request": query},
                tool_context=tool_context
            )
            
            if tool_span:
                tool_span.update(output={"result": str(result)[:1500] if result else "No result"})
                tool_span.end()
            
            return result
        except Exception as e:
            if tool_span:
                tool_span.update(output={"error": str(e)})
                tool_span.end()
            raise
    
    async def _check_travel_safety(
        self,
        destination: str,
        travel_dates: str = None,
        traveler_nationality: str = None,
        tool_context: ToolContext = None
    ) -> str:
        """
        Internal method to check travel safety constraints.
        
        Args:
            destination: Destination country/city
            travel_dates: Travel dates (optional, for weather checks)
            traveler_nationality: Traveler's nationality/passport country (optional, for visa checks)
            tool_context: The tool context for state management
        """
        print(f"--- TOOL CALL: check_travel_safety (Destination: {destination}, Dates: {travel_dates}, Nationality: {traveler_nationality}) ---")
        
        # Build comprehensive safety check query
        query_parts = []
        
        if traveler_nationality:
            query_parts.append(f"visa requirements for {traveler_nationality} passport holders")
        
        query_parts.append("travel advisory")
        query_parts.append("safety warnings")
        
        if travel_dates:
            query_parts.append(f"weather conditions {travel_dates}")
            query_parts.append("extreme weather risks")
        
        query_parts.append("political situation")
        query_parts.append("security concerns")
        
        query = f"{destination} {' '.join(query_parts)}"
        
        # Create a tool span as child of the query span
        tool_span = create_tool_span("check_travel_safety", {
            "destination": destination,
            "travel_dates": travel_dates,
            "traveler_nationality": traveler_nationality,
            "safety_query": query
        })
        
        try:
            agent_tool = AgentTool(agent=self.safety_agent)
            result = await agent_tool.run_async(
                args={"request": query},
                tool_context=tool_context
            )
            
            if tool_span:
                tool_span.update(output={"result": str(result)[:1500] if result else "No result"})
                tool_span.end()
        except Exception as e:
            if tool_span:
                tool_span.update(output={"error": str(e)})
                tool_span.end()
            raise
        
        # Store safety check results in context
        if tool_context:
            tool_context.state["safety_check"] = result
        
        return result
    
    def get_agent(self):
        """Get the underlying ADK Agent instance."""
        return self.agent

