import shutil
import argparse
import os
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


def prepare_audio_with_silence(timer_duration, alarm_duration, alarm_sound_path, sound_folder):
    """
    Prepares an audio file with silence matching the timer duration 
    and adds the alarm sound at the end.
    - `duration`: Duration of the timer in seconds.
    - `alarm_duration`: Duration of the alarm sound in seconds.
    - `alarm_sound_path`: Path to the alarm sound file.
    - `sound_folder`: Folder where temporary audio files will be stored.
    - `background_music_path`: Path to music background.
    """
    silence = AudioSegment.silent(duration=timer_duration * 1000)

    if alarm_sound_path == "alarm.mp3":
        alarm_sound_path = generate_alarm_sound(sound_folder, duration=alarm_duration)
    alarm = AudioSegment.from_file(alarm_sound_path)

    combined_audio = silence + alarm
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

def generate_timer_video(duration, output_video, frame_rate=24, alarm_sound="alarm.mp3", alarm_duration=5):
    """
    Generate a video from timer images and add alarm sound when timer reaches zero.
    - `duration`: Timer duration in seconds.
    - `output_video`: Path to the output video file.
    - `frame_rate`: Frames per second for the video.
    - `alarm_sound`: Path to the alarm sound file.
    - `alarm_duration`: Duration of the alarm sound in seconds.    
    """
    frames_folder = "timer_frames"
    sound_folder = "sounds"

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

    clip = ImageSequenceClip(frame_files, fps=frame_rate)

    audio_with_alarm = prepare_audio_with_silence(duration, alarm_duration, alarm_sound, sound_folder)
    audio_clip = AudioFileClip(audio_with_alarm)
    clip = clip.set_audio(audio_clip)

    clip.write_videofile(output_video, codec="libx264")
    shutil.rmtree(sound_folder, ignore_errors=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Timer video generator.")
    parser.add_argument("-m", "--minutes", type=int, default=0, help="Timer minutes.")
    parser.add_argument("-s", "--seconds", type=int, default=0, help="Timer seconds.")
    parser.add_argument("-a", "--alarm", type=str, default="alarm.mp3", help="Alarm audio file.")
    parser.add_argument("-o", "--outputfile", type=str, default="timer.mp4", help="Output filename.")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    timer_duration = args.minutes * 60 + args.seconds
    FILENAME = args.outputfile
    try:
        generate_timer_video(duration=timer_duration, output_video=FILENAME, alarm_sound=args.alarm)
        logger.info(f"🎥 Generated video: {FILENAME}")
    except Exception as e:
        logger.error(f"❌ Error generating video: {str(e)}")
