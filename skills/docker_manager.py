"""
skills/docker_manager.py
─────────────────────────
Tool: Manage Docker containers.
Supports listing, restarting, and stopping containers.
"""
import subprocess


def _run(cmd: list) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode != 0:
            return f"Error (exit {r.returncode}): {err or out}"
        return out or "(No output)"
    except FileNotFoundError:
        return "Docker is not installed or not accessible."
    except Exception as e:
        return f"Error: {e}"


def list_containers() -> str:
    result = _run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Image}}"])
    return result if result else "No running containers."


def restart_container(container_name: str) -> str:
    return _run(["docker", "restart", container_name])


def stop_container(container_name: str) -> str:
    return _run(["docker", "stop", container_name])


TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_containers",
            "description": "List all currently running Docker containers with their status and image.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restart_container",
            "description": "Restart a specific Docker container by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "container_name": {"type": "string", "description": "The name of the container to restart"}
                },
                "required": ["container_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_container",
            "description": "Stop a specific running Docker container by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "container_name": {"type": "string", "description": "The name of the container to stop"}
                },
                "required": ["container_name"],
            },
        },
    },
]

TOOL_FUNCTION = {
    "list_containers": list_containers,
    "restart_container": restart_container,
    "stop_container": stop_container,
}
