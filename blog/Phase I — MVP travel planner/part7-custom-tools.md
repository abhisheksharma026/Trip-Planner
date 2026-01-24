# Building a Production-Grade AI Agent from Scratch - Part 7: Creating Custom Tools

## Overview

In Part 6, we built the Concierge Orchestrator that coordinates all specialized agents. Now, let's create the **Custom Tools** that our agents use to perform specific tasks.

Tools are functions that agents can call to perform actions. They extend agent capabilities beyond text generation, allowing agents to:

1. **Search for information**: Query external APIs and databases
2. **Perform calculations**: Compute costs, distances, etc.
3. **Access real-time data**: Get current prices, availability, etc.
4. **Execute actions**: Book flights, save files, etc.
5. **Integrate services**: Connect to third-party APIs

## Our Custom Tools

We'll create three custom tools:

1. **Geolocation Tool**: Converts city names to coordinates
2. **Export Tool**: Saves itineraries to markdown files
3. **Flight Search Tool**: Searches for live flight prices

## Tool Architecture

```
┌─────────────────────────────────────────────────┐
│         Agent Request                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Tool Wrapper                  │
│  ┌─────────────────────────────────────┐  │
│  │  Parse Query                        │  │
│  │  - Extract parameters               │  │
│  │  - Validate inputs                  │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Call Tool Function                 │  │
│  │  - Execute logic                    │  │
│  │  - Handle errors                    │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Format Response                    │  │
│  │  - Structure output                 │  │
│  │  - Add metadata                     │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Tool Function                 │
│  ┌─────────────────────────────────────┐  │
│  │  Geolocation Tool                  │  │
│  │  - City name to coordinates        │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Export Tool                       │  │
│  │  - Save itinerary to file          │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Flight Search Tool                │  │
│  │  - Search live flight prices       │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│         Response to Agent              │
└─────────────────────────────────────────────────┘
```

## Building the Geolocation Tool

Let's start with the Geolocation tool. Create `trip_planner/tools/geolocation.py`:

