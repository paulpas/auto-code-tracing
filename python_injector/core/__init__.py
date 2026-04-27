# DEBUG: injected by python‑injector
"""Core injection components."""

from .injector import EnhancedCodeInjector

# Backward compatibility
CodeInjector = EnhancedCodeInjector

__all__ = ['EnhancedCodeInjector', 'CodeInjector']
