#!/usr/bin/env python3
"""Code validation and linting functionality with language detection."""

import re
import logging
import pathlib
import difflib
from typing import Optional
from generic_parser import language_for_extension
from llm.prompts import get_language_specific_lint_tips

log = logging.getLogger(__name__)

class CodeValidator:
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def validate_debug_instrumentation(self, content: str, language: str) -> bool:
        """Validate that critical debug instrumentation is present."""
        patterns = {
            "go": [
                r'debug_enter\(',
                r'debug_exit\(',
                r'\[TELEMETRY\|'
            ],
            "python": [
                r'debug_enter\(',
                r'debug_exit\(',
                r'\[TELEMETRY\|'
            ],
            "java": [
                r'debug_enter\(',
                r'debug_exit\(',
                r'\[TELEMETRY\|'
            ],
            "javascript": [
                r'debug_enter\(',
                r'debug_exit\(',
                r'\[TELEMETRY\|'
            ]
        }
        
        lang_patterns = patterns.get(language.lower(), [
            r'debug_enter',
            r'debug_exit',
            r'\[TELEMETRY\|'
        ])
        
        missing_patterns = []
        for pattern in lang_patterns:
            if not re.search(pattern, content):
                missing_patterns.append(pattern)
        
        if missing_patterns:
            log.warning(f"⚠️  Missing debug patterns in {language}: {', '.join(missing_patterns)}")
            return False
        
        return True
    
    def lint_debug_file(self, src_path: pathlib.Path, debug_path: pathlib.Path) -> bool:
        """Use the LLM to lint and fix syntax issues."""
        if not debug_path.is_file():
            log.error(f"❌  Debug file {debug_path} not found for linting")
            return False
        
        try:
            src_content = src_path.read_text(encoding="utf-8")
            debug_content = debug_path.read_text(encoding="utf-8")
            
            # Detect language
            lang_obj = language_for_extension(src_path.suffix)
            lang_name = lang_obj if isinstance(lang_obj, str) else getattr(lang_obj, "name", "unknown")
            
            # Quick validation first
            if self.validate_debug_instrumentation(debug_content, lang_name):
                log.debug(f"✅ Debug instrumentation validated for {debug_path.name}")
                return True
            
            # If validation fails, try to fix with LLM
            diff = '\n'.join(difflib.unified_diff(
                src_content.splitlines(),
                debug_content.splitlines(),
                fromfile=str(src_path),
                tofile=str(debug_path),
                lineterm=''
            ))
            
            lint_prompt = self._build_lint_prompt(src_content, debug_content, diff, lang_name)
            
            log.info(f"🔍 Linting {debug_path.name} with LLM...")
            
            # Use empty system prompt for linting - let the user prompt handle everything
            fixed_content = self.llm_client.call(lint_prompt, "")
            
            if not fixed_content or fixed_content.strip() == debug_content.strip():
                log.info(f"ℹ️  No changes needed for {debug_path.name}")
                return True
            
            # Save the fixed content
            debug_path.write_text(fixed_content, encoding="utf-8")
            log.info(f"🔧 Fixed and updated {debug_path.name}")
            
            # Validate the fixed content
            return self.validate_debug_instrumentation(fixed_content, lang_name)
            
        except Exception as e:
            log.error(f"❌ Error during linting of {debug_path.name}: {e}")
            return False
    
    def _build_lint_prompt(self, src_content: str, debug_content: str, diff: str, lang_name: str) -> str:
        """Build the linting prompt for the LLM."""
        return f"""You are a code linting assistant. Fix syntax errors and issues in the instrumented code below.

ORIGINAL SOURCE FILE ({lang_name}):

Copy code
{src_content}


INSTRUMENTED FILE WITH POTENTIAL ISSUES:
{debug_content}


CHANGES MADE (DIFF):
{diff}


REQUIREMENTS:
1. Fix any syntax errors in the instrumented code
2. Ensure debug functions are not duplicated across files in the same package/module  
3. Merge all imports into a single import block
4. Keep ALL debug instrumentation intact
5. Maintain the original code's functionality
6. Ensure proper {lang_name} syntax and conventions

LANGUAGE-SPECIFIC REQUIREMENTS:
{get_language_specific_lint_tips(lang_name)}

Return ONLY the corrected source code without any explanations or markdown formatting."""
