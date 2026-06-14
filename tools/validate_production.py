import argparse
import json
from pathlib import Path

from moviepy import VideoFileClip


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "video": "{episode}.mp4",
    "thumbnail": "thumbnail.png",
    "subtitles": "subtitles-ko.srt",
    "metadata": "youtube.txt",
    "script": "script-ko-fr.md",
}


def probe_duration(path):
    try:
        clip = VideoFileClip(str(path))
        duration = clip.duration
        clip.close()
        return duration
    except Exception:
        return None


def validate(number):
    episode = f"EP{number:03d}"
    folder = ROOT / "ready-to-upload" / episode
    errors = []
    video_name = "EP001-lost-star.mp4" if number == 1 else f"{episode}.mp4"
    for label, template in REQUIRED.items():
        filename = video_name if label == "video" else template.format(episode=episode)
        path = folder / filename
        if not path.exists() or path.stat().st_size == 0:
            errors.append(f"missing-{label}")

    archive = ROOT / "ready-to-upload" / f"{episode}-upload-pack.zip"
    if not archive.exists() or archive.stat().st_size == 0:
        errors.append("missing-archive")

    video = folder / video_name
    if video.exists() and video.stat().st_size:
        duration = probe_duration(video)
        if duration is None:
            errors.append("unreadable-duration")
        elif number == 1 and not 240.0 <= duration <= 330.0:
            errors.append(f"duration-{duration:.3f}")
        elif number != 1 and abs(duration - 180.0) > 0.15:
            errors.append(f"duration-{duration:.3f}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=100)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = {
        f"EP{number:03d}": validate(number)
        for number in range(args.start, args.end + 1)
    }
    failed = {episode: errors for episode, errors in report.items() if errors}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        complete = len(report) - len(failed)
        print(f"complete={complete} failed={len(failed)} total={len(report)}")
        for episode, errors in failed.items():
            print(f"{episode}: {', '.join(errors)}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
