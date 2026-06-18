from __future__ import annotations

import re
import threading
from typing import Callable

import ollama

from ri import config
from ri.system_info import get_system_context
from ri.tools.registry import ToolRegistry, build_tool_registry


SYSTEM_PROMPT = """You are RI (Rishi Intelligence), a fast local PC agent with full system control.

{context}

Capabilities: shell commands, files, apps, browser URLs, GUI automation (click/type/hotkeys),
screenshots, clipboard, notifications, volume, screen lock, processes, web search.

Rules:
1. Use tools to act — don't just describe what to run.
2. Prefer dedicated tools over raw shell when available.
3. Adapt commands to the detected Desktop Environment (GNOME/KDE/etc).
4. Be concise in spoken replies; fuller detail is fine in text mode.
5. If a tool returns BLOCKED, explain the action and ask for confirmation.
6. Chain multiple tools for multi-step tasks.
7. After tool results, summarize outcomes clearly for the user.
8. Never invent tool output — only report actual results.
9. For GUI tasks: take_screenshot or get_screen_size first, then click/type/focus_window.
10. Do not include <think> tags in user-facing replies.
"""


class RIAgent:
    def __init__(self, speak_callback: Callable[[str], None] | None = None) -> None:
        self.tools: ToolRegistry = build_tool_registry()
        self.speak = speak_callback or (lambda text: print(f"RI: {text}"))
        self._lock = threading.Lock()
        self.messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=get_system_context())}
        ]
        self._ensure_model()

    def _ensure_model(self) -> None:
        print(f"Checking Ollama model: {config.OLLAMA_MODEL}")
        try:
            listed = ollama.list()
            models = getattr(listed, "models", None) or listed.get("models", [])
            names = []
            for m in models:
                if isinstance(m, dict):
                    names.append(m.get("name", ""))
                else:
                    names.append(getattr(m, "model", None) or getattr(m, "name", ""))

            if not any(config.OLLAMA_MODEL in n for n in names):
                print(f"Pulling {config.OLLAMA_MODEL}...")
                for progress in ollama.pull(config.OLLAMA_MODEL, stream=True):
                    if progress.get("status"):
                        print(f"  {progress['status']}", end="\r")
                print()

            print("Warming up model...")
            ollama.chat(
                model=config.OLLAMA_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                options=config.OLLAMA_OPTIONS,
                think=config.OLLAMA_THINK,
            )
            print("Model ready.")
        except Exception as exc:
            print(f"Ollama error: {exc}. Run: ollama serve")

    def _trim_history(self) -> None:
        if len(self.messages) <= config.MAX_HISTORY_MESSAGES:
            return
        system = self.messages[0]
        self.messages = [system] + self.messages[-(config.MAX_HISTORY_MESSAGES - 1) :]

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"<think[^>]*>.*", "", text, flags=re.DOTALL)
        return text.strip()

    def _handle_confirmation_input(self, text: str, *, quiet: bool = False) -> bool:
        lower = text.lower().strip()
        if any(w in lower for w in config.CONFIRM_WORDS):
            if self.tools.pending_confirmation:
                pending = self.tools.pending_confirmation
                self.tools.confirm_pending()
                self.messages.append({
                    "role": "user",
                    "content": f"User confirmed: {pending.get('reason', 'proceed')}",
                })
                self._run_tool_loop(stream_final=False, speak_final=True, quiet=quiet)
                return True
        if any(w in lower for w in config.DENY_WORDS):
            self.tools.deny_pending()
            self.speak("Cancelled.")
            return True
        return False

    def process_input(
        self, text: str, *, stream: bool = True, speak: bool = True, quiet: bool = False
    ) -> str:
        text = text.strip()
        if not text:
            return ""

        with self._lock:
            if self.tools.pending_confirmation and self._handle_confirmation_input(text, quiet=quiet):
                return ""

            if not quiet or config.VERBOSE:
                print(f"You: {text}")
            self.messages.append({"role": "user", "content": text})
            return self._run_tool_loop(stream_final=stream, speak_final=speak, quiet=quiet)

    def _run_tool_loop(self, *, stream_final: bool, speak_final: bool, quiet: bool = False) -> str:
        final_response = ""
        show_detail = config.VERBOSE or not quiet

        for round_i in range(config.MAX_TOOL_ROUNDS):
            if round_i == 0 and show_detail and stream_final:
                print("RI: ", end="", flush=True)

            if round_i > 0 or not stream_final:
                response = ollama.chat(
                    model=config.OLLAMA_MODEL,
                    messages=self.messages,
                    tools=self.tools.get_definitions(),
                    options=config.OLLAMA_OPTIONS,
                    think=config.OLLAMA_THINK,
                )
                message = response["message"]
            else:
                message = {"role": "assistant", "content": ""}
                stream = ollama.chat(
                    model=config.OLLAMA_MODEL,
                    messages=self.messages,
                    tools=self.tools.get_definitions(),
                    options=config.OLLAMA_OPTIONS,
                    stream=True,
                    think=config.OLLAMA_THINK,
                )
                tool_calls = None
                content_parts: list[str] = []
                for chunk in stream:
                    part = chunk.get("message", {})
                    if part.get("content"):
                        token = part["content"]
                        content_parts.append(token)
                        if show_detail:
                            print(token, end="", flush=True)
                    if part.get("tool_calls"):
                        tool_calls = part["tool_calls"]
                if show_detail:
                    print()
                message["content"] = "".join(content_parts)
                if tool_calls:
                    message["tool_calls"] = tool_calls

            self.messages.append(message)
            self._trim_history()

            if message.get("tool_calls"):
                for call in message["tool_calls"]:
                    fn = call["function"]["name"]
                    args = call["function"]["arguments"]
                    if isinstance(args, str):
                        import json
                        args = json.loads(args)
                    if show_detail:
                        print(f"[tool] {fn}({args})")
                    result = self.tools.dispatch(fn, args)
                    if show_detail:
                        preview = result[:300] + ("..." if len(result) > 300 else "")
                        print(f"[result] {preview}")
                    self.messages.append({"role": "tool", "content": str(result)})
                continue

            content = self._clean_text(message.get("content") or "")
            if content:
                final_response = content
                if speak_final:
                    self._speak_response(content)
            return final_response

        self.speak("I hit my step limit. Please narrow the request.")
        return "step limit reached"

    def _speak_response(self, text: str) -> None:
        # Keep voice replies short for low latency
        spoken = text
        if len(spoken) > 500:
            cut = spoken[:500].rfind(".")
            spoken = spoken[: cut + 1] if cut > 100 else spoken[:500] + "..."
        self.speak(spoken)

    def reset_conversation(self) -> None:
        self.messages = self.messages[:1]
        self.tools.clear_confirmation()
        print("Conversation reset.")