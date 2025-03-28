import shutil
import argparse
import os
import sys
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, AudioFileClip
from pydub import AudioSegment
from pydub.generators import Sine
from logger import Logger

logger = Logger("countdown_generator")

def generate_alarm_sound(output_folder, duration=5, frequency=1000):
    """
    Generate a sine wave alarm sound and save it in the specified folder.
    - `output_folder`: The folder where the sound will be saved.
    - `duration`: Length of the alarm in seconds.
    - `frequency`: Frequency of the beep in Hz (default is 1000Hz).
    """
    os.makedirs(output_folder, exist_ok=True)
    sound_path = os.path.join(output_folder, "alarm_sound.wav")
    beep = Sine(frequency).to_audio_segment(duration=duration * 1000)
    beep.export(sound_path, format="wav")
    return sound_path


def prepare_audio(duration, alarm_duration, alarm_sound_path, sound_folder, background_music_path):
    """
    Prepares an audio file with silence matching the timer duration and adds the alarm sound at the end.
    - `timer_duration`: Duration of the timer in seconds.
    - `alarm_duration`: Duration of the alarm sound in seconds.
    - `alarm_sound_path`: Path to the alarm sound file.
    - `sound_folder`: Folder where temporary audio files will be stored.
    - `background_music_path`: Path to music background.
    """
    if background_music_path:
        bg = AudioSegment.from_file(background_music_path)
        required_ms = duration * 1000
        bg_ms = len(bg)
        if bg_ms < required_ms:
            loops = required_ms // bg_ms + 1
            looped_bg = bg * loops
            bg_segment = looped_bg[:required_ms]
        else:
            bg_segment = bg[:required_ms]
    else:
        bg_segment = AudioSegment.silent(duration=duration * 1000)

    if alarm_sound_path == "alarm.mp3":
        alarm_sound_path = generate_alarm_sound(sound_folder, duration=alarm_duration)
    alarm = AudioSegment.from_file(alarm_sound_path)
    alarm_ms = len(alarm)
    required_alarm_ms = alarm_duration * 1000

    if alarm_ms < required_alarm_ms:
        loops = required_alarm_ms // alarm_ms + 1
        alarm = alarm * loops
    alarm = alarm[:required_alarm_ms]

    combined_audio = bg_segment + alarm
    output_path = os.path.join(sound_folder, "final_audio_with_alarm.wav")
    combined_audio.export(output_path, format="wav")
    return output_path

