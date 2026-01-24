# Building a Production-Grade AI Agent from Scratch - Part 2: Configuration and Environment

## Overview

In Part 1, we introduced the architecture and project structure. Now, let's get our development environment set up. This is foundational work that everything else will build upon.

## What We'll Build

In this part, we'll create:

1. **Configuration Module** - Manages API keys, model settings, and observability
2. **Virtual Environment** - Isolates project dependencies
3. **Dependency Installation** - Installs all required packages
4. **Environment Variables** - Sets up API keys and configuration

## Why This Matters

### Configuration is Critical

Without proper configuration, our agent will:
- Fail to start (missing API keys)
- Be hard to test (hardcoded values)
- Be difficult to deploy (environment-specific settings)
- Lack observability (can't track behavior)

### Environment Isolation

Virtual environments ensure:
- **Dependency Isolation**: Different projects don't conflict
- **Python Version Control**: Use specific Python version (3.10+)
- **Clean Workspace**: Easy to start fresh if needed

## Step 1: Create Project Structure

First, let's create our directory structure. Open your terminal and run:

```bash
# Create main project directory
mkdir trip-planner
cd trip-planner

# Create package structure
mkdir -p trip_planner/{agents,tools,core}
mkdir -p templates static/{css,js}

# Create empty __init__.py files for Python packages
touch trip_planner/__init__.py
touch trip_planner/agents/__init__.py
touch trip_planner/tools/__init__.py
touch trip_planner/core/__init__.py
```

This creates:

```
trip-planner/
├── trip_planner/
│   ├── __init__.py
│   ├── agents/
│   │   └── __init__.py
│   ├── tools/
│   │   └── __init__.py
│   └── core/
│       └── __init__.py
├── templates/
├── static/
│   ├── css/
│   └── js/
```

## Step 2: Create Virtual Environment

Virtual environments are crucial for Python projects. They isolate your project dependencies from your system Python.

```bash
# Create a virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment

# On macOS/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

**You'll know your virtual environment is active when you see `(venv)` at the beginning of your terminal prompt.**

## Step 3: Create Requirements File

Now let's define all the dependencies we need. Create a `requirements.txt` file in your project root:

```bash
cd trip-planner

cat > requirements.txt << 'EOF'
google-adk>=0.1.0
google-generativeai>=0.3.0
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
jinja2>=3.1.0
python-dotenv>=1.0.0
opik>=0.1.0
httpx>=0.25.0
EOF
```

This file includes:

- **google-adk**: Agent Development Kit for building multi-agent systems
- **google-generativeai**: Google's generative AI library (for Gemini models)
- **fastapi**: Modern, fast web framework
- **uvicorn**: ASGI server to run FastAPI applications
- **python-dotenv**: Load environment variables from .env files
- **opik**: Observability platform for tracking agent behavior
- **httpx**: Modern HTTP client for async requests
- **jinja2**: Template engine for HTML rendering
- **python-multipart**: Support for file uploads in FastAPI

## Step 4: Install Dependencies

Now let's install all the packages:

```bash
# Make sure you're in the virtual environment
# You should see (venv) at the start of your prompt

# Install all dependencies
pip install -r requirements.txt
```

This will download and install all the packages listed in requirements.txt.

## Step 5: Get Google API Key

We need a Google API key to use Google's AI services. Here's how to get one:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key (it starts with `AIzaSy...`)

## Step 6: Configure API Key

There are two ways to configure your API key:

### Option 1: Using .env File (Recommended)

Create a `.env` file in your project root:

```bash
cd trip-planner

cat > .env << 'EOF'
GOOGLE_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-2.5-flash
EOF
```

Replace `your_actual_api_key_here` with your actual API key from Google AI Studio.

**Why .env?**
- Keeps sensitive data out of your code
- Easy to configure for different environments (dev, staging, prod)
- Standard practice in production applications

### Option 2: Environment Variable

Set it directly in your terminal:

```bash
# On macOS/Linux:
export GOOGLE_API_KEY=your_actual_api_key_here

# On Windows (Command Prompt):
set GOOGLE_API_KEY=your_actual_api_key_here

# On Windows (PowerShell):
$env:GOOGLE_API_KEY="your_actual_api_key_here"
```

**Note**: If you use this method, you'll need to set it every time you open a new terminal.

## Step 7: Configure Opik (Optional)

Opik is an observability platform that helps us track and analyze our agent's behavior. It's optional but highly recommended.

### Get Opik API Key

1. Go to [Comet](https://www.comet.com/)
2. Sign up or log in
3. Create a workspace
4. Generate an API key

### Configure Opik

Add to your `.env` file:

```bash
cat >> .env << 'EOF'

# Opik Configuration (Optional)
OPIK_API_KEY=your_opik_api_key_here
OPIK_WORKSPACE=default
OPIK_PROJECT_NAME=AI Travel Planner
EOF
```

**If you don't have Opik**: Don't worry! The code will work without it. Observability features will simply be disabled.

## Step 8: Verify Installation

Let's verify everything is installed correctly:

```bash
# Check Python version (should be 3.10+)
python --version

# Check if packages are installed
pip list | grep -E "google|fastapi|opik"

# Test Google ADK import
python -c "import google.adk; print('ADK installed successfully')"

# Test FastAPI import
python -c "import fastapi; print('FastAPI installed successfully')"

# Test Generative AI import
python -c "import google.generativeai; print('Generative AI installed successfully')"
```

Expected output:

```
Python 3.11.0
google-adk           0.1.0
google-generativeai    0.3.0
fastapi               0.109.0
opik                  0.1.0

ADK installed successfully!
FastAPI installed successfully!
Generative AI installed successfully!
```

## Step 9: Create .gitignore

To prevent committing sensitive data and unnecessary files to version control:

```bash
cd trip-planner

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
itineraries/
*.log
EOF
```

## Common Issues and Solutions

### Issue: Python Version Too Old

**Symptom:**
```
MCP requires Python 3.10 or above
```

**Solution:**
```bash
# Check your Python version
python --version

# If it's older than 3.10, install Python 3.10+ and recreate venv
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Module Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'google.adk'
```

**Solution:**
```bash
# Make sure you're in the virtual environment
# You should see (venv) at the start of your prompt
which python

# If not showing venv/bin/python, activate it:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: API Key Not Found

**Symptom:**
```
GOOGLE_API_KEY not found in environment variables or .env file.
```

**Solution:**
```bash
# Check if .env file exists
cat .env

# Verify API key is set
echo $GOOGLE_API_KEY

# If empty, add it:
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### Issue: Permission Denied

**Symptom:**
```
Permission denied: ./setup.sh
```

**Solution:**
```bash
# Make script executable
chmod +x setup.sh

# Or run directly with bash
bash setup.sh
```

## What We've Accomplished

In this part, we:
- Created project directory structure
- Set up a virtual environment
- Installed all required dependencies
- Configured Google API key
- Optionally configured Opik for observability
- Verified installation
- Created .gitignore for version control

## What's Next

Congratulations! Your development environment is now set up. In Part 3, we'll build the core configuration module that will manage our API keys and settings throughout the application.

## Summary

### Key Takeaways

1. **Virtual Environments**: Essential for isolating project dependencies
2. **Requirements Files**: Define all dependencies in one place
3. **Environment Variables**: Secure way to manage API keys
4. **.env Files**: Standard practice for configuration management
5. **Verification**: Always test your installation before proceeding

### Files Created

- `requirements.txt` - All project dependencies
- `.env` - Configuration file (you'll add your API key)
- `.gitignore` - Files to exclude from version control

### Next Steps

In Part 3, we'll create the configuration module that will:
- Load API keys from environment variables
- Configure Google Generative AI SDK
- Set up Opik for observability
- Provide model configuration

## Resources

- [Python Virtual Environments](https://docs.python.org/3/library/venv.html)
- [Python pip Documentation](https://pip.pypa.io/en/stable/)
- [Google AI Studio](https://aistudio.google.com/)
- [Opik Documentation](https://www.comet.com/site/products/opik/)
- [Environment Variables Best Practices](https://12factor.net/blog/environment-variables/)

---

Continue to Part 3: Configuration Module
