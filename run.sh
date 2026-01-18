#!/bin/bash

# AI Trip Planner - Run Script
# This script activates the virtual environment and runs the application

set -e  # Exit on error

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if API key is set
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Warning: GOOGLE_API_KEY environment variable is not set."
    echo "The application will prompt you to enter it."
    echo ""
fi

# Determine which mode to run
MODE=${1:-web}

case $MODE in
    web)
        echo "=========================================="
        echo "Starting AI Trip Planner Web App"
        echo "=========================================="
        echo ""
        
        # Check if port 5000 is in use
        if command -v lsof &> /dev/null; then
            if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo "Port 5000 is already in use."
                echo "The app will automatically find an available port."
                echo ""
            fi
        fi
        
        echo "Server will start on: http://localhost:5000 (or next available port)"
        echo "Press Ctrl+C to stop the server"
        echo ""
        python app.py
        ;;
    cli)
        echo "=========================================="
        echo "Starting AI Trip Planner CLI"
        echo "=========================================="
        echo ""
        if [ -n "$2" ]; then
            # Single query mode
            python main.py "$2"
        else
            # Interactive mode
            python main.py
        fi
        ;;
    *)
        echo "Usage: ./run.sh [web|cli] [query]"
        echo ""
        echo "Examples:"
        echo "  ./run.sh          # Start web app (default)"
        echo "  ./run.sh web       # Start web app"
        echo "  ./run.sh cli       # Start CLI in interactive mode"
        echo "  ./run.sh cli 'I want to plan a trip to Paris'  # Single query"
        exit 1
        ;;
esac

