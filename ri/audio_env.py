"""Configure audio environment before PyAudio/speech_recognition load."""

from __future__ import annotations

import ctypes
import os
import sys
from contextlib import contextmanager

ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
    None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p
)


def _py_error_handler(filename, line, function, err, fmt):
    pass


_c_error_handler = ERROR_HANDLER_FUNC(_py_error_handler)


def configure() -> None:
    """Call once at startup — prevents JACK auto-connect spam on Linux."""
    os.environ.setdefault("JACK_NO_START_SERVER", "1")
    os.environ.setdefault("JACK_NO_AUDIO_RESERVATION", "1")
    os.environ.setdefault("PULSE_PROP_media.role", "phone")
    os.environ.setdefault("SDL_AUDIODRIVER", "pulse")


@contextmanager
def no_alsa_err():
    """Suppress ALSA lib error spam."""
    try:
        asound = ctypes.cdll.LoadLibrary("libasound.so")
        asound.snd_lib_error_set_handler(_c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except OSError:
        yield


@contextmanager
def suppress_audio_noise():
    """Mute stderr from ALSA/JACK/portaudio during mic capture."""
    configure()
    try:
        with open(os.devnull, "w") as devnull:
            old_stderr = os.dup(2)
            try:
                os.dup2(devnull.fileno(), 2)
                yield
            finally:
                os.dup2(old_stderr, 2)
                os.close(old_stderr)
    except OSError:
        yield


@contextmanager
def suppress_stderr():
    """General stderr suppression for noisy subprocess/tool output."""
    try:
        with open(os.devnull, "w") as devnull:
            old = sys.stderr
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stderr = old
    except OSError:
        yield