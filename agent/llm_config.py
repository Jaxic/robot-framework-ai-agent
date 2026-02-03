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

import httpx
from langchain_ollama import ChatOllama

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_TEMPERATURE,
)

logger = logging.getLogger("agent.llm_config")


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
        temperature=OLLAMA_TEMPERATURE,
        num_ctx=OLLAMA_NUM_CTX,
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
    except httpx.ConnectError as exc:
        # Connection refused - Ollama not running
        print(f"[FAIL] Cannot reach Ollama at {OLLAMA_BASE_URL}")
        print("  -> Is Ollama running?  Start it with:  ollama serve")
        logger.error("Ollama connection failed: %s", exc)
        return False
    except httpx.HTTPStatusError as exc:
        # HTTP error (404 = model not found, etc.)
        print(f"[FAIL] Ollama returned HTTP error: {exc.response.status_code}")
        if exc.response.status_code == 404:
            print(f"  -> Model not pulled?  Run:  ollama pull {OLLAMA_MODEL}")
        else:
            print(f"  -> Error: {exc}")
        logger.error("Ollama HTTP error: %s", exc)
        return False
    except (httpx.RequestError, ValueError) as exc:
        # Other network errors or response parsing issues
        print(f"[FAIL] Cannot reach Ollama at {OLLAMA_BASE_URL}")
        print(f"  -> Error: {type(exc).__name__}: {str(exc)[:200]}")
        logger.error("Ollama connection test failed: %s", exc)
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_connection()
