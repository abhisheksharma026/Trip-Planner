#!/bin/bash

# AI Trip Planner - Setup Script
# This script sets up a virtual environment and installs dependencies

set -e  # Exit on error

echo "=========================================="
echo "AI Trip Planner - Setup"
echo "=========================================="
echo ""

# Function to find a suitable Python 3.10+ executable
find_python3() {
    # Try common Python 3.x names in order of preference
    for py_cmd in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v $py_cmd &> /dev/null; then
            PYTHON_VERSION=$($py_cmd --version 2>&1 | cut -d' ' -f2)
            PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
            PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
            
            # Check if version is 3.10 or higher
            if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
                echo "$py_cmd"
                return 0
            fi
        fi
    done
    
    # Also check common installation paths
    for py_path in /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.13 \
                   /usr/local/bin/python3.11 /usr/local/bin/python3.12 /usr/local/bin/python3.13; do
        if [ -f "$py_path" ] && [ -x "$py_path" ]; then
            PYTHON_VERSION=$($py_path --version 2>&1 | cut -d' ' -f2)
            PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
            PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
            
            if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
                echo "$py_path"
                return 0
            fi
        fi
    done
    
    return 1
}

# Find suitable Python executable
PYTHON_CMD=$(find_python3)

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.10 or higher is required but not found."
    echo "Please install Python 3.10 or higher, or ensure it's in your PATH."
    echo ""
    echo "If you have Python 3.11+ installed (e.g., at /opt/homebrew/bin/python3.11),"
    echo "you can specify it by setting PYTHON_CMD:"
    echo "  export PYTHON_CMD=/opt/homebrew/bin/python3.11"
    echo "  ./setup.sh"
    exit 1
fi

# Allow override via environment variable
if [ -n "$PYTHON_CMD_ENV" ]; then
    if [ -f "$PYTHON_CMD_ENV" ] && [ -x "$PYTHON_CMD_ENV" ]; then
        PYTHON_CMD="$PYTHON_CMD_ENV"
    fi
fi

# Get Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "Found Python $PYTHON_VERSION at: $PYTHON_CMD"

# Verify version one more time
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "Error: Python 3.10 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi

echo "Python version check passed (3.10+ required)"

# Create virtual environment if it doesn't exist or if Python version is too old
RECREATE_VENV=false
if [ ! -d "venv" ]; then
    RECREATE_VENV=true
    echo ""
    echo "Creating virtual environment..."
else
    # Check Python version in existing venv
    VENV_PYTHON_VERSION=$(venv/bin/python --version 2>&1 | cut -d' ' -f2)
    VENV_MAJOR=$(echo $VENV_PYTHON_VERSION | cut -d'.' -f1)
    VENV_MINOR=$(echo $VENV_PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$VENV_MAJOR" -lt 3 ] || ([ "$VENV_MAJOR" -eq 3 ] && [ "$VENV_MINOR" -lt 10 ]); then
        echo ""
        echo "Existing virtual environment uses Python $VENV_PYTHON_VERSION (requires 3.10+)"
        echo "Recreating virtual environment with Python $PYTHON_VERSION..."
        rm -rf venv
        RECREATE_VENV=true
    else
        echo "Virtual environment already exists with Python $VENV_PYTHON_VERSION"
    fi
fi

if [ "$RECREATE_VENV" = true ]; then
    $PYTHON_CMD -m venv venv
    echo "Virtual environment created with Python $PYTHON_VERSION"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Set your API key (choose one method):"
echo ""
echo "   Option 1 - Create .env file (Recommended):"
echo "   echo 'GOOGLE_API_KEY=your_api_key_here' > .env"
echo ""
echo "   Option 2 - Environment variable:"
echo "   export GOOGLE_API_KEY=your_api_key_here"
echo ""
echo "   Get your key from: https://aistudio.google.com/app/apikey"
echo ""
echo "2. Run the application:"
echo "   ./run.sh"
echo ""
echo "   Or for web app:"
echo "   ./run.sh web"
echo ""
echo "   Or for CLI:"
echo "   ./run.sh cli"
echo ""

