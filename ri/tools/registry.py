from __future__ import annotations

import json
from typing import Any, Callable


class ToolRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., str]] = {}
        self._schemas: list[dict[str, Any]] = []
        self.pending_confirmation: dict[str, Any] | None = None
        self._confirmed: set[str] = set()

    def register(self, schema: dict[str, Any], handler: Callable[..., str]) -> None:
        name = schema["function"]["name"]
        self._handlers[name] = handler
        self._schemas.append(schema)

    def get_definitions(self) -> list[dict[str, Any]]:
        return self._schemas

    def clear_confirmation(self) -> None:
        self.pending_confirmation = None

    def confirm_pending(self) -> bool:
        if not self.pending_confirmation:
            return False
        fp = self.pending_confirmation.get("fingerprint")
        if fp:
            self._confirmed.add(fp)
        self.pending_confirmation = None
        return True

    def deny_pending(self) -> None:
        self.pending_confirmation = None

    def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        if name not in self._handlers:
            return f"Error: unknown tool '{name}'."
        try:
            return self._handlers[name](**arguments)
        except TypeError as exc:
            return f"Error: invalid arguments for {name}: {exc}"
        except Exception as exc:
            return f"Error executing {name}: {exc}"


def _tool(name: str, description: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }


def build_tool_registry() -> ToolRegistry:
    from ri.tools import desktop, files, gui, shell, system

    registry = ToolRegistry()
    shell.register(registry)
    files.register(registry)
    desktop.register(registry)
    gui.register(registry)
    system.register(registry)
    return registry