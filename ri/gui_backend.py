"""GUI automation backends: tkinter, pynput, pyautogui, Pillow, xdotool, scrot."""

from __future__ import annotations

import os
import subprocess
import shutil
from datetime import datetime

from ri import config

# ---------------------------------------------------------------------------
# Tkinter — enables Pillow ImageGrab + pyautogui on Linux
# ---------------------------------------------------------------------------
_tk_root = None
_tk_available = False
_tk_checked = False


def _init_tk() -> bool:
    global _tk_root, _tk_available, _tk_checked
    if _tk_checked:
        return _tk_available
    _tk_checked = True
    try:
        import tkinter as tk
        _tk_root = tk.Tk()
        _tk_root.withdraw()
        _tk_root.update_idletasks()
        _tk_available = True
    except Exception as exc:
        print(f"tkinter unavailable ({exc}) — using pynput/scrot fallbacks")
        _tk_available = False
    return _tk_available


def _screen_size_xrandr() -> tuple[int, int] | None:
    if not shutil.which("xrandr"):
        return None
    try:
        r = subprocess.run(["xrandr", "--current"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            if " connected " in line and "+" in line:
                res = line.split()[3]
                if "x" in res:
                    w, h = res.split("x", 1)
                    return int(w), int(h)
    except Exception:
        pass
    return None


def screen_size() -> tuple[int, int]:
    if _init_tk() and _tk_root:
        return _tk_root.winfo_screenwidth(), _tk_root.winfo_screenheight()
    xr = _screen_size_xrandr()
    if xr:
        return xr
    try:
        pg = _pyautogui(allow_without_tk=False)
        return pg.size()
    except Exception:
        return 1920, 1080


def mouse_position() -> tuple[int, int]:
    try:
        from pynput.mouse import Controller
        pos = Controller().position
        return int(pos[0]), int(pos[1])
    except Exception as exc:
        return 0, 0 if not str(exc) else (0, 0)


# ---------------------------------------------------------------------------
# pyautogui (only when tk is available)
# ---------------------------------------------------------------------------
_pyautogui_mod = None
_pyautogui_failed = False


def _pyautogui(*, allow_without_tk: bool = False):
    global _pyautogui_mod, _pyautogui_failed
    if _pyautogui_mod is not None:
        return _pyautogui_mod
    if _pyautogui_failed:
        raise RuntimeError("pyautogui unavailable")
    if not allow_without_tk and not _init_tk():
        raise RuntimeError("pyautogui requires tkinter — install tk package")
    try:
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.04
        _pyautogui_mod = pyautogui
        return _pyautogui_mod
    except Exception as exc:
        _pyautogui_failed = True
        raise RuntimeError(f"pyautogui unavailable: {exc}") from exc


# ---------------------------------------------------------------------------
# pynput — primary input backend
# ---------------------------------------------------------------------------
def click(x: int, y: int, button: str = "left", clicks: int = 1) -> str:
    try:
        from pynput.mouse import Button, Controller
        btn_map = {"left": Button.left, "right": Button.right, "middle": Button.middle}
        mouse = Controller()
        mouse.position = (x, y)
        b = btn_map.get(button, Button.left)
        for _ in range(max(1, clicks)):
            mouse.click(b, 1)
        return f"Clicked {button} at ({x}, {y}) [pynput]"
    except Exception as exc:
        try:
            pg = _pyautogui()
            pg.click(x=x, y=y, button=button, clicks=clicks or 1)
            return f"Clicked {button} at ({x}, {y}) [pyautogui]"
        except Exception:
            return f"Click failed: {exc}"


def move_mouse(x: int, y: int) -> str:
    try:
        from pynput.mouse import Controller
        Controller().position = (x, y)
        return f"Moved mouse to ({x}, {y})"
    except Exception as exc:
        try:
            _pyautogui().moveTo(x, y, duration=0.15)
            return f"Moved mouse to ({x}, {y}) [pyautogui]"
        except Exception:
            return f"Move failed: {exc}"


def type_text(text: str, interval: float = 0.02) -> str:
    try:
        from pynput.keyboard import Controller
        import time
        kb = Controller()
        for ch in text:
            kb.type(ch)
            if interval:
                time.sleep(interval)
        return f"Typed {len(text)} characters [pynput]"
    except Exception as exc:
        try:
            _pyautogui().write(text, interval=interval)
            return f"Typed {len(text)} characters [pyautogui]"
        except Exception:
            return f"Type failed: {exc}"


def hotkey(keys: list[str]) -> str:
    normalized = [_normalize_key(k) for k in keys]
    try:
        from pynput.keyboard import Controller, Key
        kb = Controller()
        key_objs = [_to_pynput_key(k, Key) for k in normalized]
        for k in key_objs:
            kb.press(k)
        for k in reversed(key_objs):
            kb.release(k)
        return f"Pressed hotkey: {'+'.join(keys)} [pynput]"
    except Exception as exc:
        try:
            _pyautogui().hotkey(*normalized)
            return f"Pressed hotkey: {'+'.join(keys)} [pyautogui]"
        except Exception:
            return f"Hotkey failed: {exc}"


def scroll(clicks: int, x: int | None = None, y: int | None = None) -> str:
    try:
        from pynput.mouse import Controller
        mouse = Controller()
        if x is not None and y is not None:
            mouse.position = (x, y)
        mouse.scroll(0, clicks)
        where = f" at ({x}, {y})" if x is not None else ""
        return f"Scrolled {clicks}{where} [pynput]"
    except Exception as exc:
        try:
            pg = _pyautogui()
            if x is not None and y is not None:
                pg.scroll(clicks, x=x, y=y)
            else:
                pg.scroll(clicks)
            return f"Scrolled {clicks} [pyautogui]"
        except Exception:
            return f"Scroll failed: {exc}"


def _normalize_key(key: str) -> str:
    aliases = {
        "control": "ctrl", "ctl": "ctrl", "option": "alt",
        "super": "win", "meta": "win", "command": "win", "cmd": "win",
        "escape": "esc", "return": "enter",
    }
    return aliases.get(key.strip().lower(), key.strip().lower())


def _to_pynput_key(key: str, Key):
    special = {
        "ctrl": Key.ctrl, "alt": Key.alt, "shift": Key.shift,
        "win": Key.cmd, "enter": Key.enter, "esc": Key.esc,
        "tab": Key.tab, "space": Key.space, "backspace": Key.backspace,
        "delete": Key.delete, "up": Key.up, "down": Key.down,
        "left": Key.left, "right": Key.right, "home": Key.home,
        "end": Key.end, "pageup": Key.page_up, "pagedown": Key.page_down,
        **{f"f{i}": getattr(Key, f"f{i}") for i in range(1, 13)},
    }
    if key in special:
        return special[key]
    if len(key) == 1:
        return key
    raise ValueError(f"Unknown key: {key}")


# ---------------------------------------------------------------------------
# Screenshots
# ---------------------------------------------------------------------------
def take_screenshot(region: list[int] | None = None) -> str:
    os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(config.SCREENSHOT_DIR, f"screenshot_{ts}.png")

    pil_bbox = None
    pg_region = None
    scrot_region = None
    if region and len(region) == 4:
        x, y, w, h = region
        pil_bbox = (x, y, x + w, y + h)
        pg_region = (x, y, w, h)
        scrot_region = f"{x},{y},{w},{h}"

    # scrot — works without tk
    if shutil.which("scrot"):
        try:
            cmd = ["scrot", "-a", scrot_region, path] if scrot_region else ["scrot", path]
            subprocess.run(cmd, check=True, timeout=10)
            return f"Screenshot saved: {path} [scrot]"
        except Exception:
            pass

    # Pillow + tk
    if _init_tk():
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(bbox=pil_bbox)
            img.save(path)
            return f"Screenshot saved: {path} ({img.size[0]}x{img.size[1]}) [Pillow]"
        except Exception:
            pass

    # pyautogui + tk
    try:
        pg = _pyautogui()
        img = pg.screenshot(path, region=pg_region) if pg_region else pg.screenshot(path)
        return f"Screenshot saved: {path} ({img.size[0]}x{img.size[1]}) [pyautogui]"
    except Exception:
        pass

    if shutil.which("gnome-screenshot"):
        try:
            subprocess.run(["gnome-screenshot", "-f", path], check=True, timeout=10)
            return f"Screenshot saved: {path} [gnome-screenshot]"
        except Exception:
            pass

    return "Screenshot failed. Install scrot, or tk+Pillow, or gnome-screenshot."


# ---------------------------------------------------------------------------
# xdotool — window management
# ---------------------------------------------------------------------------
def _xdotool(*args: str) -> str:
    if not shutil.which("xdotool"):
        return ""
    try:
        r = subprocess.run(["xdotool", *args], text=True, capture_output=True, timeout=8)
        return (r.stdout or r.stderr or "").strip()
    except Exception:
        return ""


def active_window_title() -> str:
    for args in (["getactivewindow", "getwindowname"], ["getwindowfocus", "getwindowname"]):
        title = _xdotool(*args)
        if title:
            return title
    return ""


def list_windows() -> str:
    out = _xdotool("search", "--onlyvisible", "--name", ".*")
    if not out:
        return "No windows found. Install xdotool."
    lines = []
    for wid in out.splitlines()[:30]:
        name = _xdotool("getwindowname", wid) or "(untitled)"
        lines.append(f"id={wid} title={name}")
    return "\n".join(lines)


def focus_window(title_contains: str) -> str:
    out = _xdotool("search", "--name", title_contains)
    if not out:
        return f"No window matching '{title_contains}'."
    wid = out.splitlines()[0]
    _xdotool("windowactivate", wid)
    name = _xdotool("getwindowname", wid)
    return f"Focused window id={wid} title={name}"


def resize_window(title_contains: str, width: int, height: int) -> str:
    out = _xdotool("search", "--name", title_contains)
    if not out:
        return f"No window matching '{title_contains}'."
    wid = out.splitlines()[0]
    _xdotool("windowsize", wid, str(width), str(height))
    return f"Resized window {wid} to {width}x{height}"


_init_tk()