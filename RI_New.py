
import os
import sys
import subprocess
import json
import threading
import time
import requests
import pyttsx3
import speech_recognition as sr
import whisper
import numpy as np
import ollama
import tempfile
import torch
import ctypes
import platform
from contextlib import contextmanager

# --- ALSA Error Suppression ---
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)

def py_error_handler(filename, line, function, err, fmt):
    pass

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)

@contextmanager
def no_alsa_err():
    try:
        asound = ctypes.cdll.LoadLibrary('libasound.so')
        asound.snd_lib_error_set_handler(c_error_handler)
        yield
        asound.snd_lib_error_set_handler(None)
    except:
        yield

# --- Configuration ---
OLLAMA_MODEL = "lfm2.5-thinking:1.2b"
WHISPER_MODEL_SIZE = "small"
WAKE_WORDS = ["ri", "r i", "hey ri", "hi ri","yo ri","yo r i","yo r i","hey R.I","R.I","Agent R.I","chipi","computer","Hello Computer"]
QUIT_WORDS = ["rishi quit", "quit rishi", "shut down rishi", "stop listening"]

class VoiceInterface:
    def __init__(self):
        print(f"Loading Whisper model: {WHISPER_MODEL_SIZE}...")
        self.whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
        self.recognizer = sr.Recognizer()
        
        # Initialize TTS engine safely
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 170)
            # Try to pick a decent voice
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if "english" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"Warning: TTS Engine failed to initialize: {e}")
            self.engine = None

    def speak(self, text):
        """Synthesize text to speech."""
        print(f"RI says: {text}")
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")

    def listen(self, timeout=None, phrase_time_limit=None, calibrate=False):
        """Listen for audio and return the recognizer audio object."""
        with no_alsa_err():
            with sr.Microphone() as source:
                if calibrate:
                    print("Calibrating background noise...")
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("Listening...")
                try:
                    audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                    return audio
                except sr.WaitTimeoutError:
                    return None
                except Exception as e:
                    print(f"Microphone error: {e}")
                    return None

    def transcribe(self, audio):
        """Transcribe audio using local Whisper model."""
        if audio is None:
            return ""
        
        try:
            # Save audio to a temporary wav file for Whisper
            # delete=False is redundant if we handle it, but required for Windows compat usually. 
            # On Linux NamedTemporaryFile works fine.
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
                temp_wav.write(audio.get_wav_data())
                temp_wav_path = temp_wav.name

            # Transcribe
            # IMPORTANT: fp16=False prevents NaN on CPU/some GPUs
            result = self.whisper_model.transcribe(temp_wav_path, fp16=False)
            text = result["text"].strip().lower()
            
            # Clean up
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            return text
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

class OSTools:
    """Defines tools for controlling the OS."""
    
    @staticmethod
    def get_tool_definitions():
        return [
            {
                'type': 'function',
                'function': {
                    'name': 'execute_shell_command',
                    'description': 'Execute a shell command on the host Linux OS. Use this to list files, read files, move files, etc.',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'command': {
                                'type': 'string',
                                'description': 'The shell command to execute (e.g., ls -la, cat file.txt)'
                            }
                        },
                        'required': ['command']
                    }
                }
            },
            {
                'type': 'function',
                'function': {
                    'name': 'get_time',
                    'description': 'Get the current system time',
                    'parameters': {
                        'type': 'object',
                        'properties': {},
                    }
                }
            }
        ]

    def execute_shell_command(self, command):
        """Executes a shell command."""
        print(f"Executing command via Tool: {command}")
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            output = result.stdout
            if result.stderr:
                output += f"\nError: {result.stderr}"
            return output.strip() or "Command executed successfully (no output)."
        except Exception as e:
            return f"Failed to execute command: {e}"

    def get_time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

def get_system_context():
    """Gather system details to provide context to the LLM."""
    try:
        user = os.getlogin()
    except Exception:
        user = "unknown"
    
    os_name = platform.system()
    os_release = platform.release()
    os_version = platform.version()
    
    # Detect Linux Distribution
    distro_name = ""
    try:
        import distro
        distro_name = distro.name(pretty=True)
    except ImportError:
        # Fallback if distro lib not installed (it wasn't in requirements, but we can try reading /etc/os-release or just generic)
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro_name = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            pass

    # Detect DE/WM
    desktop = os.environ.get('XDG_CURRENT_DESKTOP') or os.environ.get('DESKTOP_SESSION') or "Unknown"
    
    # Shell
    shell = os.environ.get('SHELL', '/bin/bash')

    context = f"""
    System Information:
    - OS: {os_name} {os_release}
    - Distro: {distro_name}
    - User: {user}
    - Desktop Environment: {desktop}
    - Shell: {shell}
    - Date/Time: {time.strftime("%Y-%m-%d %H:%M:%S")}
    """
    return context.strip()

