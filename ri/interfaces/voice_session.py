"""Multi-turn voice conversation — stay active after wake until timeout or dismiss."""

from __future__ import annotations

import re
import time
from typing import Callable

from ri import config
from ri.agent import RIAgent
from ri.interfaces.voice import VoiceInterface


_FILLER = frozenset({"hey", "hi", "yo", "hello", "okay", "ok", "please", "the", "a", "um", "uh"})

# Whisper often mishears wake words — fuzzy variants
_WAKE_ALIASES: list[tuple[str, str]] = [
    (r"\bri\b", "ri"),
    (r"\br\s*i\b", "ri"),
    (r"\brye\b", "ri"),
    (r"\bare\s*eye\b", "ri"),
    (r"\bhey\s*ri\b", "ri"),
    (r"\bhi\s*ri\b", "ri"),
    (r"\bcomputer\b", "computer"),
    (r"\bcomputers\b", "computer"),
    (r"\bcomputa\b", "computer"),
    (r"\bkomputer\b", "computer"),
    (r"\bhello\s+computer\b", "computer"),
    (r"\bhey\s+computer\b", "computer"),
]


def _normalize_heard(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"[^\w\s']", " ", t)
    return " ".join(t.split())


def _strip_wake_words(text: str) -> str:
    lower = _normalize_heard(text)
    for ww in sorted(config.WAKE_WORDS, key=len, reverse=True):
        if ww in lower:
            lower = lower.replace(ww, " ", 1)
    for pattern, _ in _WAKE_ALIASES:
        lower = re.sub(pattern, " ", lower)
    words = [w for w in lower.split() if w not in _FILLER]
    return " ".join(words)


def detect_wake(text: str) -> tuple[bool, str]:
    """Return (wake_detected, command_after_wake or '')."""
    lower = _normalize_heard(text)
    if not lower:
        return False, ""

    # Exact wake phrases from config
    for ww in sorted(config.WAKE_WORDS, key=len, reverse=True):
        if ww in lower:
            return True, _strip_wake_words(lower)

    # Fuzzy regex aliases
    for pattern, _ in _WAKE_ALIASES:
        if re.search(pattern, lower):
            return True, _strip_wake_words(lower)

    return False, ""


def is_quit(text: str) -> bool:
    t = _normalize_heard(text)
    return any(q in t for q in config.QUIT_WORDS)


def is_standby(text: str) -> bool:
    t = _normalize_heard(text)
    return any(s in t for s in config.STANDBY_WORDS)


def run_session(
    voice: VoiceInterface,
    agent: RIAgent,
    *,
    first_command: str | None = None,
    on_end: Callable[[str], None] | None = None,
) -> str:
    deadline = time.monotonic() + config.CONVERSATION_TIMEOUT_SEC
    turns = 0
    pending_cmd = first_command

    while turns < config.CONVERSATION_MAX_TURNS:
        if time.monotonic() > deadline:
            if on_end:
                on_end("timeout")
            return "timeout"

        if pending_cmd is not None:
            cmd_text = pending_cmd.strip()
            pending_cmd = None
        else:
            cmd_text = ""
            for phrase in voice.iter_phrases(deadline=deadline):
                cmd_text = phrase
                deadline = time.monotonic() + config.CONVERSATION_TIMEOUT_SEC
                break
            if not cmd_text:
                if on_end:
                    on_end("timeout")
                return "timeout"

        if not cmd_text:
            voice.speak("I didn't catch that.")
            turns += 1
            continue

        _echo_phrase(cmd_text, woke=False)

        if is_quit(cmd_text):
            voice.speak("Shutting down.")
            return "quit"

        cmd_text = _strip_wake_words(cmd_text)
        if not cmd_text:
            turns += 1
            continue

        if not agent.tools.pending_confirmation and is_standby(cmd_text):
            voice.speak("Okay, I'll be here.")
            if on_end:
                on_end("standby")
            return "standby"

        agent.process_input(cmd_text, stream=False, speak=True, quiet=True)
        turns += 1

    if on_end:
        on_end("max_turns")
    return "max_turns"


def handle_wake_utterance(
    voice: VoiceInterface,
    agent: RIAgent,
    heard: str,
    *,
    on_session_end: Callable[[str], None] | None = None,
) -> str | None:
    woke, inline_cmd = detect_wake(heard)
    if not woke:
        return None

    if inline_cmd:
        voice.speak("On it.")
        first = inline_cmd
    else:
        voice.speak("Yes?")
        first = ""
        deadline = time.monotonic() + config.CONVERSATION_LISTEN_TIMEOUT
        for phrase in voice.iter_phrases(deadline=deadline):
            first = phrase
            break

    if first and is_quit(first):
        voice.speak("Shutting down.")
        return "quit"

    result = run_session(voice, agent, first_command=first or None, on_end=on_session_end)
    return "quit" if result == "quit" else None


def _echo_phrase(phrase: str, *, woke: bool) -> None:
    """Show the user that speech was heard (helps debug wake issues)."""
    if not config.HEAR_ECHO and not config.VERBOSE:
        return
    tag = "WAKE" if woke else "heard"
    print(f"[{tag}] {phrase}")


def run_wake_loop(
    voice: VoiceInterface,
    agent: RIAgent,
    *,
    should_stop: Callable[[], bool],
    on_quit: Callable[[], None],
) -> None:
    voice.start_continuous_mic()

    for phrase in voice.iter_phrases():
        if should_stop():
            break
        if not phrase:
            continue

        if is_quit(phrase):
            voice.speak("Shutting down.")
            on_quit()
            return

        woke, _ = detect_wake(phrase)
        if not woke:
            _echo_phrase(phrase, woke=False)
            continue

        _echo_phrase(phrase, woke=True)
        if handle_wake_utterance(voice, agent, phrase) == "quit":
            on_quit()
            return