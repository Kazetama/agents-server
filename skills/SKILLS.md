# 🛠️ Skills Documentation

This directory contains all the **AI Agent Tools** (Function Calling skills) that the bot can invoke autonomously.

## Adding a New Skill

1. Create a new file `skills/your_skill.py`
2. Define your functions
3. Add `TOOL_SCHEMA` (list or single dict in Ollama format)
4. Add `TOOL_FUNCTION` (callable or `{"name": callable}` dict)
5. Import it in `skills/registry.py` under `SKILL_MODULES`

---

## Available Skills

### 🖥️ `server_monitor.py`
Monitor server hardware resource usage in real-time.

| Function | Description |
|---|---|
| `get_system_status()` | Returns CPU %, RAM usage, Disk usage, and system uptime |

---

### 🐳 `docker_manager.py`
Manage Docker containers on the server.

| Function | Parameters | Description |
|---|---|---|
| `list_containers()` | — | List all running containers with status and image |
| `restart_container(container_name)` | `container_name: str` | Restart a container by name |
| `stop_container(container_name)` | `container_name: str` | Stop a container by name |

---

### 📦 `package_manager.py`
Manage apt packages on the Ubuntu server.

| Function | Parameters | Description |
|---|---|---|
| `check_apt_updates()` | — | Check how many packages have available upgrades |
| `install_package(package_name)` | `package_name: str` | Install a package via `apt-get install` |

---

### 📋 `log_analyzer.py`
Read and analyze server log files.

| Function | Parameters | Description |
|---|---|---|
| `tail_log(log_path, lines)` | `log_path: str`, `lines: int` | Read the last N lines of any log file |

**Default log path:** `/var/log/syslog`

---

### 🖱️ `shell_executor.py`
Execute arbitrary shell commands on the server.

| Function | Parameters | Description |
|---|---|---|
| `execute_command(command)` | `command: str` | Run any bash command and return the output |

> ⚠️ **Security Note:** This tool is the most powerful. Access is restricted to `OWNER_ID` via the security middleware.

---

### 🌐 `network_checker.py`
Network diagnostics and connectivity tools.

| Function | Parameters | Description |
|---|---|---|
| `ping_host(host, count)` | `host: str`, `count: int` | Ping a host and return RTT stats |
| `check_port(host, port)` | `host: str`, `port: int` | Check if a TCP port is open |
| `get_public_ip()` | — | Get the server's current public IP address |
