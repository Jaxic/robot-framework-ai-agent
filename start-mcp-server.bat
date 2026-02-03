@echo off
REM ============================================================================
REM Start MCP Server (FastAPI)
REM ============================================================================
REM
REM This script starts the Model Context Protocol (MCP) server which exposes
REM Robot Framework test operations as HTTP endpoints.
REM
REM Endpoints provided:
REM   POST /tools/list_tests   - List available test suites
REM   POST /tools/execute      - Run a test suite by name
REM   POST /tools/results      - Get results from previous runs
REM   POST /tools/search_logs  - Search test execution logs
REM   GET  /health             - Health check endpoint
REM   GET  /docs               - Swagger UI documentation
REM
REM The server binds to localhost only (127.0.0.1:8000) for security.
REM
REM Prerequisites:
REM   - Python virtual environment with dependencies installed
REM   - Run from the project root directory
REM
REM The server will run in this window. Press Ctrl+C to stop.
REM ============================================================================

echo Starting MCP Server...
echo.
echo This server provides the bridge between the AI agent and Robot Framework.
echo It handles test execution, result parsing, and log searching.
echo.
echo Server URL: http://127.0.0.1:8000
echo Swagger UI: http://127.0.0.1:8000/docs
echo Health:     http://127.0.0.1:8000/health
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================================
echo.

REM Activate virtual environment and start server
call venv\Scripts\activate
python -m mcp_server.server
