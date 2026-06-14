"""
skills/package_manager.py
──────────────────────────
Tool: Manage apt packages.
Supports checking for updates and installing packages.
"""
import subprocess


def _run(cmd: list, timeout: int = 60) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode != 0:
            return f"Error (exit {r.returncode}): {err or out}"
        return out or "(Done, no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error: {e}"


def check_apt_updates() -> str:
    subprocess.run(["sudo", "apt-get", "update", "-qq"], capture_output=True)
    result = subprocess.run(["apt-get", "-s", "upgrade"], capture_output=True, text=True)
    upgradable = [l for l in result.stdout.splitlines() if l.startswith("Inst")]
    count = len(upgradable)
    if count == 0:
        return "All packages are up to date."
    sample = "\n".join(upgradable[:5])
    return f"{count} package(s) can be upgraded:\n{sample}{'...' if count > 5 else ''}"


def install_package(package_name: str) -> str:
    subprocess.run(["sudo", "apt-get", "update", "-qq"], capture_output=True)
    result = _run(["sudo", "apt-get", "install", "-y", package_name], timeout=120)
    if "Error" in result:
        return result
    return f"✅ Package '{package_name}' installed successfully."


TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "check_apt_updates",
            "description": "Check how many apt packages are available for upgrade on the server.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "install_package",
            "description": "Install a package on the server using apt-get. Use this when the user asks to install software like php, nginx, nodejs, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_name": {"type": "string", "description": "The exact apt package name to install (e.g. php, nginx, nodejs)"}
                },
                "required": ["package_name"],
            },
        },
    },
]

TOOL_FUNCTION = {
    "check_apt_updates": check_apt_updates,
    "install_package": install_package,
}
