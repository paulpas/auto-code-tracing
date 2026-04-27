# DEBUG: injected by python‑injector
"""Modular debug system components."""

from .registry import DebugFunctionRegistry, DebugStage, DebugFunction
from .template_generator import DebugTemplateGenerator
from .snippet_injector import SnippetInjector, CodeSnippet

__all__ = [
    'DebugFunctionRegistry',
    'DebugStage', 
    'DebugFunction',
    'DebugTemplateGenerator',
    'SnippetInjector',
    'CodeSnippet'
]
