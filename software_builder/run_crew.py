#!/usr/bin/env python3
"""
run_crew.py

A tiny, self‑contained example that shows how to turn the YAML files
loaded by software_builder.py into real CrewAI agents and execute a crew.

How to run:

    # From the repository root (the folder that contains software_builder.py)
    python run_crew.py

All output goes to stdout and also to logs/crewai.log (the same log file
used by the loader).
"""

# -------------------------------------------------
# 1️⃣  Imports
# -------------------------------------------------
import logging
import sys
from pathlib import Path

# Import the loader we just built
from software_builder import load_all_agents, AgentConfig

# -------------------------------------------------
# 2️⃣  (Optional) set up a *second* logger for this script.
# -------------------------------------------------
log = logging.getLogger(__name__)

# -------------------------------------------------
# 3️⃣  Helper: turn an AgentConfig → a CrewAI Agent
# -------------------------------------------------
def config_to_crewai_agent(cfg: AgentConfig):
    """
    Convert an AgentConfig (our thin wrapper) into a real CrewAI Agent.
    Handles the fact that the tools defined in the YAML may miss the
    mandatory ``description`` field required by CrewAI’s pydantic model.
    """
    try:
        from crewai import Agent
        from crewai.tools import Tool  # Base class – all custom tools inherit from it
    except Exception as exc:                     # pragma: no cover
        log.error("CrewAI import failed – %s", exc)
        sys.exit(1)

    # -----------------------------------------------------------------
    # 1️⃣  Build proper Tool objects from the raw dicts in the YAML.
    # -----------------------------------------------------------------
    def dict_to_tool(d: dict) -> Tool:
        """
        Convert a raw dict from the YAML into a CrewAI Tool instance.
        If the dict already contains a ``description`` we keep it,
        otherwise we inject a generic placeholder.
        """
        # The name of the tool class is stored under the key ``class``.
        # CrewAI expects the class *object*, not the string.
        tool_cls = d.get("class")
        if isinstance(tool_cls, str):
            # Resolve the class name to the actual class object.
            # We import only the known built‑in tools; any custom tool must be
            # importable from the path given in ``module``.
            try:
                # Built‑in CrewAI tools
                if tool_cls == "GoogleSearchTool":
                    from crewai.tools import GoogleSearchTool
                    tool_cls = GoogleSearchTool
                elif tool_cls == "PythonREPLTool":
                    from crewai.tools import PythonREPLTool
                    tool_cls = PythonREPLTool
                elif tool_cls == "BashTool":
                    from crewai.tools import BashTool
                    tool_cls = BashTool
                else:
                    # Fallback: try to import a custom class by full dotted path
                    module_path, class_name = tool_cls.rsplit(".", 1)
                    mod = __import__(module_path, fromlist=[class_name])
                    tool_cls = getattr(mod, class_name)
            except Exception as exc:               # pragma: no cover
                log.warning("Unable to resolve tool class %s – using generic Tool", d.get("class"))
                from crewai.tools import Tool
                tool_cls = Tool

        # Ensure required fields exist – description is mandatory.
        # If the YAML omitted it we add a generic placeholder.
        description = d.get("description", f"Tool {d.get('name', 'unknown')}")
        # Build the concrete tool instance.
        return tool_cls(
            name=d.get("name", "unnamed_tool"),
            description=description,
            # ``config`` may hold any extra kwargs the tool expects.
            **d.get("config", {})
        )

    # -----------------------------------------------------------------
    # 2️⃣  Build the Agent, converting the raw ``tools`` list.
    # -----------------------------------------------------------------
    llm_cfg = cfg.llm_config or {}
    tools_objects = [dict_to_tool(t) for t in cfg.tools] if cfg.tools else []

    agent = Agent(
        role=cfg.role,
        goal=cfg.goal,
        backstory=cfg.backstory,
        tools=tools_objects,
        llm=llm_cfg,
    )
    return agent

# -------------------------------------------------
# 4️⃣  Main workflow
# -------------------------------------------------
def main() -> None:
    log.info("🚀 Starting run_crew.py – loading agent configs")
    # 1️⃣ Load every YAML file as AgentConfig objects
    configs = load_all_agents()                     # type: Dict[str, AgentConfig]

    # 2️⃣ Convert each config into a real CrewAI Agent instance
    crew_agents = [config_to_crewai_agent(cfg) for cfg in configs.values()]

    # 3️⃣ Build the Crew
    try:
        from crewai import Crew
    except Exception as exc:
        log.error("Could not import CrewAI – is it installed? %s", exc)
        sys.exit(1)

    crew = Crew(
        agents=crew_agents,
        # Optional: give the crew a name / description – helps with logging
        # name="MyDemoCrew",
        # description="A quick demo crew built from YAML configs",
    )
    log.info("✅ Crew built with %d agents – kicking off", len(crew_agents))

    # 4️⃣ Run the crew.  The actual method name depends on the CrewAI version:
    #    * crew.kickoff()  (most recent versions)
    #    * crew.run()      (older versions)
    # We'll try both, falling back if one raises AttributeError.
    try:
        result = crew.kickoff()
    except AttributeError:
        # Older API
        result = crew.run()

    log.info("🏁 Crew finished – result type: %s", type(result))
    print("\n===== CREW RESULT =====")
    print(result)
    print("=======================\n")


# -------------------------------------------------
# 5️⃣  Guard – only run when executed as a script
# -------------------------------------------------
if __name__ == "__main__":
    # The loader already configured a root logger that writes to logs/crewai.log.
    # Here we just make sure our own logger propagates to the same file.
    logging.basicConfig(level=logging.INFO)   # INFO → stdout, DEBUG → file only
    main()
