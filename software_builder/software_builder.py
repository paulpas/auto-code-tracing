#!/usr/bin/env python3
"""
software_builder.py

A tiny helper that loads CrewAI-style YAML agent configurations from the
top-level ``agents/`` directory and makes them available as Python objects.

You can run it in **either** of the following ways:

* As a plain script (works from any current working directory):
      python /path/to/software_builder.py

* As a module (requires the repository root to be on PYTHONPATH, which is
  automatically true when you run it from the repo root):
      python -m software_builder

Both commands produce identical behaviour – they load every ``*.yaml`` file
under ``agents/`` and print a short demo of the loaded data.
"""

# --------------------------------------------------------------
# 1️⃣  Standard-library imports
# --------------------------------------------------------------
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any

# --------------------------------------------------------------
# 2️⃣  Make sure the repository root is on sys.path
# --------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# --------------------------------------------------------------
# 3️⃣  Logging configuration (console + file)
# --------------------------------------------------------------
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)          # create ``logs/`` if missing
LOG_FILE = LOG_DIR / "crewai.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)

log = logging.getLogger(__name__)

# --------------------------------------------------------------
# 4️⃣  Thin wrapper around a single agent's YAML data
# --------------------------------------------------------------
class AgentConfig:
    """Simple container for a parsed YAML agent configuration."""

    def __init__(self, name: str, yaml_path: Path, data: Dict[str, Any]):
        self.name = name
        self.yaml_path = yaml_path
        self.data = data

    # ----- convenience accessors -------------------------------------------------
    @property
    def role(self) -> str:
        return self.data.get("role", "")

    @property
    def goal(self) -> str:
        return self.data.get("goal", "")

    @property
    def backstory(self) -> str:
        return self.data.get("backstory", "")

    @property
    def tools(self) -> list:
        return self.data.get("tools", [])

    @property
    def llm_config(self) -> dict:
        return self.data.get("llm", {})

    # ----- representation ---------------------------------------------------------
    def __repr__(self) -> str:
        return f"<AgentConfig name={self.name!r} file={self.yaml_path.name}>"

    def as_dict(self) -> Dict[str, Any]:
        """Expose the raw dict – handy when feeding the config to CrewAI."""
        return self.data


# --------------------------------------------------------------
# 5️⃣  Core YAML-loading helpers
# --------------------------------------------------------------
def _load_yaml_file(yaml_path: Path) -> Dict[str, Any]:
    """Read a YAML file and return its content as a Python dict."""
    if not yaml_path.is_file():
        log.error("YAML file not found: %s", yaml_path)
        raise FileNotFoundError(yaml_path)

    try:
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        log.debug("Loaded %s (%d keys)", yaml_path.name, len(data))
        return data
    except yaml.YAMLError as exc:
        log.exception("Failed to parse YAML file %s", yaml_path)
        raise exc


def load_agent(name: str) -> AgentConfig:
    """Load a single agent configuration given its logical name."""
    yaml_path = REPO_ROOT / "agents" / f"{name}.yaml"
    data = _load_yaml_file(yaml_path)
    cfg = AgentConfig(name=name, yaml_path=yaml_path, data=data)
    log.info("✅ Loaded agent %s from %s", name, yaml_path.name)
    return cfg


def load_all_agents() -> Dict[str, AgentConfig]:
    """
    Scan the ``agents/`` directory, load every ``*.yaml`` file and return a
    dictionary keyed by the agent name (filename without extension).
    """
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.is_dir():
        log.error("Agents directory missing: %s", agents_dir)
        raise RuntimeError(f"Directory {agents_dir} does not exist")

    agents: Dict[str, AgentConfig] = {}
    for yaml_file in agents_dir.glob("*.yaml"):
        name = yaml_file.stem
        try:
            agents[name] = load_agent(name)
        except Exception as exc:
            log.error("Skipping %s because of error: %s", name, exc)

    log.info("✅ Loaded %d agent configuration(s)", len(agents))
    return agents


# --------------------------------------------------------------
# 6️⃣  Tiny demo that shows the data you have just loaded
# --------------------------------------------------------------
def _demo_print(agents: Dict[str, AgentConfig]) -> None:
    """Print a few interesting fields from each loaded agent."""
    log.info("=== Demo: a quick overview of every agent ===")
    for name, cfg in agents.items():
        log.info(
            "Agent %s – role: %s | goal: %s | tools: %d",
            name,
            cfg.role,
            cfg.goal,
            len(cfg.tools),
        )
        # Uncomment the next line if you want the full dict in the log:
        # log.debug("Full config for %s: %s", name, cfg.as_dict())


# --------------------------------------------------------------
# 7️⃣  Main entry-point (script or module)
# --------------------------------------------------------------
def main() -> None:
    """Entry-point used when the file is executed directly."""
    log.info("🚀 Starting software_builder")
    try:
        agents = load_all_agents()
        _demo_print(agents)
        log.info("✅ software_builder finished successfully")
    except Exception as exc:                     # catch-all so we always log the failure
        log.exception("❌ software_builder failed: %s", exc)
        sys.exit(1)


# --------------------------------------------------------------
# 8️⃣  Guard so the file can be executed *as a script* or *as a module*
# --------------------------------------------------------------
if __name__ == "__main__":
    # Running it as a **script** (python software_builder.py) works from any cwd
    # because we resolve all paths relative to __file__.
    main()
