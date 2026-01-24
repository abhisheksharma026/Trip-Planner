# Building a Production-Grade AI Agent from Scratch - Part 3: Configuration Module

## Overview

In Part 2, we set up our development environment and installed dependencies. Now, let's build the **configuration module** - a critical component that manages API keys, model settings, and observability configuration throughout our application.

## Why Configuration Matters

In production systems, configuration is not just about storing API keys. It's about:

1. **Security**: Keeping sensitive data out of code
2. **Flexibility**: Easy to change settings without code changes
3. **Environment Awareness**: Different configs for dev, staging, and production
4. **Validation**: Ensuring required settings are present before running
5. **Observability**: Setting up tracking and monitoring

## Understanding the Configuration Module

Our configuration module needs to handle:

- **API Key Management**: Securely load and validate Google API key
- **Model Configuration**: Allow model switching (e.g., gemini-2.5-flash vs gemini-2.5-pro)
- **Opik Setup**: Configure observability platform (optional but recommended)
- **Environment Variables**: Load from .env file or system environment
- **Graceful Degradation**: Work even if optional components fail

## Building the Configuration Module

Let's create our configuration module. Create `trip_planner/config.py`:

```python
"""
Configuration module for Trip Planner application.
Handles environment variables and API key setup.
"""

import os
from getpass import getpass
from pathlib import Path
import google.generativeai as genai

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root (where app.py/main.py are located)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"Loading .env file from: {env_path}")
    else:
        # Also try loading from current directory
        load_dotenv(override=True)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass
except Exception as e:
    # If there's an error loading .env, continue anyway
    print(f"Warning: Could not load .env file: {e}")


def setup_api_key():
    """
    Configure Google API key from environment variable, .env file, or prompt user.
    
    This function tries multiple sources in order:
    1. Environment variable GOOGLE_API_KEY
    2. .env file
    3. User prompt (interactive mode)
    
    Returns:
        str: The configured API key
    
    Raises:
        ValueError: If no API key can be found
    """
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not api_key:
        print("GOOGLE_API_KEY not found in environment variables or .env file.")
        print("Make sure you have a .env file in the project root with:")
        api_key = getpass('Enter your Google API Key (from https://aistudio.google.com/app/apikey): ')
    else:
        print("API Key loaded from environment/.env file")
    
    # Validate API key format
    if not api_key or len(api_key) < 10:
        raise ValueError("Invalid API key format. API keys are typically 39 characters long.")
    
    # Configure the generative AI library
    genai.configure(api_key=api_key)
    
    # Set environment variable for ADK
    os.environ['GOOGLE_API_KEY'] = api_key
    
    print("API Key configured successfully!")
    return api_key


def get_model_name():
    """
    Get the default model name for agents.
    
    This allows easy model switching without code changes.
    Set GEMINI_MODEL environment variable to override default.
    
    Returns:
        str: Model name (e.g., 'gemini-2.5-flash')
    """
    return os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')


def setup_opik():
    """
    Configure Opik for observability tracking.
    Sets environment variables that Opik SDK will read.
    
    Opik is optional - if not configured, the application
    will still work, just without observability features.
    
    Returns:
        bool: True if Opik is configured successfully, False otherwise
    """
    try:
        import opik
        
        # Get Opik configuration from environment
        api_key = os.environ.get('OPIK_API_KEY')
        workspace = os.environ.get('OPIK_WORKSPACE', 'default')
        project_name = os.environ.get('OPIK_PROJECT_NAME', 'AI Travel Planner')
        url_override = os.environ.get('OPIK_URL_OVERRIDE')
        
        if not api_key:
            print("OPIK_API_KEY not found in environment variables or .env file.")
            # Set default project name even if API key is missing (for when it's added later)
            os.environ['OPIK_PROJECT_NAME'] = project_name
            return False
        
        # Set environment variables for Opik SDK
        # The SDK reads from these environment variables
        os.environ['OPIK_API_KEY'] = api_key
        os.environ['OPIK_WORKSPACE'] = workspace
        os.environ['OPIK_PROJECT_NAME'] = project_name
        if url_override:
            os.environ['OPIK_URL_OVERRIDE'] = url_override
        
        # Try to configure using CLI-style configuration if available
        # The SDK will read from environment variables automatically
        try:
            # Check if tracing is active (indicates successful configuration)
            if hasattr(opik, 'is_tracing_active'):
                # Enable tracing if not already enabled
                if hasattr(opik, 'set_tracing_active'):
                    opik.set_tracing_active(True)
        except Exception:
            pass  # SDK will use environment variables
        
        print(f"Opik configured successfully!")
        print(f"Project: {project_name}")
        print(f"Workspace: {workspace}")
        return True
        
    except ImportError:
        print("Opik package not installed. Install with: pip install opik")
        return False
    except Exception as e:
        print(f"Error configuring Opik: {e}")
        return False
```

## Understanding Each Function

