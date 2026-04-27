# DEBUG: injected by python‑injector
#!/usr/bin/env python3
"""Language-agnostic system prompts for the LLM with API specifications."""

SYSTEM_PROMPT = """
You are a code-generation assistant that creates comprehensive debug instrumentation for any programming language.
Do NOT include any reasoning, thoughts, plans, or explanations.
Return ONLY the **instrumented source code** in the detected language.

CORE PRINCIPLES:
* **Detect the programming language** from the source code automatically
* **Adapt to language conventions** - use appropriate syntax, imports, and patterns for that language
* **Use provided API specifications** - if debug function signatures are provided, use them exactly
* **Avoid code duplication** - if multiple files exist in the same namespace/package/module, share debug functions appropriately
* **Merge imports/includes** - integrate new dependencies into existing import sections

TELEMETRY REQUIREMENTS (adapt to language capabilities):
* **Timestamps**: Highest precision available (nanoseconds preferred, milliseconds acceptable)
* **Function Tracing**: Entry and exit logging with execution duration
* **Memory Usage**: Current memory consumption where language provides APIs
* **Data Flow**: Log input/output data sizes and types for significant operations
* **Network Calls**: Wrap HTTP/network operations with request/response metrics
* **Error Tracking**: Log exceptions, errors, and failure conditions
* **Concurrency**: Track threads/goroutines/processes where applicable

LOG FORMAT STANDARD:
* Consistent format: `[TELEMETRY|SERVICE_NAME|TIMESTAMP] LEVEL: DETAILS`
* All output to STDOUT for log aggregation
* Structured data that can be parsed later
* Levels: ENTER, EXIT, SUB-TASK, DATA-FLOW, MEMORY, NETWORK, ERROR

INSTRUMENTATION STRATEGY:
* **Every function/method** must be wrapped with entry/exit tracing
* **Significant operations** need sub-task timing
* **Data processing** requires input/output size logging  
* **Network operations** need comprehensive request/response metrics
* **Memory-intensive operations** need memory usage tracking
* **Error conditions** need error logging

LANGUAGE-SPECIFIC ADAPTATIONS:
* **Compiled languages** (Go, Java, C++): Prefer compile-time checks, static variables
* **Interpreted languages** (Python, JavaScript): Use runtime detection, global variables
* **Functional languages**: Adapt to functional patterns and immutability
* **Object-oriented languages**: Use appropriate class/instance patterns

ACTIVATION CONTROL:
* Debug instrumentation only activates when environment variables are set to "true" or "enabled" (case-insensitive)
* Minimal performance impact when disabled
* Thread-safe where concurrency is possible

CRITICAL RULES:
* **DO NOT duplicate function definitions** across files in the same namespace/package/module
* **First file processed** in a package/module gets the debug function definitions
* **Subsequent files** only get debug function calls, never definitions
* **Maintain original functionality** - only add instrumentation, never change business logic
* **Handle edge cases** gracefully (null values, network failures, etc.)

The output must be **plain source code only** - no markdown fences, explanations, or additional text.
"""

