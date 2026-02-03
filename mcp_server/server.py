"""
FastAPI server that exposes the Robot Framework MCP tools over HTTP.

Endpoints:
    GET  /health                  — Health check.
    GET  /tools                   — List registered MCP tools.
    POST /tools/list_tests        — List available .robot test suites.
    POST /tools/execute           — Run a test suite by name.
    POST /tools/results           — Fetch latest parsed results.
    POST /tools/search_logs       — Search output.xml log messages.

Run:
    python -m mcp_server.server
    uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000 --reload
"""

from __future__ import annotations

import json
import logging
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import re

from pydantic import BaseModel, Field, field_validator

from mcp_server.tools import (
    execute_test_suite,
    get_latest_results,
    list_available_tests,
    search_test_logs,
)
from config import (
    CORS_HEADERS,
    CORS_METHODS,
    CORS_ORIGINS,
    LOG_FORMAT,
    LOG_LEVEL,
    MCP_SERVER_HOST,
    MCP_SERVER_PORT,
    VALID_LOG_LEVELS,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger("mcp_server.server")

# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Input validation patterns (defense in depth against injection)
# ---------------------------------------------------------------------------
# Suite names must be simple identifiers — no paths, commands, or metacharacters
SAFE_SUITE_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,63}$")
# Dangerous patterns that should never appear in any input
DANGEROUS_PATTERNS = re.compile(r"[/\\;|&$`<>\"']|\.\.|\x00")
# Note: VALID_LOG_LEVELS is imported from config


def _validate_suite_name(value: str, field_name: str = "suite_name", allow_empty: bool = False) -> str:
    """Validate suite name is safe — raises ValueError if suspicious."""
    if not value:
        if allow_empty:
            return value
        raise ValueError(f"{field_name} cannot be empty")
    if DANGEROUS_PATTERNS.search(value):
        raise ValueError(
            f"{field_name} contains forbidden characters. "
            "Only alphanumeric characters and underscores are allowed."
        )
    if not SAFE_SUITE_NAME_PATTERN.match(value):
        raise ValueError(
            f"{field_name} must start with a letter and contain only "
            "alphanumeric characters and underscores (max 64 chars)."
        )
    return value


class ExecuteRequest(BaseModel):
    suite_name: str = Field(
        ..., description="Stem of the .robot file, e.g. 'bitlocker_compliance'"
    )

    @field_validator("suite_name")
    @classmethod
    def validate_suite_name(cls, v: str) -> str:
        return _validate_suite_name(v, "suite_name")


class ResultsRequest(BaseModel):
    suite_name: Optional[str] = Field(
        default=None,
        description="Filter to a specific suite. Omit for the most recent result.",
    )

    @field_validator("suite_name")
    @classmethod
    def validate_suite_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_suite_name(v, "suite_name")


class SearchLogsRequest(BaseModel):
    keyword: str = Field(..., description="Case-insensitive substring to search for.")
    log_level: str = Field(
        default="FAIL",
        description="Minimum severity: FAIL, ERROR, WARN, INFO, DEBUG, or TRACE.",
    )

    @field_validator("keyword")
    @classmethod
    def validate_keyword(cls, v: str) -> str:
        # Keywords can be more permissive but should not contain null bytes or be excessively long
        if "\x00" in v:
            raise ValueError("keyword contains invalid characters")
        if len(v) > 200:
            raise ValueError("keyword is too long (max 200 characters)")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in VALID_LOG_LEVELS:
            raise ValueError(
                f"log_level must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}"
            )
        return v_upper

class HealthResponse(BaseModel):
    status: str = "ok"

class ToolInfo(BaseModel):
    name: str
    description: str

class ToolsListResponse(BaseModel):
    tools: list[ToolInfo]

