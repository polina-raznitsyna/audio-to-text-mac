import pyaudio
import wave
import threading
import time
import requests
import pyperclip
from pynput import keyboard
import os
import argparse
import rumps
from pydub.utils import mediainfo
from AppKit import NSApplication, NSApp

# Replace this with your OpenAI API key
API_KEY = ""

# API endpoint for Whisper model
API_URL = "https://api.openai.com/v1/audio/transcriptions"

# Set up the keyboard shortcut
SHORTCUT = {keyboard.Key.cmd, keyboard.KeyCode.from_char('e')}

# Updated audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 21845  # New sample rate
RECORD_SECONDS = 600  # 10 minutes in seconds
WAVE_OUTPUT_FILENAME = "output.wav"
DOWNLOADS_DIR = "/Users/polina_raznisyna/Downloads"

# Define the arguments for command-line execution
parser = argparse.ArgumentParser(description="Audio Recorder and Transcriber using OpenAI API.")
parser.add_argument("--file", type=str, help="Path to an audio file for transcription")
parser.add_argument("--model", type=str, default="whisper-1", help="Model to use for transcription (default: whisper-1)")
args = parser.parse_args()

# Cost per minute for Whisper API
COST_PER_MINUTE = 0.006  # Example: $0.006 per minute of audio

# Audio Recorder class
class AudioRecorder:
    def __init__(self, app):
        self.recording = False
        self.frames = []
        self.app = app
        self.start_time = None

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.frames = []
            self.start_time = time.time()
            threading.Thread(target=self._record).start()

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.app.title = ""  # Clear the timer from the menu bar
            time.sleep(1)  # Small delay to ensure the file is saved

    def _record(self):
        audio = pyaudio.PyAudio()
        try:
            stream = audio.open(format=FORMAT, channels=CHANNELS,
                                rate=RATE, input=True,
                                frames_per_buffer=CHUNK)

            print("Recording started")
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                if not self.recording:
                    break
                data = stream.read(CHUNK, exception_on_overflow=False)
                self.frames.append(data)
                
                # Update timer in menu bar
                elapsed_time = int(time.time() - self.start_time)
                minutes, seconds = divmod(elapsed_time, 60)
                self.app.title = f"{minutes:02}:{seconds:02}"

            print("Recording stopped (10 minutes limit reached)" if self.recording else "Recording stopped")
            self.recording = False
            self.app.title = ""  # Clear the timer from the menu bar
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
        if os.path.exists(WAVE_OUTPUT_FILENAME):
            print(f"Audio saved as {WAVE_OUTPUT_FILENAME}")
        else:
            print(f"Failed to save audio as {WAVE_OUTPUT_FILENAME}")

# Function to get the duration of the audio file in minutes
def get_audio_duration_minutes(file_path):
    try:
        info = mediainfo(file_path)
        duration = float(info['duration'])  # Duration in seconds
        duration_minutes = round(duration / 60, 2)  # Duration in minutes, rounded to 2 decimals
        print(f"Audio duration: {duration_minutes:.2f} minutes")
        return duration_minutes
    except Exception as e:
        print(f"Error calculating duration of audio: {e}")
        return 0

# Function to transcribe audio using OpenAI's API
def transcribe_audio(file_path):
    try:
        print(f"Attempting to transcribe file at: {file_path}")
        with open(file_path, "rb") as f:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
            }
            files = {
                "file": f
            }
            data = {
                "model": args.model
            }

            start_time = time.time()
            response = requests.post(API_URL, headers=headers, files=files, data=data)
            end_time = time.time()

            if response.status_code == 200:
                response_data = response.json()
                text = response_data.get("text")
                elapsed_time = end_time - start_time

                # Calculate cost based on duration
                duration_minutes = get_audio_duration_minutes(file_path)
                cost = duration_minutes * COST_PER_MINUTE
                print(f"Transcription completed in {elapsed_time:.2f} seconds.")
                print(f"Estimated cost: ${cost:.4f}")

                return text
            else:
                print(f"Error during transcription: {response.status_code} {response.text}")
                return None
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Function to copy text to clipboard
def copy_text(text):
    if text:
        cleaned_text = text.strip()
        pyperclip.copy(cleaned_text)
        print(f"Text copied to clipboard: {cleaned_text}")
        # Play sound to indicate completion
        os.system('afplay /System/Library/Sounds/Glass.aiff')
    else:
        print("No text to copy")

# Function to handle transcription and clipboard copying
def process_transcription(file_path):
    if os.path.exists(file_path):
        text = transcribe_audio(file_path)
        if text:
            copy_text(text)
    else:
        print(f"File not found: {file_path}")

# Function to get the full file path
def get_file_path(file_name):
    if os.path.isabs(file_name):
        return file_name
    else:
        return os.path.join(DOWNLOADS_DIR, file_name)

# Headless timer update in the menu bar
class HeadlessTimerApp(rumps.App):
    def __init__(self, recorder):
        super().__init__("", quit_button=None)
        self.recorder = recorder
        self.timer = rumps.Timer(self.update_timer, 1)
        self.timer.start()

    def update_timer(self, _):
        if self.recorder.recording:
            elapsed_time = int(time.time() - self.recorder.start_time)
            minutes, seconds = divmod(elapsed_time, 60)
            self.title = f"{minutes:02}:{seconds:02}"
        else:
            self.title = ""

# Handling keyboard shortcuts
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
            current_keys.clear()  # Clear keys after processing

def on_release(key):
    if key in SHORTCUT:
        current_keys.discard(key)

recorder = AudioRecorder(None)
current_keys = set()

# Hide the dock icon
NSApplication.sharedApplication()
NSApp.setActivationPolicy_(1)  # NSApplicationActivationPolicyAccessory

# If a file is provided, transcribe it and exit
if args.file:
    file_path = get_file_path(args.file)
    if os.path.exists(file_path):
        print(f"Transcribing file: {file_path}")
        process_transcription(file_path)
else:
    # Start the Rumps application and keyboard listener
    app = HeadlessTimerApp(recorder)
    recorder.app = app
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        app.run()
        listener.join()
