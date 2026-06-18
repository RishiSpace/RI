import os

# --- LLM ---
OLLAMA_MODEL = os.environ.get("RI_MODEL", "ri-instruct:latest")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_OPTIONS = {
    "num_gpu": 999,
    "temperature": 0.5,
    "num_ctx": 4096,
    "top_p": 0.9,
}

# Disable model thinking/reasoning for faster responses (supported by many instruct models)
# Set RI_THINK=1 to enable, RI_THINK=low/medium/high for levels
_think_env = os.environ.get("RI_THINK", "").lower().strip()
if _think_env in ("1", "true", "yes", "on"):
    OLLAMA_THINK = True
elif _think_env in ("0", "false", "no", "off", ""):
    OLLAMA_THINK = False
else:
    OLLAMA_THINK = _think_env  # e.g. "low", "medium", "high"

# --- Speech ---
WHISPER_BACKEND = os.environ.get("RI_WHISPER", "faster")  # faster | openai
WHISPER_WAKE_MODEL = os.environ.get("RI_WHISPER_WAKE", "base")
WHISPER_COMMAND_MODEL = os.environ.get("RI_WHISPER_CMD", "small")
TTS_ENGINE = os.environ.get("RI_TTS", "piper")  # piper | edge | espeak | pyttsx3
PIPER_VOICE = os.environ.get("RI_PIPER_VOICE", "en_US-lessac-medium")
EDGE_VOICE = os.environ.get("RI_EDGE_VOICE", "en-US-JennyNeural")
ESPEAK_VOICE = os.environ.get("RI_ESPEAK_VOICE", "en-us")
TTS_RATE = 175
VERBOSE = os.environ.get("RI_VERBOSE", "0") == "1"
HEAR_ECHO = os.environ.get("RI_HEAR_ECHO", "1") != "0"  # print transcribed phrases
MIC_DEVICE_INDEX = int(os.environ["RI_MIC_INDEX"]) if os.environ.get("RI_MIC_INDEX") else None

# --- Agent ---
MAX_HISTORY_MESSAGES = int(os.environ.get("RI_MAX_HISTORY", "30"))
MAX_TOOL_ROUNDS = 12
SHELL_TIMEOUT_SEC = int(os.environ.get("RI_SHELL_TIMEOUT", "120"))
REQUIRE_CONFIRMATION = os.environ.get("RI_REQUIRE_CONFIRM", "1") != "0"

# --- Wake / quit ---
WAKE_WORDS = [
    "ri", "r i", "hey ri", "hi ri", "yo ri", "hey r.i", "r.i",
    "agent r.i", "computer", "hello computer",
]
QUIT_WORDS = ["rishi quit", "quit rishi", "shut down rishi", "stop listening", "exit ri"]
STANDBY_WORDS = [
    "standby", "go to sleep", "sleep", "that's all", "that is all",
    "thank you", "thanks", "goodbye", "bye", "cancel conversation",
]
CONFIRM_WORDS = ["yes", "confirm", "do it", "proceed", "go ahead", "yeah", "yep", "sure"]
DENY_WORDS = ["no", "cancel", "stop", "don't", "nope", "never mind"]

# --- Voice conversation session ---
CONVERSATION_TIMEOUT_SEC = float(os.environ.get("RI_CONV_TIMEOUT", "25"))
CONVERSATION_LISTEN_TIMEOUT = float(os.environ.get("RI_CONV_LISTEN", "12"))
CONVERSATION_PHRASE_LIMIT = float(os.environ.get("RI_CONV_PHRASE", "15"))
CONVERSATION_MAX_TURNS = int(os.environ.get("RI_CONV_MAX_TURNS", "15"))

# --- Continuous mic (always-on wake listening) ---
CONTINUOUS_ENERGY_THRESHOLD = float(os.environ.get("RI_MIC_THRESHOLD", "300"))
CONTINUOUS_PAUSE_SEC = float(os.environ.get("RI_MIC_PAUSE", "0.8"))
CONTINUOUS_MAX_PHRASE_SEC = float(os.environ.get("RI_MIC_MAX_PHRASE", "18"))

# --- Paths ---
AUD_DIR = "./aud"
SCREENSHOT_DIR = os.path.expanduser("~/Pictures/RI-Screenshots")