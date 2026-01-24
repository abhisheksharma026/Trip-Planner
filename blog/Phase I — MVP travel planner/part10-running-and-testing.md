# Building a Production-Grade AI Agent from Scratch - Part 10: Running and Testing Agent

## Overview

In Part 9, we added observability with Opik. Now, let's run and test our complete agent system. This is the final part of Phase I - MVP, where we'll verify everything works together.

## What We'll Test

We'll test:

1. **Configuration**: Environment setup and API keys
2. **Session Management**: Creating and managing sessions
3. **Specialized Agents**: All five agents working correctly
4. **Concierge Orchestrator**: Coordinating all agents
5. **Custom Tools**: Geolocation, Export, Flight Search
6. **Web Interface**: FastAPI backend and frontend
7. **Observability**: Opik traces and spans
8. **End-to-End**: Complete user workflows

## Testing Architecture

```
┌─────────────────────────────────────────────────┐
│         Test Suite                  │
│  ┌─────────────────────────────────────┐  │
│  │  Unit Tests                        │  │
│  │  - Configuration                   │  │
│  │  - Session Manager                 │  │
│  │  - Agents                         │  │
│  │  - Tools                          │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  Integration Tests                │  │
│  │  - Agent coordination              │  │
│  │  - Tool integration               │  │
│  │  - Session management             │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │  End-to-End Tests                │  │
│  │  - Complete workflows             │  │
│  │  - Web interface                 │  │
│  │  - Observability                 │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Prerequisites

Before testing, ensure you have:

1. **Environment Setup** (from Part 2)
2. **API Keys** (from Part 3)
3. **Dependencies Installed** (from Part 2)
4. **Opik Configured** (from Part 9, optional)

Check your environment:

```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|google-adk|opik)"

# Check environment variables
cat .env
```

## Running Tests

### 1. Configuration Test

Test that configuration is set up correctly:

```bash
# Test configuration
python -c "
from trip_planner.config import initialize_config, get_model_name

initialize_config()
print('Configuration initialized successfully!')
print(f'Model: {get_model_name()}')
"
```

Expected output:

```
Configuration initialized successfully!
Model: gemini-2.5-flash
```

### 2. Session Manager Test

Test session management by running the web interface and verifying sessions are created properly:

```bash
python app.py
```

Then open your browser to `http://localhost:8000` and interact with the agent. The session manager will automatically create sessions for each user.

### 3. Specialized Agents Test

Test specialized agents by running the web interface and verifying agents are loaded:

```bash
python app.py
```

Open `http://localhost:8000` and interact with the agent. The concierge will automatically load and coordinate all specialized agents.

### 4. Concierge Test

Test concierge orchestrator by running the web interface:

```bash
python app.py
```

Open `http://localhost:8000` and interact with the agent. The concierge will coordinate all specialized agents automatically.

### 5. Custom Tools Test

Test custom tools by running the web interface:

```bash
python app.py
```

Open `http://localhost:8000` and interact with the agent. Try queries like:
- "What are the coordinates of Paris?"
- "Export my itinerary"
- "Find flights from JFK to PAR on 2025-03-15"

### 6. Opik Integration Test

Test Opik observability by running the web interface with Opik configured:

```bash
python app.py
```

Open `http://localhost:8000` and interact with the agent. With Opik configured, traces and spans will be automatically created for each conversation.

Check your Opik dashboard to view traces and spans:
https://www.comet.com/site/products/opik/

### 7. Web Interface Test

Test the web interface:

```bash
# Start the web server
python app.py
```

Expected output:

```
Starting server on port 8000
Configuration initialized
Session manager initialized
Concierge agent initialized
Runner initialized
Application startup complete!
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Now open your browser and navigate to `http://localhost:8000`. You should see:

1. A beautiful gradient interface
2. A welcome message from the assistant
3. Sample queries to click on
4. An input field to type your queries
5. A feedback form

Try the following:

1. **Click on a sample query** - e.g., "I want to plan a trip to Paris in March 2025 with a $1,500 budget"
2. **Type your own query** - e.g., "Find me flights from New York to London for next week"
3. **Submit feedback** - After receiving a response, provide feedback

### 8. CLI Interactive Test

Test the CLI interactive mode:

```bash
python main.py
```

Expected output:

