#!/usr/bin/env python3
"""Inject debug statements into code snippets using precise LLM calls."""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from .registry import DebugFunctionRegistry, DebugFunction, DebugStage

log = logging.getLogger(__name__)

class CodeSnippet:
    """Represents a snippet of code to be instrumented."""
    def __init__(self, content: str, start_line: int, snippet_type: str, context: str = ""):
        self.content = content
        self.start_line = start_line
        self.snippet_type = snippet_type  # 'function', 'method', 'block', 'top_level'
        self.context = context
        self.instrumented_content = ""
        self.debug_functions_used: List[str] = []

class SnippetInjector:
    """Injects debug statements into code snippets."""
    
    def __init__(self, llm_client, language: str, service_name: str):
        self.llm_client = llm_client
        self.language = language.lower()
        self.service_name = service_name
        self.registry = DebugFunctionRegistry()
        self.debug_functions = self.registry.register_language_functions(language, service_name)
    
    def parse_code_into_snippets(self, source_code: str, file_path: str) -> List[CodeSnippet]:
        """Parse source code into manageable snippets for instrumentation."""
        try:
            if self.language == 'go':
                return self._parse_go_code(source_code)
            elif self.language == 'python':
                return self._parse_python_code(source_code)
            elif self.language == 'java':
                return self._parse_java_code(source_code)
            else:
                # Generic parsing - split by meaningful chunks
                return self._parse_generic_code(source_code)
                
        except Exception as e:
            log.error(f"❌ Error parsing code into snippets: {e}")
            return []
    
    def _parse_go_code(self, source_code: str) -> List[CodeSnippet]:
        """Parse Go code into snippets."""
        snippets = []
        lines = source_code.split('\n')
        
        # Find package and imports first
        package_section = []
        import_section = []
        current_line = 0
        
        # Parse package declaration
        while current_line < len(lines):
            line = lines[current_line].strip()
            if line.startswith('package '):
                package_section.append(lines[current_line])
                current_line += 1
                break
            elif line and not line.startswith('//'):
                break
            current_line += 1
        
        # Parse imports
        in_import_block = False
        while current_line < len(lines):
            line = lines[current_line].strip()
            if line.startswith('import '):
                import_section.append(lines[current_line])
                if '(' in line:
                    in_import_block = True
                current_line += 1
            elif in_import_block:
                import_section.append(lines[current_line])
                if ')' in line:
                    in_import_block = False
                    current_line += 1
                    break
                current_line += 1
            else:
                break
        
        # Add package/import section as first snippet
        if package_section or import_section:
            header_content = '\n'.join(package_section + import_section)
            snippets.append(CodeSnippet(
                content=header_content,
                start_line=0,
                snippet_type='header',
                context='Package declaration and imports'
            ))
        
        # Parse functions
        func_pattern = r'func\s+(\w+)\s*$[^)]*$(?:\s*[^{]+)?\s*\{'
        remaining_code = '\n'.join(lines[current_line:])
        
        for match in re.finditer(func_pattern, remaining_code, re.MULTILINE):
            func_name = match.group(1)
            func_start = match.start()
            
            # Find the complete function by matching braces
            brace_count = 0
            pos = match.end() - 1  # Start at opening brace
            func_end = pos
            
            while pos < len(remaining_code):
                if remaining_code[pos] == '{':
                    brace_count += 1
                elif remaining_code[pos] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        func_end = pos + 1
                        break
                pos += 1
            
            func_content = remaining_code[func_start:func_end]
            
            # Split large functions into smaller snippets
            if len(func_content.split('\n')) > 50:
                sub_snippets = self._split_large_function(func_content, func_name)
                snippets.extend(sub_snippets)
            else:
                snippets.append(CodeSnippet(
                    content=func_content,
                    start_line=current_line + remaining_code[:func_start].count('\n'),
                    snippet_type='function',
                    context=f'Function: {func_name}'
                ))
        
        # Parse top-level code (variables, constants, types)
        top_level_patterns = [
            r'var\s+\w+',
            r'const\s+\w+',
            r'type\s+\w+',
        ]
        
        for pattern in top_level_patterns:
            for match in re.finditer(pattern, remaining_code, re.MULTILINE):
                # Extract the complete declaration
                decl_start = match.start()
                lines_before = remaining_code[:decl_start].count('\n')
                
                # Find end of declaration (next blank line or function)
                decl_lines = remaining_code[decl_start:].split('\n')
                decl_content = []
                
                for line in decl_lines:
                    decl_content.append(line)
                    if not line.strip() or line.strip().startswith('func '):
                        break
                
                if len(decl_content) > 1:  # Skip single-line declarations for now
                    snippets.append(CodeSnippet(
                        content='\n'.join(decl_content[:-1]).strip(),
                        start_line=current_line + lines_before,
                        snippet_type='declaration',
                        context='Top-level declaration'
                    ))
        
        return snippets
    
    def _split_large_function(self, func_content: str, func_name: str) -> List[CodeSnippet]:
        """Split large functions into smaller snippets."""
        # This is a simplified version - you could make it more sophisticated
        lines = func_content.split('\n')
        snippets = []
        
        # Split every 30 lines or at logical boundaries
        chunk_size = 30
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            chunk_content = '\n'.join(chunk_lines)
            
            context = f"Function: {func_name} (part {i//chunk_size + 1})"
            if i == 0:
                context += " - start"
            elif i + chunk_size >= len(lines):
                context += " - end"
            else:
                context += " - middle"
            
            snippets.append(CodeSnippet(
                content=chunk_content,
                start_line=0,  # Will be adjusted later
                snippet_type='function_part',
                context=context
            ))
        
        return snippets
    
    def _parse_python_code(self, source_code: str) -> List[CodeSnippet]:
        """Parse Python code into snippets."""
        snippets = []
        
        # Python parsing logic (similar to Go but with Python syntax)
        func_pattern = r'def\s+(\w+)\s*$[^)]*$:'
        
        for match in re.finditer(func_pattern, source_code, re.MULTILINE):
            func_name = match.group(1)
            # Extract function body using indentation
            # This is simplified - you'd want more robust Python parsing
            
            snippets.append(CodeSnippet(
                content=match.group(0),  # Simplified
                start_line=source_code[:match.start()].count('\n'),
                snippet_type='function',
                context=f'Function: {func_name}'
            ))
        
        return snippets
    
    def _parse_java_code(self, source_code: str) -> List[CodeSnippet]:
        """Parse Java code into snippets."""
        # Similar implementation for Java
        return []
    
    def _parse_generic_code(self, source_code: str) -> List[CodeSnippet]:
        """Generic code parsing."""
        # Split into chunks of reasonable size
        lines = source_code.split('\n')
        snippets = []
        chunk_size = 50
        
        for i in range(0, len(lines), chunk_size):
            chunk_lines = lines[i:i + chunk_size]
            snippets.append(CodeSnippet(
                content='\n'.join(chunk_lines),
                start_line=i,
                snippet_type='chunk',
                context=f'Code chunk {i//chunk_size + 1}'
            ))
        
        return snippets
    
    def instrument_snippet(self, snippet: CodeSnippet) -> bool:
        """Instrument a single code snippet with debug calls."""
        try:
            # Determine which debug functions should be used for this snippet
            recommended_functions = self._recommend_debug_functions(snippet)
            
            if not recommended_functions:
                log.debug(f"No debug functions recommended for {snippet.snippet_type}")
                snippet.instrumented_content = snippet.content
                return True
            
            # Build instrumentation prompt
            prompt = self._build_instrumentation_prompt(snippet, recommended_functions)
            
            log.debug(f"🔄 Instrumenting {snippet.snippet_type} snippet ({len(snippet.content)} chars)")
            
            # Get instrumented version from LLM
            instrumented = self.llm_client.call(prompt, "")
            
            if not instrumented:
                log.warning(f"⚠️  No instrumentation returned for {snippet.snippet_type}")
                snippet.instrumented_content = snippet.content
                return False
            
            # Clean and validate the instrumented code
            instrumented = self._clean_instrumented_code(instrumented)
            
            if self._validate_instrumented_snippet(snippet, instrumented):
                snippet.instrumented_content = instrumented
                snippet.debug_functions_used = [f.name for f in recommended_functions]
                log.info(f"✅ Instrumented {snippet.snippet_type} snippet")
                return True
            else:
                log.warning(f"⚠️  Instrumented code validation failed for {snippet.snippet_type}")
                snippet.instrumented_content = snippet.content
                return False
                
        except Exception as e: 
            log.error(f"❌ Error instrumenting snippet: {e}")
            snippet.instrumented_content = snippet.content
            return False
    
    def _recommend_debug_functions(self, snippet: CodeSnippet) -> List[DebugFunction]:
        """Recommend which debug functions should be used for this snippet."""
        recommended = []
        
        # Get available functions for this language
        available_functions = {f.name: f for f in self.debug_functions}
        
        if snippet.snippet_type == 'function':
            # Functions should have entry/exit debugging
            if 'debug_enter' in available_functions:
                recommended.append(available_functions['debug_enter'])
            if 'debug_exit' in available_functions:
                recommended.append(available_functions['debug_exit'])
                
            # Check if function has network calls, data processing, etc.
            if any(keyword in snippet.content.lower() for keyword in ['http', 'request', 'response', 'client']):
                if 'debug_network_call' in available_functions:
                    recommended.append(available_functions['debug_network_call'])
                    
            if any(keyword in snippet.content.lower() for keyword in ['parse', 'json', 'xml', 'data']):
                if 'debug_data_flow' in available_functions:
                    recommended.append(available_functions['debug_data_flow'])
                    
            if any(keyword in snippet.content.lower() for keyword in ['error', 'err', 'exception']):
                if 'debug_error' in available_functions:
                    recommended.append(available_functions['debug_error'])
        
        elif snippet.snippet_type == 'function_part':
            # Partial functions might need sub-task debugging
            if 'debug_sub_task' in available_functions:
                recommended.append(available_functions['debug_sub_task'])
            if 'debug_memory_check' in available_functions:
                recommended.append(available_functions['debug_memory_check'])
        
        elif snippet.snippet_type == 'header':
            # Headers don't need instrumentation usually
            pass
        
        return recommended
    
    def _build_instrumentation_prompt(self, snippet: CodeSnippet, functions: List[DebugFunction]) -> str:
        """Build prompt for instrumenting a specific snippet."""
        functions_info = ""
        for func in functions:
            functions_info += f"- {func.signature}\n"
            functions_info += f"  Usage: {func.usage_pattern}\n"
            functions_info += f"  Purpose: {func.description}\n\n"
        
        return f"""Add debug instrumentation to this {self.language} code snippet.

ORIGINAL CODE SNIPPET:
```{self.language}
{snippet.content}
SNIPPET TYPE: {snippet.snippet_type} CONTEXT: {snippet.context}

AVAILABLE DEBUG FUNCTIONS: {functions_info}

INSTRUMENTATION REQUIREMENTS:

Add appropriate debug function calls based on the snippet type and content
Preserve all original functionality - only ADD debug calls
Use the exact function signatures provided above
Place debug calls at logical points (entry/exit for functions, before/after significant operations)
Handle edge cases gracefully (null checks, error conditions)
Keep original code structure and formatting as much as possible
SPECIFIC GUIDANCE:

For functions: Add debug_enter() at start, debug_exit() at end (with defer in Go)
For network operations: Add debug_network_call() around HTTP requests
For data processing: Add debug_data_flow() for input/output data
For error handling: Add debug_error() in error conditions
For memory-intensive operations: Add debug_memory_check() at key points
CRITICAL: Return ONLY the instrumented code without explanations or markdown formatting. The code must compile and run identically to the original, just with added debug output."""