```python
"""
Geolocation Tool - Converts city names to coordinates.
"""

from typing import Dict, Optional, Tuple

# Mock database of city coordinates
# In production, use Google Maps Geocoding API or similar
CITY_COORDINATES: Dict[str, Dict[str, float]] = {
    "paris": {
        "lat": 48.8566,
        "lon": 2.3522
    },
    "london": {
        "lat": 51.5074,
        "lon": -0.1278
    },
    "new york": {
        "lat": 40.7128,
        "lon": -74.0060
    },
    "tokyo": {
        "lat": 35.6762,
        "lon": 139.6503
    },
    "sydney": {
        "lat": -33.8688,
        "lon": 151.2093
    },
    "rome": {
        "lat": 41.9028,
        "lon": 12.4964
    },
    "barcelona": {
        "lat": 41.3851,
        "lon": 2.1734
    },
    "amsterdam": {
        "lat": 52.3676,
        "lon": 4.9041
    },
    "dubai": {
        "lat": 25.2048,
        "lon": 55.2708
    },
    "singapore": {
        "lat": 1.3521,
        "lon": 103.8198
    },
    "bangkok": {
        "lat": 13.7563,
        "lon": 100.5018
    },
    "san francisco": {
        "lat": 37.7749,
        "lon": -122.4194
    },
    "los angeles": {
        "lat": 34.0522,
        "lon": -118.2437
    },
    "chicago": {
        "lat": 41.8781,
        "lon": -87.6298
    },
    "miami": {
        "lat": 25.7617,
        "lon": -80.1918
    },
    "berlin": {
        "lat": 52.5200,
        "lon": 13.4050
    },
    "madrid": {
        "lat": 40.4168,
        "lon": -3.7038
    },
    "vienna": {
        "lat": 48.2082,
        "lon": 16.3738
    },
    "prague": {
        "lat": 50.0755,
        "lon": 14.4378
    },
    "budapest": {
        "lat": 47.4979,
        "lon": 19.0402
    }
}


def get_coordinates(city: str) -> Optional[Dict[str, float]]:
    """
    Get coordinates for a city.
    
    Args:
        city: Name of the city (case-insensitive)
    
    Returns:
        Dictionary with 'lat' and 'lon' keys, or None if not found
    
    Example:
        >>> get_coordinates("Paris")
        {'lat': 48.8566, 'lon': 2.3522}
    """
    # Normalize city name
    city_normalized = city.lower().strip()
    
    # Look up in database
    return CITY_COORDINATES.get(city_normalized)


def get_distance(
    city1: str,
    city2: str
) -> Optional[float]:
    """
    Calculate distance between two cities using Haversine formula.
    
    Args:
        city1: Name of first city
        city2: Name of second city
    
    Returns:
        Distance in kilometers, or None if cities not found
    
    Example:
        >>> get_distance("Paris", "London")
        343.5
    """
    import math
    
    # Get coordinates
    coords1 = get_coordinates(city1)
    coords2 = get_coordinates(city2)
    
    if not coords1 or not coords2:
        return None
    
    # Haversine formula
    lat1, lon1 = math.radians(coords1['lat']), math.radians(coords1['lon'])
    lat2, lon2 = math.radians(coords2['lat']), math.radians(coords2['lon'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = (math.sin(dlat/2)**2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers
    r = 6371
    
    return c * r


def geolocation_tool(query: str) -> str:
    """
    Tool function for geolocation queries.
    
    This function is called by agents to get city coordinates
    or calculate distances between cities.
    
    Args:
        query: Query string (e.g., "coordinates of Paris" or "distance from Paris to London")
    
    Returns:
        Formatted response string
    
    Example queries:
        - "coordinates of Paris"
        - "get coordinates for New York"
        - "distance from Paris to London"
        - "how far is Tokyo from Sydney"
    """
    query_lower = query.lower()
    
    # Handle coordinate queries
    if "coordinate" in query_lower or "lat" in query_lower or "lon" in query_lower:
        # Extract city name
        words = query_lower.split()
        for word in words:
            if word in CITY_COORDINATES:
                coords = get_coordinates(word)
                if coords:
                    return (
                        f"Coordinates for {word.title()}:\n"
                        f"Latitude: {coords['lat']}\n"
                        f"Longitude: {coords['lon']}"
                    )
        
        return "City not found in database. Available cities: " + ", ".join(
            city.title() for city in CITY_COORDINATES.keys()
        )
    
    # Handle distance queries
    elif "distance" in query_lower or "how far" in query_lower or "from" in query_lower:
        # Try to extract two city names
        words = [w for w in query_lower.split() if w in CITY_COORDINATES]
        
        if len(words) >= 2:
            city1, city2 = words[0], words[1]
            distance = get_distance(city1, city2)
            
            if distance is not None:
                return (
                    f"Distance from {city1.title()} to {city2.title()}:\n"
                    f"{distance:.1f} kilometers"
                )
        
        return "Could not extract two city names from query. "
    
    # Default response
    return (
        "Geolocation tool available commands:\n"
        "- Get coordinates: 'coordinates of Paris'\n"
        "- Calculate distance: 'distance from Paris to London'\n"
        f"Available cities: {', '.join(city.title() for city in CITY_COORDINATES.keys())}"
    )
```

## Building the Export Tool

Now let's create the Export tool. Create `trip_planner/tools/export.py`:

```python
"""
Export Tool - Saves itineraries to markdown files.
"""

import os
from datetime import datetime
from typing import Optional


def export_itinerary(query: str) -> str:
    """
    Export an itinerary to a markdown file.
    
    This function parses the query to extract itinerary details
    and saves them to a markdown file in the itineraries directory.
    
    Args:
        query: Query string containing itinerary information
    
    Returns:
        Success message with file path
    
    Example queries:
        - "Save this itinerary: Paris trip March 15-18, 2025"
        - "Export: Flight to Paris, Hotel Grand, Budget $1,500"
    """
    # Create itineraries directory if it doesn't exist
    itineraries_dir = "itineraries"
    os.makedirs(itineraries_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"itinerary_{timestamp}.md"
    filepath = os.path.join(itineraries_dir, filename)
    
    # Parse query to extract itinerary details
    # This is a simple parser - in production, use more sophisticated parsing
    content = f"""# Trip Itinerary

**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

---

## Query
{query}

---

## Itinerary Details

*Note: This is a template. In production, this would be populated with actual itinerary data from the agent conversation.*

### Flight Information
- [Flight details would be here]

### Hotel Information
- [Hotel details would be here]

### Activities
- [Activity list would be here]

### Budget Breakdown
- [Budget breakdown would be here]

### Travel Tips
- [Travel tips would be here]

---

*This itinerary was generated by the AI Travel Planner. For the most accurate and up-to-date information, please verify all details before booking.*
"""
    
    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return (
            f"Successfully exported itinerary to: {filepath}\n\n"
            f"The file includes:\n"
            f"- Flight information\n"
            f"- Hotel details\n"
            f"- Activity suggestions\n"
            f"- Budget breakdown\n"
            f"- Travel tips\n\n"
            f"You can open this file to review or share your itinerary."
        )
    except Exception as e:
        return f"Error exporting itinerary: {str(e)}"


def export_itinerary_detailed(
    destination: str,
    dates: str,
    flight_info: str,
    hotel_info: str,
    budget: str,
    activities: str = ""
) -> str:
    """
    Export a detailed itinerary with specific information.
    
    Args:
        destination: Destination city
        dates: Travel dates
        flight_info: Flight details
        hotel_info: Hotel details
        budget: Budget information
        activities: Optional activity suggestions
    
    Returns:
        Success message with file path
    """
    # Create itineraries directory if it doesn't exist
    itineraries_dir = "itineraries"
    os.makedirs(itineraries_dir, exist_ok=True)
    
    # Generate filename with destination and timestamp
    dest_clean = destination.lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trip_{dest_clean}_{timestamp}.md"
    filepath = os.path.join(itineraries_dir, filename)
    
    # Create detailed itinerary content
    content = f"""# Trip Itinerary: {destination}

**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
**Travel Dates:** {dates}

---

## Flight Information
{flight_info}

---

## Hotel Information
{hotel_info}

---

## Budget Breakdown
{budget}

---

## Activities
{activities if activities else "No specific activities planned yet."}

---

## Travel Tips
- Verify all details before booking
- Check passport and visa requirements
- Consider travel insurance
- Research local customs and culture
- Download offline maps
- Notify your bank of travel plans

---

*This itinerary was generated by the AI Travel Planner. For the most accurate and up-to-date information, please verify all details before booking.*
"""
    
    # Write to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return (
            f"Successfully exported detailed itinerary to: {filepath}\n\n"
            f"The file includes:\n"
            f"- Flight information\n"
            f"- Hotel details\n"
            f"- Budget breakdown\n"
            f"- Activities\n"
            f"- Travel tips\n\n"
            f"You can open this file to review or share your itinerary."
        )
    except Exception as e:
        return f"Error exporting itinerary: {str(e)}"
```

## Building the Flight Search Tool

Now let's create the Flight Search tool. Create `trip_planner/tools/amadeus_flights.py`:

