# Web Application Quick Start Guide

## Starting the Web App

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key** (or enter when prompted):
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

3. **Start the server**:
   ```bash
   python app.py
   ```

4. **Open your browser**:
   Navigate to `http://localhost:5000`

## Sample Queries

The web interface includes 5 sample queries that demonstrate the agent's capabilities:

### 1. Complete Trip Planning
**Query:**
```
Hi! I want to plan a trip to Paris, France. I'm traveling from San Francisco on March 15, 2025 and returning on March 22, 2025. My budget is $3000 total. I prefer direct flights and hate long layovers.
```

**What it demonstrates:**
- Full trip planning workflow
- Flight recommendations with preferences
- Hotel suggestions
- Budget analysis
- Preference memory (no long layovers)

### 2. Vague Request
**Query:**
```
I want to go somewhere warm next week.
```

**What it demonstrates:**
- Agent asks clarifying questions
- Handles incomplete information
- Proactive information gathering

### 3. Hotel Search
**Query:**
```
Find me hotels in Tokyo for March 10-17, 2025. I'd like something central, around $200 per night, with a gym and breakfast included.
```

**What it demonstrates:**
- Specific hotel search
- Multiple preference handling
- Budget constraints
- Amenity requirements

### 4. Flight Search
**Query:**
```
I need flights from New York to London departing on April 1, 2025 and returning April 10. My budget is $800 and I prefer non-stop flights.
```

**What it demonstrates:**
- Flight search with specific dates
- Budget constraints
- Flight preference (non-stop)
- Round-trip planning

### 5. Budget Analysis
**Query:**
```
I've found flights for $600 and hotels for $150/night for 5 nights. Can you analyze if this fits my $2000 budget and suggest activities?
```

**What it demonstrates:**
- Financial analysis
- Budget comparison
- Cost breakdown
- Activity recommendations

## Using the Web Interface

### Chat Interface
- Type your query in the input box
- Press Enter or click Send
- The agent will respond with recommendations
- Continue the conversation naturally

### Sample Queries Panel
- Click on any sample query card
- The query will be populated in the input box
- Click Send or modify the query first

### New Session Button
- Click "New Session" to start fresh
- This clears conversation history
- Useful for planning a different trip

## Expected Query Formats

### Good Query Examples:
**Complete Information:**
```
I want to plan a trip to Barcelona from June 1-7, 2025. My budget is $2500. I'm traveling from Los Angeles and prefer direct flights.
```

**Specific Search:**
```
Find hotels in Paris near the Eiffel Tower for March 20-25, 2025. Budget is $200 per night.
```

**Follow-up Questions:**
```
Can you also check flights for my return trip?
What about activities in the area?
```

### Less Effective Queries:
**Too Vague:**
```
I want to travel somewhere.
```

**Missing Key Information:**
```
Find me a hotel.
```

**Tip:** The agent will ask clarifying questions, but providing complete information upfront gets better results faster.

## Features

- **Real-time Chat**: Instant responses from the AI agent
- **Session Memory**: The agent remembers your preferences throughout the conversation
- **Multi-Agent System**: Specialized agents handle flights, hotels, and finances
- **Source Citations**: All recommendations include sources
- **Budget Tracking**: Automatic cost analysis and budget comparison
- **Responsive Design**: Works on desktop, tablet, and mobile

## Troubleshooting

**Server won't start:**
- Check that port 5000 is available
- Verify your API key is set correctly
- Check that all dependencies are installed

**No response from agent:**
- Check browser console for errors
- Verify the Flask server is running
- Check API key is valid

**Session issues:**
- Click "New Session" to reset
- Refresh the page if needed

## Next Steps

After trying the sample queries, try:
1. Planning your own trip with specific dates and preferences
2. Asking follow-up questions about recommendations
3. Requesting budget analysis for your planned trip
4. Exporting your itinerary (when implemented)

Happy trip planning!

