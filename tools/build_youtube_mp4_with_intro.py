import concurrent.futures
import re
import subprocess
from pathlib import Path

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "ready-to-upload"
OUTPUT = READY / "PACK-YOUTUBE-100-MP4-AVEC-INTRO"
WORK = ROOT / "production" / "youtube-final-intro"
INTRO = READY / "GENERIQUE-INTRO" / "LUNI-GENERIQUE-V6-VRAIMENT-ANIME.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def run(command, capture=False):
    return subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
        text=capture,
    )


def make_intro(output, width, height, fps, level):
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(INTRO),
            "-vf",
            f"fps={fps},scale={width}:{height}:flags=lanczos,format=yuv420p",
            "-c:v",
            "libx264",
            "-profile:v",
            "baseline",
            "-level",
            level,
            "-preset",
            "medium",
            "-crf",
            "18",
            "-video_track_timescale",
            "12288",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def source_for(number):
    episode = f"EP{number:03d}"
    filename = "EP001-lost-star.mp4" if number == 1 else f"{episode}.mp4"
    return READY / episode / filename


def duration(path):
    result = run(
        [FFMPEG, "-hide_banner", "-i", str(path), "-f", "null", "NUL"],
        capture=True,
    )
    match = re.search(
        r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)",
        result.stderr,
    )
    if not match:
        raise RuntimeError(f"Duration unreadable: {path}")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def assemble(number, intro_720, intro_1080):
    episode = f"EP{number:03d}"
    source = source_for(number)
    if not source.exists() or source.stat().st_size < 1_000_000:
        raise FileNotFoundError(source)

    intro = intro_1080 if number == 1 else intro_720
    output = OUTPUT / f"{episode}-YOUTUBE-AVEC-INTRO.mp4"
    concat_file = WORK / f"{episode}-concat.txt"
    concat_file.write_text(
        f"file '{intro.as_posix()}'\nfile '{source.as_posix()}'\n",
        encoding="utf-8",
    )

    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-ar",
            "44100",
            "-ac",
            "2",
            "-af",
            "aresample=async=1:first_pts=0",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )
    concat_file.unlink(missing_ok=True)

    expected = duration(source) + duration(intro)
    actual = duration(output)
    if abs(actual - expected) > 0.25:
        raise RuntimeError(
            f"{episode}: duration {actual:.2f}s, expected {expected:.2f}s"
        )
    return episode, output.stat().st_size, actual


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)

    intro_720 = WORK / "intro-720p24.mp4"
    intro_1080 = WORK / "intro-1080p12.mp4"
    make_intro(intro_720, 1280, 720, 24, "3.1")
    make_intro(intro_1080, 1920, 1080, 12, "4.0")

    failures = []
    completed = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(assemble, number, intro_720, intro_1080): number
            for number in range(1, 101)
        }
        for future in concurrent.futures.as_completed(futures):
            number = futures[future]
            try:
                episode, size, seconds = future.result()
                completed.append(episode)
                print(
                    f"{episode} OK {seconds:.2f}s {size / 1024 / 1024:.1f}MB",
                    flush=True,
                )
            except Exception as error:
                failures.append((number, str(error)))
                print(f"EP{number:03d} FAILED {error}", flush=True)

    if failures:
        details = "; ".join(
            f"EP{number:03d}: {message}" for number, message in failures
        )
        raise RuntimeError(details)
    if len(completed) != 100:
        raise RuntimeError(f"Expected 100 videos, built {len(completed)}")
    print(f"PACK READY: {OUTPUT}")


if __name__ == "__main__":
    main()