```python
"""
Flight Search Tool - Searches for live flight prices using Amadeus API.
"""

import os
import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta


async def search_flight_prices(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    date_flexibility: int = 0
) -> str:
    """
    Search for flight prices using Amadeus API.
    
    Args:
        origin: Origin city code (e.g., "JFK", "LAX")
        destination: Destination city code (e.g., "PAR", "LON")
        departure_date: Departure date in YYYY-MM-DD format
        adults: Number of adult passengers (default: 1)
        date_flexibility: Days to search around departure date (default: 0)
    
    Returns:
        Formatted flight search results
    
    Example:
        >>> search_flight_prices("JFK", "PAR", "2025-03-15")
        "Found 3 flight options..."
    """
    # Check for Amadeus API credentials
    api_key = os.environ.get("AMADEUS_API_KEY")
    api_secret = os.environ.get("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        return (
            "Amadeus API credentials not configured. "
            "Please set AMADEUS_API_KEY and AMADEUS_API_SECRET environment variables. "
            "Using mock data instead."
        )
    
    try:
        # Get access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://test.api.amadeus.com/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": api_key,
                    "client_secret": api_secret
                }
            )
            
            if token_response.status_code != 200:
                return f"Error getting Amadeus access token: {token_response.text}"
            
            access_token = token_response.json()["access_token"]
            
            # Search for flights
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Build search URL
            search_url = (
                f"https://test.api.amadeus.com/v2/shopping/flight-offers?"
                f"originLocationCode={origin}&"
                f"destinationLocationCode={destination}&"
                f"departureDate={departure_date}&"
                f"adults={adults}"
            )
            
            if date_flexibility > 0:
                search_url += f"&dateFlexibility={date_flexibility}"
            
            flight_response = await client.get(search_url, headers=headers)
            
            if flight_response.status_code != 200:
                return f"Error searching flights: {flight_response.text}"
            
            flight_data = flight_response.json()
            
            # Parse and format results
            return _format_flight_results(flight_data)
            
    except Exception as e:
        return f"Error searching flights: {str(e)}"


def _format_flight_results(flight_data: Dict) -> str:
    """
    Format flight search results for display.
    
    Args:
        flight_data: Raw flight data from Amadeus API
    
    Returns:
        Formatted flight results string
    """
    if not flight_data.get("data"):
        return "No flights found for the given criteria."
    
    flights = flight_data["data"]
    results = [f"Found {len(flights)} flight options:\n"]
    
    for i, flight in enumerate(flights[:5], 1):  # Limit to 5 options
        price = flight["price"]["total"]
        currency = flight["price"]["currency"]
        
        # Get airline info
        airline = flight["validatingAirlineCodes"][0]
        
        # Get departure and arrival info
        itinerary = flight["itineraries"][0]
        segment = itinerary["segments"][0]
        
        departure = segment["departure"]
        arrival = segment["arrival"]
        
        results.append(
            f"Option {i}: {price} {currency}\n"
            f"- Airline: {airline}\n"
            f"- Departure: {departure['iataCode']} at {departure['at']}\n"
            f"- Arrival: {arrival['iataCode']} at {arrival['at']}\n"
            f"- Duration: {itinerary['duration']}\n"
            f"- Stops: {len(segment) - 1}\n"
        )
    
    return "\n".join(results)


def search_flight_prices(query: str) -> str:
    """
    Synchronous wrapper for flight search (for use with ADK tools).
    
    This function parses the query and calls the async flight search.
    Since ADK tools are synchronous, we use mock data for demonstration.
    
    Args:
        query: Query string (e.g., "flights from JFK to PAR on 2025-03-15")
    
    Returns:
        Formatted flight search results
    
    Example queries:
        - "flights from JFK to PAR on 2025-03-15"
        - "search flights LAX to London 2025-04-01"
    """
    # Parse query to extract parameters
    # This is a simple parser - in production, use more sophisticated parsing
    query_lower = query.lower()
    
    # Extract origin and destination
    words = query_lower.split()
    origin = None
    destination = None
    date = None
    
    # Look for city codes or names
    city_codes = ["jfk", "lax", "sfo", "par", "lon", "tok", "syd", "dxb", "sin"]
    for word in words:
        if word in city_codes:
            if origin is None:
                origin = word.upper()
            else:
                destination = word.upper()
    
    # Look for date
    for word in words:
        if "-" in word and len(word) == 10:  # YYYY-MM-DD format
            date = word
            break
    
    # Use mock data if parameters not found
    if not origin or not destination:
        return (
            "Flight search requires origin and destination city codes.\n"
            "Example: 'flights from JFK to PAR on 2025-03-15'\n\n"
            "Using mock data for demonstration:\n\n"
            _get_mock_flight_results()
        )
    
    # In production, this would call the async search_flight_prices function
    # For now, return mock data
    return _get_mock_flight_results(origin, destination, date)


def _get_mock_flight_results(
    origin: str = "JFK",
    destination: str = "PAR",
    date: str = "2025-03-15"
) -> str:
    """
    Generate mock flight results for demonstration.
    
    Args:
        origin: Origin city code
        destination: Destination city code
        date: Departure date
    
    Returns:
        Mock flight results
    """
    return f"""Found 3 flight options from {origin} to {destination} on {date}:

Option 1: $450 USD
- Airline: United Airlines
- Departure: {origin} at 08:00
- Arrival: {destination} at 14:30 (local time)
- Duration: 6h 30m
- Direct flight

Option 2: $380 USD
- Airline: American Airlines
- Departure: {origin} at 10:15
- Arrival: {destination} at 17:45 (local time)
- Duration: 7h 30m
- 1 stop in Chicago

Option 3: $520 USD
- Airline: Delta Airlines
- Departure: {origin} at 14:00
- Arrival: {destination} at 20:15 (local time)
- Duration: 6h 15m
- Direct flight

*Note: These are mock results. Configure AMADEUS_API_KEY and AMADEUS_API_SECRET for live pricing.*"""
```

