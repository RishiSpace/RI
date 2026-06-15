# Rishi Intelligence (RI) v3

Locally-hosted AI agent with **fast text + voice conversation** and **full system-level PC control**.

## Features

- **Hybrid interface** — type commands anytime while voice wake-word runs in background
- **Low-latency voice** — faster-whisper STT with separate wake/command models
- **Streaming text replies** — see responses as they generate
- **20+ system tools** — shell, files, apps, GUI automation, screenshots, clipboard, notifications, volume, lock screen, processes, web search
- **Safety rails** — destructive actions require explicit confirmation
- **100% local** — Ollama LLM + local speech; no cloud APIs required

## Prerequisites

1. [Ollama](https://ollama.com/) running (`ollama serve`)
2. Python 3.10+
3. System packages (Arch example):
   ```bash
   sudo pacman -S portaudio ffmpeg espeak-ng tk xclip wl-clipboard xdotool scrot
   ```

## Install

```bash
git clone https://github.com/RishiSpace/RI.git
cd RI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull lfm2.5   # default model tag: lfm2.5:latest
```

## Usage

```bash
# Hybrid mode (default) — text + voice together
./venv/bin/python main.py

# Text only — fastest for power users
./venv/bin/python main.py --mode text

# Voice only
./venv/bin/python main.py --mode voice

# Use a different model
RI_MODEL=qwen2.5:7b ./venv/bin/python main.py   # optional stronger model
```

### Text commands
- Type naturally: `list files here`, `open firefox`, `lock screen`, `screenshot`
- `/help` — show commands
- `/reset` — clear conversation
- `/quit` — exit

### Voice
- **Mic stays on** — RI listens continuously and ignores speech until you say the wake word
- Wake: **"RI"**, **"Hey RI"**, **"Computer"** — or *"computer lock the screen"* in one phrase
- **Multi-turn**: keep talking after RI replies; no need to re-wake (~25s window)
- End session: **"standby"** / **"that's all"**
- Quit app: **"Rishi quit"**

## Tool capabilities

| Category | Tools |
|----------|-------|
| Shell | `execute_shell_command`, `run_script` |
| Files | `read_file`, `write_file`, `list_directory`, `move_path`, `delete_path` |
| Desktop | `open_application`, `open_url`, `lock_screen`, `set_volume`, `send_notification` |
| Processes | `list_processes`, `kill_process` |
| GUI | `gui_click`, `gui_type`, `gui_hotkey`, `gui_scroll`, `gui_move_mouse`, `take_screenshot`, `get_screen_size`, `get_active_window`, `list_windows`, `focus_window`, `resize_window` |
| System | `get_time`, `get_system_info`, `get_clipboard`, `set_clipboard`, `web_search` |

## Configuration (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `RI_MODEL` | `lfm2.5:latest` | Ollama model |
| `RI_WHISPER` | `faster` | STT backend (`faster` or `openai`) |
| `RI_WHISPER_WAKE` | `base` | Fast wake-word model |
| `RI_WHISPER_CMD` | `small` | Command transcription model |
| `RI_REQUIRE_CONFIRM` | `1` | Block dangerous commands until confirmed |
| `RI_TTS` | `piper` | TTS engine: `piper`, `edge`, `espeak`, `pyttsx3` |
| `RI_PIPER_VOICE` | `en_US-lessac-medium` | Natural local Piper voice |
| `RI_EDGE_VOICE` | `en-US-JennyNeural` | Edge TTS voice (if `RI_TTS=edge`) |
| `RI_VERBOSE` | `0` | Show tool/debug logs (off in voice mode) |
| `RI_CONV_TIMEOUT` | `25` | Seconds to keep listening for follow-ups after each reply |

## Verify setup

```bash
./venv/bin/python test_components.py
./venv/bin/python scripts/test_mic.py   # speak — should print [heard] lines
```

If wake never triggers, you'll still see `[heard] "your words"` — that means mic works but wake word wasn't matched. Try `RI_VERBOSE=1` or `RI_MIC_INDEX=11` (pulse device).

## Legacy

Previous Groq/cloud version is in `Archive/`.

## License

GPLv3 — see [LICENSE](LICENSE).