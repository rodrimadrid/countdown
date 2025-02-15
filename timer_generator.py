import shutil
import argparse
import os
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, AudioFileClip
from pydub import AudioSegment
from pydub.generators import Sine


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
    Prepares an audio file with silence matching the timer duration and adds the alarm sound at the end.
    - `timer_duration`: Duration of the timer in seconds.
    - `alarm_duration`: Duration of the alarm sound in seconds.
    - `alarm_sound_path`: Path to the alarm sound file.
    - `sound_folder`: Folder where temporary audio files will be stored.
    """
    silence = AudioSegment.silent(duration=timer_duration * 1000)

    if alarm_sound_path == "alarm.mp3":
        alarm_sound_path = generate_alarm_sound(sound_folder, duration=alarm_duration)
    alarm = AudioSegment.from_file(alarm_sound_path)

    combined_audio = silence + alarm
    output_path = os.path.join(sound_folder, "final_audio_with_alarm.wav")
    combined_audio.export(output_path, format="wav")
    return output_path


def generate_timer_frames(duration, frame_rate, output_folder, alarm_duration=5):
    """
    Generates a sequence of images representing the timer.
    - `duration`: Timer duration in seconds.
    - `frame_rate`: Frames per second.
    - `output_folder`: Folder where frames will be stored.
    - `alarm_duration`: Duration of alarm frames in seconds.
    """
    os.makedirs(output_folder, exist_ok=True)
    font_size = 120
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        print("⚠️ The specified font could not be found. Using default font.")
        font = ImageFont.load_default()

    total_frames = int(duration * frame_rate) +1

    print("Building frames...")
    for frame in range(total_frames):
        img = Image.new("RGB", (1280, 720), color="black")
        draw = ImageDraw.Draw(img)
        current_time = duration - (frame / frame_rate)
        if current_time < 0:
            current_time = 0
        minutes, seconds = divmod(int(current_time), 60)
        time_text = f"{minutes:02}:{seconds:02}"
        text_width, text_height = draw.textsize(time_text, font=font)
        position = ((1280 - text_width) // 2, (720 - text_height) // 2)
        draw.text(position, time_text, fill="white", font=font)
        img.save(os.path.join(output_folder, f"frame_{frame:04d}.png"))

    if current_time == 0:
        for frame in range(total_frames, total_frames + frame_rate * alarm_duration):
            img = Image.new("RGB", (1280, 720), color="black")
            draw = ImageDraw.Draw(img)
            time_text = "00:00"
            text_width, text_height = draw.textsize(time_text, font=font)
            position = ((1280 - text_width) // 2, (720 - text_height) // 2)
            draw.text(position, time_text, fill="red", font=font)
            img.save(os.path.join(output_folder, f"frame_{frame:04d}.png"))


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

    try:
        generate_timer_frames(duration, frame_rate, frames_folder, alarm_duration)

        total_frames = int(duration * frame_rate)
        frame_files = [
            os.path.join(frames_folder, f"frame_{i:04d}.png") for i in range(total_frames)
        ]

        frame_files += [
            os.path.join(frames_folder, f"frame_{i:04d}.png")
            for i in range(total_frames, total_frames + frame_rate * alarm_duration)
        ]

        clip = ImageSequenceClip(frame_files, fps=frame_rate)

        audio_with_alarm = prepare_audio_with_silence(duration, alarm_duration, alarm_sound, sound_folder)
        audio_clip = AudioFileClip(audio_with_alarm)
        clip = clip.set_audio(audio_clip)

        clip.write_videofile(output_video, codec="libx264")
    finally:
        shutil.rmtree(frames_folder, ignore_errors=True)
        shutil.rmtree(sound_folder, ignore_errors=True)

def parse_args():
    """
    Defines command line arguments and processes them.
    """
    parser = argparse.ArgumentParser(description="Countdown Timer Video Generator.")

    parser.add_argument("-m", "--minutes", type=int, default=0, help="Timer minutes.")
    parser.add_argument("-s", "--seconds", type=int, default=0, help="Timer seconds.")
    parser.add_argument("-a", "--alarm", type=str, default="alarm.mp3", help="Alarm audio file.")
    parser.add_argument("-o", "--outputfile", type=str, default="timer.mp4", help="Output filename")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    timer_duration = args.minutes * 60 + args.seconds
    FILENAME = args.outputfile

    generate_timer_video(duration=timer_duration, output_video=FILENAME, alarm_sound=args.alarm)
    print(f"🎥 Generated video: {FILENAME}")
