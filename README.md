### README for "Countdown Timer Video Generator"

---

## Description

This script generates a video displaying a countdown timer with an alarm at the end. It uses libraries such as **Pillow**, **moviepy**, and **pydub** to create timer frames, add an alarm sound, and combine everything into a final video.

---

## System Requirements

Before running the script, make sure you meet the following requirements:

### Python Dependencies
- Python 3.8 or higher.
- Required libraries can be installed by running:
  ```bash
  pip install pillow moviepy pydub colorlog
  ```

### System Dependencies
- **FFmpeg**: Required for video and audio processing. Install it according to your operating system:
  - **Ubuntu/Debian**:  
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```
  - **Windows**: Download the executable from [FFmpeg.org](https://ffmpeg.org/download.html) and add it to your `PATH`.
  - **MacOS**:  
    ```bash
    brew install ffmpeg
    ```

---

## Environment Setup

1. **Clone or download this repository.**
   ```bash
   git clone https://github.com/user/timer-generator.git
   cd timer-generator
   ```

2. **Create a virtual environment (optional but recommended).**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/MacOS
   venv\Scripts\activate      # On Windows
   ```

3. **Install dependencies.**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure FFmpeg is installed correctly.**
   Run the following command:
   ```bash
   ffmpeg -version
   ```
   This should display the installed FFmpeg version.

---

## Script Usage

The script runs from the command line and accepts several arguments:

### Basic Syntax
```bash
python timer_generator.py -m <minutes> -s <seconds> -a <alarm_file> -o <output_file>
```

### Available Arguments
- `-m` or `--minutes`: Minutes for the timer (default `0`).
- `-s` or `--seconds`: Seconds for the timer (default `0`).
- `-a` or `--alarm`: Audio file for the alarm (default `alarm.mp3`). If not provided, a default alarm sound will be generated.
- `-o` or `--outputfile`: Name of the generated video file (default `timer.mp4`).

### Example
```bash
python timer_generator.py -m 1 -s 30 -a custom_alarm.wav -o my_timer.mp4
```

This command creates a timer for 1 minute and 30 seconds with the alarm `custom_alarm.wav`, and saves the video as `my_timer.mp4`.

---

## Important Notes

1. **Default Fonts**: The script uses the `DejaVuSans-Bold.ttf` font to render text. If unavailable, a default font will be used.

