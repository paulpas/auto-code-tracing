#!/usr/bin/env python3
"""Configuration management for debug injection with legacy support."""

import yaml
import pathlib
import logging
import os
from typing import Dict, Any

log = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_file: str = "debug_config.yaml"):
        self.config_file = pathlib.Path(config_file)
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with legacy support."""
        if not self.config_file.exists():
            log.error(f"❌ Config file {self.config_file} not found")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            # Transform legacy format to new format
            config = self._transform_legacy_config(raw_config)
            
            # Expand environment variables
            config = self._expand_env_vars(config)
            
            log.info(f"✅ Loaded config from {self.config_file}")
            return config
            
        except Exception as e:
            log.error(f"❌ Error loading config file: {e}")
            return self._get_default_config()
    
    def _transform_legacy_config(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform legacy config format to new structure."""
        config = {}
        
        # Handle LLM configuration
        provider = raw_config.get("provider", raw_config.get("llm", {}).get("provider", "ollama"))
        
        llm_config = {
            "provider": provider,
            "temperature": 0.0
        }
        
        # Handle provider-specific settings
        if provider == "ollama":
            ollama_config = raw_config.get("ollama", {})
            llm_config.update({
                "host": ollama_config.get("host", "http://localhost:11434"),
                "model": ollama_config.get("model", "llama3.2:latest"),
                "temperature": ollama_config.get("temperature", 0.0),
                "max_tokens": ollama_config.get("max_tokens", 8192)
            })
        elif provider == "openai":
            openai_config = raw_config.get("openai", {})
            llm_config.update({
                "base_url": openai_config.get("base_url", "https://api.openai.com/v1"),
                "model": openai_config.get("model", "gpt-4o-mini"),
                "api_key": openai_config.get("api_key", "${OPENAI_API_KEY}")
            })
        
        config["llm"] = llm_config
        
        # Handle debug variables
        debug_vars = (
            raw_config.get("debug_vars", []) or 
            raw_config.get("debug_env_vars", []) or 
            ["DEBUG", "DEBUG_MODE"]
        )
        config["debug_vars"] = debug_vars
        
        # Handle cache settings
        cache_dir = raw_config.get("cache_dir", raw_config.get("cache", {}).get("directory", ".debug_cache"))
        config["cache"] = {
            "enabled": True,
            "directory": cache_dir
        }
        
        # Handle file extensions
        config["file_extensions"] = raw_config.get("file_extensions", [".go", ".py", ".js", ".java"])
        
        # Handle telemetry (use defaults if not specified)
        config["telemetry"] = raw_config.get("telemetry", {
            "enabled": True,
            "precision": "nanosecond",
            "include_memory": True,
            "include_network": True,
            "include_data_flow": True
        })
        
        # Handle advanced settings
        config["services"] = raw_config.get("services", {})
        config["code_generation"] = raw_config.get("code_generation", {})
        config["advanced"] = raw_config.get("advanced", {})
        
        return config
    
    def _expand_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Expand environment variables in config values."""
        def expand_value(value):
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                return os.getenv(env_var, value)
            elif isinstance(value, dict):
                return {k: expand_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [expand_value(item) for item in value]
            return value
        
        return expand_value(config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "llm": {
                "provider": "ollama",
                "host": "http://localhost:11434", 
                "model": "llama3.2:latest",
                "temperature": 0.0
            },
            "debug_vars": ["DEBUG", "DEBUG_MODE"],
            "file_extensions": [".go", ".py", ".js", ".java"],
            "cache": {
                "enabled": True,
                "directory": ".debug_cache"
            },
            "telemetry": {
                "enabled": True,
                "precision": "nanosecond",
                "include_memory": True,
                "include_network": True
            }
        }
    
    # Legacy compatibility methods
    def ollama_config(self) -> Dict[str, Any]:
        """Get Ollama configuration (backward compatibility)."""
        config = self.load_config()
        return config.get("llm", {})
    
    def get_debug_vars(self) -> list:
        """Get debug environment variables."""
        config = self.load_config()
        return config.get("debug_vars", ["DEBUG"])
