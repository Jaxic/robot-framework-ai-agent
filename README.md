# Robot Framework AI Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Robot Framework](https://img.shields.io/badge/Robot%20Framework-7.4%2B-green.svg)](https://robotframework.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2%2B-orange.svg)](https://python.langchain.com/)

A natural-language interface for managing and executing Robot Framework compliance tests on Windows endpoints. Ask questions in plain English and let the AI agent run tests, analyze results, and suggest remediations — all powered by a local LLM with no cloud dependencies.

## Overview

This project bridges the gap between Robot Framework's powerful test automation and the accessibility of conversational AI. Instead of writing commands or navigating test reports manually, you interact through a chat interface:

```
You:   "Is BitLocker enabled on this machine?"
Agent: Runs the BitLocker compliance suite, reports 4/5 tests failed,
       and explains that encryption is disabled on drive C: with remediation steps.
```

The entire stack runs locally — your data never leaves the machine.

## Features

- **Natural language test management** — ask questions, run tests, and investigate failures conversationally
- **Local-first architecture** — Ollama LLM, no API keys, no cloud dependencies
- **Windows compliance testing** — BitLocker encryption, application deployment, Windows services
- **MCP tool integration** — Model Context Protocol server exposes Robot Framework as AI-callable tools
- **Streamlit chat UI** — browser-based interface with reasoning step visibility
- **Extensible** — add new `.robot` test suites and they're automatically discovered

## Architecture

```
+------------------+     +-------------------+     +------------------+     +------------------+
|                  |     |                   |     |                  |     |                  |
|   Streamlit UI   +---->+  LangChain Agent  +---->+   MCP Server     +---->+ Robot Framework  |
|   (port 8501)    |     |  (ReAct + Tools)  |     |   (FastAPI 8000) |     |  (.robot suites) |
|                  |     |                   |     |                  |     |                  |
+------------------+     +--------+----------+     +------------------+     +--------+---------+
                                  |                                                  |
                                  v                                                  v
                         +--------+----------+                              +--------+---------+
                         |                   |                              |                  |
                         |   Ollama LLM      |                              |   PowerShell     |
                         |   (port 11434)    |                              |   (Windows APIs) |
                         |                   |                              |                  |
                         +-------------------+                              +------------------+
```

**Data flow:** User message -> Streamlit -> LangChain Agent -> Ollama (decides which tool) -> MCP Server HTTP API -> Robot Framework `robot.run()` -> PowerShell commands -> Results parsed and returned as natural language.

## Prerequisites

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Tested on 3.13 |
| Ollama | Latest | [ollama.com](https://ollama.com) |
| OS | Windows 10/11 | PowerShell 5.1+ required for test suites |
| RAM | 16 GB | 32 GB recommended for 32B model |
| GPU | Optional | Significantly speeds up LLM inference |
| Disk | ~20 GB | For model weights |

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Jaxic/robot-framework-ai-agent.git
cd robot-framework-ai-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install langchain-ollama
```

### 4. Configure UI login credentials (recommended)

Create a local `.env` file in the project root (it is ignored by git). You can copy the template:

```bash
copy env.example .env
```

Then edit `.env` and set:

```text
RFAI_USERNAME=admin
RFAI_PASSWORD=your_secure_password
```

### 4. Pull the Ollama model

```bash
ollama pull qwen2.5:32b-instruct-q4_k_m
```

### 5. Start the services

Open three terminals (each with the venv activated):

**Terminal 1 — Ollama** (if not already running):
```bash
ollama serve
```

**Terminal 2 — MCP Server:**
```bash
python -m mcp_server.server
```

**Terminal 3 — Streamlit UI:**
```bash
streamlit run ui/app.py
```

### 6. Open your browser

Navigate to [http://localhost:8501](http://localhost:8501) and start chatting.

## Usage

### Example questions

| Question | What happens |
|----------|-------------|
| "What tests are available?" | Lists all `.robot` suites with descriptions |
| "Run the Windows services check" | Executes the suite, returns pass/fail summary |
| "What's our BitLocker compliance status?" | Runs BitLocker tests, explains failures |
| "Show me recent test failures" | Retrieves last results without re-running |
| "Why did the service test fail?" | Searches logs for FAIL entries, identifies root cause |

### Command-line agent (no UI)

```bash
python -m agent.agent
```

This starts an interactive REPL where you type questions directly.

### Test Ollama connection

```bash
python -m agent.llm_config
```

## Project Structure

```
robot-framework-ai-agent/
├── agent/                      # LangChain AI agent
│   ├── __init__.py
│   ├── agent.py                # ReAct agent with 4 MCP tools
│   └── llm_config.py           # Ollama LLM configuration
├── mcp_server/                 # MCP tool server
│   ├── __init__.py
│   ├── server.py               # FastAPI HTTP wrapper
│   └── tools.py                # Tool implementations (list, execute, results, search)
├── tests/                      # Robot Framework test suites
│   ├── bitlocker_compliance.robot
│   ├── application_deployment.robot
│   └── windows_services.robot
├── ui/                         # Streamlit chat interface
│   └── app.py
├── results/                    # Test execution output (auto-generated)
├── docs/                       # Documentation
├── config/                     # Configuration files
├── scripts/                    # Utility scripts
├── requirements.txt
├── LICENSE
└── README.md
```

## Configuration

### LLM model

Edit `agent/llm_config.py` to change the model:

```python
OLLAMA_MODEL = "qwen2.5:32b-instruct-q4_k_m"  # Default
OLLAMA_BASE_URL = "http://localhost:11434"
TEMPERATURE = 0.1
NUM_CTX = 2048
```

### MCP server port

Edit `mcp_server/server.py` (bottom of file) and `agent/agent.py` (`MCP_SERVER_URL`):

```python
# mcp_server/server.py
uvicorn.run("mcp_server.server:app", host="127.0.0.1", port=8000)

# agent/agent.py
MCP_SERVER_URL = "http://127.0.0.1:8000"
```

### Switching to a cloud LLM

Replace the import in `agent/llm_config.py`:

```python
# OpenAI
from langchain_openai import ChatOpenAI
def get_llm():
    return ChatOpenAI(model="gpt-4o", temperature=0.1)

# Anthropic
from langchain_anthropic import ChatAnthropic
def get_llm():
    return ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.1)
