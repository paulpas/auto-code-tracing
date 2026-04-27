# DEBUG: injected by python‑injector
#!/usr/bin/env python3
"""Enhanced code injector with modular debug system."""

import json
import pathlib
import logging
import traceback
import subprocess
from typing import Optional, List, Dict, Any, Union
from generic_parser import language_for_extension
from llm.prompts import SYSTEM_PROMPT

log = logging.getLogger(__name__)

class EnhancedCodeInjector:
    """Enhanced code injector using modular debug functions."""
    
    def __init__(self, llm_client, cache_manager, validator, filesystem_manager, service_name="unknown"):
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        self.validator = validator
        self.filesystem_manager = filesystem_manager
        self.service_name = service_name
        self.processed_files = []
        self.max_project_attempts = 3
        
        # Placeholder for modular components (will implement step by step)
        self.debug_module_path = None
    
    def process_service_files(self, service_dir: pathlib.Path, file_extensions: List[str]) -> int:
        """Process all files using the enhanced approach."""
        try:
            files_by_language = self._organize_files_by_language(service_dir, file_extensions)
            
            if not files_by_language:
                log.warning(f"⚠️  No source files found in {service_dir}")
                return 0
            
            log.info(f"🔍 Found files by language: {dict((k, len(v)) for k, v in files_by_language.items())}")
            
            processed_count = 0
            
            for lang_name, files in files_by_language.items():
                log.info(f"🎯 Processing {len(files)} {lang_name} files...")
                
                success = self._process_language_group(service_dir, files, lang_name)
                if success:
                    processed_count += len(files)
                    self.processed_files.extend([f.name for f in files])
                else:
                    log.error(f"❌ Failed to process {lang_name} files")
            
            return processed_count
            
        except Exception as e:
            log.error(f"❌ Fatal error in process_service_files: {e}")
            log.debug(f"Full traceback: {traceback.format_exc()}")
            return 0
    
    def _organize_files_by_language(self, service_dir: pathlib.Path, file_extensions: List[str]) -> Dict[str, List[pathlib.Path]]:
        """Organize source files by programming language."""
        files_by_language = {}
        
        for ext in file_extensions:
            for src_file in service_dir.glob(f"*{ext}"):
                if not self.filesystem_manager.should_skip_file(src_file):
                    try:
                        lang_obj = language_for_extension(src_file.suffix)
                        lang_name = lang_obj if isinstance(lang_obj, str) else getattr(lang_obj, "name", "unknown")
                        
                        if lang_name not in files_by_language:
                            files_by_language[lang_name] = []
                        files_by_language[lang_name].append(src_file)
                    except Exception as e:
                        log.warning(f"⚠️  Could not determine language for {src_file.name}: {e}")
                        continue
        
        return files_by_language
    
    def _process_language_group(self, service_dir: pathlib.Path, files: List[pathlib.Path], lang_name: str) -> bool:
        """Process a language group - simplified version for now."""
        try:
            debug_dir = self.filesystem_manager.create_debug_directory_structure(service_dir)
            
            log.info(f"📋 Creating debug functions for {lang_name}...")
            debug_module_created = self._create_debug_module(debug_dir, lang_name)
            
            if not debug_module_created:
                log.error("❌ Failed to create debug module")
                return False
            
            sorted_files = self._sort_files_for_language(files, lang_name)
            
            if self._can_skip_processing(sorted_files, debug_dir, lang_name):
                log.info(f"✅ All {lang_name} files up-to-date and project builds successfully")
                return True
            
            log.info(f"🔄 Processing {len(sorted_files)} files...")
            
            for project_attempt in range(1, self.max_project_attempts + 1):
                log.info(f"🏗️  Project attempt {project_attempt}/{self.max_project_attempts}")
                
                all_files_processed = True
                for src_file in sorted_files:
                    success = self._process_single_file(src_file, service_dir, project_attempt)
                    if not success:
                        log.error(f"❌ Failed to process {src_file.name}")
                        all_files_processed = False
                        break
                
                if not all_files_processed:
                    continue
                
                log.info("🔨 Verifying project build...")
                build_result = self._verify_project_build(debug_dir, lang_name, return_errors=True)
                
                if build_result == True or build_result == "":
                    log.info(f"✅ Project builds successfully on attempt {project_attempt}")
                    return True
                
                build_errors = str(build_result) if build_result else "Unknown build error"
                log.warning(f"⚠️  Project build failed on attempt {project_attempt}:")
                log.warning(f"Build errors: {build_errors[:500]}...")
                
                if project_attempt < self.max_project_attempts:
                    log.info("🔧 Attempting to fix build issues...")
                    fixes_applied = self._fix_build_issues(sorted_files, debug_dir, build_errors, lang_name)
                    if fixes_applied:
                        log.info("Applied fixes, retesting...")
                    else:
                        log.warning("Could not apply effective fixes, will retry")
            
            log.error(f"❌ Failed to create working {lang_name} project after {self.max_project_attempts} attempts")
            return False
            
        except Exception as e:
            log.error(f"❌ Error in language group processing: {e}")
            log.debug(f"Full traceback: {traceback.format_exc()}")
            return False
    
    def _create_debug_module(self, debug_dir: pathlib.Path, lang_name: str) -> bool:
        """Create debug function module for the language."""
        try:
            if lang_name.lower() == 'go':
                debug_file = debug_dir / "debug_telemetry.go"
                debug_content = self._generate_go_debug_module()
            elif lang_name.lower() == 'python':
                debug_file = debug_dir / "debug_telemetry.py"
                debug_content = self._generate_python_debug_module()
            else:
                log.warning(f"⚠️  No debug module template for {lang_name}")
                return True  # Don't fail for unknown languages
            
            debug_file.write_text(debug_content, encoding="utf-8")
            self.debug_module_path = str(debug_file)
            log.info(f"✅ Created debug module: {debug_file.name}")
            return True
            
        except Exception as e:
            log.error(f"❌ Error creating debug module: {e}")
            return False
    
    def _generate_go_debug_module(self) -> str:
        """Generate Go debug module content."""
        return f'''package main

import (
	"fmt"
	"os"
	"runtime"
	"strings"
	"sync"
	"time"
)

// Debug telemetry globals for service: {self.service_name}
var (
	debugEnabled   bool
	serviceName    string
	debugMutex     sync.RWMutex
)

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

func debug_enter(functionName string) time.Time {{
	if !debugEnabled {{
		return time.Time{{}}
	}}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	fmt.Printf("[TELEMETRY|%s|%d] ENTER: %s | Memory: %d bytes | Goroutines: %d\\n",
		serviceName, timestamp.UnixNano(), functionName, memStats.HeapInuse, runtime.NumGoroutine())
	return timestamp
}}

func debug_exit(functionName string, startTime time.Time) {{
	if !debugEnabled {{
		return
	}}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	duration := timestamp.Sub(startTime).Nanoseconds()
	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)
	fmt.Printf("[TELEMETRY|%s|%d] EXIT: %s | Duration: %d ns (%.3f ms) | Memory: %d bytes\\n",
		serviceName, timestamp.UnixNano(), functionName, duration, float64(duration)/1e6, memStats.HeapInuse)
}}

func debug_data_flow(direction, dataType string, dataSize int64, destination string) {{
	if !debugEnabled {{
		return
	}}
	debugMutex.RLock()  
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	fmt.Printf("[TELEMETRY|%s|%d] DATA-FLOW: %s | Type: %s | Size: %d bytes | Destination: %s\\n",
		serviceName, timestamp.UnixNano(), direction, dataType, dataSize, destination)
}}

func debug_network_call(method, url string, requestSize, responseSize int64, duration time.Duration, statusCode int) {{
	if !debugEnabled {{
		return
	}}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	fmt.Printf("[TELEMETRY|%s|%d] NETWORK: %s %s | Request: %d bytes | Response: %d bytes | Duration: %d ns (%.3f ms) | Status: %d\\n",
		serviceName, timestamp.UnixNano(), method, url, requestSize, responseSize, duration.Nanoseconds(), float64(duration.Nanoseconds())/1e6, statusCode)
}}

func debug_error(functionName, errorMsg string) {{
	if !debugEnabled {{
		return
	}}
	debugMutex.RLock()
	defer debugMutex.RUnlock()
	timestamp := time.Now()
	fmt.Printf("[TELEMETRY|%s|%d] ERROR in %s: %s\\n",
		serviceName, timestamp.UnixNano(), functionName, errorMsg)
}}
'''
    
    def _generate_python_debug_module(self) -> str:
        """Generate Python debug module content."""
        return f'''"""Debug telemetry module for {self.service_name}."""

import time
import os
import sys

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

def debug_enter(function_name: str) -> float:
    if not debug_enabled:
        return 0.0
    start_time = time.time()
    timestamp_ns = int(start_time * 1e9)
    print(f"[TELEMETRY|{{service_name}}|{{timestamp_ns}}] ENTER: {{function_name}}")
    return start_time

def debug_exit(function_name: str, start_time: float) -> None:
    if not debug_enabled:
        return
    end_time = time.time()
    timestamp_ns = int(end_time * 1e9)
    duration_ns = int((end_time - start_time) * 1e9)
    duration_ms = (end_time - start_time) * 1000
    print(f"[TELEMETRY|{{service_name}}|{{timestamp_ns}}] EXIT: {{function_name}} | Duration: {{duration_ns}} ns ({{duration_ms:.3f}} ms)")

def debug_error(function_name: str, error_msg: str) -> None:
    if not debug_enabled:
        return
    timestamp_ns = int(time.time() * 1e9)
    print(f"[TELEMETRY|{{service_name}}|{{timestamp_ns}}] ERROR in {{function_name}}: {{error_msg}}")
'''
    
    def _process_single_file(self, src_file: pathlib.Path, service_dir: pathlib.Path, attempt: int) -> bool:
        """Process a single file with instrumentation."""
        try:
            debug_dir = service_dir / "debug"
            debug_file = debug_dir / f"{src_file.stem}_debug{src_file.suffix}"
            
            log.info(f"🔄 Processing {src_file.name} (attempt {attempt})")
            
            source_code = src_file.read_text(encoding="utf-8")
            
            # Simple instrumentation for now
            instrumented_code = self._add_basic_instrumentation(source_code, src_file.suffix)
            
            if self._validate_instrumented_file(src_file, instrumented_code):
                debug_file.write_text(instrumented_code, encoding="utf-8")
                log.info(f"✅ Generated {debug_file.name}")
                return True
            else:
                log.error(f"❌ Validation failed for {debug_file.name}")
                return False
                
        except Exception as e:
            log.error(f"❌ Error processing {src_file.name}: {e}")
            return False
    
    def _add_basic_instrumentation(self, code: str, file_extension: str) -> str:
        """Add instrumentation using LLM."""
        try:
            lang_name = self._get_language_from_extension(file_extension)
            
            # Build instrumentation prompt
            user_prompt = self._build_instrumentation_prompt(code, lang_name)
            
            log.debug(f"🔄 Requesting LLM instrumentation for {file_extension} file")
            
            # Call LLM with system prompt
            instrumented_code = self.llm_client.call(user_prompt, SYSTEM_PROMPT)
            
            if not instrumented_code or len(instrumented_code.strip()) < len(code.strip()):
                log.warning("⚠️  LLM returned empty or shorter code, using original")
                return code
            
            # Clean up the response
            instrumented_code = self._extract_from_json_if_needed(instrumented_code)
            instrumented_code = self._clean_llm_response(instrumented_code)
            
            log.info("✅ LLM instrumentation completed")
            return instrumented_code
            
        except Exception as e:
            log.error(f"❌ Error in LLM instrumentation: {e}")
            log.debug(f"Full traceback: {traceback.format_exc()}")
            return code
    
    def _get_language_from_extension(self, file_extension: str) -> str:
        """Get language name from file extension."""
        ext_map = {
            '.go': 'Go',
            '.py': 'Python', 
            '.java': 'Java',
            '.js': 'JavaScript',
            '.cpp': 'C++',
            '.c': 'C'
        }
        return ext_map.get(file_extension.lower(), 'Unknown')
    
    def _build_instrumentation_prompt(self, code: str, lang_name: str) -> str:
        """Build prompt for LLM instrumentation."""
        return f"""Add comprehensive debug instrumentation to this {lang_name} code.

ORIGINAL CODE:
```{lang_name.lower()}
{code}

Copy code
AVAILABLE DEBUG FUNCTIONS (already defined in debug_telemetry file):

debug_enter(functionName) -> startTime // Call at function start
debug_exit(functionName, startTime) // Call at function end (use defer in Go)
debug_data_flow(direction, dataType, dataSize, destination) // For data processing
debug_network_call(method, url, reqSize, respSize, duration, statusCode) // For HTTP calls
debug_error(functionName, errorMessage) // For error conditions
INSTRUMENTATION REQUIREMENTS:

Add debug_enter() at the START of every function/method
Add debug_exit() at the END of every function/method (use defer in Go)
Add debug_data_flow() around significant data processing operations
Add debug_network_call() around HTTP requests/responses
Add debug_error() in error handling blocks
Keep ALL original functionality intact
Use proper {lang_name} syntax and conventions
CRITICAL RULES:

DO NOT modify the original business logic
DO NOT remove any existing code
ONLY ADD debug function calls
Use exact function signatures provided above
For Go: use defer for debug_exit calls
For Python: call debug_exit in finally blocks or at function end
Handle null/nil values safely in debug calls
SERVICE CONTEXT:

Service Name: {self.service_name}
Debug functions are available (defined in debug_telemetry module)
All debug output goes to STDOUT with format: [TELEMETRY|SERVICE|TIMESTAMP] LEVEL: DETAILS
Return ONLY the instrumented source code without explanations or markdown formatting."""

