# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Rishi Intelligence (RI) v3
Produces a standalone binary for Linux (and usable as template for Windows).

Usage (from project root, with venv active or via venv python):
  python -m PyInstaller RI.spec --clean --noconfirm

Outputs:
  dist/RI          (Linux onefile)
  or dist/RI.exe   (on Windows)

Notes:
- Does NOT bundle Ollama or the LLM model. User must have `ollama serve` + ri-instruct.
- Heavy deps (torch, faster-whisper, onnxruntime) make the binary 1.5-3+ GB.
- Onedir mode is often faster for large apps; change to onefile=False + COLLECT for that.
- Linux build only on Linux hosts. Windows .exe requires Windows (or Wine, with mixed results).
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

project_root = os.path.abspath(os.getcwd())

# ------------------------------------------------------------------
# Data files to bundle (sounds, icon, etc.)
# ------------------------------------------------------------------
datas = [
    (os.path.join(project_root, "aud"), "aud"),
    (os.path.join(project_root, "RishiAI.ico"), "."),
    # If you add other static files (e.g. a default Modelfile copy), list them here.
]

# ------------------------------------------------------------------
# Hidden imports (many are dynamic in whisper/torch/piper/sr/etc.)
# ------------------------------------------------------------------
hiddenimports = [
    # Core
    "ollama",
    "psutil",
    "distro",
    "webbrowser",
    # Audio / STT
    "speech_recognition",
    "pyaudio",
    "faster_whisper",
    "faster_whisper.feature_extractor",
    "faster_whisper.tokenizer",
    "faster_whisper.transcribe",
    "whisper",
    "whisper.audio",
    "whisper.decoding",
    "whisper.model",
    "whisper.tokenizer",
    "torch",
    "torch.nn",
    "torch.nn.functional",
    "torch.utils",
    "torch.cuda",
    "numpy",
    "soundfile",
    "soundfile._sndfile",
    # TTS
    "piper",
    "piper.voice",
    "edge_tts",
    "edge_tts.communicate",
    "pyttsx3",
    "pyttsx3.drivers",
    "pyttsx3.drivers.espeak",
    "pyttsx3.drivers.sapi5",
    "pyttsx3.drivers.nsss",
    "asyncio",
    "pygame",
    "pygame.mixer",
    # GUI / automation
    "pyautogui",
    "pynput",
    "pynput.keyboard",
    "pynput.mouse",
    "tkinter",
    "tkinter.ttk",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "PIL._tkinter_finder",
    # Other runtime
    "ctypes",
    "queue",
    "threading",
    "tempfile",
    "pathlib",
    "subprocess",
    "urllib.request",
]

# Collect everything from big packages that use lazy loading
for pkg in ("torch", "faster_whisper", "whisper", "onnxruntime", "piper"):
    try:
        datas_pkg, bins_pkg, hiddens_pkg = collect_all(pkg)
        datas.extend(datas_pkg)
        hiddenimports.extend(hiddens_pkg)
    except Exception:
        pass

# Try to pull tkinter + tcl/tk data (highly recommended for pyautogui)
try:
    tcl_datas = collect_data_files("tkinter")
    datas.extend(tcl_datas)
except Exception:
    pass
try:
    # Some distributions ship tk/tcl as top level packages
    for p in ("_tkinter", "Tkinter", "tcl", "tk"):
        try:
            datas.extend(collect_data_files(p))
        except Exception:
            pass
except Exception:
    pass

# Extra submodules that often get missed
for mod in ("ctranslate2", "tokenizers", "safetensors", "huggingface_hub"):
    try:
        hiddenimports.extend(collect_submodules(mod))
    except Exception:
        pass

hiddenimports = sorted(set(hiddenimports))

# ------------------------------------------------------------------
# Binaries / shared libs to include explicitly if needed
# (PyInstaller usually auto-detects most via hooks)
# ------------------------------------------------------------------
binaries = []

# ------------------------------------------------------------------
# Excludes to keep size down a bit (optional, be careful)
# ------------------------------------------------------------------
excludes = [
    "matplotlib",
    "jupyter",
    "notebook",
    "IPython",
    "pytest",
    "sphinx",
    # tensorflow if somehow pulled in
    "tensorflow",
    "tensorboard",
]

a = Analysis(
    ["main.py"],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ------------------------------------------------------------------
# One-folder (onedir) build — RECOMMENDED for this project
# Large torch/onnxruntime/faster-whisper content makes onefile very slow
# to build and slow to start (it extracts to temp every run).
# ------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="RishiAI.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="RI",
)

# ------------------------------------------------------------------
# ONEFILE alternative (uncomment if you really want a single executable):
#
# exe_onefile = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     [],
#     name="RI",
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=False,
#     console=True,
#     icon="RishiAI.ico",
# )
#
# Note: onefile builds for this app can take 10-20+ minutes and produce
# a 2GB+ binary that extracts slowly on every launch.
# ------------------------------------------------------------------
