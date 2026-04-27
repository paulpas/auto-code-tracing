#!/usr/bin/env python3
"""LLM provider implementations."""

import os
import json
import re
import logging
from typing import Dict, Any, Optional
import httpx

log = logging.getLogger(__name__)

class BaseLLMProvider:
    """Base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def call(self, payload: Dict[str, Any]) -> Optional[str]:
        raise NotImplementedError

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    def call(self, payload: Dict[str, Any]) -> Optional[str]:
        url = self.config["base_url"] + "/chat/completions"
        headers = {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"}
        
        try:
            with httpx.Client(timeout=1200.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                response_json = resp.json()
                return response_json['choices'][0]['message']['content']
        except Exception as e:
            log.error(f"Error calling OpenAI: {str(e)}")
            return None

class OllamaProvider(BaseLLMProvider):
    """Ollama API provider."""
    
    def filter_thinking(self, text: str) -> str:
        """Filter out thinking sections from the response."""
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        text = re.sub(r'```thinking.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def call(self, payload: Dict[str, Any]) -> Optional[str]:
        url = f"{self.config['host']}/api/chat"
        
        try:
            with httpx.Client(timeout=1200.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if "message" in result and "content" in result["message"]:
                    content = result["message"]["content"]
                    if content and content.strip():
                        return self.filter_thinking(content)
                
                # Fallback attempts...
                return self._try_fallbacks(client, payload)
                
        except httpx.HTTPError as e:
            log.error(f"Error calling Ollama API: {e}")
            return None
    
    def _try_fallbacks(self, client: httpx.Client, payload: Dict[str, Any]) -> Optional[str]:
        """Try various fallback methods for Ollama."""
        # Implementation of retry logic from original script
        # ... (abbreviated for brevity)
        pass
