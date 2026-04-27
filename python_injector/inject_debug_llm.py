# python_injector/inject_debug_llm.py
"""Zero-touch instrumentation helper."""
import pathlib, sys, logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def add_stub(src: str) -> str:
    return "# DEBUG: injected by python_injector\n" + src

def process_file(p: pathlib.Path) -> None:
    txt = p.read_text(encoding="utf-8")
    if "# DEBUG: injected" in txt:
        log.debug("Already instrumented: %s", p)
        return
    p.write_text(add_stub(txt), encoding="utf-8")
    log.info("Instrumented %s", p)

def main(root: pathlib.Path) -> int:
    for py in root.rglob("*.py"):
        process_file(py)
    return 0

if __name__ == "__main__":
    sys.exit(main(pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")))
