#!/usr/bin/env python3
"""
Main entry point for the AI Trip Planner application.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trip_planner.config import setup_api_key
from trip_planner.core.session_manager import SessionManager
from trip_planner.core.runner import TripPlannerRunner


async def main():
    """Main function to run the trip planner application."""
    # Setup API key
    try:
        setup_api_key()
    except Exception as e:
        print(f"Failed to setup API key: {e}")
        print("Please set GOOGLE_API_KEY environment variable or enter it when prompted.")
        sys.exit(1)
    
    # Initialize components
    session_manager = SessionManager()
    runner = TripPlannerRunner(session_manager)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        await runner.run_query(query)
    else:
        # Interactive mode
        await runner.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())

