import os
import platform
import time

import psutil


def _distro_name() -> str:
    try:
        import distro
        return distro.name(pretty=True)
    except ImportError:
        pass
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "Unknown"


def get_system_context() -> str:
    try:
        user = os.getlogin()
    except OSError:
        user = os.environ.get("USER", "unknown")

    desktop = (
        os.environ.get("XDG_CURRENT_DESKTOP")
        or os.environ.get("DESKTOP_SESSION")
        or "Unknown"
    )
    shell = os.environ.get("SHELL", "/bin/bash")
    cwd = os.getcwd()
    mem = psutil.virtual_memory()

    return f"""System Information:
- OS: {platform.system()} {platform.release()}
- Distro: {_distro_name()}
- User: {user}
- Desktop Environment: {desktop}
- Shell: {shell}
- Working Directory: {cwd}
- CPU Cores: {psutil.cpu_count(logical=True)}
- RAM: {round(mem.total / (1024 ** 3), 1)} GB total, {mem.percent}% used
- Date/Time: {time.strftime("%Y-%m-%d %H:%M:%S")}"""


def get_desktop_env() -> str:
    return (
        os.environ.get("XDG_CURRENT_DESKTOP")
        or os.environ.get("DESKTOP_SESSION")
        or ""
    ).lower()