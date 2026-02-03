@echo off
REM One-click startup for Robot Framework AI Agent

echo Setting up environment...

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing/upgrading dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Starting services in new windows...
start "Ollama" cmd /c start-ollama.bat
start "MCP Server" cmd /c start-mcp-server.bat
start "Streamlit UI" cmd /c start-ui.bat

echo.
echo All services launched. UI will open at http://localhost:8501
echo Close windows individually or Ctrl+C in each to stop.