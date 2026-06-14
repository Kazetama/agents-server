"""
skills/server_monitor.py
─────────────────────────
Tool: Monitor server resource usage.
Uses psutil to read CPU, RAM, and disk stats.
"""
import psutil


def get_system_status() -> str:
    cpu   = psutil.cpu_percent(interval=1)
    ram   = psutil.virtual_memory()
    disk  = psutil.disk_usage("/")
    boot  = psutil.boot_time()

    import datetime
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot)
    uptime_str = str(uptime).split(".")[0]  # strip microseconds

    return (
        f"CPU     : {cpu}%\n"
        f"RAM     : {ram.used / 1024**3:.2f} GB / {ram.total / 1024**3:.2f} GB ({ram.percent}%)\n"
        f"Disk    : {disk.used / 1024**3:.2f} GB / {disk.total / 1024**3:.2f} GB ({disk.percent}%)\n"
        f"Uptime  : {uptime_str}"
    )


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_system_status",
        "description": "Get the current server resource usage: CPU percentage, RAM usage, disk usage, and system uptime.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}

TOOL_FUNCTION = get_system_status
