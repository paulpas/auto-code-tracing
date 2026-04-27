#!/usr/bin/env python3
# config.py
"""
Global configuration for all agents.

You can switch between:
* OpenAI (default)
* Anthropic
* HuggingFace
* Local Ollama
* Custom endpoint (e.g. Azure)

Per‑agent overrides are possible – each agent may have its own
``config`` dict inside its YAML file.
"""

import os
from pathlib import Path
import json

# -------------------------------------------------------------------------
# 1️⃣  Global defaults (used if an agent does not specify its own)
# -------------------------------------------------------------------------
GLOBAL_LLM = {
    "provider": os.getenv("LLM_PROVIDER", "openai"),   # openai | anthropic | huggingface | ollama
    "model": os.getenv("LLM_MODEL", "gpt-4o-mini"),
    "api_key": os.getenv("LLM_API_KEY", ""),          # for OpenAI / Anthropic / HF
    "base_url": os.getenv("LLM_BASE_URL", ""),        # e.g. http://localhost:11434 for Ollama
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
}

# -------------------------------------------------------------------------
# 2️⃣  Google PSE (Programmable Search Engine) credentials
# -------------------------------------------------------------------------
GOOGLE_PSE_ID = os.getenv("GOOGLE_PSE_ID", "")
GOOGLE_PSE_KEY = os.getenv("GOOGLE_PSE_KEY", "")

# -------------------------------------------------------------------------
# 3️⃣  Helper to build the LLM config dict that CrewAI expects
# -------------------------------------------------------------------------
def build_llm_config(overrides: dict | None = None) -> dict:
    """
    Return a dict that can be passed to ``Agent(llm=…)``.
    ``overrides`` can contain per‑agent customisation.
    """
    cfg = {
        "provider": GLOBAL_LLM["provider"],
        "model": GLOBAL_LLM["model"],
        "temperature": GLOBAL_LLM["temperature"],
        "api_key": GLOBAL_LLM["api_key"],
        "base_url": GLOBAL_LLM["base_url"],
    }
    if overrides:
        cfg.update(overrides)
    return cfg

# -------------------------------------------------------------------------
# 4️⃣  Helper to build a Google‑PSE search tool (wrapper around httpx)
# -------------------------------------------------------------------------
def google_pse_tool() -> dict:
    """
    Returns a dict compatible with CrewAI's ``WebSearchTool`` constructor.
    The actual tool class lives in ``crewai.tools`` – we only need to
    provide the name, class and the required ``api_key``/``engine_id``.
    """
    if not GOOGLE_PSE_ID or not GOOGLE_PSE_KEY:
        raise RuntimeError("Google PSE credentials not set (GOOGLE_PSE_ID / GOOGLE_PSE_KEY)")

    return {
        "name": "google_pse",
        "class": "crewai.tools.GoogleSearchTool",   # built‑in CrewAI tool
        "config": {
            "api_key": GOOGLE_PSE_KEY,
            "engine_id": GOOGLE_PSE_ID,
        },
        "description": "Search the web via Google Programmable Search Engine",
    }
