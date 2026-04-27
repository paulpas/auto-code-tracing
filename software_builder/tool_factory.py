#!/usr/bin/env python3
# tool_factory.py
"""
Utility that turns the plain dictionaries read from the YAML files into
actual CrewAI tool objects, filling missing required fields (like description)
with sensible defaults.
"""

from typing import List, Dict, Any
import logging

log = logging.getLogger(__name__)

def _import_tool_class(class_path: str):
    """
    Resolve a dotted class path (e.g. "crewai.tools.WebSearchTool") to the
    actual Python class object.
    """
    module_path, class_name = class_path.rsplit(".", 1)
    mod = __import__(module_path, fromlist=[class_name])
    return getattr(mod, class_name)

def build_tool(tool_dict: Dict[str, Any]):
    """
    Build a single CrewAI Tool instance from a dict that may be missing
    optional fields.  Required fields for CrewAI >=0.2 are:
        - name
        - description
        - class (full dotted import path)
        - config (optional dict of extra kwargs)

    If ``description`` is missing we create a generic placeholder.
    """
    name = tool_dict.get("name", "unnamed_tool")
    description = tool_dict.get("description", f"Tool {name}")
    class_path = tool_dict.get("class")
    if not class_path:
        raise ValueError(f"Tool '{name}' does not specify a 'class' field.")
    config = tool_dict.get("config", {})

    # Resolve the class and instantiate it.
    ToolCls = _import_tool_class(class_path)
    # Most built‑in tools accept ``name`` and ``description`` plus any extra config.
    return ToolCls(name=name, description=description, **config)

def build_tool_list(raw_tools: List[Dict[str, Any]]) -> List[Any]:
    """
    Convert a list of raw dicts into a list of CrewAI tool objects.
    """
    tools = []
    for td in raw_tools:
        try:
            tool_obj = build_tool(td)
            tools.append(tool_obj)
        except Exception as exc:
            log.warning("Failed to build tool from %s – %s – skipping", td, exc)
    return tools
