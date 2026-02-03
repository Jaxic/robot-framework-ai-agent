# Code Quality Improvement Plan

Based on the comprehensive audit, this plan addresses 74 identified issues across the codebase.

---

## Summary of Findings

| File | HIGH | MEDIUM | LOW | Total |
|------|------|--------|-----|-------|
| agent/agent.py | 2 | 6 | 2 | 10 |
| agent/llm_config.py | 1 | 5 | 1 | 7 |
| agent/__init__.py | 0 | 2 | 0 | 2 |
| mcp_server/server.py | 3 | 8 | 4 | 15 |
| mcp_server/tools.py | 4 | 8 | 5 | 17 |
| mcp_server/__init__.py | 0 | 2 | 0 | 2 |
| ui/app.py | 4 | 10 | 7 | 21 |
| **TOTAL** | **14** | **41** | **19** | **74** |

---

## Phase 1: Critical Security & Stability Fixes (HIGH Priority)

### 1.1 Remove hardcoded default password
**File:** `ui/app.py:58`
**Issue:** Default password `rfai2024` embedded in source code
**Fix:** Remove default, require environment variable, add startup validation

```python
# Before
AUTH_PASSWORD = os.environ.get("RFAI_PASSWORD", "rfai2024")

# After
AUTH_USERNAME = os.environ.get("RFAI_USERNAME")
AUTH_PASSWORD = os.environ.get("RFAI_PASSWORD")

def _validate_auth_config():
    """Validate authentication is properly configured."""
    if not AUTH_USERNAME or not AUTH_PASSWORD:
        raise RuntimeError(
            "Authentication not configured. Set RFAI_USERNAME and RFAI_PASSWORD "
            "environment variables before starting the application."
        )
```

### 1.2 Restrict CORS configuration
**File:** `mcp_server/server.py:194-195`
**Issue:** `allow_methods=["*"]` too permissive
**Fix:** Specify only needed methods and headers

```python
# Before
allow_methods=["*"],
allow_headers=["*"],

# After
allow_methods=["GET", "POST", "OPTIONS"],
allow_headers=["Content-Type", "Accept"],
```

### 1.3 Fix bare exception handlers
**Files:** Multiple locations
**Issue:** `except Exception:` hides programming errors
**Fix:** Use specific exception types

| Location | Replace with |
|----------|--------------|
| `agent/agent.py:66` | `requests.RequestException` |
| `agent/llm_config.py:73` | `requests.RequestException, AttributeError` |
| `mcp_server/tools.py:223` | `robot.errors.RobotError, OSError` |
| `ui/app.py:189,198` | `requests.RequestException` |
| `ui/app.py:450` | `Exception` (keep but add specific handling first) |

### 1.4 Fix signal handler for graceful shutdown
**File:** `mcp_server/server.py:265`
**Issue:** `sys.exit(0)` bypasses cleanup
**Fix:** Raise KeyboardInterrupt for proper shutdown

```python
# Before
def _handle_sigint(sig, frame):
    logger.info("Received SIGINT, shutting down...")
    sys.exit(0)

# After
def _handle_sigint(sig, frame):
    logger.info("Received SIGINT, initiating graceful shutdown...")
    raise KeyboardInterrupt
```

### 1.5 Add JSON parsing error handling
**File:** `mcp_server/server.py:235,242,249,256`
**Issue:** `json.loads()` without try-catch
**Fix:** Wrap in try-except with fallback

---

## Phase 2: Configuration Centralization (MEDIUM Priority)

### 2.1 Create centralized configuration module
**New file:** `config.py`
**Purpose:** Single source of truth for all configuration

```python
"""
Centralized configuration for Robot Framework AI Agent.

All configuration values can be overridden via environment variables.
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_ROOT / "tests"
RESULTS_DIR = PROJECT_ROOT / "results"

# ---------------------------------------------------------------------------
# Server Configuration
# ---------------------------------------------------------------------------
MCP_SERVER_HOST = os.environ.get("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT = int(os.environ.get("MCP_SERVER_PORT", "8000"))
MCP_SERVER_URL = f"http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}"

# ---------------------------------------------------------------------------
# Ollama Configuration
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "localhost")
OLLAMA_PORT = int(os.environ.get("OLLAMA_PORT", "11434"))
OLLAMA_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:32b-instruct-q4_k_m")
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.1"))
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
    "http://localhost:3000",  # Development
]
```

