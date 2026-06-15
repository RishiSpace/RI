from __future__ import annotations

import os
import tempfile

import speech_recognition as sr

from ri import config
from ri.audio_env import configure, no_alsa_err, suppress_audio_noise
from ri.interfaces.continuous_listen import ContinuousListener
from ri.tts import speak as tts_speak

configure()


class VoiceInterface:
    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6

        self._wake_model = None
        self._command_model = None
        self._openai_whisper = None
        self._backend = config.WHISPER_BACKEND
        self._continuous: ContinuousListener | None = None

        self._init_stt()
        print(f"TTS engine: {config.TTS_ENGINE} (voice: {config.PIPER_VOICE if config.TTS_ENGINE == 'piper' else config.EDGE_VOICE})")

    def _init_stt(self) -> None:
        if self._backend == "faster":
            try:
                from faster_whisper import WhisperModel
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute = "float16" if device == "cuda" else "int8"
                if config.VERBOSE:
                    print(f"Loading faster-whisper wake={config.WHISPER_WAKE_MODEL} cmd={config.WHISPER_COMMAND_MODEL}")
                self._wake_model = WhisperModel(config.WHISPER_WAKE_MODEL, device=device, compute_type=compute)
                if config.WHISPER_COMMAND_MODEL != config.WHISPER_WAKE_MODEL:
                    self._command_model = WhisperModel(
                        config.WHISPER_COMMAND_MODEL, device=device, compute_type=compute
                    )
                else:
                    self._command_model = self._wake_model
                self._backend = "faster"
                return
            except ImportError:
                print("faster-whisper not installed, falling back to openai-whisper")

        import whisper

        print(f"Loading openai-whisper: {config.WHISPER_COMMAND_MODEL}")
        self._openai_whisper = whisper.load_model(config.WHISPER_COMMAND_MODEL)
        self._backend = "openai"

    def _ensure_continuous(self) -> ContinuousListener:
        if self._continuous is None:
            self._continuous = ContinuousListener(
                transcribe=lambda wav: self._transcribe_wav_bytes(wav, command=True),
            )
        return self._continuous

    def start_continuous_mic(self) -> None:
        self._ensure_continuous().start()

    def stop_continuous_mic(self) -> None:
        if self._continuous:
            self._continuous.stop()

    def iter_phrases(self, *, deadline: float | None = None):
        """Yield phrases from the always-on mic."""
        return self._ensure_continuous().iter_phrases(deadline=deadline)

    def speak(self, text: str) -> None:
        mic = self._continuous
        if mic:
            mic.pause()
            try:
                tts_speak(text)
            finally:
                mic.drain_while_paused(0.35)
                mic.resume()
        else:
            tts_speak(text)

    def listen(self, timeout: float | None = None, phrase_time_limit: float | None = None) -> sr.AudioData | None:
        with suppress_audio_noise(), no_alsa_err():
            with sr.Microphone() as source:
                try:
                    audio = self.recognizer.listen(
                        source, timeout=timeout, phrase_time_limit=phrase_time_limit
                    )
                    return audio
                except sr.WaitTimeoutError:
                    return None
                except Exception as exc:
                    if config.VERBOSE:
                        print(f"Mic error: {exc}")
                    return None

    def calibrate(self, duration: float = 0.8) -> None:
        """Calibration handled by ContinuousListener on start."""
        if self._continuous and self._continuous._running:
            return
        if config.VERBOSE:
            print("Mic will calibrate when always-on stream starts.")

    def _transcribe_wav_bytes(self, wav_bytes: bytes, *, command: bool = False) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav.write(wav_bytes)
            temp_path = temp_wav.name
        try:
            return self._transcribe_file(temp_path, command=command)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _transcribe_file(self, path: str, *, command: bool = False) -> str:
        try:
            with suppress_audio_noise():
                if self._backend == "faster":
                    model = self._command_model if command else self._wake_model
                    segments, _ = model.transcribe(path, beam_size=1, vad_filter=True)
                    return " ".join(seg.text for seg in segments).strip().lower()
                import torch
                result = self._openai_whisper.transcribe(path, fp16=torch.cuda.is_available())
                return result["text"].strip().lower()
        except Exception as exc:
            if config.VERBOSE:
                print(f"Transcribe error: {exc}")
            return ""

    def transcribe(self, audio: sr.AudioData | None, *, command: bool = False) -> str:
        if audio is None:
            return ""
        return self._transcribe_wav_bytes(audio.get_wav_data(), command=command)