```
AI Travel Planner - Interactive Mode
Type 'exit' or 'quit' to end the conversation
--------------------------------------------------

You: I want to plan a trip to Paris in March 2025

Assistant: Great! I can help you plan a trip to Paris in March 2025. To provide you with the best recommendations, I need a bit more information:

1. What's your budget for this trip?
2. When exactly in March are you planning to travel? (specific dates)
3. How many people will be traveling?
4. How many days/nights are you planning to stay?

Once you provide these details, I can search for flights, hotels, and activities that match your preferences!

You: My budget is $1,500, I'm traveling March 15-18, 2025, just me, for 3 nights

Assistant: Perfect! Based on your constraints (budget: $1,500, dates: March 15-18, 2025, 1 traveler, 3 nights), I've found some great options:

Flight Options:
Option 1: $450 - United Airlines, Direct, 6h 30m
Option 2: $380 - American Airlines, 1 stop, 7h 30m

Hotel Options:
Option 1: $180/night - Grand Hotel, 4.5 stars, Downtown
Option 2: $120/night - City Inn, 4.2 stars, Midtown

Total Cost:
- Flights: $450
- Hotels (3 nights): $540
- Estimated activities: $150
- Estimated food: $120
- TOTAL: $1,260 (within your $1,500 budget)

Recommendation:
I recommend Option 1 for flights (direct is worth the extra $70) and Option 1 for hotels (excellent location and amenities). This gives you a great experience while staying within budget.

Would you like me to:
- Adjust any of these options?
- Get more information about any option?
- Export this itinerary?
- Help with anything else?

You: What if I increase my budget to $2,000?

Assistant: If you increase your budget to $2,000:

New Options:
- Flights: $550 (business class upgrade available)
- Hotels: $250/night (luxury hotel option)
- Activities: $250 (premium experiences)
- Food: $180 (fine dining options)
- NEW TOTAL: $1,730

Comparison:
- Previous total: $1,260
- New total: $1,730
- Difference: +$470

With the higher budget, you get:
- Better flight options (business class)
- Luxury hotel with spa and amenities
- Premium activities and experiences
- Fine dining options

Would you like to proceed with these options, or would you prefer to stick with the original recommendations?

You: Export my itinerary

Assistant: I've exported your itinerary to: itineraries/trip_paris_march_2025.md

The file includes:
- Flight details
- Hotel information
- Cost breakdown
- Activity suggestions
- Travel tips

You can open this file to review or share your itinerary.

You: exit

Ending conversation. Goodbye!
```

## End-to-End Test Scenarios

### Scenario 1: Simple Trip Planning

**User Query**: "I want to plan a trip to Paris in March 2025 with a $1,500 budget"

**Expected Behavior**:
1. Concierge acknowledges request
2. Asks for missing details (dates, number of people, duration)
3. User provides details
4. Concierge checks constraints
5. Concierge routes to Flight Recommender
6. Concierge routes to Hotel Specialist
7. Concierge routes to Financial Planner
8. Concierge routes to Safety Checker
9. Concierge presents recommendations with explanations

### Scenario 2: What-If Scenario

**User Query**: "What if I increase my budget to $2,000?"

**Expected Behavior**:
1. Concierge acknowledges change
2. Concierge re-checks constraints
3. Concierge gets new recommendations
4. Concierge compares with previous options
5. Concierge explains impact of change
6. Concierge presents new options

### Scenario 3: Constraint Violation

**User Query**: "I want to plan a week in Paris with a $500 budget"

**Expected Behavior**:
1. Concierge identifies constraint violation
2. Concierge explains issue politely
3. Concierge suggests alternatives
4. Concierge offers to help with alternatives

### Scenario 4: Export Itinerary

**User Query**: "Export my itinerary to a file"

**Expected Behavior**:
1. Concierge calls export tool
2. Concierge confirms file location
3. Concierge explains what was saved

## Performance Testing

### Response Time

Test average response time:

```bash
python -c "
import time
import asyncio
from trip_planner.config import initialize_config
from trip_planner.core.session_manager import SessionManager
from trip_planner.core.runner import TripPlannerRunner
from trip_planner.agents.concierge import create_concierge

async def test_response_time():
    initialize_config()
    session_manager = SessionManager()
    concierge = create_concierge()
    runner = TripPlannerRunner(session_manager, concierge)
    
    query = 'I want to plan a trip to Paris in March 2025'
    
    start = time.time()
    response = await runner.run_query(query, 'test_user')
    end = time.time()
    
    print(f'Response time: {end - start:.2f} seconds')
    print(f'Response length: {len(response)} characters')

asyncio.run(test_response_time())
"
```

