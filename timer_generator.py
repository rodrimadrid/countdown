import shutil
import argparse
import os
import sys
import re
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, VideoClip
from pydub import AudioSegment
from pydub.generators import Sine
from constants import RESOLUTION, FONT_PATH, FONT_SIZE
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

    size = (1280, 720)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    time_text = f"{mm:02}:{ss:02}" if not is_alarm else "00:00"
    text_width, text_height = draw.textsize(time_text, font=font)
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)

    padding = 20
    draw.rectangle([
        position[0] - padding,
        position[1] - padding,
        position[0] + text_width + padding,
        position[1] + text_height + padding
    ], fill=(0, 0, 0, 160))

    draw.text(position, time_text, fill="red" if is_alarm else "white", font=font)
    img.save(path)



def reuse_video(video_path):
    """
    Reuses a previously created timer video if it exists.
    Assumes video files follow the format 'timer_<N>m.mp4' or 'timer_<N>m_<R>.mp4'.
    If the video is a repetition (e.g., 'timer_5m_2.mp4'), it tries to copy the base version
    (e.g., 'timer_5m.mp4').
    - `video_path`(str): Path where the video should be reused/copied to.
    Returns:
        bool: True if the video was copied from a base file, False otherwise.
    """
    base_name, ext = os.path.splitext(os.path.basename(video_path))

    match = re.match(r'(timer_\d+m)(?:_\d+)?$', base_name)
    if match:
        base_filename = f"{match.group(1)}{ext}"
        source_path = os.path.join(os.path.dirname(video_path), base_filename)
        if os.path.exists(source_path):
            try:
                shutil.copy(source_path, video_path)
                logger.info(f"✅ Reused video: {source_path} → {video_path}")
                return True
            except OSError as e:
                logger.error(f"❌ Failed to copy video: {e}")
                return False
        else:
            logger.info(f"ℹ️ Base video not found: {source_path}")
    return False


def check_or_generate_frames(duration, frames_folder, font, background_video=None):
    """
    Checks if all required timer frames exist and generates any missing frames.
    - `duration`(int): Duration of the countdown in seconds.
    - `frames_folder`(str):  Directory where the frame images are stored.
    - `font`(str): Font to use for rendering text.
    - `background_video`(str or None): If provided, forces regeneration of frames.
    """
    os.makedirs(frames_folder, exist_ok=True)
    required_seconds = list(range(duration, 0, -1))
    missing = [s for s in required_seconds if not os.path.exists(os.path.join(frames_folder, f"frame_{s//60:02}{s%60:02}.png")) or background_video]
    alarm_path = os.path.join(frames_folder, "frame_0000.png")
    if not os.path.exists(alarm_path):
        missing.append(0)

    if missing:
        logger.info(f"🖼️ Generating {len(missing)} missing frames...")
        for s in missing:
            is_alarm = s == 0
            generate_frame(s, frames_folder, font, is_alarm=is_alarm)

def load_frame_paths(duration, frames_folder, frame_rate, alarm_duration):
    """
    Generates a list of frame image paths representing the countdown and alarm period.
    For each second in the countdown, it repeats the corresponding frame path based on
    the specified frame rate. It then appends the alarm frame, repeated to match the 
    alarm duration in seconds and frame rate.
    - `duration`(int): Duration of the countdown in seconds.
    - `frames_folder`(str):  Directory where the frame images are stored.
    - `frame_rate`(int): Number of frames per second.
    - `alarm_duration`(int): Duration of the alarm phase in seconds.
    Returns:
        list[str]: Ordered list of frame image paths representing the full timer video.
    """
    countdown = []
    for s in range(duration, 0, -1):
        mm, ss = divmod(s, 60)
        path = os.path.join(frames_folder, f"frame_{mm:02}{ss:02}.png")
        countdown.extend([path] * frame_rate)

    alarm_path = os.path.join(frames_folder, "frame_0000.png")
    alarm_frames = [alarm_path] * frame_rate * alarm_duration
    return countdown + alarm_frames

