"""
Ollama LLM configuration for the Robot Framework AI Agent.

Default model: qwen2.5:32b-instruct-q4_k_m running on local Ollama.

To switch to a cloud LLM, replace get_llm() with one of these:

    # OpenAI
    pip install langchain-openai
    from langchain_openai import ChatOpenAI
    def get_llm():
        return ChatOpenAI(model="gpt-4o", temperature=0.1)

    # Anthropic
    pip install langchain-anthropic
    from langchain_anthropic import ChatAnthropic
    def get_llm():
        return ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.1)

Requires Ollama running locally: https://ollama.com
Pull the model first:  ollama pull qwen2.5:32b-instruct-q4_k_m
"""

from __future__ import annotations

import logging

from langchain_ollama import ChatOllama

logger = logging.getLogger("agent.llm_config")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:32b-instruct-q4_k_m"
TEMPERATURE = 0.1
NUM_CTX = 2048


def get_llm() -> ChatOllama:
    """Return a configured ChatOllama instance.

    Returns a BaseChatModel, which is required by ``create_agent``
    and supports ``.bind_tools()`` for ReAct-style tool calling.

    Usage::

        llm = get_llm()
        result = llm.invoke("Hello")
    """
    logger.info("Creating ChatOllama: model=%s base_url=%s", OLLAMA_MODEL, OLLAMA_BASE_URL)
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
        num_ctx=NUM_CTX,
    )


def test_connection() -> bool:
    """Verify that Ollama is reachable and the model is available.

    Returns True on success, False on failure.  Prints a diagnostic
    message either way.
    """
    llm = get_llm()
    try:
        response = llm.invoke("Reply with exactly: OK")
        logger.info("Ollama responded: %s", response.content.strip()[:80])
        print(f"[OK] Ollama connected — model {OLLAMA_MODEL} is responding")
        return True
    except Exception as exc:
        msg = str(exc)
        print(f"[FAIL] Cannot reach Ollama at {OLLAMA_BASE_URL}")
        if "Connection refused" in msg or "ConnectError" in msg:
            print("  -> Is Ollama running?  Start it with:  ollama serve")
        elif "not found" in msg.lower() or "404" in msg:
            print(f"  -> Model not pulled?  Run:  ollama pull {OLLAMA_MODEL}")
        else:
            print(f"  -> Error: {msg[:200]}")
        logger.error("Ollama connection test failed: %s", msg)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_connection()