def _clean_llm_response(self, response: str) -> str:
    """Clean up LLM response."""
    # Remove markdown code blocks if present
    if response.startswith('```'):
        lines = response.split('\n')
        # Remove first line if it's a code block marker
        if lines[0].startswith('```'):
            lines = lines[1:]
        # Remove last line if it's a closing code block marker
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        response = '\n'.join(lines)
    
    return response.strip()

def _extract_from_json_if_needed(self, response: str) -> str:
    """Extract code from JSON response if needed."""
    try:
        if response.strip().startswith('{') and ('"message":' in response or '"response":' in response):
            json_obj = json.loads(response)
            if "message" in json_obj and "content" in json_obj["message"]:
                return json_obj["message"]["content"]
            elif "response" in json_obj:
                return json_obj["response"]
    except:
        pass
    
    return response

def _validate_instrumented_file(self, src_file: pathlib.Path, instrumented_code: str) -> bool:
    """Enhanced validation of instrumented file."""
    try:
        # Basic length check
        if len(instrumented_code.strip()) < 50:
            log.error("Instrumented code is too short")
            return False
        
        # Check that instrumentation was actually added
        debug_functions = ['debug_enter', 'debug_exit', 'debug_data_flow', 'debug_network_call', 'debug_error']
        has_debug_calls = any(func in instrumented_code for func in debug_functions)
        
        if not has_debug_calls:
            log.warning("⚠️  No debug function calls found in instrumented code")
            # Don't fail completely, but warn
        
        # Language-specific validation
        if src_file.suffix.lower() == '.go':
            return self._validate_go_instrumentation(instrumented_code)
        elif src_file.suffix.lower() == '.py':
            return self._validate_python_instrumentation(instrumented_code)
        
        return True
        
    except Exception as e:
        log.error(f"❌ Validation error for {src_file.name}: {e}")
        return False