```

## Development

### Adding a new test suite

1. Create a `.robot` file in the `tests/` directory
2. Include a `*** Settings ***` section with `Documentation`
3. The MCP server discovers it automatically — no code changes needed

### Adding a new MCP tool

1. Add a `@mcp.tool()` function in `mcp_server/tools.py`
2. Add a corresponding FastAPI endpoint in `mcp_server/server.py`
3. Add a `@tool` function in `agent/agent.py` that calls the new endpoint
4. Add the tool to the `_TOOLS` list in `agent/agent.py`

### Running tests directly (without the agent)

```bash
robot --outputdir results/windows_services tests/windows_services.robot
```

## Troubleshooting

### Ollama not responding

```
[FAIL] Cannot reach Ollama at http://localhost:11434
```

- Ensure Ollama is running: `ollama serve`
- Verify the model is pulled: `ollama list`
- If the model isn't listed: `ollama pull qwen2.5:32b-instruct-q4_k_m`

### MCP server won't start

```
[WinError 10048] Only one usage of each socket address is normally permitted
```

- Port 8000 is in use. Either stop the other process or change the port in `mcp_server/server.py`

### Import errors in Streamlit

```
ModuleNotFoundError: No module named 'agent'
```

- Ensure you're running from the project root directory
- Verify your venv is activated: `venv\Scripts\activate`

### Test execution hangs

- Some PowerShell commands (like `Get-BitLockerVolume`) require administrator privileges
- Run the terminal as Administrator for BitLocker tests

### Agent doesn't respond after tool call

- Check the Ollama terminal for errors
- The model may have run out of context. Try reducing `NUM_CTX` or using a smaller prompt
- Verify the MCP server is still running and healthy: `curl http://127.0.0.1:8000/health`

## API Reference

The MCP server exposes these HTTP endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| GET | `/tools` | List available tools |
| POST | `/tools/list_tests` | Discover `.robot` test suites |
| POST | `/tools/execute` | Run a test suite by name |
| POST | `/tools/results` | Get latest results for a suite |
| POST | `/tools/search_logs` | Search log messages by keyword |

Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Acknowledgments

- [Robot Framework](https://robotframework.org/) — test automation framework
- [LangChain](https://python.langchain.com/) — LLM application framework
- [Model Context Protocol](https://modelcontextprotocol.io/) — tool integration standard
- [Ollama](https://ollama.com/) — local LLM runtime
- [Streamlit](https://streamlit.io/) — rapid UI development
- [FastAPI](https://fastapi.tiangolo.com/) — modern Python web framework
