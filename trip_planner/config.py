"""
Configuration module for the Trip Planner application.
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
    
    Returns:
        str: The configured API key
    """
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not api_key:
        print("GOOGLE_API_KEY not found in environment variables or .env file.")
        print("Make sure you have a .env file in the project root with:")
        api_key = getpass('Enter your Google API Key (from https://aistudio.google.com/app/apikey): ')
    else:
        print("API Key loaded from environment/.env file")
    
    # Configure the generative AI library
    genai.configure(api_key=api_key)
    
    # Set environment variable for ADK
    os.environ['GOOGLE_API_KEY'] = api_key
    
    print("API Key configured successfully!")
    return api_key


def get_model_name():
    """Get the default model name for agents."""
    return os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')


def setup_opik():
    """
    Configure Opik for observability tracking.
    Sets environment variables that Opik SDK will read.
    
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

