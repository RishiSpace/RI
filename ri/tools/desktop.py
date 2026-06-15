import os
import subprocess
import webbrowser

import psutil

from ri.system_info import get_desktop_env
from ri.tools.registry import ToolRegistry, _tool


def register(registry: ToolRegistry) -> None:
    registry.register(
        _tool(
            "open_application",
            "Launch an application, file, folder, or URL. Examples: 'firefox', 'code', 'https://google.com', '~/Documents'.",
            {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "App name, binary, path, or URL"},
                },
                "required": ["target"],
            },
        ),
        _open_application,
    )

    registry.register(
        _tool(
            "open_url",
            "Open a URL in the default browser.",
            {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        ),
        _open_url,
    )

    registry.register(
        _tool(
            "lock_screen",
            "Lock the workstation screen immediately.",
            {"type": "object", "properties": {}, "required": []},
        ),
        lambda: _lock_screen(),
    )

    registry.register(
        _tool(
            "set_volume",
            "Set system volume. Level 0-100, or 'mute'/'unmute'.",
            {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "0-100 percentage, or 'mute' / 'unmute'",
                    },
                },
                "required": ["level"],
            },
        ),
        _set_volume,
    )

    registry.register(
        _tool(
            "send_notification",
            "Show a desktop notification to the user.",
            {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "message": {"type": "string"},
                },
                "required": ["title", "message"],
            },
        ),
        _send_notification,
    )

    registry.register(
        _tool(
            "list_processes",
            "List running processes sorted by CPU usage.",
            {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max processes (default 15)"},
                    "filter_name": {"type": "string", "description": "Filter by process name substring"},
                },
                "required": [],
            },
        ),
        _list_processes,
    )

    registry.register(
        _tool(
            "kill_process",
            "Terminate a process by name or PID.",
            {
                "type": "object",
                "properties": {
                    "name_or_pid": {"type": "string", "description": "Process name or numeric PID"},
                },
                "required": ["name_or_pid"],
            },
        ),
        lambda name_or_pid: _kill_process(registry, name_or_pid),
    )

    registry.register(
        _tool(
            "get_clipboard",
            "Read the current clipboard text content.",
            {"type": "object", "properties": {}, "required": []},
        ),
        lambda: _clipboard("get"),
    )

    registry.register(
        _tool(
            "set_clipboard",
            "Set clipboard text content.",
            {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        ),
        lambda text: _clipboard("set", text),
    )


def _run(cmd: str) -> str:
    try:
        r = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=30)
        out = (r.stdout or r.stderr or "").strip()
        return out or f"exit={r.returncode}"
    except Exception as exc:
        return str(exc)


def _open_application(target: str) -> str:
    target = target.strip()
    expanded = os.path.expanduser(target)

    if target.startswith(("http://", "https://")):
        webbrowser.open(target)
        return f"Opened URL: {target}"

    if os.path.exists(expanded):
        subprocess.Popen(["xdg-open", expanded], start_new_session=True)
        return f"Opened: {expanded}"

    for cmd in (
        f"gtk-launch {target}",
        f"xdg-open {target}",
        f"{target}",
        f"which {target} && {target}",
    ):
        try:
            subprocess.Popen(cmd, shell=True, start_new_session=True)
            return f"Launched: {target}"
        except Exception:
            continue
    return f"Could not launch '{target}'. Try the full binary name or path."


def _open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}"


def _lock_screen() -> str:
    de = get_desktop_env()
    commands = []

    if "gnome" in de or "unity" in de:
        commands.extend([
            "gdbus call --session --dest org.gnome.ScreenSaver --object-path /org/gnome/ScreenSaver --method org.gnome.ScreenSaver.Lock",
            "loginctl lock-session",
        ])
    elif "kde" in de or "plasma" in de:
        commands.extend([
            "qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock",
            "loginctl lock-session",
        ])
    else:
        commands.extend([
            "loginctl lock-session",
            "xdg-screensaver lock",
            "i3lock",
            "swaylock",
        ])

    for cmd in commands:
        r = _run(cmd)
        if "error" not in r.lower() and "not found" not in r.lower():
            return f"Screen locked via: {cmd.split()[0]}"
    return "Tried lock commands but none succeeded. Use execute_shell_command for your DE."


