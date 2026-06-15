"""Always-on microphone via speech_recognition background listener."""

from __future__ import annotations

import queue
import threading
import time
from typing import Callable, Iterator

import speech_recognition as sr

from ri import config
from ri.audio_env import configure, no_alsa_err, suppress_audio_noise

configure()


def _find_mic_index() -> int | None:
    """Pick pulse/default mic — most reliable on PipeWire/Linux."""
    if config.MIC_DEVICE_INDEX is not None:
        return config.MIC_DEVICE_INDEX
    try:
        names = sr.Microphone.list_microphone_names()
    except Exception:
        return None
    for prefer in ("pulse", "default", "pipewire"):
        for i, name in enumerate(names):
            if prefer in name.lower():
                if config.VERBOSE:
                    print(f"[mic] using device {i}: {name}")
                return i
    return None


class ContinuousListener:
    """
    Mic stays open via listen_in_background. Each completed phrase is
    transcribed and queued. Wake loop discards non-wake phrases.
    """

    def __init__(self, transcribe: Callable[[bytes], str]) -> None:
        self._transcribe = transcribe
        self._recognizer = sr.Recognizer()
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.energy_threshold = config.CONTINUOUS_ENERGY_THRESHOLD
        self._recognizer.pause_threshold = config.CONTINUOUS_PAUSE_SEC
        self._recognizer.phrase_threshold = 0.25
        self._recognizer.non_speaking_duration = 0.4

        self._mic_index = _find_mic_index()
        self._mic = sr.Microphone(device_index=self._mic_index)
        self._phrase_queue: queue.Queue[str | None] = queue.Queue()
        self._running = False
        self._paused = False
        self._pause_lock = threading.Lock()
        self._stop_bg: Callable | None = None

    def start(self) -> None:
        if self._running:
            return

        with suppress_audio_noise(), no_alsa_err():
            with self._mic as source:
                print("[mic] calibrating...")
                self._recognizer.adjust_for_ambient_noise(source, duration=1.0)
                if config.VERBOSE:
                    print(f"[mic] energy threshold = {self._recognizer.energy_threshold:.0f}")

        def _callback(recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
            with self._pause_lock:
                if self._paused:
                    return
            try:
                with suppress_audio_noise():
                    text = self._transcribe(audio.get_wav_data())
                if text:
                    self._phrase_queue.put(text.strip().lower())
            except Exception as exc:
                if config.VERBOSE:
                    print(f"[mic] transcribe error: {exc}")

        with suppress_audio_noise(), no_alsa_err():
            self._stop_bg = self._recognizer.listen_in_background(
                self._mic,
                _callback,
                phrase_time_limit=config.CONTINUOUS_MAX_PHRASE_SEC,
            )

        self._running = True
        print("[mic] always-on — say 'computer' or 'RI'")

    def stop(self) -> None:
        self._running = False
        if self._stop_bg:
            try:
                self._stop_bg(wait_for_stop=False)
            except Exception:
                pass
            self._stop_bg = None
        self._phrase_queue.put(None)

    def pause(self) -> None:
        with self._pause_lock:
            self._paused = True

    def resume(self) -> None:
        with self._pause_lock:
            self._paused = False

    def drain_while_paused(self, seconds: float = 0.4) -> None:
        time.sleep(seconds)

    def iter_phrases(self, *, deadline: float | None = None) -> Iterator[str]:
        while self._running:
            if deadline and time.monotonic() > deadline:
                return
            timeout = None
            if deadline:
                timeout = max(0.05, deadline - time.monotonic())
            try:
                phrase = self._phrase_queue.get(timeout=timeout)
            except queue.Empty:
                return
            if phrase is None:
                return
            yield phrase