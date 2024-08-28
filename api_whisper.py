import pyaudio
import wave
import threading
import time
import requests
import pyperclip
from pynput import keyboard
import os
import argparse
import sys

# Replace this with your OpenAI API key
API_KEY = ""

# API endpoint for Whisper model
API_URL = "https://api.openai.com/v1/audio/transcriptions"

# Set up the keyboard shortcut
SHORTCUT = {keyboard.Key.cmd, keyboard.KeyCode.from_char('e')}

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WAVE_OUTPUT_FILENAME = "output.wav"
DOWNLOADS_DIR = "/Users/polina_raznisyna/Downloads"

# Define the arguments for command-line execution
parser = argparse.ArgumentParser(description="Audio Recorder and Transcriber using OpenAI API.")
parser.add_argument("--file", type=str, help="Path to an audio file for transcription")
parser.add_argument("--model", type=str, default="whisper-1", help="Model to use for transcription (default: whisper-1)")
args = parser.parse_args()

# Audio Recorder class
class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.frames = []
            threading.Thread(target=self._record).start()

    def stop_recording(self):
        if self.recording:
            self.recording = False

    def _record(self):
        audio = pyaudio.PyAudio()
        try:
            stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK)
            
            print("Recording started")
            while self.recording:
                data = stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
            
            print("Recording stopped")
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

        self.save_audio()

    def save_audio(self):
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print(f"Audio saved as {WAVE_OUTPUT_FILENAME}")

# Function to transcribe audio using OpenAI's API
def transcribe_audio(file_path):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    files = {
        "file": open(file_path, "rb")
    }
    data = {
        "model": args.model
    }
    
    start_time = time.time()
    response = requests.post(API_URL, headers=headers, files=files, data=data)
    end_time = time.time()

    if response.status_code == 200:
        text = response.json().get("text")
        elapsed_time = end_time - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds.")
        return text
    else:
        print(f"Error during transcription: {response.status_code} {response.text}")
        return None

# Function to copy text to clipboard
def copy_text(text):
    if text:
        cleaned_text = text.strip()
        pyperclip.copy(cleaned_text)
        print(f"Text copied to clipboard: {cleaned_text}")
    else:
        print("No text to copy")

# Function to handle transcription and clipboard copying
def process_transcription(file_path):
    text = transcribe_audio(file_path)
    if text:
        copy_text(text)

# Function to get the full file path
def get_file_path(file_name):
    if os.path.isabs(file_name):
        return file_name
    else:
        return os.path.join(DOWNLOADS_DIR, file_name)

recorder = AudioRecorder()
current_keys = set()

def on_press(key):
    if key in SHORTCUT:
        current_keys.add(key)
        if all(k in current_keys for k in SHORTCUT):
            if not recorder.recording:
                print("Starting recording...")
                recorder.start_recording()
            else:
                print("Stopping recording...")
                recorder.stop_recording()
                print("Transcribing...")
                process_transcription(WAVE_OUTPUT_FILENAME)

def on_release(key):
    if key in SHORTCUT:
        current_keys.discard(key)

# If a file is provided, transcribe it and exit
if args.file:
    file_path = get_file_path(args.file)
    if os.path.exists(file_path):
        print(f"Transcribing file: {file_path}")
        process_transcription(file_path)
    else:
        print(f"File not found: {file_path}")
    sys.exit(0)

# If no file is provided, run in normal mode (recording and transcribing)
print(f"Press {'+'.join(str(k).replace('Key.', '') for k in SHORTCUT)} to start/stop recording.")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
