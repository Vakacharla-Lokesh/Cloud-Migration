"""
llm.py — Single source of truth for the LLM.
Configure the model here. All agents import from this file.

Current default: gemini-2.5-flash-lite via langchain-google-genai.
Swap the model string or the import to change the underlying provider.
"""

from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm() -> ChatGoogleGenerativeAI:
    """Return the configured LLM instance.

    Uses Google ADC (Application Default Credentials).
    Set GOOGLE_CLOUD_PROJECT env var if needed.
    Model: gemini-2.5-flash-lite — fast, cheap, good for structured output.
    """
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=0,            # deterministic for IaC generation
        max_retries=2,
    )
