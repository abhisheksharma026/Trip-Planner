#!/bin/bash

# Script to recreate virtual environment with correct Python version

set -e  # Exit on error

echo "=========================================="
echo "Recreating Virtual Environment"
echo "=========================================="
echo ""

# Function to find a suitable Python 3.10+ executable
find_python3() {
    for py_cmd in python3.13 python3.12 python3.11 python3.10 python3; do
        if command -v $py_cmd &> /dev/null; then
            PYTHON_VERSION=$($py_cmd --version 2>&1 | cut -d' ' -f2)
            PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
            PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
            
            if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
                echo "$py_cmd"
                return 0
            fi
        fi
    done
    
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
    echo "Please install Python 3.10 or higher."
    exit 1
fi

# Allow override via environment variable
if [ -n "$PYTHON_CMD_ENV" ]; then
    if [ -f "$PYTHON_CMD_ENV" ] && [ -x "$PYTHON_CMD_ENV" ]; then
        PYTHON_CMD="$PYTHON_CMD_ENV"
    fi
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "Found Python $PYTHON_VERSION at: $PYTHON_CMD"
echo ""

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
    echo "Old virtual environment removed"
    echo ""
fi

# Create new virtual environment
echo "Creating new virtual environment with Python $PYTHON_VERSION..."
$PYTHON_CMD -m venv venv
echo "Virtual environment created"
echo ""

# Activate virtual environment
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
echo "Virtual environment recreated successfully!"
echo "=========================================="
echo ""
echo "You can now run the application:"
echo "  ./run.sh"
echo ""

