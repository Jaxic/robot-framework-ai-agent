"""
Streamlit chat interface for the Robot Framework AI Agent.

Provides a conversational UI where users can ask questions about
infrastructure compliance tests and have the LangChain agent
execute Robot Framework suites via the MCP server.

Run with::

    streamlit run ui/app.py

Requires:
    - MCP server running  (python -m mcp_server.server)
    - Ollama running       (ollama serve)
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure the project root is on sys.path so "agent" and "mcp_server" are importable
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import requests
import streamlit as st

from config import (
    AUTH_PASSWORD,
    AUTH_USERNAME,
    HEALTH_CHECK_TIMEOUT,
    LOG_FORMAT,
    LOG_LEVEL,
    MCP_SERVER_URL,
    OLLAMA_BASE_URL,
)

# ---------------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Robot Framework AI Assistant",
    page_icon="\U0001f916",
    layout="centered",
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger("ui.app")


def _check_auth_configured() -> bool:
    """Check if authentication credentials are configured.

    Returns:
        True if both username and password are set, False otherwise.
    """
    return bool(AUTH_USERNAME and AUTH_PASSWORD)


def _show_auth_missing_error() -> None:
    """Display error message when auth credentials are not configured."""
    st.error(
        "**Authentication not configured.**\n\n"
        "You must set credentials before starting the application.\n\n"
        "**Recommended:** create a local `.env` file in the project root (it is gitignored)."
    )
    st.code(
        "# Option A (recommended): .env file in project root\n"
        "copy env.example .env\n"
        "# Edit .env and set:\n"
        "RFAI_USERNAME=admin\n"
        "RFAI_PASSWORD=your_secure_password\n\n"
        "# Option B: set environment variables for this session\n"
        "# Windows (Command Prompt)\n"
        "set RFAI_USERNAME=admin\n"
        "set RFAI_PASSWORD=your_secure_password\n\n"
        "# Windows (PowerShell)\n"
        "$env:RFAI_USERNAME='admin'\n"
        "$env:RFAI_PASSWORD='your_secure_password'\n\n"
        "# Then restart: streamlit run ui/app.py",
        language="bash"
    )
    logger.error("Missing RFAI_USERNAME or RFAI_PASSWORD environment variables")


def check_password() -> bool:
    """Show login form and verify credentials.

    Returns True if authenticated, False otherwise.
    Uses session state to persist authentication across reruns.

    If credentials are not configured via environment variables,
    displays an error message and returns False.
    """
    # Check if auth is configured
    if not _check_auth_configured():
        st.title("\U0001f512 Robot Framework AI Assistant")
        _show_auth_missing_error()
        return False

    def password_entered() -> None:
        """Validate entered credentials using constant-time comparison."""
        username_correct = hmac.compare_digest(
            st.session_state.get("username", "").encode(),
            (AUTH_USERNAME or "").encode()
        )
        password_correct = hmac.compare_digest(
            st.session_state.get("password", "").encode(),
            (AUTH_PASSWORD or "").encode()
        )

        if username_correct and password_correct:
            st.session_state["authenticated"] = True
            # Clear password from session state for security
            del st.session_state["password"]
            del st.session_state["username"]
            logger.info("User authenticated successfully")
        else:
            st.session_state["authenticated"] = False
            logger.warning("Failed authentication attempt")

    # Already authenticated
    if st.session_state.get("authenticated", False):
        return True

    # Show login form
    st.title("\U0001f512 Robot Framework AI Assistant")
    st.markdown("Please log in to continue.")

    with st.form("login_form"):
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            password_entered()
            if st.session_state.get("authenticated", False):
                st.rerun()

    if st.session_state.get("authenticated") == False:
        st.error("Invalid username or password")

    return False


# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Authentication gate - must pass before showing any content
# ---------------------------------------------------------------------------
if not check_password():
    st.stop()

st.markdown(
    """
    <style>
    /* Hide default Streamlit header/footer/deploy for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Chat message styling */
    .stChatMessage {
        padding: 0.75rem 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.5rem;
    }

    /* Sidebar status badges */
    .status-ok {
        color: #22c55e;
        font-weight: 600;
    }
    .status-err {
        color: #ef4444;
        font-weight: 600;
    }

    /* Timestamp styling */
    .msg-time {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.25rem;
    }

    /* Example prompt buttons */
    div.stButton > button {
        width: 100%;
        text-align: left;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.25rem;
        background: #f9fafb;
        transition: background 0.15s;
    }
    div.stButton > button:hover {
        background: #f3f4f6;
        border-color: #6366f1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Health-check helpers
# ---------------------------------------------------------------------------
def check_mcp_server() -> bool:
    """Return True if the MCP server /health endpoint responds.

    Returns:
        True if server is healthy, False otherwise.
    """
    try:
        resp = requests.get(f"{MCP_SERVER_URL}/health", timeout=HEALTH_CHECK_TIMEOUT)
        return resp.status_code == 200
    except requests.RequestException:
        # Connection error, timeout, or other request failure
        return False


def check_ollama() -> bool:
    """Return True if Ollama is reachable.

    Returns:
        True if Ollama API responds, False otherwise.
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=HEALTH_CHECK_TIMEOUT)
        return resp.status_code == 200
    except requests.RequestException:
        # Connection error, timeout, or other request failure
        return False


# ---------------------------------------------------------------------------
# Agent initialisation (cached so it's created only once)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading AI agent...")
def load_agent():
    """Create and cache the LangChain agent."""
    from agent.agent import get_agent  # noqa: import here to avoid slow startup on every rerun

    return get_agent()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("\U0001f916 RF AI Assistant")
    st.caption("Robot Framework test automation powered by AI")

    st.divider()

    # --- Server status ---
    st.subheader("Server Status")
    mcp_ok = check_mcp_server()
    ollama_ok = check_ollama()

    col1, col2 = st.columns(2)
    with col1:
        if mcp_ok:
            st.markdown('<span class="status-ok">MCP Server</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-err">MCP Server</span>', unsafe_allow_html=True)
    with col2:
        if ollama_ok:
            st.markdown('<span class="status-ok">Ollama LLM</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-err">Ollama LLM</span>', unsafe_allow_html=True)

    if not mcp_ok:
        st.warning("MCP server is not reachable. Start it with:\n\n`python -m mcp_server.server`")
    if not ollama_ok:
        st.warning("Ollama is not running. Start it with:\n\n`ollama serve`")

    st.divider()

    # --- Project info ---
    st.subheader("About")
    st.markdown(
        "This assistant can **list**, **execute**, and **inspect** "
        "Robot Framework compliance test suites through natural language."
    )
    st.markdown(
        "**Test suites:**\n"
        "- BitLocker Compliance\n"
        "- Application Deployment\n"
        "- Windows Services"
    )

    st.divider()

    # --- Links ---
    st.subheader("Resources")
    st.markdown("[Robot Framework docs](https://robotframework.org/)")
    st.markdown("[LangChain docs](https://python.langchain.com/)")
    st.markdown("[Ollama](https://ollama.com/)")

    st.divider()

    # --- Clear chat ---
    if st.button("\U0001f5d1 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # --- Logout ---
    if st.button("\U0001f6aa Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("\U0001f916 Robot Framework AI Assistant")
st.markdown("Ask questions about your infrastructure tests in natural language.")

# --- Warnings if services are down ---
if not mcp_ok or not ollama_ok:
    st.error(
        "One or more backend services are offline. "
        "The agent may not work correctly until they are started."
    )

# ---------------------------------------------------------------------------
# Example prompt buttons (only shown when chat is empty)
# ---------------------------------------------------------------------------
if not st.session_state.messages:
    st.markdown("#### Try an example:")
    examples = [
        "What tests are available?",
        "Run the Windows services check",
        "Show me recent test failures",
        "What's our BitLocker compliance status?",
    ]
    cols = st.columns(2)
    for idx, example in enumerate(examples):
        with cols[idx % 2]:
            if st.button(example, key=f"ex_{idx}"):
                st.session_state.pending_prompt = example
                st.rerun()

# ---------------------------------------------------------------------------
# Display chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("time"):
            st.markdown(f'<div class="msg-time">{msg["time"]}</div>', unsafe_allow_html=True)
        # Show reasoning steps in an expandable section
        if msg.get("steps"):
            with st.expander("Agent reasoning steps"):
                for step in msg["steps"]:
                    st.text(step)

# ---------------------------------------------------------------------------
# Chat input — accept from text box or from pending example-button click
# ---------------------------------------------------------------------------
user_input = st.chat_input("Type your question here...")

# If an example button was clicked on the previous run, pick it up now
if user_input is None and st.session_state.get("pending_prompt"):
    user_input = st.session_state.pop("pending_prompt")

if user_input:
    # Append user message
    timestamp = datetime.now().strftime("%H:%M")
    st.session_state.messages.append(
        {"role": "user", "content": user_input, "time": timestamp}
    )

    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
        st.markdown(f'<div class="msg-time">{timestamp}</div>', unsafe_allow_html=True)

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("\U0001f914 Thinking..."):
            try:
                agent = load_agent()

                # Stream the agent response, collecting intermediate steps
                steps: list[str] = []
                final_content = ""

                for chunk in agent.stream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    stream_mode="updates",
                ):
                    # Each chunk is a dict keyed by node name
                    for node_name, node_output in chunk.items():
                        if node_name == "agent":
                            # Agent thinking / tool calls
                            agent_msgs = node_output.get("messages", [])
                            for am in agent_msgs:
                                has_tool_calls = getattr(am, "tool_calls", None)
                                if has_tool_calls:
                                    for tc in has_tool_calls:
                                        steps.append(
                                            f"Calling tool: {tc['name']}({tc.get('args', {})})"
                                        )
                                # Capture content from agent messages.
                                # The last agent message with content is the final answer.
                                content = getattr(am, "content", None)
                                # Handle list-style content (some models return structured blocks)
                                if isinstance(content, list):
                                    text_parts = []
                                    for block in content:
                                        if isinstance(block, str):
                                            text_parts.append(block)
                                        elif isinstance(block, dict) and block.get("text"):
                                            text_parts.append(block["text"])
                                    content = "\n".join(text_parts) if text_parts else ""
                                if content and isinstance(content, str) and content.strip():
                                    if has_tool_calls:
                                        # Agent is thinking before calling a tool
                                        steps.append(f"Agent: {content[:200]}")
                                    else:
                                        # Final answer (no tool calls)
                                        final_content = content

                        elif node_name == "tools":
                            # Tool responses
                            tool_msgs = node_output.get("messages", [])
                            for tm in tool_msgs:
                                content = getattr(tm, "content", None)
                                if content and isinstance(content, str):
                                    preview = content[:200]
                                    if len(content) > 200:
                                        preview += "..."
                                    steps.append(f"Tool result: {preview}")

                # Fallback: if streaming didn't capture a final answer, use invoke()
                if not final_content:
                    logger.warning("Streaming did not capture final content, falling back to invoke()")
                    result = agent.invoke(
                        {"messages": [{"role": "user", "content": user_input}]}
                    )
                    last_msg = result["messages"][-1]
                    final_content = getattr(last_msg, "content", "") or ""
                    if isinstance(final_content, list):
                        parts = []
                        for b in final_content:
                            if isinstance(b, str):
                                parts.append(b)
                            elif isinstance(b, dict) and b.get("text"):
                                parts.append(b["text"])
                        final_content = "\n".join(parts)
                if not final_content:
                    final_content = "I wasn't able to generate a response. Please try again."

                st.markdown(final_content)
                resp_time = datetime.now().strftime("%H:%M")
                st.markdown(
                    f'<div class="msg-time">{resp_time}</div>',
                    unsafe_allow_html=True,
                )

                if steps:
                    with st.expander("Agent reasoning steps"):
                        for step in steps:
                            st.text(step)

                # Store assistant message
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": final_content,
                        "time": resp_time,
                        "steps": steps if steps else None,
                    }
                )

            except Exception as exc:
                error_msg = f"An error occurred: {exc}"
                logger.error("Agent invocation failed: %s", exc, exc_info=True)
                st.error(error_msg)
                st.info("Please check that the MCP server and Ollama are running, then try again.")

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"\u274c {error_msg}",
                        "time": datetime.now().strftime("%H:%M"),
                    }
                )
