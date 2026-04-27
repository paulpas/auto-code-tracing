# DEBUG: injected by python‑injector
# utils.py
from __future__ import annotations
import pathlib
import logging
from typing import Iterable

log = logging.getLogger(__name__)

def iter_python_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    """Yield all *.py files under *root* (recursively)."""
    yield from root.rglob("*.py")

def read_file(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")

def write_file(path: pathlib.Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