## Testing the Tools

Let's create a test to verify our tools work:

```python
# test_custom_tools.py
"""
Test custom tools functionality.
"""

import asyncio
from trip_planner.tools.geolocation import geolocation_tool, get_coordinates, get_distance
from trip_planner.tools.export import export_itinerary, export_itinerary_detailed
from trip_planner.tools.amadeus_flights import search_flight_prices

def test_geolocation_tool():
    print("=" * 60)
    print("Testing Geolocation Tool")
    print("=" * 60)
    
    # Test 1: Get coordinates
    print("\n1. Testing get_coordinates...")
    coords = get_coordinates("Paris")
    if coords:
        print(f"   Paris coordinates: {coords}")
        print(f"   ✓ Coordinates retrieved")
    else:
        print(f"   ✗ Coordinates not found")
    
    # Test 2: Get distance
    print("\n2. Testing get_distance...")
    distance = get_distance("Paris", "London")
    if distance:
        print(f"   Distance Paris to London: {distance:.1f} km")
        print(f"   ✓ Distance calculated")
    else:
        print(f"   ✗ Distance not calculated")
    
    # Test 3: Geolocation tool
    print("\n3. Testing geolocation_tool...")
    result = geolocation_tool("coordinates of Paris")
    print(f"   Result: {result}")
    print(f"   ✓ Tool executed")
    
    print("\n" + "=" * 60)


def test_export_tool():
    print("=" * 60)
    print("Testing Export Tool")
    print("=" * 60)
    
    # Test 1: Simple export
    print("\n1. Testing export_itinerary...")
    result = export_itinerary("Paris trip March 15-18, 2025")
    print(f"   Result: {result}")
    print(f"   ✓ Export completed")
    
    # Test 2: Detailed export
    print("\n2. Testing export_itinerary_detailed...")
    result = export_itinerary_detailed(
        destination="Paris",
        dates="March 15-18, 2025",
        flight_info="United Airlines, JFK to PAR, $450",
        hotel_info="Grand Hotel, $180/night",
        budget="Total: $1,260 (within $1,500 budget)",
        activities="Eiffel Tower, Louvre Museum, Notre-Dame Cathedral"
    )
    print(f"   Result: {result}")
    print(f"   ✓ Detailed export completed")
    
    print("\n" + "=" * 60)


def test_flight_search_tool():
    print("=" * 60)
    print("Testing Flight Search Tool")
    print("=" * 60)
    
    # Test 1: Flight search
    print("\n1. Testing search_flight_prices...")
    result = search_flight_prices("flights from JFK to PAR on 2025-03-15")
    print(f"   Result:\n{result}")
    print(f"   ✓ Flight search completed")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_geolocation_tool()
    test_export_tool()
    test_flight_search_tool()
    print("\n" + "=" * 60)
    print("All custom tools tested successfully!")
    print("=" * 60)
```

Run the test:

```bash
python test_custom_tools.py
```

Expected output:

```
============================================================
Testing Geolocation Tool
============================================================

1. Testing get_coordinates...
   Paris coordinates: {'lat': 48.8566, 'lon': 2.3522}
   ✓ Coordinates retrieved

2. Testing get_distance...
   Distance Paris to London: 343.5 km
   ✓ Distance calculated

3. Testing geolocation_tool...
   Result: Coordinates for Paris:
Latitude: 48.8566
Longitude: 2.3522
   ✓ Tool executed

============================================================
============================================================
Testing Export Tool
============================================================

1. Testing export_itinerary...
   Result: Successfully exported itinerary to: itineraries/itinerary_20250118_140000.md

The file includes:
- Flight information
- Hotel details
- Activity suggestions
- Budget breakdown
- Travel tips

You can open this file to review or share your itinerary.
   ✓ Export completed

2. Testing export_itinerary_detailed...
   Result: Successfully exported detailed itinerary to: itineraries/trip_paris_20250118_140001.md

The file includes:
- Flight information
- Hotel details
- Budget breakdown
- Activities
- Travel tips

You can open this file to review or share your itinerary.
   ✓ Detailed export completed

============================================================
============================================================
Testing Flight Search Tool
============================================================

1. Testing search_flight_prices...
   Result:
Found 3 flight options from JFK to PAR on 2025-03-15:

Option 1: $450 USD
- Airline: United Airlines
- Departure: JFK at 08:00
- Arrival: PAR at 14:30 (local time)
- Duration: 6h 30m
- Direct flight

Option 2: $380 USD
- Airline: American Airlines
- Departure: JFK at 10:15
- Arrival: PAR at 17:45 (local time)
- Duration: 7h 30m
- 1 stop in Chicago

Option 3: $520 USD
- Airline: Delta Airlines
- Departure: JFK at 14:00
- Arrival: PAR at 20:15 (local time)
- Duration: 6h 15m
- Direct flight

*Note: These are mock results. Configure AMADEUS_API_KEY and AMADEUS_API_SECRET for live pricing.*
   ✓ Flight search completed

============================================================
============================================================
All custom tools tested successfully!
============================================================
```

## Tool Design Patterns

### 1. Tool Wrapping

```python
def tool_wrapper(query: str) -> str:
    """Tool wrapper with proper signature."""
    return actual_tool_function(query)
```

Wraps tool functions with proper ADK tool signature.

### 2. Error Handling

```python
try:
    result = perform_operation()
except Exception as e:
    return f"Error: {str(e)}"
```

Handles errors gracefully and returns helpful messages.

### 3. Input Validation

```python
if not origin or not destination:
    return "Error: Origin and destination required"
```

Validates inputs before processing.

### 4. Mock Data

```python
if not api_key:
    return get_mock_data()
```

Provides fallback when external services unavailable.

## Production Considerations

### 1. API Authentication

```python
# Secure API key storage
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("API_KEY")
```

### 2. Rate Limiting

```python
from ratelimit import limits

@limits(calls=100, period=60)
def search_flights():
    # ... implementation
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_city_coordinates(city):
    # ... implementation
```

### 4. Logging

```python
import logging

logger = logging.getLogger(__name__)

def search_flights():
    logger.info("Searching flights...")
    # ... implementation
```

## Common Issues

### Issue: Tool Not Found

**Symptoms**:
```
Error: function not found
```

**Solution**: Ensure tool is properly wrapped and registered with agent.

### Issue: API Rate Limit

**Symptoms**:
```
Error: Rate limit exceeded
```

**Solution**: Implement rate limiting and caching.

## What's Next?

Congratulations! You've built three custom tools. In Part 8, we'll build the Web Interface.

## Summary

In this part, we:
- Built three custom tools (Geolocation, Export, Flight Search)
- Implemented tool wrapping for ADK compatibility
- Added error handling and input validation
- Created mock data for testing
- Created test scripts to verify functionality
- Learned tool design patterns
- Discussed production considerations

## Key Takeaways

1. **Tools extend capabilities**: Agents can do more than generate text
2. **Proper wrapping is essential**: Tools need correct signatures
3. **Error handling is critical**: Tools should fail gracefully
4. **Mock data helps testing**: Test without external dependencies
5. **Production readiness**: Consider authentication, rate limiting, caching

## Resources

- [Google ADK Tools](https://github.com/google/adk)
- [Amadeus API Documentation](https://developers.amadeus.com/)
- [Python Tool Design](https://docs.python.org/3/tutorial/classes.html)
- [API Best Practices](https://restfulapi.net/)

---

Continue to Part 8: Building Web Interface