### Memory Usage

Monitor memory usage during extended conversations:

```bash
python -c "
import psutil
import os

process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

## Troubleshooting

### Issue: Import Errors

**Symptoms**:
```
ModuleNotFoundError: No module named 'trip_planner'
```

**Solution**:
```bash
# Ensure you're in the project root
cd /path/to/trip-planner

# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: API Key Errors

**Symptoms**:
```
Error: API key not found
```

**Solution**:
```bash
# Check .env file exists
ls -la .env

# Check environment variables
echo $GOOGLE_API_KEY

# Reload .env file
source .env
```

### Issue: Port Already in Use

**Symptoms**:
```
OSError: [Errno 48] Address already in use
```

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
python app.py  # Will automatically find available port
```

### Issue: Opik Not Working

**Symptoms**:
```
Could not initialize Opik client
```

**Solution**:
```bash
# Check Opik API key
echo $OPIK_API_KEY

# Install Opik
pip install opik

# Test Opik connection
python -c "
import opik
client = opik.Opik(project_name='test')
print('Opik client initialized successfully!')
"
```

## Production Checklist

Before deploying to production, ensure:

- [ ] All API keys are configured
- [ ] Environment variables are set
- [ ] Dependencies are installed
- [ ] Tests pass
- [ ] Web interface works
- [ ] Observability is configured
- [ ] Error handling is in place
- [ ] Logging is enabled
- [ ] Rate limiting is configured
- [ ] Authentication is set up
- [ ] HTTPS is enabled
- [ ] Database is configured
- [ ] Backup strategy is in place
- [ ] Monitoring is set up
- [ ] Documentation is complete

## Next Steps

Congratulations! You've completed Phase I - MVP of your production-grade AI agent. Here's what you can do next:

### Phase II - Enhancements

1. **Authentication**: Add user authentication and authorization
2. **Persistent Storage**: Store sessions and conversations in a database
3. **Infrastructure**: Deploy to cloud (AWS, GCP, Azure)
4. **Performance**: Optimize response times and resource usage
5. **Security**: Add security best practices

### Phase III - Advanced Features

1. **Multi-Modal Support**: Add image and voice input
2. **Personalization**: Learn user preferences over time
3. **Real-Time Updates**: Live flight and hotel prices
4. **Social Features**: Share itineraries with friends
5. **Mobile App**: Build native mobile applications

### Phase IV - Scaling

1. **Load Balancing**: Handle multiple concurrent users
2. **Caching**: Cache frequent queries and responses
3. **Microservices**: Split into microservices architecture
4. **Global Deployment**: Deploy to multiple regions
5. **Analytics**: Advanced analytics and insights

## Summary

In this part, we:
- Ran comprehensive tests on all components
- Verified configuration and environment setup
- Tested session management
- Tested all specialized agents
- Tested concierge orchestrator
- Tested custom tools
- Tested web interface
- Tested observability with Opik
- Ran end-to-end test scenarios
- Performed performance testing
- Troubleshooting common issues
- Created production checklist

## Key Takeaways

1. **Testing is critical**: Verify everything works before deployment
2. **End-to-end testing**: Test complete workflows, not just components
3. **Performance matters**: Monitor response times and resource usage
4. **Troubleshooting skills**: Know how to debug common issues
5. **Production readiness**: Have a checklist before deploying

## What You've Built

You've successfully built a production-grade AI agent system with:

- Multi-agent architecture with specialized agents
- Session management for conversational context
- Custom tools for real-world functionality
- Modern web interface with FastAPI
- Observability with Opik
- Comprehensive testing and documentation

This is a solid foundation for a production AI application. Continue building and improving!

## Resources

- [Google ADK Documentation](https://github.com/google/adk)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Opik Documentation](https://www.comet.com/site/products/opik/)
- [Python Testing](https://docs.python.org/3/library/unittest.html)
- [Production Deployment](https://www.djangoproject.com/start/deployment/)

---

Congratulations! You've completed Phase I - MVP of Building a Production-Grade AI Agent from Scratch!

Ready for Phase II? Check back for upcoming articles on Authentication, Persistent Storage, and Infrastructure Setup.
