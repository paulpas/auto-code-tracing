"""
tools/llm_tool.py
-----------------
A thin wrapper around OpenAI / Anthropic APIs that matches the
signature expected by the ExecutorAgent's `tool_map`.
"""

import os
import httpx
from typing import Any, Dict

class LLMTool:
    """
    Parameters are passed from the YAML `tool_map` entry.
    Example config:
        provider: openai
        model: gpt-4o-mini
        temperature: 0.7
    """
    def __init__(self, config: Dict[str, Any]):
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-4o-mini")
        self.temperature = config.get("temperature", 0.7)

        # Load API keys from environment – never hard-code them.
        if self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = "https://api.openai.com/v1"
        elif self.provider == "anthropic":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            self.base_url = "https://api.anthropic.com/v1"
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        self.client = httpx.AsyncClient(timeout=60.0)

    async def __call__(self, prompt: str, **kwargs) -> str:
        """Call the LLM and return the generated text."""
        if self.provider == "openai":
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "max_tokens": kwargs.get("max_tokens", 1024),
            }
            headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = await self.client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

        elif self.provider == "anthropic":
            payload = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 1024),
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            Hallo = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
            resp = await self.client.post(f"{self.base_url}/messages", json=payload, headers=Hallo)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]

        else:
            raise RuntimeError("Logic error – provider should have been validated.")
