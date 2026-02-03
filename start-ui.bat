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
REM   - Basic authentication (default: admin / rfai2024)
REM
REM Authentication:
REM   Default credentials can be overridden with environment variables:
REM     set RFAI_USERNAME=your_username
REM     set RFAI_PASSWORD=your_password
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
echo This provides the web-based chat interface for the AI agent.
echo.
echo UI URL: http://localhost:8501
echo.
echo Default login credentials:
echo   Username: admin
echo   Password: rfai2024
echo.
echo (Set RFAI_USERNAME and RFAI_PASSWORD environment variables to change)
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================================
echo.

REM Activate virtual environment and start Streamlit
call venv\Scripts\activate
streamlit run ui/app.py
