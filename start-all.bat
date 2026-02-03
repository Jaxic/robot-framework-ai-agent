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
REM   Set credentials via environment variables before running:
REM     set RFAI_USERNAME=your_username
REM     set RFAI_PASSWORD=your_password
REM
REM   Or let the script use defaults (admin/changeme123) for development.
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

REM Set default credentials if not already set
if not defined RFAI_USERNAME (
    set RFAI_USERNAME=admin
    echo  [Auth] Using default username: admin
)
if not defined RFAI_PASSWORD (
    set RFAI_PASSWORD=RobotFun
    echo  [Auth] Using default password: changeme123
)
echo.

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
REM Pass credentials to the new window
start "Streamlit UI" cmd /k "cd /d %SCRIPT_DIR% && set RFAI_USERNAME=%RFAI_USERNAME% && set RFAI_PASSWORD=%RFAI_PASSWORD% && call start-ui.bat"

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
echo    - Username: %RFAI_USERNAME%
echo    - Password: [set via RFAI_PASSWORD]
echo.
echo  To change credentials, set RFAI_USERNAME and RFAI_PASSWORD
echo  environment variables before running this script.
echo.
echo  The Streamlit UI should open in your browser automatically.
echo  If not, navigate to http://localhost:8501
echo.
echo  To stop all services, close each window or run stop-all.bat
echo ============================================================================
