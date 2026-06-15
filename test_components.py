#!/usr/bin/env python3
"""Verify RI components and tool registry."""

import sys


def test_imports():
    print("Testing package imports...")
    from ri.agent import RIAgent
    from ri.tools.registry import build_tool_registry
    from ri.interfaces.voice import VoiceInterface
    print("  imports OK")
    return True


def test_tool_registry():
    print("Testing tool registry...")
    from ri.tools.registry import build_tool_registry

    registry = build_tool_registry()
    tools = registry.get_definitions()
    names = {t["function"]["name"] for t in tools}
    expected = {
        "execute_shell_command",
        "read_file",
        "write_file",
        "open_application",
        "gui_click",
        "take_screenshot",
        "lock_screen",
        "web_search",
        "get_system_info",
    }
    missing = expected - names
    if missing:
        print(f"  MISSING tools: {missing}")
        return False
    print(f"  {len(tools)} tools registered")
    return True


def test_ollama():
    print("Testing Ollama...")
    try:
        import ollama
        ollama.list()
        print("  Ollama OK")
        return True
    except Exception as exc:
        print(f"  Ollama failed: {exc}")
        return False


def test_whisper():
    print("Testing STT backend...")
    try:
        from faster_whisper import WhisperModel
        print("  faster-whisper available")
        return True
    except ImportError:
        try:
            import whisper
            whisper.load_model("tiny")
            print("  openai-whisper OK (tiny)")
            return True
        except Exception as exc:
            print(f"  STT failed: {exc}")
            return False


def test_tts():
    print("Testing TTS...")
    try:
        from ri.tts import speak
        from ri import config
        print(f"  engine={config.TTS_ENGINE} voice={config.PIPER_VOICE}")
        # Don't play audio in CI-like test; just verify piper loads if selected
        if config.TTS_ENGINE == "piper":
            from ri.tts import _load_piper
            _load_piper()
            print("  Piper voice loaded")
        return True
    except Exception as exc:
        print(f"  TTS failed: {exc}")
        return False


def test_gui_backend():
    print("Testing GUI backend (tk + backends)...")
    from ri.gui_backend import screen_size, mouse_position, _init_tk
    ok = _init_tk()
    w, h = screen_size()
    x, y = mouse_position()
    print(f"  tk={ok} screen={w}x{h} mouse=({x},{y})")
    return w > 0 and h > 0


def test_safety():
    print("Testing safety module...")
    from ri.safety import assess_shell_command

    safe, _ = assess_shell_command("ls -la")
    unsafe, reason = assess_shell_command("rm -rf /")
    assert safe is True
    assert unsafe is False
    print("  safety OK")
    return True


if __name__ == "__main__":
    tests = [
        test_imports,
        test_tool_registry,
        test_gui_backend,
        test_safety,
        test_ollama,
        test_whisper,
        test_tts,
    ]
    results = [t() for t in tests]
    if all(results):
        print("\nAll checks passed.")
        sys.exit(0)
    print("\nSome checks failed.")
    sys.exit(1)