class RIAssistant:
    def __init__(self):
        self.voice = VoiceInterface()
        self.tools = OSTools()
        
        sys_context = get_system_context()
        print(f"Loaded System Context:\n{sys_context}\n")
        
        self.messages = [
            {"role": "system", "content": f"You are RI, an intelligent assistant running on a Linux system. \n{sys_context}\n\nYou can control the operating system using tools. When asked to do something, use the provided tools.\nIMPORTANT: Adapting to the specific Desktop Environment (e.g., GNOME, KDE, i3) is critical for commands like locking the screen, changing volume, etc.\nBe concise in your voice responses. Do not include <think> tags in your spoken response logic, but you can use them for internal reasoning. If you receive tool outputs, interpret them for the user."}
        ]
        self.check_ollama()

    def check_ollama(self):
        """Checks if Ollama model is available, pulls if not."""
        print(f"Checking for model {OLLAMA_MODEL}...")
        try:
            # Simple check via list
            try:
                list_response = ollama.list()
                # Handle response format variations (object vs dict)
                if hasattr(list_response, 'models'):
                    models = list_response.models
                elif isinstance(list_response, dict) and 'models' in list_response:
                    models = list_response['models']
                else:
                    models = [] # Fallback
                
                # If models is a list of objects, convert to list of names
                model_names = []
                for m in models:
                    if isinstance(m, dict):
                        model_names.append(m.get('name', ''))
                    elif hasattr(m, 'model'):
                         model_names.append(m.model)
                    elif hasattr(m, 'name'):
                         model_names.append(m.name)
                         
                found = any(OLLAMA_MODEL in name for name in model_names)
            except Exception as e:
                print(f"Error listing models: {e}. Assuming not found.")
                found = False

            if not found:
                print(f"Model {OLLAMA_MODEL} not found or check failed. Attempting to pull... (this may take a while)")
                text = ""
                # Streaming pull to show progress
                for progress in ollama.pull(OLLAMA_MODEL, stream=True):
                    if 'status' in progress:
                        print(f"Pulling: {progress['status']}", end='\r')
                print("\nModel pull complete/ready.")
            
            # Preload/Warmup the model
            print(f"Preloading {OLLAMA_MODEL} into VRAM...")
            ollama.chat(
                model=OLLAMA_MODEL, 
                messages=[{'role': 'user', 'content': 'hi'}], 
                options={'num_gpu': 999}
            )
            print("Model loaded.")

        except Exception as e:
            print(f"Critical Error connecting to Ollama: {e}. Is 'ollama serve' running?")

    def process_user_input(self, text):
        if not text:
            return

        print(f"User Transcribed: {text}")
        self.messages.append({"role": "user", "content": text})
        
        self.run_generation_loop()

    def run_generation_loop(self):
        """Runs the LLM generation, handles tool calls, and responds."""
        try:
            print("Thinking...")
            response = ollama.chat(
                model=OLLAMA_MODEL,
                messages=self.messages,
                tools=self.tools.get_tool_definitions(),
                options={
                    "num_gpu": 999, # Request max layers on GPU
                    "temperature": 0.7
                }
            )
            
            message = response['message']
            self.messages.append(message)

            if message.get('tool_calls'):
                for tool in message['tool_calls']:
                    function_name = tool['function']['name']
                    arguments = tool['function']['arguments']
                    
                    print(f"Tool Call: {function_name}({arguments})")
                    
                    if hasattr(self.tools, function_name):
                        func = getattr(self.tools, function_name)
                        try:
                            tool_result = func(**arguments)
                        except TypeError:
                             # Fallback for empty args
                            tool_result = func()
                    else:
                        tool_result = f"Error: Tool {function_name} not found."
                    
                    print(f"Tool Result: {tool_result}")

                    self.messages.append({
                        'role': 'tool',
                        'content': str(tool_result),
                    })
                
                # Recursive call
                self.run_generation_loop()
            
            else:
                content = message['content']
                clean_content = self.remove_think_tags(content)
                if clean_content:
                    self.voice.speak(clean_content)

        except Exception as e:
            print(f"LLM Error: {e}")
            self.voice.speak("I encountered an error processing that request.")

    def remove_think_tags(self, text):
        import re
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

    def run(self):
        self.voice.speak("System initialized. I am ready.")
        
        import torch
        if torch.cuda.is_available():
            print(f"CUDA Available: {torch.cuda.get_device_name(0)}")
        else:
            print("CUDA NOT detected by PyTorch/Whisper.")
            
        print("RI Assistant Started. Say 'RI' to wake.")
        
        # Initial calibration
        try:
            with no_alsa_err():
                with sr.Microphone() as source:
                   print("Calibrating background noise (1s)...")
                   self.voice.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception:
            pass

        while True:
            # Calibrate=False inside loop to capture speed, relies on initial calibration or per-listen if needed
            audio = self.voice.listen(phrase_time_limit=5)
            if audio:
                text = self.voice.transcribe(audio)
                if not text:
                    continue
                
                print(f"Heard: {text}")
                
                if any(qw in text for qw in QUIT_WORDS):
                    self.voice.speak("Shutting down.")
                    break
                
                if any(ww in text for ww in WAKE_WORDS):
                    self.voice.speak("Yes?")
                    # Longer listen for command
                    command_audio = self.voice.listen(phrase_time_limit=10)
                    command_text = self.voice.transcribe(command_audio)
                    if command_text:
                        self.process_user_input(command_text)
                    else:
                        self.voice.speak("I didn't hear anything.")

if __name__ == "__main__":
    if not os.path.exists("./aud"):
        os.makedirs("./aud")
        
    app = RIAssistant()
    app.run()