### 2.2 Update imports across all modules
Replace hardcoded values with config imports in:
- `agent/agent.py`
- `agent/llm_config.py`
- `mcp_server/server.py`
- `mcp_server/tools.py`
- `ui/app.py`

---

## Phase 3: Type Hints & Documentation (MEDIUM Priority)

### 3.1 Add return type hints to all functions

**agent/agent.py:**
```python
def _mcp_post(endpoint: str, payload: Optional[dict] = None) -> dict | list: ...
def _format_response(data: dict | list) -> str: ...
@tool
def ListTests() -> str: ...
@tool
def ExecuteTest(suite_name: str) -> str: ...
@tool
def GetResults(suite_name: str = "") -> str: ...
@tool
def SearchLogs(keyword: str, log_level: str = "FAIL") -> str: ...
def get_agent() -> CompiledGraph: ...
```

**agent/llm_config.py:**
```python
def get_llm() -> ChatOllama: ...
def test_connection() -> bool: ...
```

**mcp_server/server.py:**
```python
async def health_check() -> HealthResponse: ...
async def list_tools() -> ToolsListResponse: ...
async def tool_list_tests() -> JSONResponse: ...
async def tool_execute(req: ExecuteRequest) -> JSONResponse: ...
async def tool_results(req: ResultsRequest) -> JSONResponse: ...
async def tool_search_logs(req: SearchLogsRequest) -> JSONResponse: ...
```

**mcp_server/tools.py:**
```python
def _extract_suite_doc(robot_file: Path) -> str: ...
def _result_to_dict(result: ExecutionResult, suite_name: str) -> dict: ...
def list_available_tests() -> str: ...
def execute_test_suite(suite_name: str) -> str: ...
def get_test_results(suite_name: str = "") -> str: ...
def search_test_logs(keyword: str, log_level: str = "FAIL") -> str: ...
```

**ui/app.py:**
```python
def check_password() -> bool: ...
def check_mcp_server() -> bool: ...
def check_ollama() -> bool: ...
def load_agent() -> CompiledGraph: ...
```

### 3.2 Complete all docstrings with Args/Returns/Raises

Template for all functions:
```python
def function_name(param1: str, param2: int = 0) -> dict:
    """Short description of what the function does.

    Longer description if needed, explaining the behavior,
    side effects, or important details.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter. Defaults to 0.

    Returns:
        Description of return value and its structure.

    Raises:
        ValueError: When param1 is empty.
        ConnectionError: When service is unreachable.

    Example:
        >>> result = function_name("test", 42)
        >>> print(result["status"])
        'ok'
    """
```

### 3.3 Add module-level docstrings to `__init__.py` files

**agent/__init__.py:**
```python
"""
Robot Framework AI Agent - LangChain agent module.

This package provides the AI agent that interprets natural language
queries and translates them into Robot Framework test operations.

Exports:
    get_agent: Factory function to create a configured agent instance.
    get_llm: Factory function to get the configured LLM.

Example:
    >>> from agent import get_agent
    >>> agent = get_agent()
    >>> result = agent.invoke({"messages": [{"role": "user", "content": "List tests"}]})
"""
```

**mcp_server/__init__.py:**
```python
"""
Robot Framework AI Agent - MCP Server module.

This package provides the Model Context Protocol server that exposes
Robot Framework operations as HTTP-callable tools.

Exports:
    mcp: FastMCP instance with registered tools.
    app: FastAPI application for HTTP access.

Example:
    >>> from mcp_server import app
    >>> # Run with: uvicorn mcp_server:app --host 127.0.0.1 --port 8000
"""
```

---

## Phase 4: Error Handling Standardization (MEDIUM Priority)

### 4.1 Define standard error response schema

**New file or add to config:** `schemas.py`
```python
from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    """Standard error response structure."""
    error: str
    code: str
    details: Optional[str] = None

# Error codes
class ErrorCodes:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    PARSE_ERROR = "PARSE_ERROR"
```

