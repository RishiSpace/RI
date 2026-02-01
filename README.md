# Rishi Intelligence (RI)

## Overview

Rishi Intelligence (RI) is a locally-hosted, voice-activated AI assistant designed to control your Operating System. 

**v2 Update**: The system has been completely re-architected to run **100% Locally** using:
- **Ollama**: For the LLM logic (`lfm2.5-thinking:1.2b`).
- **OpenAI Whisper**: For speech-to-text (running locally).
- **Python**: For the core logic and OS interaction.

It allows you to control your PC by speaking natural language commands.

## Features

- **Local & Private**: No data leaves your machine. All processing (Voice & AI) is done on your hardware.
- **Voice Activation**: Wakes up to the phrase **"RI"** (or "Hey RI").
- **OS Awareness**: Automatically detects your OS (Arch Linux, etc.), Desktop Environment (GNOME, KDE), and User to execute the correct commands.
- **Thinking Mode**: The AI "thinks" before acting, ensuring safer and more accurate command execution.
- **MCP-Style Tools**: Uses a structured tool-calling interface to execute shell commands, check time, etc.

## Setup

### Prerequisites
1.  **Ollama**: Install [Ollama](https://ollama.com/) and ensure it is running (`ollama serve`).
2.  **Model**: The script automatically pulls `lfm2.5-thinking:1.2b`.
3.  **Python 3.10+**

### Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/RishiSpace/RI.git
    cd RI
    ```

2.  **Install System Dependencies** (Arch Linux Example):
    ```bash
    sudo pacman -S portaudio ffmpeg espeak-ng xclip
    ```

3.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Assistant**:
    ```bash
    ./venv/bin/python RI_New.py
    ```

2.  **Interact**:
    - **Wake**: Say "**RI**", "**Hey RI**", or "**Computer**".
    - **Command**: Say "List files in this directory", "Lock the PC", "What time is it?".
    - **Quit**: Say "Rishi Quit".

## Legacy Version

The previous version of RI (using Groq API and remote speech recognition) has been moved to the `Archive/` directory.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](LICENSE) file for details.