def _set_volume(level: str) -> str:
    level = str(level).strip().lower()
    de = get_desktop_env()

    if level in ("mute", "unmute"):
        pct = "0%" if level == "mute" else "50%"
        mute_flag = "1" if level == "mute" else "0"
        cmds = [
            f"pactl set-sink-mute @DEFAULT_SINK@ {mute_flag}",
            f"amixer -D pulse sset Master {pct}",
            f"wpctl set-mute @DEFAULT_AUDIO_SINK@ {mute_flag}",
        ]
    else:
        try:
            pct = max(0, min(100, int(level.replace("%", ""))))
        except ValueError:
            return "Invalid level. Use 0-100, mute, or unmute."
        cmds = [
            f"pactl set-sink-volume @DEFAULT_SINK@ {pct}%",
            f"amixer -D pulse sset Master {pct}%",
            f"wpctl set-volume @DEFAULT_AUDIO_SINK@ {pct / 100:.2f}",
        ]

    for cmd in cmds:
        r = _run(cmd)
        if "error" not in r.lower():
            return f"Volume set with: {cmd}"
    return f"Volume command failed for level={level}"


def _send_notification(title: str, message: str) -> str:
    safe_title = title.replace('"', "'")
    safe_msg = message.replace('"', "'")
    cmds = [
        f'notify-send "{safe_title}" "{safe_msg}"',
        f'gdbus call --session --dest org.freedesktop.Notifications --object-path /org/freedesktop/Notifications --method org.freedesktop.Notifications.Notify "{safe_title}" 0 "" "" "{safe_msg}" [] {{}} 5000',
    ]
    for cmd in cmds:
        r = _run(cmd)
        if "error" not in r.lower():
            return f"Notification sent: {title}"
    return "Failed to send notification."


def _list_processes(limit: int = 15, filter_name: str | None = None) -> str:
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            if filter_name and filter_name.lower() not in (info["name"] or "").lower():
                continue
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
    lines = []
    for p in procs[: max(1, limit)]:
        lines.append(
            f"pid={p['pid']} name={p['name']} cpu={p.get('cpu_percent', 0):.1f}% mem={p.get('memory_percent', 0):.1f}%"
        )
    return "\n".join(lines) or "No matching processes."


def _process_name_matches(name: str, query: str) -> bool:
    """Exact process name match only — avoids killing every substring hit."""
    n = (name or "").lower()
    q = query.lower().strip()
    if not n or not q:
        return False
    return n == q or n == f"{q}.exe"


def _find_processes(name_or_pid: str) -> list[psutil.Process]:
    if name_or_pid.isdigit():
        try:
            return [psutil.Process(int(name_or_pid))]
        except psutil.NoSuchProcess:
            return []
    matches = []
    for p in psutil.process_iter(["name", "pid"]):
        try:
            if _process_name_matches(p.info.get("name") or "", name_or_pid):
                matches.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matches


def _kill_process(registry: ToolRegistry, name_or_pid: str) -> str:
    targets = _find_processes(name_or_pid)
    if not targets:
        return f"No process found with exact name or PID '{name_or_pid}'."

    fp = f"kill-{name_or_pid}"
    if fp not in registry._confirmed:
        desc = ", ".join(f"{p.pid}:{p.name()}" for p in targets[:5])
        extra = f" (+{len(targets) - 5} more)" if len(targets) > 5 else ""
        registry.pending_confirmation = {
            "tool": "kill_process",
            "target": name_or_pid,
            "reason": f"Killing {len(targets)} process(es): {desc}{extra}",
            "fingerprint": fp,
        }
        return (
            f"BLOCKED - will kill {len(targets)} process(es) ({desc}{extra}). "
            "Ask user to confirm."
        )

    import os
    import signal

    killed = 0
    try:
        # Suppress stderr noise from dying processes (JACK, zygote, etc.)
        devnull = open(os.devnull, "w")
        old_stderr = os.dup(2)
        os.dup2(devnull.fileno(), 2)
        try:
            for p in targets:
                try:
                    p.send_signal(signal.SIGTERM)
                    killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        finally:
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            devnull.close()
    except Exception as exc:
        return f"Kill failed: {exc}"

    return f"Terminated {killed} process(es) matching '{name_or_pid}'."


def _clipboard(action: str, text: str | None = None) -> str:
    if action == "get":
        for cmd in ("xclip -selection clipboard -o", "wl-paste", "xsel --clipboard --output"):
            r = _run(cmd)
            if r and "not found" not in r.lower() and "can't open" not in r.lower():
                return r[:4000] or "(empty clipboard)"
        return "Clipboard read failed. Install xclip or wl-clipboard."

    if not text:
        return "No text provided."
    escaped = text.replace("'", "'\\''")
    for cmd in (
        f"printf '%s' '{escaped}' | xclip -selection clipboard",
        f"printf '%s' '{escaped}' | wl-copy",
    ):
        r = _run(cmd)
        if "error" not in r.lower():
            return f"Clipboard set ({len(text)} chars)."
    return "Clipboard write failed."