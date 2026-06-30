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
2. Python 3.10+ (3.12 or 3.13 **strongly recommended on Windows** for wheel availability)
3. `hf` CLI (to download the custom GGUF model):
   ```bash
   pip install -U "huggingface_hub[cli]"
   ```
4. System packages
   - **Linux** (Arch example):
     ```bash
     sudo pacman -S portaudio ffmpeg espeak-ng tk xclip wl-clipboard xdotool scrot
     ```
   - **Windows**: Microsoft Visual C++ Redistributable (latest). Many dependencies install their own DLLs.

## Install

```bash
git clone https://github.com/RishiSpace/RI.git
cd RI
python -m venv venv          # or RI-Env on Windows
# Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
pip install -r requirements.txt
```

See the **Packaging (binaries)** section below for Windows-specific install troubleshooting (especially pygame + pyaudio).

## Model Setup (required)

**RI-Instruct is not available on the Ollama registry.** You must download the GGUF + Modelfile from Hugging Face and import it locally.

The official `Modelfile` lives in the model repo: https://huggingface.co/RishiSpace/RI-Instruct-v0.2-GGUF

Always download the latest Modelfile from Hugging Face (do not rely on a local copy) to avoid version mismatches.

Run the following **from inside the RI directory**:

```bash
# 1. Download the model weights (~5.9 GB) and the official Modelfile
hf download RishiSpace/RI-Instruct-v0.2-GGUF \
  RI-Instruct-v0.2-Q5_K_M.gguf Modelfile --local-dir .

# 2. Import it into Ollama (creates the "ri-instruct:latest" tag)
ollama create ri-instruct:latest -f Modelfile
```

Verify:

```bash
ollama list
```

You should see `ri-instruct:latest`.

**Alternative** (no `hf` CLI):

```bash
curl -L -o RI-Instruct-v0.2-Q5_K_M.gguf \
  https://huggingface.co/RishiSpace/RI-Instruct-v0.2-GGUF/resolve/main/RI-Instruct-v0.2-Q5_K_M.gguf

curl -L -o Modelfile \
  https://huggingface.co/RishiSpace/RI-Instruct-v0.2-GGUF/raw/main/Modelfile
```

The `Modelfile` and `.gguf` must be in the same directory when running `ollama create`.

> **Note:** The RI app runs with thinking disabled by default (`RI_THINK=0`) for faster responses. Set `RI_THINK=1` if you want the model to show its reasoning steps.

## Usage

```bash
# Hybrid mode (default) — text + voice together
./venv/bin/python main.py

# Text only — fastest for power users
./venv/bin/python main.py --mode text

# Voice only
./venv/bin/python main.py --mode voice

# Use a different model (after creating it in Ollama)
RI_MODEL=qwen3:8b ./venv/bin/python main.py

# Enable thinking/reasoning on the RI model (slower but may be smarter)
RI_THINK=1 ./venv/bin/python main.py
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
| `RI_MODEL` | `ri-instruct:latest` | Ollama model tag (created locally via the steps above) |
| `RI_THINK` | `0` (false) | Set `1`/`true` to enable model thinking (reasoning steps); or `low`/`medium`/`high` |
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

## Packaging (binaries)

RI can be packaged into standalone executables with PyInstaller.

### Linux

From the project root:

```bash
# 1. Make sure your venv has everything (or use system python with all deps)
# 2. Build
bash scripts/build_linux.sh
# or manually:
python -m PyInstaller RI.spec --clean --noconfirm
```

Result: `dist/RI/RI` (the executable) + `dist/RI/_internal/` (all bundled libs).

Run:

```bash
./dist/RI/RI --mode text
```

**Size note**: Expect 6–8+ GB because of PyTorch + faster-whisper + onnxruntime.

### Windows

Cross-building from Linux is **not reliable** (native wheels and DLLs differ). Build on a real Windows machine.

#### Recommended Python version
Use **Python 3.12 or 3.13**. Python 3.14 frequently lacks pre-built wheels for `pygame`, `pyaudio`, `torch`, `faster-whisper`, etc., causing long and often failing source compiles.

#### Install steps (PowerShell / CMD)

```powershell
# 1. Create and activate a venv (example name RI-Env)
python -m venv RI-Env
RI-Env\Scripts\activate

# 2. Upgrade core tools
python -m pip install --upgrade pip setuptools wheel

# 3. Install pygame FIRST (this is the package that usually fails)
pip install pygame

# If you see the error:
#   ModuleNotFoundError: No module named 'setuptools._distutils.msvccompiler'
# run these and then retry the pygame line:
#   pip install "setuptools<70"
#   pip install pygame

# 4. Install the rest of the dependencies
pip install -r requirements.txt

# 5. PyInstaller
pip install --upgrade pyinstaller
```

Special cases:
- **pyaudio** often fails on Windows:
  ```powershell
  pip install pipwin
  pipwin install pyaudio
  ```
- If any heavy package (torch, onnxruntime, faster-whisper) complains about CUDA vs CPU, install the CPU-only torch first if needed:
  ```powershell
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
  ```

#### Build the binary

```bat
scripts\build_windows.bat
```

Or manually:

```powershell
python -m PyInstaller RI.spec --clean --noconfirm
```

Result: `dist\RI\RI.exe` (and supporting files in `dist\RI\` for the default onedir layout).

Run the packaged app:
```powershell
dist\RI\RI.exe --mode text
```

You can zip the entire `dist\RI` folder. The target PC will still need Ollama running.

### Important notes about binaries

- **Ollama is not bundled**. The user must install and run `ollama serve` + have the `ri-instruct:latest` model created.
- **Native system libraries** are still required on the target:
  - Linux: `tk`, `portaudio`, `ffmpeg`, `espeak-ng`, `xclip`/`wl-clipboard`, `xdotool` (or equivalent for your DE).
  - Windows: appropriate Visual C++ runtimes, and audio devices.
- GUI automation (pyautogui) and audio work best when the corresponding system packages are present.
- For smaller distributions you can edit `RI.spec` to use more aggressive excludes or switch TTS engine.

## Legacy

Previous Groq/cloud version is in `Archive/`.

## License

GPLv3 — see [LICENSE](LICENSE).