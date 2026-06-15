import hashlib
import re
from typing import Optional

DANGEROUS_PATTERNS = [
    r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?/.*",
    r"\brm\s+-rf\b",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpoweroff\b",
    r"\binit\s+0\b",
    r"\bchmod\s+-R\s+777\b",
    r">\s*/dev/sd",
    r"\bformat\s+c:",
    r"\bdel\s+/[fs]",
    r"curl\s+.*\|\s*(ba)?sh",
    r"\bwget\s+.*\|\s*(ba)?sh",
    r"\bkill\s+-9\s+1\b",
    r"\b:(){ :|:& };:",
]


def command_fingerprint(command: str) -> str:
    return hashlib.sha256(command.strip().encode()).hexdigest()[:16]


def assess_shell_command(command: str) -> tuple[bool, Optional[str]]:
    normalized = command.strip().lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, f"Potentially destructive command matched pattern: {pattern}"
    return True, None


def assess_file_write(path: str) -> tuple[bool, Optional[str]]:
    protected_prefixes = ("/etc/", "/usr/", "/bin/", "/sbin/", "/boot/", "/sys/", "/proc/")
    expanded = path.strip()
    for prefix in protected_prefixes:
        if expanded.startswith(prefix):
            return False, f"Writing to protected system path: {prefix}"
    return True, None