# ---------------------------------------------------------------------------
# Tool registry (for the /tools discovery endpoint)
# ---------------------------------------------------------------------------
_TOOL_REGISTRY: list[dict] = [
    {"name": "list_available_tests", "description": "Scan tests/ for .robot files."},
    {"name": "execute_test_suite", "description": "Run a test suite and return results."},
    {"name": "get_latest_results", "description": "Parse the most recent output.xml."},
    {"name": "search_test_logs", "description": "Search log messages by keyword and level."},
]

# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Log available tools on startup, clean up on shutdown."""
    logger.info("=" * 60)
    logger.info("Robot Framework MCP Server starting")
    logger.info("Available tools:")
    for t in _TOOL_REGISTRY:
        logger.info("  - %-25s %s", t["name"], t["description"])
    logger.info("=" * 60)
    yield
    logger.info("Robot Framework MCP Server shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Robot Framework MCP Server",
    description="HTTP wrapper around MCP tools for Robot Framework test management.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — restricted to configured origins only (from config.py).
# Only allow methods and headers actually needed by the application.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

# ---------------------------------------------------------------------------
# Request-logging middleware
# ---------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    ts = datetime.now(timezone.utc).isoformat()
    logger.info("%s  %s %s", ts, request.method, request.url.path)
    response = await call_next(request)
    logger.info(
        "%s  %s %s -> %s",
        ts, request.method, request.url.path, response.status_code,
    )
    return response

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Return server health status."""
    return HealthResponse()


@app.get("/tools", response_model=ToolsListResponse)
async def list_tools():
    """Return the list of registered MCP tools."""
    return ToolsListResponse(
        tools=[ToolInfo(**t) for t in _TOOL_REGISTRY]
    )


def _safe_json_parse(raw: str) -> dict | list:
    """Parse JSON string, returning error dict on failure.

    Args:
        raw: JSON string to parse.

    Returns:
        Parsed JSON object, or error dict if parsing fails.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse tool response as JSON: %s", exc)
        return {"error": "Internal error: tool returned invalid JSON"}


@app.post("/tools/list_tests")
async def api_list_tests() -> JSONResponse:
    """List available Robot Framework test suites.

    Returns:
        JSON array of test suite objects with name, file, and description.
    """
    raw = list_available_tests()
    return JSONResponse(content=_safe_json_parse(raw))


@app.post("/tools/execute")
async def api_execute(req: ExecuteRequest) -> JSONResponse:
    """Execute a test suite by name.

    Args:
        req: Request containing suite_name to execute.

    Returns:
        JSON object with execution results including status, passed/failed counts.
    """
    raw = execute_test_suite(req.suite_name)
    return JSONResponse(content=_safe_json_parse(raw))


@app.post("/tools/results")
async def api_results(req: ResultsRequest) -> JSONResponse:
    """Fetch the latest parsed results.

    Args:
        req: Request with optional suite_name filter.

    Returns:
        JSON object with test results from the most recent output.xml.
    """
    raw = get_latest_results(req.suite_name or "")
    return JSONResponse(content=_safe_json_parse(raw))


@app.post("/tools/search_logs")
async def api_search_logs(req: SearchLogsRequest) -> JSONResponse:
    """Search output.xml log messages.

    Args:
        req: Request with keyword and log_level filters.

    Returns:
        JSON array of matching log entries with test context.
    """
    raw = search_test_logs(req.keyword, req.log_level)
    return JSONResponse(content=_safe_json_parse(raw))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _handle_sigint(sig, frame):
    """Handle SIGINT (Ctrl+C) by raising KeyboardInterrupt for graceful shutdown.

    This allows the FastAPI lifespan context manager to run its cleanup code
    rather than exiting abruptly with sys.exit().
    """
    logger.info("Received SIGINT — initiating graceful shutdown")
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _handle_sigint)

    print("\n  Robot Framework MCP Server")
    print(f"  http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    print(f"  http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/docs  (Swagger UI)")
    print("  Press Ctrl+C to stop\n")

    uvicorn.run(
        "mcp_server.server:app",
        host=MCP_SERVER_HOST,
        port=MCP_SERVER_PORT,
        log_level=LOG_LEVEL.lower(),
    )