def generate_frame(seconds, output_folder, font, is_alarm=False):
    """
    Generates a sequence of images representing the timer.
    - `duration`: Timer duration in seconds.
    - `frame_rate`: Frames per second.
    - `output_folder`: Folder where frames will be stored.
    - `alarm_duration`: Duration of alarm frames in seconds.
    """
    mm, ss = divmod(seconds, 60)
    filename = f"frame_{mm:02}{ss:02}.png" if not is_alarm else "frame_0000.png"
    path = os.path.join(output_folder, filename)

    if os.path.exists(path):
        return

    img = Image.new("RGB", (1280, 720), color="black")
    draw = ImageDraw.Draw(img)
    time_text = f"{mm:02}:{ss:02}" if not is_alarm else "00:00"
    text_width, text_height = draw.textsize(time_text, font=font)
    position = ((1280 - text_width) // 2, (720 - text_height) // 2)
    fill_color = "red" if is_alarm else "white"
    draw.text(position, time_text, fill=fill_color, font=font)
    img.save(path)

def load_images_as_numpy(frame_files):
    """Carga imágenes en memoria como arrays NumPy para evitar que MoviePy las procese una por una."""
    return [np.array(Image.open(f)) for f in frame_files]

def generate_timer_video(duration, output_video, frame_rate=24, alarm_sound="alarm.mp3", alarm_duration=5, background_music=None):
    """
    Generate a video from timer images and add alarm sound when timer reaches zero.
    - `duration`: Timer duration in seconds.
    - `output_video`: Path to the output video file.
    - `frame_rate`: Frames per second for the video.
    - `alarm_sound`: Path to the alarm sound file.
    - `alarm_duration`: Duration of the alarm sound in seconds.
    - `background_music`: Path to music background. 
    """
    frames_folder = "timer_frames"
    sound_folder = "sounds"

    base_name, ext = os.path.splitext(output_video)
    n = base_name[-1]
    if n.isdigit():
        file_path = base_name[0:-2] + ext
        if os.path.exists(file_path):
            try:
                shutil.copy(file_path, output_video)
                logger.info(f"✅ File copied successfully: {file_path}")
                return
            except OSError:
                logger.error(f"❌ Failed to copy the video to '{output_video}'.")

    os.makedirs(frames_folder, exist_ok=True)
    os.makedirs(sound_folder, exist_ok=True)

    font_size = 120
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        logger.warning("⚠️ The specified font could not be found. Using default font.")
        font = ImageFont.load_default()

    required_countdown_seconds = list(range(duration, 0, -1))
    missing_countdown_seconds = []
    for second in required_countdown_seconds:
        mm, ss = divmod(second, 60)
        filename = f"frame_{mm:02}{ss:02}.png"
        path = os.path.join(frames_folder, filename)
        if not os.path.exists(path):
            missing_countdown_seconds.append(second)

    alarm_path = os.path.join(frames_folder, "frame_0000.png")
    missing_alarm = not os.path.exists(alarm_path)

    if missing_countdown_seconds or missing_alarm:
        logger.info(f"Generating {len(missing_countdown_seconds)} missing frames...")
        for second in missing_countdown_seconds:
            generate_frame(second, frames_folder, font)
        if missing_alarm:
            generate_frame(0, frames_folder, font, is_alarm=True)

    countdown_frames = []
    for second in required_countdown_seconds:
        mm, ss = divmod(second, 60)
        filename = f"frame_{mm:02}{ss:02}.png"
        path = os.path.join(frames_folder, filename)
        countdown_frames.extend([path] * frame_rate)

    alarm_frames = [alarm_path] * (frame_rate * alarm_duration)
    frame_files = countdown_frames + alarm_frames

    clip = ImageSequenceClip(frame_files, fps=frame_rate, load_images=False)


    audio_with_alarm = prepare_audio(
        duration,
        alarm_duration,
        alarm_sound,
        sound_folder,
        background_music
    )
    audio_clip = AudioFileClip(audio_with_alarm)
    clip = clip.set_audio(audio_clip)
    clip.write_videofile(output_video, codec="libx265")
    shutil.rmtree(sound_folder, ignore_errors=True)

def parse_timer_expression(expression):
    pattern = r'm(\d+)|x(\d+)'
    matches = re.findall(pattern, expression)

    timers = []
    repeat_sequence = []
    repeat_count = 1

    for minutes, repeat in matches:
        if minutes:
            repeat_sequence.append(int(minutes))
        elif repeat:
            repeat_count = int(repeat)
            timers.extend(repeat_sequence * repeat_count)
            repeat_sequence = []

    timers.extend(repeat_sequence)

    file_names = []
    counter = {}
    for minutes in timers:
        base_name = f"timer_{minutes}m"
        if base_name in counter:
            counter[base_name] += 1
            file_names.append(f"{base_name}_{counter[base_name]}.mp4")
        else:
            counter[base_name] = 1
            file_names.append(f"{base_name}.mp4")

    return list(zip(timers, file_names))

def parse_args():
    parser = argparse.ArgumentParser(description="Timer video generator.")
    parser.add_argument("-m", "--minutes", type=int, default=0, help="Timer minutes.")
    parser.add_argument("-s", "--seconds", type=int, default=0, help="Timer seconds.")
    parser.add_argument("-a", "--alarm", type=str, default="alarm.mp3", help="Alarm audio file.")
    parser.add_argument("-o", "--outputfile", type=str, default="timer.mp4", help="Output filename.")
    parser.add_argument("-bm", "--backgroundmusic", type=str, help="Background music file.")
    parser.add_argument("-e", "--expression", type=str, help="Timer expression format (e.g., 'm25m5x2m15' where 'mX' sets minutes and 'xY' sets repetitions).")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    timer_duration = args.minutes * 60 + args.seconds
    FILENAME = args.outputfile
    try:
        if args.expression is None:
            generate_timer_video(
                duration=timer_duration,
                output_video=FILENAME,
                alarm_sound=args.alarm,
                background_music=args.backgroundmusic
              )
            logger.info(f"🎥 Generated video: {FILENAME}")
        else:
            timers = parse_timer_expression(args.expression)
            if not timers:
                logger.error("❌ No valid timers parsed from expression.")
                sys.exit(1)
            for duration, filename in timers:
                generate_timer_video(
                    duration=duration * 60,
                    output_video=filename,
                    alarm_sound=args.alarm,
                    background_music=args.backgroundmusic
                  )
                logger.info(f"🎥 Generated video: {filename}")
    except Exception as e:
        logger.error(f"❌ Error generating video: {str(e)}")
