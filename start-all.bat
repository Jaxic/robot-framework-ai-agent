@echo off
REM ============================================================================
REM Start All Services for Robot Framework AI Agent
REM ============================================================================
REM
REM This script starts all three required services in separate windows:
REM   1. Ollama LLM server (port 11434) - AI language model backend
REM   2. MCP Server (port 8000)         - Robot Framework test API
REM   3. Streamlit UI (port 8501)       - Web chat interface
REM
REM Each service runs in its own command window so you can monitor logs
REM and stop services individually.
REM
REM Authentication:
REM   Credentials MUST be set via environment variables OR a local .env file
REM   in the project root (recommended; it is gitignored):
REM     RFAI_USERNAME=your_username
REM     RFAI_PASSWORD=your_password
REM
REM Prerequisites:
REM   - Ollama installed with qwen2.5:32b-instruct-q4_k_m model pulled
REM   - Python virtual environment set up with: pip install -r requirements.txt
REM
REM To stop all services:
REM   - Close each window individually, or
REM   - Run stop-all.bat
REM
REM ============================================================================

echo ============================================================================
echo  Robot Framework AI Agent - Starting All Services
echo ============================================================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

echo [1/3] Starting Ollama LLM server...
start "Ollama LLM" cmd /k "cd /d %SCRIPT_DIR% && call start-ollama.bat"

REM Wait a moment for Ollama to initialize
echo      Waiting for Ollama to initialize...
timeout /t 3 /nobreak > nul

echo [2/3] Starting MCP Server...
start "MCP Server" cmd /k "cd /d %SCRIPT_DIR% && call start-mcp-server.bat"

REM Wait for MCP server to start
echo      Waiting for MCP server to initialize...
timeout /t 3 /nobreak > nul

echo [3/3] Starting Streamlit UI...
start "Streamlit UI" cmd /k "cd /d %SCRIPT_DIR% && call start-ui.bat"

echo.
echo ============================================================================
echo  All services started in separate windows!
echo ============================================================================
echo.
echo  Service URLs:
echo    - Ollama:     http://localhost:11434
echo    - MCP Server: http://127.0.0.1:8000 (Swagger: /docs)
echo    - Chat UI:    http://localhost:8501
echo.
echo  Login credentials:
echo    - Username: [from .env or RFAI_USERNAME]
echo    - Password: [from .env or RFAI_PASSWORD]
echo.
echo  To change credentials, edit .env or set RFAI_USERNAME / RFAI_PASSWORD
echo  environment variables before running this script.
echo.
echo  The Streamlit UI should open in your browser automatically.
echo  If not, navigate to http://localhost:8501
echo.
echo  To stop all services, close each window or run stop-all.bat
echo ============================================================================