def _clean_instrumented_code(self, instrumented: str) -> str:
    """Clean up instrumented code from LLM."""
    # Remove markdown code blocks
    if instrumented.startswith('```'):
        lines = instrumented.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
        instrumented = '\n'.join(lines)
    
    return instrumented.strip()

def _validate_instrumented_snippet(self, original: CodeSnippet, instrumented: str) -> bool:
    """Validate that instrumented code is reasonable."""
    # Basic validation
    if len(instrumented) < len(original.content) - 10:
        log.warning("Instrumented code is shorter than original")
        return False
    
    # Check that debug functions are actually used
    debug_function_names = [f.name for f in self.debug_functions]
    has_debug_calls = any(func_name in instrumented for func_name in debug_function_names)
    
    if not has_debug_calls and original.snippet_type in ['function', 'function_part']:
        log.warning("No debug function calls found in instrumented code")
        return False
    
    return True

def reconstruct_file(self, snippets: List[CodeSnippet]) -> str:
    """Reconstruct complete file from instrumented snippets."""
    reconstructed_lines = []
    
    for snippet in snippets:
        if snippet.instrumented_content:
            reconstructed_lines.append(snippet.instrumented_content)
        else:
            reconstructed_lines.append(snippet.content)
    
    return '\n\n'.join(reconstructed_lines)
