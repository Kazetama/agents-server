"""
skills/shell_executor.py
─────────────────────────
Tool: Execute arbitrary shell commands.
The most powerful (and flexible) tool in the agent's arsenal.
Owner-only access enforced upstream by security middleware.
"""
import subprocess


def execute_command(command: str) -> str:
    """Run any shell command and return its output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 0:
            return stdout if stdout else "(Command completed, no output)"
        else:
            return f"Exit code {result.returncode}:\n{stderr or stdout}"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_command",
        "description": (
            "Execute any shell/bash command on the Linux server and return the output. "
            "Use this for: checking software versions (php -v, node -v, python3 --version), "
            "checking service status (systemctl status nginx), disk operations, or any other "
            "command not covered by a specialized tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The exact shell command to execute"},
            },
            "required": ["command"],
        },
    },
}

TOOL_FUNCTION = execute_command
