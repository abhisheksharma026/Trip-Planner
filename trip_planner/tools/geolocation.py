"""
Geolocation tool for converting city names to coordinates.
In production, this would integrate with Google Maps Geocoding API.
"""

# City coordinates database (mock implementation)
# In production, replace with Google Maps Geocoding API
CITY_COORDINATES = {
    "paris": {"lat": 48.8566, "lon": 2.3522, "country": "France"},
    "london": {"lat": 51.5074, "lon": -0.1278, "country": "UK"},
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "country": "Japan"},
    "new york": {"lat": 40.7128, "lon": -74.0060, "country": "USA"},
    "san francisco": {"lat": 37.7749, "lon": -122.4194, "country": "USA"},
    "lisbon": {"lat": 38.7223, "lon": -9.1393, "country": "Portugal"},
    "barcelona": {"lat": 41.3851, "lon": 2.1734, "country": "Spain"},
    "rome": {"lat": 41.9028, "lon": 12.4964, "country": "Italy"},
    "dubai": {"lat": 25.2048, "lon": 55.2708, "country": "UAE"},
    "sydney": {"lat": -33.8688, "lon": 151.2093, "country": "Australia"},
    "amsterdam": {"lat": 52.3676, "lon": 4.9041, "country": "Netherlands"},
    "berlin": {"lat": 52.5200, "lon": 13.4050, "country": "Germany"},
    "madrid": {"lat": 40.4168, "lon": -3.7038, "country": "Spain"},
    "vienna": {"lat": 48.2082, "lon": 16.3738, "country": "Austria"},
    "prague": {"lat": 50.0755, "lon": 14.4378, "country": "Czech Republic"},
    "istanbul": {"lat": 41.0082, "lon": 28.9784, "country": "Turkey"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "country": "Singapore"},
    "hong kong": {"lat": 22.3193, "lon": 114.1694, "country": "Hong Kong"},
    "seoul": {"lat": 37.5665, "lon": 126.9780, "country": "South Korea"},
    "mumbai": {"lat": 19.0760, "lon": 72.8777, "country": "India"},
    "bangkok": {"lat": 13.7563, "lon": 100.5018, "country": "Thailand"},
    "cairo": {"lat": 30.0444, "lon": 31.2357, "country": "Egypt"},
    "rio de janeiro": {"lat": -22.9068, "lon": -43.1729, "country": "Brazil"},
    "buenos aires": {"lat": -34.6037, "lon": -58.3816, "country": "Argentina"},
    "mexico city": {"lat": 19.4326, "lon": -99.1332, "country": "Mexico"},
    "los angeles": {"lat": 34.0522, "lon": -118.2437, "country": "USA"},
    "chicago": {"lat": 41.8781, "lon": -87.6298, "country": "USA"},
    "miami": {"lat": 25.7617, "lon": -80.1918, "country": "USA"},
    "toronto": {"lat": 43.6532, "lon": -79.3832, "country": "Canada"},
    "vancouver": {"lat": 49.2827, "lon": -123.1207, "country": "Canada"}
}


def get_city_coordinates(city_name: str) -> dict:
    """
    Converts a city name into geographic coordinates (latitude and longitude).
    
    This tool helps other agents understand the location for flight searches,
    hotel recommendations, and distance calculations.
    
    Args:
        city_name: The name of the city (e.g., "Paris", "New York", "Tokyo")
    
    Returns:
        A dictionary with 'lat', 'lon', 'country', and 'city' fields.
        Returns an error status if the city is not found.
    """
    print(f"TOOL CALLED: get_city_coordinates(city_name='{city_name}')")
    
    normalized_city = city_name.lower().strip()
    
    # Try exact match first
    if normalized_city in CITY_COORDINATES:
        coords = CITY_COORDINATES[normalized_city].copy()
        coords["city"] = city_name
        return {"status": "success", **coords}
    
    # Try partial match
    for key, value in CITY_COORDINATES.items():
        if key in normalized_city or normalized_city in key:
            coords = value.copy()
            coords["city"] = city_name
            return {"status": "success", **coords}
    
    return {
        "status": "error",
        "message": f"City '{city_name}' not found in database. Available cities: {', '.join(sorted(CITY_COORDINATES.keys()))}"
    }

