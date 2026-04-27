# generic_parser.py
"""
Generic parser with Tree‑sitter when available, and safe fallbacks otherwise.

Exports:
  - language_for_extension(ext) -> either a tree_sitter.Language-like object or a string ('go', 'python', 'javascript')
  - parse_functions(source, language) -> list of dicts with keys:
        name, params, start, end, body_start, source
"""

import pathlib
import re
import ast
import sys

LIB_PATH = pathlib.Path(__file__).parent / "my-languages.so"

# ------------------------------------------------------
# Try to import tree_sitter. If anything goes wrong, we
# will fall back to simpler parsers below.
# ------------------------------------------------------
TS_AVAILABLE = False
TS = None
Language = None
Parser = None

try:
    from tree_sitter import Language as TS_Language, Parser as TS_Parser
    # keep references
    TS = TS_Language
    Parser = TS_Parser
    TS_AVAILABLE = True
except Exception:
    TS_AVAILABLE = False

# ------------------------------------------------------
# Helper: attempt to create/return a language object.
# May return:
#   - a tree-sitter Language object (if successful)
#   - the plain language name string (e.g. 'go') as a fallback
# The code tries several possible tree-sitter APIs and tolerates failures.
# ------------------------------------------------------
def load_language_obj(name: str):
    if not TS_AVAILABLE:
        return name

    try:
        # Common old API: Language(path, name)
        return TS(str(LIB_PATH), name)
    except TypeError:
        # Newer/other API: Language(str(LIB_PATH)) returns a Library-like object
        # which may expose a .language(name) method. Try that.
        try:
            lib = TS(str(LIB_PATH))
            # try multiple possibilities to extract language by name
            if hasattr(lib, "language"):
                try:
                    return lib.language(name)
                except Exception:
                    # some builds expose languages as attributes or mapping
                    pass
            # some bindings expose get_language
            if hasattr(lib, "get_language"):
                return lib.get_language(name)
            # fallback: return library object (parser may still accept it)
            return lib
        except Exception:
            # give up and fall back to string
            return name
    except Exception:
        # any other error — fall back to string
        return name

def language_for_extension(ext: str):
    mapping = {
        ".go": "go",
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".rs": "rust",
        ".java": "java",
        ".cs": "c_sharp",
    }
    name = mapping.get(ext.lower())
    if not name:
        raise ValueError(f"Unsupported extension {ext}")
    return load_language_obj(name)

# ------------------------------------------------------
# Fallback parsers
# ------------------------------------------------------

# --- Go regex parser (handles nested braces) ---
_GO_FUNC_RE = re.compile(
    r'''(?P<signature>func\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*(?P<results>\([^\)]*\)|[^\{]*))\s*\{''',
    re.MULTILINE,
)

def _parse_go_functions(source: str):
    functions = []
    for m in _GO_FUNC_RE.finditer(source):
        start = m.start()
        i = m.end()  # position after opening brace
        brace_depth = 1
        while i < len(source) and brace_depth > 0:
            c = source[i]
            if c == '{':
                brace_depth += 1
            elif c == '}':
                brace_depth -= 1
            i += 1
        end = i  # position after closing brace
        func_text = source[start:end]
        functions.append({
            "name": m.group("name"),
            "params": m.group("params").strip(),
            "start": start,
            "end": end,
            "body_start": m.end(),   # first char after '{' (approx)
            "source": func_text
        })
    return functions

# --- Python AST parser (uses lineno and end_lineno) ---
def _parse_python_functions(source: str):
    functions = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return functions

    # Build line start offsets for mapping lineno -> char index
    lines = source.splitlines(keepends=True)
    line_offsets = [0]
    for ln in lines:
        line_offsets.append(line_offsets[-1] + len(ln))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # ast nodes in Python 3.8+ have end_lineno; fallback if missing
            start_line = getattr(node, "lineno", None)
            end_line = getattr(node, "end_lineno", None)
            if start_line is None:
                continue
            start_idx = line_offsets[start_line - 1]
            if end_line is not None:
                end_idx = line_offsets[end_line]  # end of line after end_lineno
            else:
                # fallback: find next top-level 'def' or EOF
                # naive fallback: scan forward for a line starting with 'def ' at col 0
                end_idx = len(source)
                for i, ln in enumerate(lines[start_line:], start=start_line+1):
                    if ln.lstrip().startswith('def ') and (ln[0] != ' ' and ln[0] != '\t'):
                        end_idx = line_offsets[i-1]
                        break
            func_text = source[start_idx:end_idx]
            # try to extract params from the def line
            header = lines[start_line - 1]
            m = re.match(r'\s*def\s+(\w+)\s*\(([^)]*)\)\s*:', header)
            name = m.group(1) if m else node.name if hasattr(node, 'name') else "anonymous"
            params = m.group(2) if m else ""
            # body_start: char after the colon line; approximate as start of next line
            body_start = start_idx + len(header)
            functions.append({
                "name": name,
                "params": params.strip(),
                "start": start_idx,
                "end": end_idx,
                "body_start": body_start,
                "source": func_text
            })
    return functions

