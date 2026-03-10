"""
Configuration module for the Trip Planner application.
Handles environment variables and API key setup.
"""

import os
from getpass import getpass
from pathlib import Path
from urllib.parse import urlparse
import google.generativeai as genai
from trip_planner.logging_utils import get_logger


logger = get_logger(__name__)


# =============================================================================
# Application Settings (MVP config-first)
# =============================================================================

# Change to "production" before deploying to a public HTTPS endpoint.
APP_ENVIRONMENT = "development"

# Session cookie settings used by authentication middleware.
SESSION_COOKIE_NAME = "trip_planner_session"
SESSION_MAX_AGE_SECONDS = 86400 * 7  # 7 days
SESSION_SAME_SITE = "lax"
# Fail-safe default: always secure unless explicitly allowed for localhost dev.
SESSION_HTTPS_ONLY = True
# Set to True only for local HTTP development on localhost.
ALLOW_INSECURE_LOCAL_DEV = False
# Used only when ALLOW_INSECURE_LOCAL_DEV is enabled.
LOCAL_DEV_BASE_URL = "http://localhost:5000"

# Logging settings
LOG_LEVEL = "INFO"

# Admin/debug endpoint settings
ADMIN_DEBUG_ENABLED = False
ADMIN_DEBUG_ALLOWED_EMAILS = []
ADMIN_DEBUG_ALLOWED_USER_IDS = []
ADMIN_DEBUG_MAX_KEYS_PER_GROUP = 25

# Rate limiting backend settings
RATE_LIMIT_BACKEND = "memory"  # valid: "memory", "redis"
RATE_LIMIT_REDIS_URL = "redis://localhost:6379/0"
RATE_LIMIT_KEY_PREFIX = "trip_planner"
USER_DAILY_RATE_LIMIT = 50

# Conversation session memory backend settings
SESSION_MEMORY_BACKEND = "memory"  # valid: "memory", "redis"
SESSION_MEMORY_REDIS_URL = "redis://localhost:6379/0"
SESSION_MEMORY_KEY_PREFIX = "trip_planner"
SESSION_MEMORY_TTL_SECONDS = 86400 * 7  # 7 days

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env file from project root (where app.py/main.py are located)
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
        logger.info("Loading .env file from: %s", env_path)
    else:
        # Also try loading from current directory
        load_dotenv(override=True)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass
except Exception as e:
    # If there's an error loading .env, continue anyway
    logger.warning("Could not load .env file: %s", e)


def get_session_settings() -> dict:
    """Return centralized session cookie settings for middleware."""
    parsed_local_dev_url = urlparse(LOCAL_DEV_BASE_URL)
    localhost_hosts = {"localhost", "127.0.0.1", "::1"}
    is_localhost_dev_url = (
        parsed_local_dev_url.scheme == "http"
        and parsed_local_dev_url.hostname in localhost_hosts
    )

    # Only allow insecure cookies when explicitly enabled for localhost development.
    allow_insecure_cookies = (
        ALLOW_INSECURE_LOCAL_DEV
        and APP_ENVIRONMENT == "development"
        and is_localhost_dev_url
    )

    return {
        "cookie_name": SESSION_COOKIE_NAME,
        "max_age_seconds": SESSION_MAX_AGE_SECONDS,
        "same_site": SESSION_SAME_SITE,
        "https_only": SESSION_HTTPS_ONLY and not allow_insecure_cookies,
        "environment": APP_ENVIRONMENT,
    }


def get_logging_settings() -> dict:
    """Return centralized logging settings."""
    return {
        "level": LOG_LEVEL,
    }


def _normalize_string_collection(values) -> list[str]:
    """Normalize a config collection into a deduplicated list of non-empty strings."""
    if values is None:
        return []

    if isinstance(values, str):
        items = [values]
    elif isinstance(values, (list, tuple, set)):
        items = list(values)
    else:
        items = [str(values)]

    normalized: list[str] = []
    seen = set()
    for item in items:
        text = str(item).strip()
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)
    return normalized


def get_admin_debug_settings() -> dict:
    """Return centralized settings for admin/debug endpoints."""
    max_keys = int(ADMIN_DEBUG_MAX_KEYS_PER_GROUP)
    if max_keys < 1:
        max_keys = 1
    if max_keys > 100:
        max_keys = 100

    normalized_emails = [
        email.lower() for email in _normalize_string_collection(ADMIN_DEBUG_ALLOWED_EMAILS)
    ]
    normalized_user_ids = _normalize_string_collection(ADMIN_DEBUG_ALLOWED_USER_IDS)

    return {
        "enabled": bool(ADMIN_DEBUG_ENABLED),
        "allowed_emails": set(normalized_emails),
        "allowed_user_ids": set(normalized_user_ids),
        "max_keys_per_group": max_keys,
    }


def get_rate_limit_settings() -> dict:
    """Return centralized rate-limiting backend settings."""
    backend = RATE_LIMIT_BACKEND.strip().lower()
    if backend not in {"memory", "redis"}:
        backend = "memory"

    return {
        "backend": backend,
        "redis_url": RATE_LIMIT_REDIS_URL,
        "key_prefix": RATE_LIMIT_KEY_PREFIX,
        "user_daily_limit": USER_DAILY_RATE_LIMIT,
    }


def get_session_memory_settings() -> dict:
    """Return centralized conversation session-memory backend settings."""
    backend = SESSION_MEMORY_BACKEND.strip().lower()
    if backend not in {"memory", "redis"}:
        backend = "memory"

    return {
        "backend": backend,
        "redis_url": SESSION_MEMORY_REDIS_URL,
        "key_prefix": SESSION_MEMORY_KEY_PREFIX,
        "ttl_seconds": SESSION_MEMORY_TTL_SECONDS,
    }


def setup_api_key():
    """
    Configure Google API key from environment variable, .env file, or prompt user.
    
    Returns:
        str: The configured API key
    """
    api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found in environment variables or .env file.")
        logger.info("Make sure you have a .env file in the project root with GOOGLE_API_KEY set.")
        api_key = getpass('Enter your Google API Key (from https://aistudio.google.com/app/apikey): ')
    else:
        logger.info("API key loaded from environment/.env file.")
    
    # Configure the generative AI library
    genai.configure(api_key=api_key)
    
    # Set environment variable for ADK
    os.environ['GOOGLE_API_KEY'] = api_key
    
    logger.info("API key configured successfully.")
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
            logger.warning("OPIK_API_KEY not found in environment variables or .env file.")
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
        except (ImportError, AttributeError, KeyError):
            # ImportError: opik not installed
            # AttributeError: opik API changed
            # KeyError: missing configuration
            pass  # SDK will use environment variables
        
        logger.info("Opik configured successfully.")
        logger.info("Opik project: %s", project_name)
        logger.info("Opik workspace: %s", workspace)
        return True
        
    except ImportError:
        logger.warning("Opik package not installed. Install with: pip install opik")
        return False
    except Exception as e:
        logger.error("Error configuring Opik: %s", e)
        return False
