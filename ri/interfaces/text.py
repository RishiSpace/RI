from __future__ import annotations

import select
import sys
import threading
from typing import Callable


class TextInterface:
    def __init__(self, on_input: Callable[[str], None]) -> None:
        self.on_input = on_input
        self._running = False
        self._thread: threading.Thread | None = None

    def start_background(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        print("\n[text] Type commands anytime. '/quit' exit, '/reset' clear history, '/help' commands.\n")
        while self._running:
            try:
                if sys.stdin.isatty():
                    line = input("you> ").strip()
                else:
                    # Non-tty: poll stdin
                    if select.select([sys.stdin], [], [], 0.5)[0]:
                        line = sys.stdin.readline().strip()
                    else:
                        continue
                if not line:
                    continue
                self._handle(line)
            except EOFError:
                break
            except KeyboardInterrupt:
                break

    def _handle(self, line: str) -> None:
        cmd = line.lower()
        if cmd in ("/quit", "/exit", "/q"):
            self.on_input("__quit__")
            self._running = False
        elif cmd == "/reset":
            self.on_input("__reset__")
        elif cmd == "/help":
            print(
                "Commands: /help /reset /quit\n"
                "Examples: list files here | open firefox | lock screen | screenshot | set volume 50"
            )
        else:
            self.on_input(line)

    def stop(self) -> None:
        self._running = False