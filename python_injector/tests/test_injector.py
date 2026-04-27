# tests/test_injector.py
from pathlib import Path
from python_injector.inject_debug_llm import add_debug_stub

def test_add_debug_stub():
    src = "print('hello')\n"
    out = add_debug_stub(src)
    assert out.startswith("# DEBUG: injected")
    assert "print('hello')" in out
