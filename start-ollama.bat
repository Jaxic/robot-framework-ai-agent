@echo off
REM ============================================================================
REM Start Ollama LLM Server
REM ============================================================================
REM
REM This script starts the Ollama server which provides the local LLM backend.
REM Ollama serves the qwen2.5:32b-instruct-q4_k_m model on port 11434.
REM
REM Prerequisites:
REM   - Ollama must be installed (https://ollama.com)
REM   - The model must be pulled: ollama pull qwen2.5:32b-instruct-q4_k_m
REM
REM The server will run in this window. Press Ctrl+C to stop.
REM ============================================================================

echo Starting Ollama LLM server...
echo.
echo This provides the AI language model for the agent.
echo The model (qwen2.5:32b-instruct-q4_k_m) will be loaded on first request.
echo.
echo Server URL: http://localhost:11434
echo.
echo Press Ctrl+C to stop the server.
echo ============================================================================
echo.

ollama serve
