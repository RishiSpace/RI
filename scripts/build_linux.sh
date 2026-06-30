#!/usr/bin/env bash
#
# Build RI Linux binary using PyInstaller
# Run from the project root:
#   bash scripts/build_linux.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

echo "==> Using Python from venv (or active env)"
PY="${PYTHON:-./venv/bin/python}"
if [[ ! -x "$PY" ]]; then
    PY="python3"
fi

echo "==> Cleaning previous builds"
rm -rf build/ dist/ RI.spec.bak 2>/dev/null || true

echo "==> Building with PyInstaller (onedir by default — see RI.spec)"
"$PY" -m PyInstaller RI.spec --clean --noconfirm

echo
if [[ -x "dist/RI/RI" ]]; then
    echo "==> SUCCESS: Linux binary folder created"
    du -sh dist/RI
    ls -lh dist/RI/RI
    echo
    echo "To run (requires Ollama + ri-instruct model):"
    echo "  ./dist/RI/RI"
    echo "  ./dist/RI/RI --mode text"
    echo
    echo "You can zip the entire dist/RI/ folder for distribution."
    echo "Target system still needs runtime libs (tk, portaudio, ffmpeg, espeak-ng etc)."
else
    echo "Build did not produce dist/RI/RI — inspect logs."
    exit 1
fi
