# Audio Recorder and Transcriber

This repository contains two Python scripts designed for recording audio and transcribing it using the Whisper model. The scripts provide a simple way to start and stop audio recording using a keyboard shortcut, and then transcribe the audio either locally using the Whisper model or through the OpenAI API. It is also possible to use scripts to transcibe files. 

## Features

- **Audio Recording**: Both scripts allow audio recording with a simple keyboard shortcut.
- **File Upload**: Both scripts also allow to transcribe audio files.
- **Transcription**: The audio can be transcribed using Whisper:
  - The first script uses a local Whisper model.
  - The second script uses OpenAI's Whisper API.
- **Clipboard Copying**: Transcribed text is automatically copied to the clipboard.
- **Notification Sound**: A sound signal plays when transcription is done and transcribed text is copied to the clipboard.

## Requirements

### Common Requirements
- Python 3.8 or later
- [PyAudio](https://pypi.org/project/PyAudio/)
- [Wave](https://docs.python.org/3/library/wave.html)
- [Whisper](https://github.com/openai/whisper) (for the local model)
- [Pyperclip](https://pypi.org/project/pyperclip/)
- [Pynput](https://pypi.org/project/pynput/)
- [Sounddevice](https://pypi.org/project/sounddevice/)
- [FFmpeg](https://ffmpeg.org/) (must be installed and accessible via PATH)

### Additional Requirements for OpenAI API Version
- [Requests](https://pypi.org/project/requests/)

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/polina-raznitsyna/audio-to-text-mac.git
    cd audio-to-text-mac
    ```

2. Install the required packages:
    ```bash
    pip install pyaudio wave whisper pyperclip pynput sounddevice requests
    ```

3. Ensure FFmpeg is installed and accessible. You can install it via Homebrew:
    ```bash
    brew install ffmpeg
    ```

## Usage

### 1. Local Whisper Model (`local_whisper.py`)

This script records audio and transcribes it using the local Whisper model.

#### How to Use

- Start the script with the desired Whisper model (possible options are tiny, small, medium, large; the default model is set to medium):
    ```bash
    python local_whisper.py --model medium
    ```
- To record audio, press `Command + E` on macOS.
- Press the same shortcut to stop recording and start transcription.
- The transcribed text will be copied to the clipboard.
- Script keeps working until you stop it with `Control + C`, you can record and transcribe audio as many times as you want while script is running.

- Alternalively, you can start the script with tag --file. The script will transcribe file, copy transcibed text to the clipboard and stop running:
    ```bash
    python local_whisper.py --model medium --file path/to/your/file.wav
    ```
- If file is inside Downloads folder on Mac, you can simply add filename after --file tag:
   ```bash
    python local_whisper.py --model medium --file file.wav
    ```
- If file is not inside Downloads folder, you should add complete file path. 

### 2. OpenAI Whisper API (`api_whisper.py`)

This script uses OpenAI's Whisper API for transcription. It requires internet connection and OpenAI API KEY with positive balance. Note that you will be charged at [current OpenAI API rates](https://openai.com/api/pricing/).

#### How to Use

- Replace `API_KEY` in the script with your OpenAI API key.
- Run the script:
    ```bash
    python api_whisper.py
    ```
- All functionality is the same as in the first script.
- The second script needs 
- Model tags are different (only whisper-1 (which is powered by open source Whisper V2 model) is currently available)

## Differences Between the Two Versions

- **Local Whisper Model (`local_whisper.py`)**: Uses Whisper's local model for transcription. This method is fully offline once the model is downloaded, but may require more setup and has higher system requirements (such as a capable GPU).
  
- **OpenAI Whisper API (`api_whisper.py`)**: Uses OpenAI's Whisper API for transcription. This version is simpler to use and requires fewer local resources but relies on an internet connection and OpenAI API key. It also may incur API usage costs.

## Troubleshooting

- **FFmpeg Not Found**: Ensure FFmpeg is installed and added to your system PATH.
- **Audio Recording Errors**: Check your microphone permissions and ensure that PyAudio is correctly installed.
- **API Errors**: Make sure your OpenAI API key is correct and that you have access to the Whisper API.
