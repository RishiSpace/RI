from __future__ import annotations

import threading

from ri import config
from ri.agent import RIAgent
from ri.interfaces.text import TextInterface
from ri.interfaces.voice import VoiceInterface
from ri.interfaces.voice_session import run_wake_loop


class HybridInterface:
    """Low-latency hybrid: always-on text + continuous voice wake word."""

    def __init__(self) -> None:
        self.voice = VoiceInterface()
        self.agent = RIAgent(speak_callback=self.voice.speak)
        self.text = TextInterface(on_input=self._on_text)
        self._stop = threading.Event()

    def _on_text(self, text: str) -> None:
        if text == "__quit__":
            self._stop.set()
            return
        if text == "__reset__":
            self.agent.reset_conversation()
            return
        self.agent.process_input(text, stream=True, speak=False, quiet=False)

    def _voice_loop(self) -> None:
        print("Voice: mic stays open — wake word starts a conversation.")
        print(f"  Follow-ups: {int(config.CONVERSATION_TIMEOUT_SEC)}s without re-waking.")
        print(f"  'standby' ends session | 'rishi quit' exits.\n")

        run_wake_loop(
            self.voice,
            self.agent,
            should_stop=self._stop.is_set,
            on_quit=self._stop.set,
        )

    def run(self) -> None:
        import torch

        if torch.cuda.is_available():
            print(f"CUDA: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA not available — using CPU.")

        self.voice.speak("RI online. Text and voice ready.")
        print(f"Model: {config.OLLAMA_MODEL} | Tools: {len(self.agent.tools.get_definitions())}")

        voice_thread = threading.Thread(target=self._voice_loop, daemon=True)
        voice_thread.start()
        self.text.start_background()

        try:
            while not self._stop.is_set():
                self._stop.wait(0.5)
        except KeyboardInterrupt:
            self._stop.set()
        finally:
            self.voice.stop_continuous_mic()

        print("Goodbye.")