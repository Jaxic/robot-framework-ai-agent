@echo off
REM ============================================================================
REM Stop All Services for Robot Framework AI Agent
REM ============================================================================
REM
REM This script stops all running services:
REM   - Ollama server
REM   - MCP Server (Python/uvicorn)
REM   - Streamlit UI
REM
REM It uses taskkill to terminate the processes. This is a forceful stop,
REM so make sure you don't have unsaved work in any of the services.
REM
REM ============================================================================

echo ============================================================================
echo  Robot Framework AI Agent - Stopping All Services
echo ============================================================================
echo.

echo [1/3] Stopping Streamlit...
taskkill /F /IM "streamlit.exe" 2>nul
REM Streamlit runs as python, so we need to find it by window title
taskkill /F /FI "WINDOWTITLE eq Streamlit*" 2>nul

echo [2/3] Stopping MCP Server (uvicorn/python)...
REM Kill uvicorn processes
taskkill /F /FI "WINDOWTITLE eq MCP Server*" 2>nul

echo [3/3] Stopping Ollama...
taskkill /F /IM "ollama.exe" 2>nul
taskkill /F /FI "WINDOWTITLE eq Ollama*" 2>nul

echo.
echo ============================================================================
echo  All services have been stopped.
echo ============================================================================
echo.
echo  Note: If any services are still running, close their windows manually
echo  or use Task Manager to end the processes.
echo ============================================================================

pause
