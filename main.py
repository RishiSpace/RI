#!/usr/bin/env python3
"""Rishi Intelligence v3 — local PC agent."""

import argparse
import os
import sys

from ri.audio_env import configure

configure()


def main() -> None:
    parser = argparse.ArgumentParser(description="RI — local voice & text PC agent")
    parser.add_argument(
        "--mode",
        choices=["hybrid", "text", "voice"],
        default="hybrid",
        help="Interaction mode (default: hybrid = text + voice)",
    )
    parser.add_argument("--model", help="Ollama model override (default: ri-instruct:latest)")
    args = parser.parse_args()

    if args.model:
        os.environ["RI_MODEL"] = args.model

    os.makedirs("./aud", exist_ok=True)
    os.makedirs(os.path.expanduser("~/Pictures/RI-Screenshots"), exist_ok=True)

    if args.mode == "hybrid":
        from ri.interfaces.hybrid import HybridInterface
        HybridInterface().run()
    elif args.mode == "text":
        from ri.agent import RIAgent
        agent = RIAgent()
        print("Text mode. /quit to exit, /reset to clear.\n")
        while True:
            try:
                line = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                continue
            if line.lower() in ("/quit", "/exit"):
                break
            if line.lower() == "/reset":
                agent.reset_conversation()
                continue
            agent.process_input(line, stream=True, speak=False)
    else:
        from ri.agent import RIAgent
        from ri.interfaces.voice import VoiceInterface
        from ri import config

        from ri.interfaces.voice_session import run_wake_loop

        voice = VoiceInterface()
        agent = RIAgent(speak_callback=voice.speak)
        voice.speak("Voice mode active.")
        stopped = False

        def _stop():
            nonlocal stopped
            stopped = True

        run_wake_loop(voice, agent, should_stop=lambda: stopped, on_quit=_stop)
        voice.stop_continuous_mic()


if __name__ == "__main__":
    main()