"""
tools/search_tool.py
-------------------
A wrapper for SerpAPI (or any other search provider) used by the
RetrieverAgent when `tool_map` points to `web_search`.
"""

import os
import httpx
from typing import Dict, Any

class WebSearchTool:
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key") or os.getenv("SERPAPI_API_KEY")
        self.engine = config.get("engine", "google")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __call__(self, query: str, **_) -> str:
        params = {
            "engine": self.engine,
            "q": query,
            "api_key": self.api_key,
        }
        resp = await self.client.get("https://serpapi.com/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        # Return a simple concatenation of the first few organic results.
        snippets = [r["snippet"] for r in data.get("organic_results", [])[:3]]
        return "\n\n".join(snippets) if snippets else "No results."
