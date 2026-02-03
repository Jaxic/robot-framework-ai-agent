@echo off
REM ============================================================================
REM Start Streamlit Chat UI
REM ============================================================================
REM
REM This script starts the Streamlit web interface for interacting with the
REM Robot Framework AI Agent through a chat interface.
REM
REM Features:
REM   - Natural language chat interface
REM   - Example prompt buttons for common queries
REM   - Service status indicators (MCP server, Ollama)
REM   - Agent reasoning steps viewer
REM   - Basic authentication (credentials required)
REM
REM Authentication:
REM   Credentials MUST be set via environment variables:
REM     set RFAI_USERNAME=your_username
REM     set RFAI_PASSWORD=your_password
REM
REM   This script sets default credentials if not already set.
REM   Change these values for production use!
REM
REM Prerequisites:
REM   - Python virtual environment with dependencies installed
REM   - MCP server running (start-mcp-server.bat)
REM   - Ollama running (start-ollama.bat)
REM
REM The UI will open in your default browser automatically.
REM Press Ctrl+C to stop the server.
REM ============================================================================

echo Starting Streamlit Chat UI...
echo.

REM Set default credentials if not already set
REM IMPORTANT: Change these for production use!
if not defined RFAI_USERNAME (
    set RFAI_USERNAME=admin
    echo Setting default RFAI_USERNAME=admin
)
if not defined RFAI_PASSWORD (
    set RFAI_PASSWORD=RobotFun!
    echo Setting default RFAI_PASSWORD=changeme123
)

echo.
echo This provides the web-based chat interface for the AI agent.
echo.
echo UI URL: http://localhost:8501
echo.
echo Login credentials:
echo   Username: %RFAI_USERNAME%
echo   Password: [hidden]
echo.
echo To use different credentials, set RFAI_USERNAME and RFAI_PASSWORD
echo environment variables before running this script.
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================================
echo.

REM Activate virtual environment and start Streamlit
call venv\Scripts\activate
streamlit run ui/app.py
