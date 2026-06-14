"""
skills/log_analyzer.py
───────────────────────
Tool: Read and analyze server logs.
Supports syslog and custom application log file paths.
"""
import subprocess
from pathlib import Path


def tail_log(log_path: str = "/var/log/syslog", lines: int = 20) -> str:
    path = Path(log_path)
    if not path.exists():
        return f"Log file not found: {log_path}"
    try:
        result = subprocess.run(
            ["tail", "-n", str(lines), str(path)],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or "(Log file is empty)"
    except Exception as e:
        return f"Error reading log: {e}"


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "tail_log",
        "description": "Read the last N lines of a log file. Defaults to /var/log/syslog. Useful for debugging system errors, app crashes, or deployment failures.",
        "parameters": {
            "type": "object",
            "properties": {
                "log_path": {"type": "string", "description": "Absolute path to the log file (default: /var/log/syslog)"},
                "lines": {"type": "integer", "description": "Number of lines to read from the end (default: 20)"},
            },
            "required": [],
        },
    },
}

TOOL_FUNCTION = tail_log
