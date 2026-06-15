import subprocess

from ri import config
from ri.safety import assess_shell_command, command_fingerprint
from ri.tools.registry import ToolRegistry, _tool


def register(registry: ToolRegistry) -> None:
    registry.register(
        _tool(
            "execute_shell_command",
            "Run a shell command. Prefer dedicated tools for files/GUI when possible. "
            "Use the user's detected shell environment.",
            {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "working_directory": {
                        "type": "string",
                        "description": "Optional working directory",
                    },
                },
                "required": ["command"],
            },
        ),
        lambda command, working_directory=None: _execute_shell(registry, command, working_directory),
    )

    registry.register(
        _tool(
            "run_script",
            "Run a short inline shell script (multiple lines). Use for compound operations.",
            {
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "Multi-line shell script"},
                    "working_directory": {"type": "string"},
                },
                "required": ["script"],
            },
        ),
        lambda script, working_directory=None: _execute_shell(registry, script, working_directory),
    )


def _execute_shell(registry: ToolRegistry, command: str, working_directory: str | None) -> str:
    safe, reason = assess_shell_command(command)
    fp = command_fingerprint(command)

    if not safe and config.REQUIRE_CONFIRMATION and fp not in registry._confirmed:
        registry.pending_confirmation = {
            "tool": "execute_shell_command",
            "command": command,
            "fingerprint": fp,
            "reason": reason,
        }
        return (
            f"BLOCKED - confirmation required: {reason}. "
            "Tell the user what will run and ask them to say 'yes confirm' or 'no cancel'."
        )

    if config.VERBOSE:
        print(f"[shell] {command[:200]}{'...' if len(command) > 200 else ''}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            stderr=subprocess.PIPE,
            timeout=config.SHELL_TIMEOUT_SEC,
            cwd=working_directory or None,
        )
        output = (result.stdout or "") + (result.stderr or "")
        output = output.strip()
        if not output:
            return f"Command finished with exit code {result.returncode} (no output)."
        if len(output) > 8000:
            output = output[:8000] + "\n... [truncated]"
        return f"exit={result.returncode}\n{output}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {config.SHELL_TIMEOUT_SEC}s."
    except Exception as exc:
        return f"Failed to execute command: {exc}"