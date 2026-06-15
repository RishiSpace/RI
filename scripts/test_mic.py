#!/usr/bin/env python3
"""Quick mic + wake-word test. Run: ./venv/bin/python scripts/test_mic.py"""

import sys
import time

sys.path.insert(0, ".")

from ri.audio_env import configure
configure()

from ri.interfaces.voice import VoiceInterface
from ri.interfaces.voice_session import detect_wake

def main():
    print("Mic test — speak a wake phrase ('computer' / 'RI'). Ctrl+C to quit.\n")
    voice = VoiceInterface()
    voice.start_continuous_mic()
    try:
        for i, phrase in enumerate(voice.iter_phrases()):
            woke, cmd = detect_wake(phrase)
            tag = "WAKE" if woke else "heard"
            extra = f" → cmd='{cmd}'" if woke and cmd else ""
            print(f"[{tag}] {phrase!r}{extra}")
            if i >= 20:
                print("(stopping after 20 phrases)")
                break
    except KeyboardInterrupt:
        pass
    finally:
        voice.stop_continuous_mic()
    print("done.")

if __name__ == "__main__":
    main()