### 4.2 Implement consistent error handling pattern

```python
def _create_error_response(
    message: str,
    code: str,
    details: Optional[str] = None
) -> dict:
    """Create a standardized error response."""
    response = {"error": message, "code": code}
    if details:
        response["details"] = details
    return response
```

### 4.3 Add client-side input validation in agent

```python
import re

SAFE_SUITE_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,63}$")

def _validate_suite_name(name: str) -> bool:
    """Validate suite name before sending to server."""
    if not name or not SAFE_SUITE_NAME_PATTERN.match(name):
        return False
    return True
```

---

## Phase 5: Code Quality Improvements (LOW Priority)

### 5.1 Replace print() with logger

**Locations:**
- `agent/agent.py:270-283` (main block)
- `agent/llm_config.py:71-81` (test_connection)
- `mcp_server/server.py:271-274` (main block)

### 5.2 Extract nested code to helper functions

**ui/app.py:** Extract agent response processing
```python
def _process_agent_chunk(chunk: dict, steps: list) -> Optional[str]:
    """Process a single agent stream chunk.

    Args:
        chunk: Stream chunk from agent.
        steps: List to append reasoning steps to.

    Returns:
        Final content if this chunk contains it, None otherwise.
    """
    # ... extracted logic
```

**mcp_server/tools.py:** Extract log search inner loop
```python
def _process_log_message(
    msg_elem: ET.Element,
    parent_map: dict,
    keyword: str,
    min_level: int
) -> Optional[dict]:
    """Process a single log message element.

    Returns:
        Log entry dict if matches criteria, None otherwise.
    """
    # ... extracted logic
```

### 5.3 Define constants for magic values

```python
# ui/app.py - Colors
class Colors:
    STATUS_OK = "#22c55e"
    STATUS_ERROR = "#ef4444"
    TEXT_MUTED = "#9ca3af"

# ui/app.py - Emojis
class Emoji:
    ROBOT = "\U0001f916"
    LOCK = "\U0001f512"
    TRASH = "\U0001f5d1"
    DOOR = "\U0001f6aa"
    THINKING = "\U0001f914"
    ERROR = "\u274c"

# mcp_server/tools.py
DEFAULT_ANCESTOR_NAME = "suite-level"
MAX_ERROR_MESSAGE_LENGTH = 200
```

### 5.4 Consolidate logging configuration

Create `logging_config.py`:
```python
"""Centralized logging configuration."""
import logging
import sys

def configure_logging(level: int = logging.INFO) -> None:
    """Configure logging for the entire application.

    Call this once at application startup, before importing other modules.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
```

---

## Phase 6: Testing & Validation (Recommended)

### 6.1 Add type checking to CI

```yaml
# .github/workflows/quality.yml or pyproject.toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
```

### 6.2 Add linting to CI

```yaml
[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N", "D", "UP", "B", "C4"]
```

### 6.3 Create unit tests for validation functions

```python
# tests/test_validation.py
def test_safe_suite_name_pattern():
    assert _validate_suite_name("bitlocker_compliance") == True
    assert _validate_suite_name("../../../etc/passwd") == False
    assert _validate_suite_name("test;rm -rf /") == False
```

---

## Implementation Order

1. **Phase 1** - Critical fixes (security, stability) - Do first
2. **Phase 2** - Configuration centralization - Enables cleaner code
3. **Phase 3** - Type hints & docs - Improves maintainability
4. **Phase 4** - Error handling - Better user experience
5. **Phase 5** - Code quality - Polish
6. **Phase 6** - Testing - Long-term quality assurance

---

## Estimated Effort

| Phase | Files Changed | Estimated Lines | Complexity |
|-------|---------------|-----------------|------------|
| Phase 1 | 5 | ~50 | Low |
| Phase 2 | 6 | ~150 | Medium |
| Phase 3 | 7 | ~200 | Low |
| Phase 4 | 4 | ~100 | Medium |
| Phase 5 | 4 | ~150 | Low |
| Phase 6 | New files | ~100 | Medium |

**Total:** ~750 lines of changes across all phases
