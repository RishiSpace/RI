# RishiAI

## Overview

RishiAI is a voice-activated command execution system that uses speech recognition to listen for activation phrases and commands. It integrates with various systems and performs tasks based on recognized commands. The system supports both Windows and Linux/Mac operating systems, leveraging the Groq API for command generation and PyAutoGUI for GUI interactions.

## Features

- **Voice Activation:** Recognizes specific phrases to activate listening for further commands.
- **Cross-Platform Support:** Executes commands for both Windows and Linux/Mac systems.
- **Sound Notifications:** Plays sound effects to indicate command recognition and completion.
- **GUI Interactions:** Uses PyAutoGUI to handle tasks that involve GUI elements.
- **Logging:** Captures and logs command execution results and errors.
- **Dynamic Command Generation:** Uses the Groq API to generate commands based on system information and task descriptions.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create and Activate a Virtual Environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```


4. **Configure API Key:**

   Create a file named `AI_Creds.py` in the project root directory and add the following content:

   ```python
   GROQ_API_KEY = '<your-groq-api-key>'
   ```

## Usage

### Running the System

To start the RishiAI system, run the following command:

```bash
python <script-name>.py
```

Replace `<script-name>` with the name of the Python script file.

### How It Works

1. **Listening for Activation Phrases:**

   The system listens for specific activation phrases. When an activation phrase is detected, it plays a sound and starts listening for a command.

2. **Processing Commands:**

   Once a command is received, the system uses the Groq API to generate appropriate commands based on the system type and the task description.

3. **Executing Commands:**

   Commands are executed based on the operating system. The system handles both non-GUI commands and GUI interactions (e.g., typing text or clicking on screen coordinates).

4. **Handling Requests for More Information:**

   If the Groq API response requires additional information, the system prints a request for more details. Users should provide this information for accurate command generation.

5. **Logging:**

   Command outputs and errors are logged in `terminal_output.log`.

## Configuration

- **Sound Files:**
  
  Ensure the sound files `ls.wav` and `le.wav` are present in the `aud` directory for the activation and completion sounds.

- **API Configuration:**

  Update `AI_Creds.py` with your Groq API key.

## Commands and GUI Interactions

- **Command Format:**
  
  Commands are executed directly in PowerShell (Windows) or Bash (Linux/Mac). For GUI interactions, use commands like "type" or "click" with appropriate parameters.

- **Example Commands:**
  
  - **Windows/PowerShell:** `Get-ChildItem`
  - **Linux/Bash:** `ls -l`
  - **GUI Interaction (Typing):** `type Hello, World!`
  - **GUI Interaction (Clicking):** `click 100 200`

## Troubleshooting

- **Common Issues:**
  - **Unintelligible Audio:** Ensure you are in a quiet environment and speak clearly.
  - **Request Errors:** Verify network connectivity and API key.

- **Logging:**
  - Check `terminal_output.log` for detailed logs of command execution and errors.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](LICENSE) file for details.