### setup_api_key()

This is our main configuration function. Let's break it down:

```python
api_key = os.environ.get('GOOGLE_API_KEY')

if not api_key:
    api_key = getpass('Enter your Google API Key: ')

if not api_key or len(api_key) < 10:
    raise ValueError("Invalid API key format")

genai.configure(api_key=api_key)
os.environ['GOOGLE_API_KEY'] = api_key
```

**Key Points**:
- Uses `getpass()` for secure input (doesn't show on screen)
- Validates API key format before using it
- Configures both Google AI SDK and sets environment variable
- Raises clear error if API key is invalid

### get_model_name()

Simple but powerful function:

```python
return os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
```

**Why This Matters**:
- Default model: `gemini-2.5-flash` (fast, cost-effective)
- Override: Set `GEMINI_MODEL=gemini-2.5-pro` for better quality
- No code changes needed to switch models

### setup_opik()

Handles observability configuration:

```python
import opik

api_key = os.environ.get('OPIK_API_KEY')
project_name = os.environ.get('OPIK_PROJECT_NAME', 'AI Travel Planner')

os.environ['OPIK_API_KEY'] = api_key
os.environ['OPIK_WORKSPACE'] = workspace
os.environ['OPIK_PROJECT_NAME'] = project_name

return True
```

**Key Points**:
- Optional: Returns False if not configured (graceful degradation)
- Environment Variables: Sets them for Opik SDK to read
- Project Name: Organizes traces in Opik dashboard
- Graceful: Handles import errors without crashing

## Testing the Configuration Module

To test the configuration module, use the web interface:

1. Start the web server:
```bash
python app.py
```

2. Open your browser and navigate to `http://localhost:8000`

3. Ask a question in the chat interface, for example:
   - "I want to plan a trip to Paris in March 2025"

4. Check the console output to verify:
   - API Key loaded from environment/.env file
   - API Key configured successfully!
   - Model name: gemini-2.5-flash
   - Opik configured successfully! (if OPIK_API_KEY is set)

Expected console output:
```
Starting server on port 8000
Configuration initialized
API Key loaded from environment/.env file
API Key configured successfully!
Opik configured successfully!
Project: AI Travel Planner
Workspace: default
Session manager initialized
Concierge agent initialized
Runner initialized
Application startup complete!
```

## Best Practices for Configuration

### 1. Never Hardcode Secrets

Wrong:
```python
api_key = "AIzaSy...hardcoded_key"
```

Right:
```python
api_key = os.environ.get('GOOGLE_API_KEY')
```

### 2. Provide Sensible Defaults

```python
return os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
```

### 3. Validate Configuration

```python
if not api_key or len(api_key) < 10:
    raise ValueError("Invalid API key format")
```

### 4. Make Optional Features Graceful

```python
try:
    import opik
    # Configure Opik
    return True
except ImportError:
    print("Opik not available, continuing without it")
    return False
```

### 5. Use Environment Variables

```python
# Load from .env
from dotenv import load_dotenv
load_dotenv('.env', override=True)

# Access
api_key = os.environ.get('GOOGLE_API_KEY')
```

## Common Issues and Solutions

### Issue: API Key Not Found

**Symptoms**:
```
GOOGLE_API_KEY not found in environment variables or .env file.
```

**Solutions**:
1. Check `.env` file exists in project root
2. Verify API key is set correctly
3. Ensure you're in the activated virtual environment

### Issue: Invalid API Key

**Symptoms**:
```
ValueError: Invalid API key format
```

**Solutions**:
1. Verify you copied the full API key from Google AI Studio
2. Check for extra spaces or quotes
3. Ensure key is 39 characters long

### Issue: Opik Not Working

**Symptoms**:
```
Opik package not installed
```

**Solutions**:
```bash
pip install opik
```

### Issue: .env File Not Loading

**Symptoms**:
```
Warning: Could not load .env file
```

**Solutions**:
1. Ensure `.env` file is in project root
2. Check file permissions
3. Verify python-dotenv is installed

## What's Next?

Congratulations! You've built a robust configuration module. In Part 4, we'll create the Session Manager - a critical component that handles conversation context and memory.

## Summary

In this part, we:
- Built a comprehensive configuration module
- Implemented secure API key management
- Added model configuration flexibility
- Set up Opik observability (optional)
- Added validation and error handling
- Created test scripts to verify functionality

## Key Takeaways

1. **Configuration is critical**: It's the foundation for everything else
2. **Security first**: Never hardcode secrets, use environment variables
3. **Graceful degradation**: Optional features shouldn't break the app
4. **Validation matters**: Fail fast with clear error messages
5. **Environment variables**: Standard practice for configuration management

## Resources

- [Python os Module](https://docs.python.org/3/library/os.html)
- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [Google AI Documentation](https://ai.google.dev/docs)
- [Opik Documentation](https://www.comet.com/site/products/opik/)

---

Continue to Part 4: Session Management
