import argparse
import asyncio
import json
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
from moviepy import AudioFileClip, CompositeAudioClip
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy import vfx

from build_episode import (
    BLEND,
    ROOT,
    build_voices,
    episode_paths,
    gentle_music,
)


def refresh(number):
    episode_dir, work, output = episode_paths(number)
    data = json.loads((episode_dir / "episode.json").read_text(encoding="utf-8"))
    scenes = data["scenes"]
    target = float(data["duration_target"])
    video_path = output / f"EP{number:03d}.mp4"
    if not video_path.exists():
        raise FileNotFoundError(video_path)

    for voice_path in work.glob("voice-*.mp3"):
        voice_path.unlink()
    asyncio.run(build_voices(scenes, work))

    opened = []
    layers = []
    position = 0.0
    for index, scene in enumerate(scenes, start=1):
        duration = float(scene["duration"])
        audio = AudioFileClip(str(work / f"voice-{index:02d}.mp3")).with_volume_scaled(0.96)
        if audio.duration > duration - 0.35:
            audio = audio.with_effects(
                [vfx.MultiplySpeed(final_duration=duration - 0.5)]
            )
        audio = audio.with_start(position)
        opened.append(audio)
        layers.append(audio)
        position += duration - BLEND

    music, sample_rate = gentle_music(target)
    music_clip = AudioArrayClip(music, fps=sample_rate).with_duration(target)
    layers.insert(0, music_clip)
    mix = CompositeAudioClip(layers).with_duration(target)
    audio_path = work / "refreshed-mix.m4a"
    mix.write_audiofile(
        str(audio_path),
        fps=44100,
        codec="aac",
        bitrate="160k",
        logger=None,
    )

    replacement = output / f"EP{number:03d}.new.mp4"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-shortest",
            str(replacement),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    replacement.replace(video_path)

    archive = ROOT / "ready-to-upload" / f"EP{number:03d}-upload-pack"
    shutil.make_archive(str(archive), "zip", output)

    mix.close()
    music_clip.close()
    for audio in opened:
        audio.close()
    audio_path.unlink(missing_ok=True)
    print(f"EP{number:03d} audio refreshed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("number", type=int)
    args = parser.parse_args()
    refresh(args.number)


if __name__ == "__main__":
    main()
