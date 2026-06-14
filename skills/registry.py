"""
skills/registry.py
───────────────────
Central tool registry. Imports all skill modules and
builds AVAILABLE_TOOLS (Ollama schema list) and
TOOL_FUNCTIONS (callable dispatch map).

To add a new skill:
  1. Create skills/your_skill.py with TOOL_SCHEMA and TOOL_FUNCTION
  2. Import and add it to SKILL_MODULES below — that's it.
"""
from skills import (
    server_monitor,
    docker_manager,
    package_manager,
    log_analyzer,
    shell_executor,
    network_checker,
)

SKILL_MODULES = [
    server_monitor,
    docker_manager,
    package_manager,
    log_analyzer,
    shell_executor,
    network_checker,
]

AVAILABLE_TOOLS: list = []
TOOL_FUNCTIONS: dict  = {}

for mod in SKILL_MODULES:
    schema   = mod.TOOL_SCHEMA
    fn       = mod.TOOL_FUNCTION

    # TOOL_SCHEMA can be a single dict or a list of dicts
    if isinstance(schema, list):
        AVAILABLE_TOOLS.extend(schema)
    else:
        AVAILABLE_TOOLS.append(schema)

    # TOOL_FUNCTION can be a single callable or a name→callable dict
    if isinstance(fn, dict):
        TOOL_FUNCTIONS.update(fn)
    else:
        fn_name = schema["function"]["name"] if isinstance(schema, dict) else schema[0]["function"]["name"]
        TOOL_FUNCTIONS[fn_name] = fn
