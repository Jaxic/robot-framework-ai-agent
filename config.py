"""
Centralized configuration for Robot Framework AI Agent.

All configuration values can be overridden via environment variables.
This module provides a single source of truth for all settings across
the application.

Usage:
    from config import MCP_SERVER_URL, OLLAMA_MODEL

Environment Variables:
    Server Configuration:
        MCP_SERVER_HOST     - MCP server bind address (default: 127.0.0.1)
        MCP_SERVER_PORT     - MCP server port (default: 8000)

    Ollama Configuration:
        OLLAMA_HOST         - Ollama server hostname (default: localhost)
        OLLAMA_PORT         - Ollama server port (default: 11434)
        OLLAMA_MODEL        - Model name (default: qwen2.5:32b-instruct-q4_k_m)
        OLLAMA_TEMPERATURE  - Sampling temperature (default: 0.1)
        OLLAMA_NUM_CTX      - Context window size (default: 2048)

    UI Configuration:
        STREAMLIT_PORT      - Streamlit server port (default: 8501)

    Security Configuration:
        RFAI_USERNAME       - Authentication username (required)
        RFAI_PASSWORD       - Authentication password (required)

    Timeouts:
        HEALTH_CHECK_TIMEOUT    - Health check timeout in seconds (default: 3)
        TEST_EXECUTION_TIMEOUT  - Test execution timeout in seconds (default: 120)
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_ROOT / "tests"
RESULTS_DIR = PROJECT_ROOT / "results"

# ---------------------------------------------------------------------------
# MCP Server Configuration
# ---------------------------------------------------------------------------
MCP_SERVER_HOST = os.environ.get("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8000"))
MCP_SERVER_URL = f"http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}"

# ---------------------------------------------------------------------------
# Ollama Configuration
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", "11434"))
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b-instruct-q4_k_m")

# LLM parameters with sensible defaults
# Temperature: 0.1 for more deterministic responses (good for tool calling)
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.1"))
# Context window: 2048 tokens is sufficient for most test-related queries
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "2048"))

# ---------------------------------------------------------------------------
# UI Configuration
# ---------------------------------------------------------------------------
STREAMLIT_PORT = int(os.environ.get("STREAMLIT_PORT", "8501"))

# ---------------------------------------------------------------------------
# Security Configuration
# ---------------------------------------------------------------------------
# These MUST be set via environment variables - no defaults for security
AUTH_USERNAME = os.environ.get("RFAI_USERNAME")
AUTH_PASSWORD = os.environ.get("RFAI_PASSWORD")

# ---------------------------------------------------------------------------
# Timeouts (seconds)
# ---------------------------------------------------------------------------
HEALTH_CHECK_TIMEOUT = int(os.environ.get("HEALTH_CHECK_TIMEOUT", "3"))
TEST_EXECUTION_TIMEOUT = int(os.environ.get("TEST_EXECUTION_TIMEOUT", "120"))

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
CORS_ORIGINS = [
    f"http://localhost:{STREAMLIT_PORT}",
    f"http://127.0.0.1:{STREAMLIT_PORT}",
    "http://localhost:3000",   # Development
    "http://127.0.0.1:3000",
]
CORS_METHODS = ["GET", "POST", "OPTIONS"]
CORS_HEADERS = ["Content-Type", "Accept", "Authorization"]

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Maximum length for error messages returned to users (prevents info leakage)
MAX_ERROR_MESSAGE_LENGTH = 200

# Valid log levels for searching test logs
VALID_LOG_LEVELS = frozenset({"FAIL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"})