def create_background_video_clip(background_video, resolution, total_duration):
    """
    Loads and processes the background video to fit the target resolution and duration.
    It resizes and crops the video to match the resolution, and loops or trims it
    to exactly match the total duration.
    - `background_video_path`(str): Path to the background video file.
    - `resolution`(tuple): Target resolution as (width, height).
    - `total_duration`(float): Total duration the video should last (in seconds).
    Returns:
        VideoFileClip: Processed background video clip ready for compositing.
    """
    logger.info(f"📹 Using background video: {background_video}")
    bg_video = VideoFileClip(background_video).resize(resolution)
    bg_w, bg_h = bg_video.size
    target_w, target_h = resolution
    bg_ratio = bg_w / bg_h
    target_ratio = target_w / target_h

    if bg_ratio > target_ratio:
        new_height = target_h
        new_width = int(bg_ratio * new_height)
        bg_video = bg_video.resize(width=new_width, height=new_height)
        x_center = bg_video.w // 2
        bg_video = bg_video.crop(x_center=x_center, width=target_w, height=target_h)
    else:
        new_width = target_w
        new_height = int(new_width / bg_ratio)
        bg_video = bg_video.resize(width=new_width, height=new_height)
        y_center = bg_video.h // 2
        bg_video = bg_video.crop(y_center=y_center, width=target_w, height=target_h)

    if bg_video.duration < total_duration:
        loops = int(total_duration // bg_video.duration) + 1
        bg_video = concatenate_videoclips([bg_video] * loops).subclip(0, total_duration)
    else:
        bg_video = bg_video.subclip(0, total_duration)

    return bg_video

def overlay_timer_on_background(bg_video, frame_files, frame_rate, duration, resolution):
    """
    Creates a VideoClip that overlays timer frames on top of the background video.
    - `bg_video_clip`(VideoFileClip): : The processed background video clip.
    - `frame_files`(list of str): List of file paths to timer frame images.
    - `frame_rate`(int): Frames per second for synchronization.
    - `resolution`(tuple): Target resolution as (width, height).
    Returns:
        CompositeVideoClip: Final video clip with timer frames composited over the background.
    """
    def make_frame(t):
        frame_idx = min(int(t * frame_rate), len(frame_files) - 1)
        timer_img = Image.open(frame_files[frame_idx]).convert("RGBA")
        bg_frame = bg_video.get_frame(t)
        bg_img = Image.fromarray(bg_frame).convert("RGBA")
        return np.array(Image.alpha_composite(bg_img, timer_img).convert("RGB"))

    overlay = VideoClip(make_frame, duration=duration)
    return CompositeVideoClip([bg_video, overlay], size=resolution)

def generate_timer_video(
    duration,
    output_video,
    frame_rate=24,
    alarm_sound="alarm.mp3",
    alarm_duration=5,
    background_music=None,
    background_video=None
):
    """
    Generate a video from timer images and add alarm sound when timer reaches zero.
    - `duration`: Timer duration in seconds.
    - `output_video`: Path to the output video file.
    - `frame_rate`: Frames per second for the video.
    - `alarm_sound`: Path to the alarm sound file.
    - `alarm_duration`: Duration of the alarm sound in seconds.
    - `background_music`: Path to background music. 
    - `background_video`: Path to background video. 
    """
    if reuse_video(output_video):
        return

    frames_folder = "timer_frames"
    sound_folder = "sounds"
    resolution = RESOLUTION

    os.makedirs(sound_folder, exist_ok=True)

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except OSError:
        logger.warning("⚠️ Font not found. Using default.")
        font = ImageFont.load_default()

    check_or_generate_frames(duration, frames_folder, font, background_video)
    frame_files = load_frame_paths(duration, frames_folder, frame_rate, alarm_duration)
    countdown_clip = ImageSequenceClip(frame_files, fps=frame_rate, load_images=False)

    if background_video:
        bg_video = create_background_video_clip(background_video, resolution, duration + alarm_duration)
        final_clip = overlay_timer_on_background(bg_video, frame_files, frame_rate, countdown_clip.duration, resolution)
    else:
        final_clip = countdown_clip.set_duration(duration + alarm_duration)

    audio_path = prepare_audio(duration, alarm_duration, alarm_sound, sound_folder, background_music)
    final_clip = final_clip.set_audio(AudioFileClip(audio_path))
    final_clip.write_videofile(output_video, codec="libx264", audio_codec="aac")
    shutil.rmtree(sound_folder, ignore_errors=True)

def parse_timer_expression(expression):
    """
      Parses a timer expression and generates a sequence of timers with corresponding filenames.
    """
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

def merge_videos(video_files, output_file="timer.mp4"):
    """
    Merge multiple MP4 video files into a single final video without re-encoding.
    """
    list_file = "videos_to_merge.txt"

    with open(list_file, "w") as f:
        for video in video_files:
            f.write(f"file '{video}'\n")

    if os.path.exists(output_file):
        os.remove(output_file)

    command = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", list_file, "-c", "copy", output_file
    ]
    subprocess.run(command, check=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a timer video with customizable options.")
    parser.add_argument("-m", "--minutes", type=int, default=0, help="Number of minutes for the timer.")
    parser.add_argument("-s", "--seconds", type=int, default=0, help="Additional seconds for the timer.")
    parser.add_argument("-a", "--alarm", type=str, default="alarm.mp3", help="Path to the alarm sound file (default: alarm.mp3).")
    parser.add_argument("-o", "--outputfile", type=str, default="timer.mp4", help="Output filename for the generated video (default: timer.mp4).")
    parser.add_argument("-bm", "--backgroundmusic", type=str, help="Optional background music file for the timer.")
    parser.add_argument("-bv", "--backgroundvideo", type=str, help="Optional background video file for the timer.")
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
                background_music=args.backgroundmusic,
                background_video=args.backgroundvideo
              )
            logger.info(f"🎥 Generated video: {FILENAME}")
        else:
            timers = parse_timer_expression(args.expression)
            if not timers:
                logger.error("❌ No valid timers parsed from expression.")
                sys.exit(1)
            timers_filenames = [filename for _, filename in timers]
            for duration, filename in timers:
                generate_timer_video(
                    duration=duration * 60,
                    output_video=filename,
                    alarm_sound=args.alarm,
                    background_music=args.backgroundmusic,
                    background_video=args.backgroundvideo
                  )
            merge_videos(timers_filenames, FILENAME)
            for filename in timers_filenames:
                os.remove(filename)
            logger.info(f"🎥 Generated video: {FILENAME}")
    except Exception as e:
        logger.error(f"❌ Error generating video: {str(e)}")