def _validate_go_instrumentation(self, code: str) -> bool:
    """Validate Go instrumentation."""
    try:
        # Check for package declaration
        if not code.strip().startswith('package '):
            log.error("Missing package declaration in Go code")
            return False
        
        # Check for balanced braces
        brace_count = code.count('{') - code.count('}')
        if brace_count != 0:
            log.error(f"Unbalanced braces in Go code: {brace_count}")
            return False
        
        # Check for proper defer usage with debug_exit
        if 'debug_exit' in code and 'defer debug_exit' not in code:
            log.warning("⚠️  debug_exit found but not used with defer in Go code")
        
        return True
        
    except Exception as e:
        log.debug(f"Go validation error: {e}")
        return True  # Don't fail on validation errors

def _validate_python_instrumentation(self, code: str) -> bool:
    """Validate Python instrumentation."""
    try:
        # Try to compile the Python code
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError as e:
        log.error(f"Python syntax error in instrumented code: {e}")
        return False
    except Exception as e:
        log.debug(f"Python validation error: {e}")
        return True

    
    def _can_skip_processing(self, source_files: List[pathlib.Path], debug_dir: pathlib.Path, lang_name: str) -> bool:
        """Check if we can skip processing."""
        return False  # Always process for now
    
    def _fix_build_issues(self, source_files: List[pathlib.Path], debug_dir: pathlib.Path, 
                         build_errors: str, lang_name: str) -> bool:
        """Fix build issues."""
        return False  # No fixes implemented yet
    
    def _verify_project_build(self, debug_dir: pathlib.Path, lang_name: str, return_errors: bool = False) -> Union[bool, str]:
        """Verify project builds."""
        if lang_name.lower() == 'go':
            return self._verify_go_project_build(debug_dir, return_errors)
        else:
            return True if not return_errors else ""
    
    def _verify_go_project_build(self, debug_dir: pathlib.Path, return_errors: bool = False) -> Union[bool, str]:
        """Verify Go project builds."""
        try:
            result = subprocess.run(
                ["go", "build", "-v", "."],
                cwd=debug_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Clean up binaries
                for item in debug_dir.glob("*"):
                    if item.is_file() and not item.suffix and item.name not in ["go.mod", "go.sum"]:
                        try:
                            item.unlink()
                        except:
                            pass
                return True if not return_errors else ""
            else:
                error_output = ""
                if result.stderr:
                    error_output += f"STDERR:\n{result.stderr}\n"
                if result.stdout:
                    error_output += f"STDOUT:\n{result.stdout}\n"
                return error_output if return_errors else False
                
        except Exception as e:
            error_msg = f"Go build error: {e}"
            return error_msg if return_errors else False
    
    def _sort_files_for_language(self, files: List[pathlib.Path], lang_name: str) -> List[pathlib.Path]:
        """Sort files for optimal processing order."""
        def sort_key(file_path):
            name = file_path.name.lower()
            if lang_name.lower() == 'go':
                if name == 'main.go':
                    return (0, name)
                elif 'main' in name:
                    return (1, name)
                else:
                    return (2, name)
            else:
                return (1, name)
        
        return sorted(files, key=sort_key)

# Backward compatibility
CodeInjector = EnhancedCodeInjector
