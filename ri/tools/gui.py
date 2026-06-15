from ri import gui_backend as gui
from ri.tools.registry import ToolRegistry, _tool


def register(registry: ToolRegistry) -> None:
    registry.register(
        _tool(
            "gui_click",
            "Click at screen coordinates (x, y). Use get_screen_size or take_screenshot first to aim.",
            {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "button": {"type": "string", "description": "left, right, or middle"},
                    "clicks": {"type": "integer", "description": "Number of clicks (default 1)"},
                },
                "required": ["x", "y"],
            },
        ),
        lambda x, y, button="left", clicks=1: gui.click(x, y, button, clicks),
    )

    registry.register(
        _tool(
            "gui_type",
            "Type text at the current keyboard focus.",
            {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "interval": {"type": "number", "description": "Seconds between keystrokes"},
                },
                "required": ["text"],
            },
        ),
        lambda text, interval=0.02: gui.type_text(text, interval),
    )

    registry.register(
        _tool(
            "gui_hotkey",
            "Press a keyboard shortcut. Keys: ['ctrl','c'], ['alt','f4'], ['ctrl','shift','t'], etc.",
            {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["keys"],
            },
        ),
        lambda keys: gui.hotkey(keys),
    )

    registry.register(
        _tool(
            "gui_move_mouse",
            "Move mouse to (x, y) without clicking.",
            {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["x", "y"],
            },
        ),
        lambda x, y, duration=0.2: gui.move_mouse(x, y),
    )

    registry.register(
        _tool(
            "gui_scroll",
            "Scroll the mouse wheel. Positive=up, negative=down. Optional x,y to scroll at a location.",
            {
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "description": "Scroll amount (e.g. 3 or -3)"},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                },
                "required": ["clicks"],
            },
        ),
        lambda clicks, x=None, y=None: gui.scroll(clicks, x, y),
    )

    registry.register(
        _tool(
            "take_screenshot",
            "Capture the screen to ~/Pictures/RI-Screenshots/. Optional region [x, y, width, height].",
            {
                "type": "object",
                "properties": {
                    "region": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
                "required": [],
            },
        ),
        gui.take_screenshot,
    )

    registry.register(
        _tool(
            "get_screen_size",
            "Get display resolution and current mouse position.",
            {"type": "object", "properties": {}, "required": []},
        ),
        _screen_info,
    )

    registry.register(
        _tool(
            "get_active_window",
            "Get the title of the currently focused window.",
            {"type": "object", "properties": {}, "required": []},
        ),
        _active_window,
    )

    registry.register(
        _tool(
            "list_windows",
            "List visible windows with IDs and titles. Use focus_window to switch.",
            {"type": "object", "properties": {}, "required": []},
        ),
        lambda: gui.list_windows(),
    )

    registry.register(
        _tool(
            "focus_window",
            "Focus/raise a window whose title contains the given text.",
            {
                "type": "object",
                "properties": {
                    "title_contains": {"type": "string", "description": "Substring of window title"},
                },
                "required": ["title_contains"],
            },
        ),
        lambda title_contains: gui.focus_window(title_contains),
    )

    registry.register(
        _tool(
            "resize_window",
            "Resize a window whose title contains the given text.",
            {
                "type": "object",
                "properties": {
                    "title_contains": {"type": "string"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                },
                "required": ["title_contains", "width", "height"],
            },
        ),
        lambda title_contains, width, height: gui.resize_window(title_contains, width, height),
    )


def _screen_info() -> str:
    w, h = gui.screen_size()
    x, y = gui.mouse_position()
    return f"screen={w}x{h} mouse=({x},{y})"


def _active_window() -> str:
    title = gui.active_window_title()
    return f"Active window: {title}" if title else "Could not determine active window. Install xdotool."