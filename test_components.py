
import os
import sys
import ollama
import pyttsx3
import whisper
import speech_recognition as sr

def test_ollama():
    print("Testing Ollama connection...")
    try:
        models = ollama.list()
        print("Ollama connection successful.")
        return True
    except Exception as e:
        print(f"Ollama connection failed: {e}")
        return False

def test_whisper():
    print("Testing Whisper model loading...")
    try:
        model = whisper.load_model("small")
        print("Whisper model loaded successfully.")
        return True
    except Exception as e:
        print(f"Whisper load failed: {e}")
        return False

def test_tts():
    print("Testing TTS...")
    try:
        engine = pyttsx3.init()
        engine.say("Testing voice system.")
        engine.runAndWait()
        print("TTS successful.")
        return True
    except Exception as e:
        print(f"TTS failed: {e}")
        return False

if __name__ == "__main__":
    tests = [test_ollama, test_whisper, test_tts]
    results = []
    for test in tests:
        results.append(test())
    
    if all(results):
        print("All components verified!")
    else:
        print("Some components failed.")
