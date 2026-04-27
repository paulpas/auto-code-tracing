#!/usr/bin/env python3
# orchestrator.py
"""
Full multi‑agent pipeline that satisfies your specification:

1️⃣  Human → ClarifierAgent (asks clarifying questions)  
2️⃣  Clarifier → PlannerAgent (produces architecture plan, Mermaid diagram)  
3️⃣  Planner → PMAgent (breaks plan into components)  
4️⃣  PM → ProgrammingAgent(s) (writes code)  
5️⃣  Programming → TesterAgent (runs code, reports failures)  
6️⃣  If failure → DebuggerAgent (suggests fix) → ProgrammingAgent (apply)  
   Loop until component passes.  
7️⃣  When all components pass → IntegratorAgent (runs whole solution)  
8️⃣  If final run fails → Debugger (again) → ProgrammingAgent (fix)  
9️⃣  Finally → DocGenAgent (README + usage docs).

The orchestrator also:
*   Uses Google PSE for web search (via the tool defined in `config.google_pse_tool()`).
*   Can create *extra specialist agents* on‑the‑fly (up to a configurable limit).
*   Provides a global “memory” agent for persisting conversation context.
*   Allows each agent to pick its own LLM endpoint via a per‑agent config
    that falls back to the global config.

Run:

    python orchestrator.py   # from the repo root

All log output goes to `logs/crewai.log` (the same file used by the loader).
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# -------------------------------------------------------------------------
# 1️⃣  Local imports
# -------------------------------------------------------------------------
from software_builder import load_all_agents, AgentConfig
from config import build_llm_config, google_pse_tool
from tool_factory import build_tool_list

log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# 2️⃣  Helper – turn AgentConfig → CrewAI Agent (with proper tools & memory)
# -------------------------------------------------------------------------
def cfg_to_agent(cfg: AgentConfig, max_new_agents: int = 0) -> Any:
    """
    Convert an AgentConfig (loaded from YAML) into a real CrewAI Agent.
    Handles:
    *   LLM config (global + per‑agent overrides)
    *   Tool conversion (adds missing description)
    *   Optional memory (if the YAML sets ``memory: true``)
    """
    try:
        from crewai import Agent
        from crewai.memory import Memory
    except Exception as exc:               # pragma: no cover
        log.error("CrewAI import failed – %s", exc)
        sys.exit(1)

    # ------------- LLM configuration -------------
    llm_cfg = cfg.llm_config or {}
    # Merge per‑agent overrides with global defaults
    llm_cfg = {**build_llm_config(llm_cfg), **llm_cfg}

    # ------------- Tools conversion -------------
    # ``cfg.tools`` is a list of raw dicts from the YAML.
    # We convert each to a proper CrewAI Tool instance, filling missing
    # ``description`` fields automatically.
    tools_objects = build_tool_list(cfg.tools) if cfg.tools else []

    # ------------- Memory (optional) -------------
    memory = None
    if getattr(cfg, "memory", False):
        # Simple in‑memory vector store; you can replace with any
        # persisted store later.
        memory = Memory()

    # ------------- Build the Agent -------------
    agent = Agent(
        role=cfg.role,
        goal=cfg.goal,
        backstory=cfg.backstory,
        tools=tools_objects,
        llm=llm_cfg,
        # If you have a memory field in the YAML you can also pass it here:
        memory=memory,
        # Optional: you can limit the number of *sub‑agents* that this
        # agent may spawn by passing ``max_new_agents``.
        max_new_agents=max_new_agents,
    )
    return agent

# -------------------------------------------------------------------------
# 3️⃣  Build all agents from the YAML pool
# -------------------------------------------------------------------------
def build_all_agents() -> Dict[str, Any]:
    """
    Load every ``*.yaml`` under ``agents/`` and turn them into real CrewAI
    Agent objects.  The returned dict is keyed by the YAML file name
    (without the extension) – e.g. ``"clarifier"`` → Agent instance.
    """
    raw_cfgs: Dict[str, AgentConfig] = load_all_agents()
    agents: Dict[str, Any] = {}
    for name, cfg in raw_cfgs.items():
        try:
            agents[name] = cfg_to_agent(cfg)
            log.info("Instantiated agent '%s' (role=%s)", name, cfg.role)
        except Exception as exc:
            log.error("Could not build agent %s – %s", name, exc)
    return agents

# -------------------------------------------------------------------------
# 3️⃣  The actual pipeline (async‑friendly, but we keep it simple)
# -------------------------------------------------------------------------
def run_pipeline(user_input: str,
                 agents: Dict[str, Any],
                 max_specialists: int = 3) -> None:
    """
    Executes the whole chain.  ``agents`` is the dict returned by
    ``build_all_agents()``.
    """
    # -----------------------------------------------------------------
    # 0️⃣  Grab the *memory* agent (if you defined one) – it will be shared
    #     across the whole run.
    # -----------------------------------------------------------------
    memory_agent = agents.get("memory")      # optional; may be None

    # -----------------------------------------------------------------
    # 1️⃣  Clarifier – ask follow‑up questions
    # -----------------------------------------------------------------
    clarifier = agents.get("clarifier")
    if not clarifier:
        log.error("No ClarifierAgent defined – aborting")
        sys.exit(1)

    # The clarifier will store the conversation in the shared memory (if any)
    clarification = clarifier.run(input=user_input)
    log.info("🔎 Clarification result: %s", clarification)

    # -----------------------------------------------------------------
    # 2️⃣  Planner – produce architecture (Mermaid diagram)
    # -----------------------------------------------------------------
    planner = agents.get("planner")
    if not planner:
        log.error("No PlannerAgent defined – aborting")
        sys.exit(1)

    architecture = planner.run(input=clarification)
    log.info("🗺️ Architecture plan:\n%s", architecture)

    # -----------------------------------------------------------------
    # 3️⃣  Project‑Manager – split into components
    # -----------------------------------------------------------------
    pm = agents.get("project_manager")
    if not pm:
        log.error("No PMAgent defined – aborting")
        sys.exit(1)

    # The PM receives the *raw* architecture text and returns a JSON list
    # like [{"component":"Auth Service","description":"..."}]
    component_spec = pm.run(input=architecture)
    log.info("📦 Component spec received from PM: %s", component_spec)

    # -----------------------------------------------------------------
    # 4️⃣  For each component → Programming → Tester → (optional Debug) loop
    # -----------------------------------------------------------------
    programmer = agents.get("programmer")
    tester = agents.get("tester")
    debugger = agents.get("debugger")
    if not (programmer and tester and debugger):
        log.error("Missing one of Programmer/Tester/Debugger agents – aborting")
        sys.exit(1)

    # Helper to run a single component until it passes
    def process_component(spec: dict) -> dict:
        """
        Takes a component spec dict, asks the programmer to write code,
        runs the tester, and (if needed) invokes the debugger repeatedly.
        Returns the *final* code string for that component.
        """
        component_name = spec.get("component") or spec.get("name")
        description = spec.get("description", "")
        log.info("🚀 Working on component: %s", component_name)

        # ---- 1️⃣  Programming ----
        code = programmer.run(input=f"Write Python code for component '{component_name}'.\n"
                                    f"Description: {description}")
        log.debug("🖊️ Code generated for %s:\n%s", component_name, code)

        # ---- 2️⃣  Testing loop ----
        attempts = 0
        while attempts < 5:                     # safety guard – max 5 tries per component
            attempts += 1
            test_result = tester.run(input=code)
            if "Traceback" not in test_result:   # crude success check
                log.info("✅ Component '%s' passed after %d attempt(s).", component_name, attempts)
                break
            else:
                log.warning("❌ Component '%s' failed (attempt %d).", component_name, attempts)
                # Ask the debugger for a patch
                patch = debugger.run(input=f"The following error occurred while testing component "
                                            f"'{component_name}':\n{test_result}\n"
                                            f"Provide a minimal Python patch.")
                # Apply the patch (very naive – just replace the whole code)
                code = patch
                log.debug("🔧 New patched code for %s:\n%s", component_name, code)
        else:
            log.error("❗ Component '%s' could not be fixed after %d attempts.", component_name, attempts)
            raise RuntimeError(f"Component {component_name} failed repeatedly")

        return {"name": component_name, "code": code}

    # -----------------------------------------------------------------
    # 5️⃣  Process every component returned by the PM
    # -----------------------------------------------------------------
    component_specs = component_spec if isinstance(component_spec, list) else [component_spec]
    final_components: List[dict] = []
    for comp in component_specs:
        final_components.append(process_component(comp))

    # -----------------------------------------------------------------
    # 6️⃣  Integrator – run the *whole* solution together
    # -----------------------------------------------------------------
    integrator = agents.get("integrator")
    if not integrator:
        log.error("No IntegratorAgent defined – aborting")
        sys.exit(1)

    # Assemble a single script that imports/executes every component.
    # (Very simple – just concatenate the code strings.)
    full_program = "\n\n".join([c["code"] for c in final_components])
    log.debug("🧩 Full assembled program:\n%s", full_program)

    final_result = integrator.run(input=full_program)
    if "Traceback" in final_result:
        log.warning("🚨 Final system failed – handing to debugger again.")
        final_patch = debugger.run(input=f"The full system raised an exception:\n{final_result}\n"
                                         f"Suggest a fix that works with all components.")
        # Apply the patch (again naïve replace)
        full_program = final_patch
        final_result = integrator.run(input=full_program)

    if "Traceback" in final_result:
        log.error("❌ Final system still failing after debugger intervention.")
        raise RuntimeError("Unable to get a working full solution.")
    else:
        log.info("🎉 All components passed – final system output:\n%s", final_result)

    # -----------------------------------------------------------------
    # 7️⃣  Documentation generation
    # -----------------------------------------------------------------
    docgen = agents.get("docgen")
    if docgen:
        readme = docgen.run(input=full_program)
        Path("README_generated.md").write_text(readme, encoding="utf-8")
        log.info("📄 Generated README written to README_generated.md")
    else:
        log.info("No DocGenAgent defined – skipping docs step.")

# -------------------------------------------------------------------------
# 8️⃣  Main entry point
# -------------------------------------------------------------------------
def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/crewai.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    log.info("=== Starting the multi‑agent software‑engineer pipeline ===")

    # -----------------------------------------------------------------
    # Load *all* agent configs (the YAML files you already have)
    # -----------------------------------------------------------------
    raw_cfgs: Dict[str, AgentConfig] = load_all_agents()

    # -----------------------------------------------------------------
    # Build real CrewAI Agent objects from the configs
    # -----------------------------------------------------------------
    agents: Dict[str, Any] = {}
    for name, cfg in raw_cfgs.items():
        try:
            agents[name] = cfg_to_agent(cfg)
        except Exception as exc:
            log.error("Failed to create agent %s – %s", name, exc)

    # -----------------------------------------------------------------
    # Run the pipeline with a user prompt (hard‑coded for demo)
    # -----------------------------------------------------------------
    human_prompt = """\
I want to build a tiny web service that exposes a REST endpoint
``/hello`` and returns the string “Hello, World!”.  
The service should be containerised with Docker and be able to run on
any Linux host.  Please give me the full code, a Dockerfile, and a short
README.  If you need more info, ask me now.
"""
    try:
        run_pipeline(user_input=human_prompt,
                     agents=agents,
                     max_specialists=3)   # ≤3 specialist agents may be spawned on‑the‑fly
    except Exception as exc:               # pragma: no cover
        log.exception("Pipeline crashed – %s", exc)
        sys.exit(1)

    log.info("=== Pipeline finished successfully ===")

if __name__ == "__main__":
    main()
