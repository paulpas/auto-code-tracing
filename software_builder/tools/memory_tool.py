"""
tools/memory_tool.py
--------------------
A very small in-process memory store.  The real persistent MemoryAgent
uses a vector DB; this tool is only for quick key/value passing.
"""

from typing import Dict, Any

class MemoryTool:
    def __init__(self, config: Dict[str, Any] = None):
        self.store: Dict[str, Any] = {}

    async def __call__(self, action: str, key: str, value: Any = None) -> str:
        if action == "set":
            self.store[key] = value
            return f"Set {key}"
        if action == "get":
            return self.store.get(key, "")
        raise ValueError(f"Unsupported action {action}")
