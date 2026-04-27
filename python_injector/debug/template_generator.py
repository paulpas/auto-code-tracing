# DEBUG: injected by python‑injector
#!/usr/bin/env python3
"""Generate debug function implementations using LLM."""

import pathlib
import logging
from typing import List, Dict, Any, Optional
from .registry import DebugFunctionRegistry, DebugFunction, DebugStage

log = logging.getLogger(__name__)

class DebugTemplateGenerator:
    """Generates debug function implementations using LLM."""
    
    def __init__(self, llm_client, service_name: str):
        self.llm_client = llm_client
        self.service_name = service_name
        self.registry = DebugFunctionRegistry()
    
    def generate_debug_module(self, language: str, debug_dir: pathlib.Path) -> Optional[str]:
        """Generate complete debug module with all functions."""
        try:
            # Register functions for this language
            functions = self.registry.register_language_functions(language, self.service_name)
            
            if not functions:
                log.warning(f"No debug functions registered for {language}")
                return None
            
            log.info(f"🔧 Generating debug module for {language} with {len(functions)} functions")
            
            # Generate implementations for each function
            for func in functions:
                func.implementation = self._generate_function_implementation(func)
                if not func.implementation:
                    log.error(f"❌ Failed to generate implementation for {func.name}")
                    return None
            
            # Assemble complete debug module
            debug_module = self._assemble_debug_module(language, functions)
            
            # Save to debug directory
            if language.lower() == 'go':
                debug_file = debug_dir / "debug_telemetry.go"
            elif language.lower() == 'python':
                debug_file = debug_dir / "debug_telemetry.py"
            elif language.lower() == 'java':
                debug_file = debug_dir / "DebugTelemetry.java"
            else:
                debug_file = debug_dir / f"debug_telemetry.{language}"
            
            debug_file.write_text(debug_module, encoding="utf-8")
            log.info(f"✅ Generated debug module: {debug_file.name}")
            
            return str(debug_file)
            
        except Exception as e:
            log.error(f"❌ Error generating debug module: {e}")
            return None
    
    def _generate_function_implementation(self, func: DebugFunction) -> Optional[str]:
        """Generate implementation for a single debug function using LLM."""
        try:
            prompt = self._build_function_generation_prompt(func)
            
            log.debug(f"🔄 Generating implementation for {func.name}")
            
            implementation = self.llm_client.call(prompt, "")
            
            if not implementation or len(implementation.strip()) < 20:
                log.warning(f"⚠️  Generated implementation too short for {func.name}")
                return None
            
            # Extract from JSON if needed
            implementation = self._extract_from_json_if_needed(implementation)
            
            # Clean up the implementation (remove markdown, etc.)
            implementation = self._clean_implementation(implementation, func.language)
            
            log.info(f"✅ Generated implementation for {func.name}")
            return implementation
            
        except Exception as e:
            log.error(f"❌ Error generating {func.name}: {e}")
            return None
    
    def _build_function_generation_prompt(self, func: DebugFunction) -> str:
        """Build prompt for generating a single debug function."""
        return f"""Generate a {func.language} function implementation with the following specification:

FUNCTION SPECIFICATION:
- Name: {func.name}
- Signature: {func.signature}
- Parameters: {', '.join(func.parameters) if func.parameters else 'none'}
- Returns: {func.returns or 'void/none'}
- Purpose: {func.description}
- Usage: {func.usage_pattern}
- Stage: {func.stage.value}

SERVICE CONTEXT:
- Service Name: {self.service_name}
- Debug Variables: DEBUG, DEBUG_MODE, TRACE, VERBOSE
- Log Format: [TELEMETRY|{self.service_name}|TIMESTAMP] LEVEL: DETAILS

REQUIREMENTS:
1. Only activate when environment debug variables are "true" or "enabled" (case-insensitive)
2. Use thread-safe operations where applicable
3. Include timestamp in nanoseconds if possible
4. Log to STDOUT using the specified format
5. Handle errors gracefully (no crashes if debug fails)
6. Minimal performance impact when disabled
7. Include relevant context (memory, timing, data sizes)

CRITICAL RULES:
- Return ONLY the function implementation code
- No explanations, comments, or markdown formatting
- Use proper {func.language} syntax and conventions
- Make it production-ready and robust
- Handle null/nil values safely

Generate the complete function implementation now:"""
    
    def _assemble_debug_module(self, language: str, functions: List[DebugFunction]) -> str:
        """Assemble all functions into a complete module."""
        if language.lower() == 'go':
            return self._assemble_go_module(functions)
        elif language.lower() == 'python':
            return self._assemble_python_module(functions)
        elif language.lower() == 'java':
            return self._assemble_java_module(functions)
        else:
            return self._assemble_generic_module(language, functions)
    
    def _assemble_go_module(self, functions: List[DebugFunction]) -> str:
        """Assemble Go debug module."""
        # Get all unique dependencies
        all_deps = set()
        for func in functions:
            all_deps.update(func.dependencies)
        
        imports = "\n".join(f'\t"{dep}"' for dep in sorted(all_deps))
        
        # Get initialization function
        init_func = next((f for f in functions if f.name == "debug_init"), None)
        
        # Build global variables section
        globals_section = f'''
// Debug telemetry globals for service: {self.service_name}
var (
	debugEnabled   bool
	serviceName    string
	debugMutex     sync.RWMutex
)
'''
        
        # Build init function or default one
        if init_func and init_func.implementation:
            init_section = init_func.implementation
        else:
            init_section = f'''
func init() {{
	// Initialize debug settings for {self.service_name}
	debugVars := []string{{"DEBUG", "DEBUG_MODE", "TRACE", "VERBOSE"}}
	for _, envVar := range debugVars {{
		if val := os.Getenv(envVar); val != "" {{
			debugEnabled = strings.ToLower(val) == "true" || strings.ToLower(val) == "enabled"
			if debugEnabled {{
				break
			}}
		}}
	}}
	serviceName = os.Getenv("SERVICE_NAME")
	if serviceName == "" {{
		serviceName = "{self.service_name}"
	}}
}}
'''
        
        # Build all function implementations
        function_implementations = []
        for func in functions:
            if func.name != "debug_init" and func.implementation:
                function_implementations.append(func.implementation)
        
        return f'''package main

import (
{imports}
)
{globals_section}
{init_section}

{chr(10).join(function_implementations)}
'''
    
    def _assemble_python_module(self, functions: List[DebugFunction]) -> str:
        """Assemble Python debug module."""
        all_deps = set()
        for func in functions:
            all_deps.update(func.dependencies)
        
        imports = "\n".join(f"import {dep}" for dep in sorted(all_deps))
        
        function_implementations = []
        for func in functions:
            if func.implementation:
                function_implementations.append(func.implementation)
        
        return f'''"""Debug telemetry module for {self.service_name}."""

{imports}

# Debug telemetry globals
debug_enabled = False
service_name = "{self.service_name}"

# Initialize debug settings
def _init_debug():
    global debug_enabled, service_name
    debug_vars = ["DEBUG", "DEBUG_MODE", "TRACE", "VERBOSE"]
    for env_var in debug_vars:
        val = os.environ.get(env_var, "").lower()
        if val in ["true", "enabled", "1"]:
            debug_enabled = True
            break
    
    service_name = os.environ.get("SERVICE_NAME", "{self.service_name}")

# Initialize on import
_init_debug()

{chr(10).join(function_implementations)}
'''
    
    def _assemble_java_module(self, functions: List[DebugFunction]) -> str:
        """Assemble Java debug module."""
        # Similar implementation for Java
        return f"""// Debug telemetry for {self.service_name}
public class DebugTelemetry {{
    // Implementation for Java
}}"""
    
    def _assemble_generic_module(self, language: str, functions: List[DebugFunction]) -> str:
        """Assemble generic debug module."""
        return f"// Debug module for {language}\n// Service: {self.service_name}"
    
    def _clean_implementation(self, implementation: str, language: str) -> str:
        """Clean up generated implementation."""
        # Remove markdown code blocks
        if implementation.startswith('```'):
            lines = implementation.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].startswith('```'):
                lines = lines[:-1]
            implementation = '\n'.join(lines)
        
        return implementation.strip()
    
    def _extract_from_json_if_needed(self, response: str) -> str:
        """Extract implementation from JSON response if needed."""
        if response.strip().startswith('{'):
            try:
                import json
                json_obj = json.loads(response)
                if "message" in json_obj and "content" in json_obj["message"]:
                    return json_obj["message"]["content"]
                elif "response" in json_obj:
                    return json_obj["response"]
            except json.JSONDecodeError:
                pass
        return response
