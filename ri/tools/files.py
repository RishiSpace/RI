import glob
import os
import shutil

from ri.safety import assess_file_write, assess_shell_command
from ri.tools.registry import ToolRegistry, _tool

MAX_READ_BYTES = 64_000


def register(registry: ToolRegistry) -> None:
    registry.register(
        _tool(
            "read_file",
            "Read a text file. Use for inspecting configs, logs, documents.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_lines": {"type": "integer", "description": "Max lines to return (default 200)"},
                },
                "required": ["path"],
            },
        ),
        _read_file,
    )

    registry.register(
        _tool(
            "write_file",
            "Write or overwrite a text file.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "append": {"type": "boolean", "description": "Append instead of overwrite"},
                },
                "required": ["path", "content"],
            },
        ),
        lambda path, content, append=False: _write_file(registry, path, content, append),
    )

    registry.register(
        _tool(
            "list_directory",
            "List files and folders in a directory.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: cwd)"},
                    "pattern": {"type": "string", "description": "Optional glob pattern e.g. *.py"},
                },
                "required": [],
            },
        ),
        _list_directory,
    )

    registry.register(
        _tool(
            "move_path",
            "Move or rename a file or directory.",
            {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "destination": {"type": "string"},
                },
                "required": ["source", "destination"],
            },
        ),
        _move_path,
    )

    registry.register(
        _tool(
            "delete_path",
            "Delete a file or empty directory. Refuses recursive directory deletion.",
            {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        ),
        lambda path: _delete_path(registry, path),
    )


def _read_file(path: str, max_lines: int = 200) -> str:
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        return f"Not a file: {expanded}"
    try:
        with open(expanded, encoding="utf-8", errors="replace") as f:
            lines = []
            size = 0
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"... [{max_lines} line limit reached]")
                    break
                size += len(line.encode("utf-8", errors="replace"))
                if size > MAX_READ_BYTES:
                    lines.append("... [size limit reached]")
                    break
                lines.append(line.rstrip("\n"))
        return "\n".join(lines) or "(empty file)"
    except Exception as exc:
        return f"Read failed: {exc}"


def _write_file(registry: ToolRegistry, path: str, content: str, append: bool) -> str:
    expanded = os.path.expanduser(path)
    safe, reason = assess_file_write(expanded)
    if not safe:
        registry.pending_confirmation = {
            "tool": "write_file",
            "path": expanded,
            "reason": reason,
            "fingerprint": expanded,
        }
        return f"BLOCKED - confirmation required: {reason}"

    try:
        os.makedirs(os.path.dirname(expanded) or ".", exist_ok=True)
        mode = "a" if append else "w"
        with open(expanded, mode, encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {expanded}"
    except Exception as exc:
        return f"Write failed: {exc}"


def _list_directory(path: str = ".", pattern: str | None = None) -> str:
    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        return f"Not a directory: {expanded}"
    try:
        if pattern:
            entries = sorted(glob.glob(os.path.join(expanded, pattern)))
        else:
            entries = sorted(os.listdir(expanded))
        if not entries:
            return "(empty)"
        lines = []
        for name in entries[:200]:
            full = name if pattern else os.path.join(expanded, name)
            if not pattern:
                name = os.path.basename(full)
            kind = "dir" if os.path.isdir(full) else "file"
            lines.append(f"[{kind}] {name}")
        if len(entries) > 200:
            lines.append(f"... and {len(entries) - 200} more")
        return "\n".join(lines)
    except Exception as exc:
        return f"List failed: {exc}"


def _move_path(source: str, destination: str) -> str:
    src = os.path.expanduser(source)
    dst = os.path.expanduser(destination)
    try:
        shutil.move(src, dst)
        return f"Moved {src} -> {dst}"
    except Exception as exc:
        return f"Move failed: {exc}"


def _delete_path(registry: ToolRegistry, path: str) -> str:
    expanded = os.path.expanduser(path)
    if os.path.isdir(expanded):
        try:
            os.rmdir(expanded)
            return f"Removed empty directory {expanded}"
        except OSError:
            registry.pending_confirmation = {
                "tool": "delete_path",
                "path": expanded,
                "reason": "Recursive directory delete requires confirmation",
                "fingerprint": expanded,
            }
            return "BLOCKED - directory not empty. Ask user to confirm recursive delete via shell."

    safe, reason = assess_shell_command(f"rm {expanded}")
    if not safe:
        registry.pending_confirmation = {
            "tool": "delete_path",
            "path": expanded,
            "reason": reason,
            "fingerprint": expanded,
        }
        return f"BLOCKED - confirmation required: {reason}"

    try:
        os.remove(expanded)
        return f"Deleted {expanded}"
    except Exception as exc:
        return f"Delete failed: {exc}"