# --- JavaScript simple regex parser (basic function declarations) ---
_JS_FUNC_RE = re.compile(
    r'''(?P<signature>function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*\{)''',
    re.MULTILINE
)

def _parse_js_functions(source: str):
    functions = []
    for m in _JS_FUNC_RE.finditer(source):
        start = m.start()
        i = m.end()
        brace_depth = 1
        while i < len(source) and brace_depth > 0:
            c = source[i]
            if c == '{':
                brace_depth += 1
            elif c == '}':
                brace_depth -= 1
            i += 1
        end = i
        functions.append({
            "name": m.group("name"),
            "params": m.group("params").strip(),
            "start": start,
            "end": end,
            "body_start": m.end(),
            "source": source[start:end]
        })
    return functions

# ------------------------------------------------------
# Main parse_functions entrypoint — accepts either a
# tree-sitter Language object or a simple string name.
# ------------------------------------------------------
def parse_functions(source: str, language):
    """
    Return list of functions with fields:
        - name
        - params
        - start, end (char offsets)
        - body_start (char offset just after opening brace/colon)
        - source (full function text)
    `language` may be:
        - a tree_sitter.Language object (if TS loaded successfully), or
        - a string like 'go', 'python', 'javascript'
    """
    # If language is a string, use name directly
    lang_name = None
    if isinstance(language, str):
        lang_name = language
    else:
        # Try to derive a name from the Language-like object
        # Tree-sitter Language objects often have .name or .__str__ that includes the name
        try:
            lang_name = getattr(language, "name", None)
        except Exception:
            lang_name = None

    # If Tree-sitter is available and we have a Language object, try to use it
    if TS_AVAILABLE and not isinstance(language, str):
        try:
            parser = Parser()
            parser.set_language(language)
            tree = parser.parse(bytes(source, "utf8"))
            root = tree.root_node
            # language-specific node types for functions
            func_kinds = {
                "go": ["function_declaration", "method_declaration"],
                "python": ["function_definition"],
                "javascript": ["function_declaration", "method_definition", "arrow_function"],
                "rust": ["function_item", "impl_item"],
            }
            kinds = func_kinds.get(lang_name, [])
            functions = []

            def walk(node):
                if node.type in kinds:
                    # name
                    name_node = next((c for c in node.children if c.type == "identifier"), None)
                    name = name_node.text.decode() if name_node else "anonymous"

                    # params
                    param_node = next(
                        (c for c in node.children if c.type in ("parameter_list", "parameters", "formal_parameters")),
                        None,
                    )
                    params = param_node.text.decode() if param_node else ""

                    body_node = next(
                        (c for c in node.children if c.type in ("block", "suite", "statement_block")),
                        None,
                    )
                    if body_node:
                        body_start = body_node.start_byte + 1
                    else:
                        body_start = node.end_byte

                    functions.append({
                        "name": name,
                        "params": params,
                        "start": node.start_byte,
                        "end": node.end_byte,
                        "body_start": body_start,
                        "source": source[node.start_byte:node.end_byte],
                    })
                for child in node.children:
                    walk(child)

            walk(root)
            return functions
        except Exception:
            # Fall through to the fallback parsers
            pass

    # Fallback by language name
    if lang_name == "go" or (isinstance(language, str) and language == "go"):
        return _parse_go_functions(source)
    if lang_name == "python" or (isinstance(language, str) and language == "python"):
        return _parse_python_functions(source)
    if lang_name == "javascript" or (isinstance(language, str) and language == "javascript"):
        return _parse_js_functions(source)

    # Generic fallback: try Go-style regex (best-effort)
    return _parse_go_functions(source)
