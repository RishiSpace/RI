# speech_recognition_tflite.py

import numpy as np
import pyaudio
import tensorflow as tf
from tensorflow.python.platform import gfile

class SpeechRecognitionTFLite:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = self.load_model(model_path)

    def load_model(self, model_path):
        # Load the TFLite model
        model = tf.lite.Interpreter(model_path=model_path)
        model.allocate_tensors()
        return model

    def recognize_speech(self, audio_data):
        # Get the input and output tensors
        input_tensor = self.model.get_input_details()[0]['index']
        output_tensor = self.model.get_output_details()[0]['index']

        # Set the input tensor
        self.model.set_tensor(input_tensor, np.expand_dims(audio_data, 0))

        # Run the model
        self.model.invoke()

        # Get the output tensor
        predictions = self.model.get_tensor(output_tensor)

        # Get the labels
        labels = ["_unknown_", "_silence_", "yes", "no", "up", "down", "left", "right", "on", "off", "stop", "go"]

        # Find the top 1 label
        index = np.argmax(predictions)
        label = labels[index]

        return label

    def listen_and_recognize(self):
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        chunk = 1024
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=chunk)

        # Listen for audio
        audio_data = np.frombuffer(stream.read(chunk), dtype=np.int16)

        # Recognize the speech
        label = self.recognize_speech(audio_data)

        # Close the stream
        stream.stop_stream()
        stream.close()
        audio.terminate()

        return label