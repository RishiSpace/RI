# Rishi Intelligence

## Overview

RishiAI is a voice-activated command execution system that uses speech recognition to listen for activation phrases and commands. It integrates with various systems and performs tasks based on recognized commands. The system supports both Windows and Linux/Mac operating systems, leveraging the Groq API for command generation and PyAutoGUI for GUI interactions.

## Features

- **Voice Activation:** Recognizes specific phrases to activate listening for further commands.
- **Cross-Platform Support:** Executes commands for both Windows and Linux/Mac systems.
- **Sound Notifications:** Plays sound effects to indicate command recognition and completion.
- **GUI Interactions:** Uses PyAutoGUI to handle tasks that involve GUI elements.
- **Logging:** Captures and logs command execution results and errors.
- **Dynamic Command Generation:** Uses the Groq API to generate commands based on system information and task descriptions.

## Installation and Setup

1. **Download the Executable:**

   Download the latest executable file for your operating system from the [releases](https://github.com/RishiSpace/RishiAI/releases) page.

2. **Configure API Key:**

   Create a file named `AI_Creds.py` in the same directory as the executable and add the following content:

   ```python
   GROQ_API_KEY = '<your-groq-api-key>'
   ```

   Make sure to replace `<your-groq-api-key>` with your actual Groq API key.

3. **Prepare Sound Files:**

   Ensure that the sound files `ls.wav` and `le.wav` are available in the `aud` directory. These files are used for activation and completion sounds. If these files are not included in the download, place them in the `aud` directory manually.

## Usage

### Running the System

To start the RishiAI system, simply run the executable file you downloaded:

- **On Windows:** Double-click the `.exe` file.
- **On Linux/Mac:** Use the terminal to navigate to the directory containing the executable and run it:

  ```bash
  ./<executable-name>
  ```

  Replace `<executable-name>` with the name of the downloaded executable file.

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

Contributions are welcome! Please contact the project maintainers if you wish to contribute.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](LICENSE) file for details.
