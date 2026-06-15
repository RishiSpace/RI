"""Natural TTS backends: Piper (local), edge-tts (optional), espeak-ng, pyttsx3."""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ri import config

_piper_voice = None
_pyttsx3_engine = None


def _piper_dir() -> Path:
    d = Path(os.environ.get("RI_PIPER_DIR", Path.home() / ".local/share/ri/piper"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ensure_piper_model() -> tuple[Path, Path]:
    voice = config.PIPER_VOICE
    d = _piper_dir()
    onnx = d / f"{voice}.onnx"
    cfg = d / f"{voice}.onnx.json"
    if onnx.exists() and cfg.exists():
        return onnx, cfg

    # rhasspy layout: en/en_US/lessac/medium/en_US-lessac-medium.onnx
    parts = voice.split("-")
    if len(parts) >= 3 and parts[0].startswith("en_"):
        locale, speaker, quality = parts[0], parts[1], parts[2]
        lang = locale.split("_")[0]
        rel = f"{lang}/{locale}/{speaker}/{quality}"
        base = f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{rel}/{voice}"
    else:
        raise RuntimeError(f"Cannot resolve download URL for Piper voice: {voice}")

    import urllib.request

    print(f"Downloading Piper voice '{voice}' (one-time, ~60MB)...")
    for url, dest in ((f"{base}.onnx", onnx), (f"{base}.onnx.json", cfg)):
        urllib.request.urlretrieve(url, dest)
    print("Piper voice ready.")
    return onnx, cfg


def _load_piper():
    global _piper_voice
    if _piper_voice is not None:
        return _piper_voice
    from piper import PiperVoice
    onnx, cfg = _ensure_piper_model()
    _piper_voice = PiperVoice.load(str(onnx), config_path=str(cfg))
    return _piper_voice


def _play_wav(path: str) -> None:
    for cmd in (
        ["paplay", path],
        ["aplay", "-q", path],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
    ):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, check=True, timeout=120, stderr=subprocess.DEVNULL)
                return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue
    raise RuntimeError("No audio player found (paplay/aplay/ffplay).")


def _speak_piper(text: str) -> None:
    import wave

    voice = _load_piper()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    try:
        with wave.open(wav_path, "wb") as wf:
            voice.synthesize_wav(text, wf)
        _play_wav(wav_path)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


def _speak_edge(text: str) -> None:
    import edge_tts

    async def _run():
        communicate = edge_tts.Communicate(text, config.EDGE_VOICE)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3 = f.name
        await communicate.save(mp3)
        return mp3

    mp3 = asyncio.run(_run())
    try:
        if shutil.which("ffplay"):
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", mp3],
                check=True, timeout=120, stderr=subprocess.DEVNULL,
            )
        elif shutil.which("mpv"):
            subprocess.run(["mpv", "--no-video", mp3], check=True, timeout=120, stderr=subprocess.DEVNULL)
        else:
            # pygame fallback for mp3
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(mp3)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)
    finally:
        if os.path.exists(mp3):
            os.remove(mp3)


def _speak_espeak(text: str) -> None:
    if not shutil.which("espeak-ng"):
        raise RuntimeError("espeak-ng not installed")
    subprocess.run(
        ["espeak-ng", "-v", config.ESPEAK_VOICE, "-s", str(config.TTS_RATE), "-g", "5", text],
        check=True, timeout=120, stderr=subprocess.DEVNULL,
    )


def _speak_pyttsx3(text: str) -> None:
    global _pyttsx3_engine
    import pyttsx3
    if _pyttsx3_engine is None:
        _pyttsx3_engine = pyttsx3.init()
        _pyttsx3_engine.setProperty("rate", config.TTS_RATE)
        for voice in _pyttsx3_engine.getProperty("voices"):
            if "english" in voice.name.lower():
                _pyttsx3_engine.setProperty("voice", voice.id)
                break
    _pyttsx3_engine.say(text)
    _pyttsx3_engine.runAndWait()


def speak(text: str) -> None:
    if not text or not text.strip():
        return
    text = text.strip()
    print(f"RI: {text}")

    engines = [config.TTS_ENGINE]
    if config.TTS_ENGINE == "piper":
        engines += ["edge", "espeak", "pyttsx3"]
    elif config.TTS_ENGINE == "edge":
        engines += ["piper", "espeak", "pyttsx3"]
    else:
        engines += ["piper", "edge", "espeak", "pyttsx3"]

    seen = set()
    for engine in engines:
        if engine in seen:
            continue
        seen.add(engine)
        try:
            if engine == "piper":
                _speak_piper(text)
            elif engine == "edge":
                _speak_edge(text)
            elif engine == "espeak":
                _speak_espeak(text)
            elif engine == "pyttsx3":
                _speak_pyttsx3(text)
            else:
                continue
            return
        except Exception as exc:
            print(f"TTS [{engine}] failed: {exc}")
    print("TTS: all engines failed.")