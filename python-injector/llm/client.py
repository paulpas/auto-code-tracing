#!/usr/bin/env python3
"""LLM client with unified interface."""

from typing import Dict, Any, Optional, Set
from .providers import OpenAIProvider, OllamaProvider

class LLMClient:
    def __init__(self, provider_name: str, config: Dict[str, Any], debug_vars: Set[str]):
        self.provider_name = provider_name
        self.debug_vars = debug_vars
        
        if provider_name == "openai":
            self.provider = OpenAIProvider(config)
        else:
            self.provider = OllamaProvider(config)
    
    def build_payload(self, user_prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Build the request payload."""
        model = self.provider.config["model"]
        temperature = self.provider.config.get("temperature", 0.0)
        
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt.format(debug_vars=", ".join(self.debug_vars))},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "temperature": temperature,
        }
    
    def call(self, user_prompt: str, system_prompt: str) -> Optional[str]:
        """Make a call to the LLM."""
        payload = self.build_payload(user_prompt, system_prompt)
        return self.provider.call(payload)
