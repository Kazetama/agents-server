"""
skills/network_checker.py
──────────────────────────
Tool: Network diagnostics.
Ping hosts, check open ports, and get the server's public IP.
"""
import subprocess
import socket
import urllib.request


def ping_host(host: str, count: int = 4) -> str:
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), host],
            capture_output=True, text=True, timeout=20
        )
        return result.stdout.strip() if result.returncode == 0 else f"Ping failed:\n{result.stderr.strip()}"
    except Exception as e:
        return f"Error: {e}"


def check_port(host: str, port: int) -> str:
    try:
        with socket.create_connection((host, port), timeout=5):
            return f"✅ Port {port} on {host} is OPEN."
    except (ConnectionRefusedError, socket.timeout):
        return f"🔴 Port {port} on {host} is CLOSED or unreachable."
    except Exception as e:
        return f"Error: {e}"


def get_public_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return f"Public IP: {r.read().decode()}"
    except Exception as e:
        return f"Could not fetch public IP: {e}"


TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "ping_host",
            "description": "Ping a hostname or IP address to check network connectivity and latency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "The hostname or IP to ping"},
                    "count": {"type": "integer", "description": "Number of ping packets to send (default: 4)"},
                },
                "required": ["host"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_port",
            "description": "Check if a specific TCP port is open on a given host.",
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Hostname or IP address"},
                    "port": {"type": "integer", "description": "Port number to check"},
                },
                "required": ["host", "port"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_public_ip",
            "description": "Get the public IP address of the server.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

TOOL_FUNCTION = {
    "ping_host": ping_host,
    "check_port": check_port,
    "get_public_ip": get_public_ip,
}
