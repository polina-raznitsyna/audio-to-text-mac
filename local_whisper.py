import pyaudio
import wave
import threading
import time
import whisper
import pyperclip
from pynput import keyboard
import subprocess
import os
import sounddevice as sd
import numpy as np
import argparse
import sys
import warnings

# Suppress UserWarning and FutureWarning
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False

if not check_ffmpeg():
    print("FFmpeg not found. Please install FFmpeg and add it to PATH.")
    print("You can install FFmpeg using: brew install ffmpeg")
    exit(1)

# Command-line arguments
parser = argparse.ArgumentParser(description="Audio Recorder and Transcriber.")
parser.add_argument("--model", type=str, default="medium", help="Choose Whisper model (small, medium, large, etc.)")
parser.add_argument("--file", type=str, help="Path to the audio file for transcription")
args = parser.parse_args()

# Keyboard shortcut Cmd+E
SHORTCUT = {keyboard.Key.cmd, keyboard.KeyCode.from_char('e')}

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WAVE_OUTPUT_FILENAME = "output.wav"
DOWNLOADS_DIR = "/Users/polina_raznisyna/Downloads"  # Your specified path

# Whisper settings
WHISPER_MODEL = args.model

# Notification sound settings
PLAY_SOUND = True

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

def transcribe_audio(file_path):
    try:
        model = whisper.load_model(WHISPER_MODEL)
        result = model.transcribe(file_path)
        return result["text"]
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def copy_text(text):
    if text:
        cleaned_text = text.strip()
        pyperclip.copy(cleaned_text)
        print(f"Text copied to clipboard. Use Cmd+V to paste.")
        print(f"Transcribed text: {cleaned_text}")
    else:
        print("No text to copy")

def play_notification_sound():
    if PLAY_SOUND:
        frequency = 440
        duration = 0.1
        samples = np.arange(int(duration * RATE)) / RATE
        waveform = np.sin(2 * np.pi * frequency * samples)
        sd.play(waveform, RATE)
        sd.wait()
        time.sleep(0.1)
        sd.play(waveform, RATE)
        sd.wait()

def get_file_path(file_name):
    if os.path.isabs(file_name):
        return file_name
    else:
        return os.path.join(DOWNLOADS_DIR, file_name)

def process_transcription(file_path):
    start_time = time.time()
    text = transcribe_audio(file_path)
    if text:
        copy_text(text)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Transcription and copying time: {elapsed_time:.2f} seconds.")
        play_notification_sound()
    else:
        print("Failed to retrieve text")

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

# If a file is provided, perform transcription and exit
if args.file:
    file_path = get_file_path(args.file)
    if os.path.exists(file_path):
        print(f"Transcribing file: {file_path}")
        process_transcription(file_path)
    else:
        print(f"File not found: {file_path}")
    sys.exit(0)

# If no file is provided, work in standard mode
print(f"Press {'+'.join(str(k).replace('Key.', '') for k in SHORTCUT)} to start/stop recording.")
print(f"Using Whisper model: {WHISPER_MODEL}")

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
