import asyncio
import shutil
import subprocess

import imageio_ffmpeg
from moviepy import AudioFileClip, CompositeAudioClip
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy import vfx

from build_ep001 import OUTPUT, ROOT, SCENES, WORK, build_audio, music_track


def main():
    video_path = OUTPUT / "EP001-lost-star.mp4"
    old_segments = []
    for index in range(1, len(SCENES) + 1):
        audio = AudioFileClip(str(WORK / f"voice-{index:02d}.mp3"))
        old_segments.append(max(audio.duration + 8.0, 18.0))
        audio.close()
    target = sum(old_segments)

    for path in WORK.glob("voice-*.mp3"):
        path.unlink()
    asyncio.run(build_audio())

    layers = []
    opened = []
    position = 0.0
    for index, segment_duration in enumerate(old_segments, start=1):
        audio = AudioFileClip(str(WORK / f"voice-{index:02d}.mp3")).with_volume_scaled(1.12)
        if audio.duration > segment_duration - 0.5:
            audio = audio.with_effects(
                [vfx.MultiplySpeed(final_duration=segment_duration - 0.5)]
            )
        audio = audio.with_start(position)
        opened.append(audio)
        layers.append(audio)
        position += segment_duration

    music, sample_rate = music_track(target)
    music_clip = AudioArrayClip(music, fps=sample_rate).with_duration(target)
    layers.insert(0, music_clip)
    mix = CompositeAudioClip(layers).with_duration(target)
    audio_path = WORK / "refreshed-mix.m4a"
    mix.write_audiofile(
        str(audio_path),
        fps=44100,
        codec="aac",
        bitrate="160k",
        logger=None,
    )

    replacement = OUTPUT / "EP001-lost-star.new.mp4"
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
    shutil.make_archive(
        str(ROOT / "ready-to-upload" / "EP001-upload-pack"),
        "zip",
        OUTPUT,
    )

    mix.close()
    music_clip.close()
    for audio in opened:
        audio.close()
    audio_path.unlink(missing_ok=True)
    print("EP001 audio refreshed")


if __name__ == "__main__":
    main()