def build_enhanced_user_prompt(source_code: str, service_name: str, debug_vars: list, file_context: dict) -> str:
    """Build language-agnostic user prompt with API specification."""
    debug_vars_str = ', '.join(debug_vars)
    
    # Include debug API specification if available
    api_spec_info = ""
    if 'debug_api_spec' in file_context:
        api_spec = file_context['debug_api_spec']
        api_spec_info = f"""
DEBUG API SPECIFICATION:
You MUST use these exact function signatures and calling conventions:

"""
        for func in api_spec.get('functions', []):
            api_spec_info += f"- {func['signature']}\n"
            api_spec_info += f"  Usage: {func['usage']}\n\n"
        
        if file_context.get('is_primary_file'):
            api_spec_info += f"""
THIS IS THE PRIMARY FILE - Include the debug functions template.
Copy the exact function implementations into this file from the template.
Required imports: {', '.join(api_spec.get('required_imports', []))}
"""
        else:
            api_spec_info += f"""
THIS IS A SECONDARY FILE - Do NOT define debug functions.
Only ADD CALLS to the debug functions using the exact signatures above.
The debug functions are already defined in the primary file.
Required imports: {', '.join(api_spec.get('required_imports', []))}
"""
    
    context_info = ""
    if file_context.get('is_primary_file'):
        context_info = """
FILE CONTEXT: This is the PRIMARY file for debug instrumentation.
- INCLUDE the complete debug function definitions using the API specification above
- Add necessary imports for instrumentation  
- Add debug calls to all functions in this file
"""
    else:
        context_info = """
FILE CONTEXT: This is a SECONDARY file.
- DO NOT define any debug functions - they exist in the primary file
- ONLY ADD debug function calls using the exact API specification above
- DO NOT duplicate any debug function definitions
"""
    
    previous_files_info = ""
    if file_context.get('processed_files') and len(file_context['processed_files']) > 0:
        previous_files_info = f"""
PROCESSED FILES IN THIS SERVICE: {', '.join(file_context['processed_files'])}
These files may already have debug functions defined. Avoid duplication.
"""
    
    return f"""---BEGIN SOURCE CODE---
{source_code}
---END SOURCE CODE---

SERVICE: {service_name}
DEBUG ACTIVATION VARIABLES: {debug_vars_str}

{api_spec_info}

{context_info}

{previous_files_info}

INSTRUCTIONS:
1. **DETECT the programming language** from the source code
2. **USE the exact debug API specification** provided above (if available)
3. **ANALYZE existing imports/includes** and merge new dependencies appropriately
4. **DETERMINE if this is a primary or secondary file** based on context
5. **IMPLEMENT comprehensive telemetry** using the specified function signatures
6. **ENSURE thread/concurrency safety** where applicable
7. **MAINTAIN original code structure** and business logic
8. **ADD instrumentation to every function/method**
9. **HANDLE errors gracefully** in instrumentation code

TELEMETRY GOALS:
- Trace every function entry/exit with duration
- Monitor memory usage at key points
- Log data flow (sizes, types, destinations)
- Instrument network calls with full metrics
- Track concurrency (threads/goroutines/etc.)
- Capture and log error conditions
- Provide structured output for analysis

CRITICAL: Use ONLY the debug function signatures provided in the API specification (if provided).
Do not invent new function signatures or parameter types.
Replace "SERVICE_NAME" with the actual service name: "{service_name}"
Replace debug activation variables with: {debug_vars_str}"""

def get_file_context(src_path, processed_files: list, service_files: list) -> dict:
    """Generate context information for the current file."""
    file_extension = src_path.suffix.lower()
    file_name = src_path.name
    
    # Determine if this should be the primary file
    is_primary = False
    
    # Language-specific primary file detection
    if file_extension == '.go':
        # For Go, main.go is typically primary, or first alphabetically
        is_primary = (file_name == 'main.go' or len(processed_files) == 0)
    elif file_extension == '.py':
        # For Python, __init__.py or main.py, or first processed
        is_primary = (file_name in ['__init__.py', 'main.py'] or len(processed_files) == 0)
    elif file_extension == '.java':
        # For Java, Main.java or Application.java, or first processed
        is_primary = ('main' in file_name.lower() or 'application' in file_name.lower() or len(processed_files) == 0)
    elif file_extension == '.js':
        # For JavaScript, index.js or main.js, or first processed
        is_primary = (file_name in ['index.js', 'main.js', 'app.js'] or len(processed_files) == 0)
    else:
        # For other languages, first file processed becomes primary
        is_primary = (len(processed_files) == 0)
    
    return {
        'is_primary_file': is_primary,
        'processed_files': processed_files.copy(),
        'total_files': len(service_files),
        'file_extension': file_extension,
        'file_name': file_name
    }

def get_language_specific_lint_tips(language: str) -> str:
    """Return language-specific linting tips, dynamically determined."""
    return f"""
LANGUAGE-SPECIFIC LINTING FOR {language.upper()}:
- Verify all imports/includes are properly merged into existing sections
- Check that debug functions are not duplicated across files in the same namespace/package/module
- Ensure debug function calls use correct syntax for the language
- Validate that global variables and initialization code exist only in primary files
- Confirm thread/concurrency safety mechanisms are appropriate for the language
- Check that error handling follows language conventions
- Verify that performance impact is minimal when debug instrumentation is disabled
- Ensure all telemetry output follows the standard format
- Validate that memory tracking uses appropriate APIs for the language
- Check that network call instrumentation doesn't interfere with original functionality
"""
