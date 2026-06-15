import argparse
import json
import zipfile
from pathlib import Path

from moviepy import VideoFileClip
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "video": "{episode}.mp4",
    "thumbnail": "thumbnail.png",
    "subtitles": "subtitles-ko.srt",
    "metadata": "youtube.txt",
    "script": "script-ko-fr.md",
}


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
        try:
            clip = VideoFileClip(str(video))
            duration = clip.duration
            expected_size = [1920, 1080] if number == 1 else [1280, 720]
            if list(clip.size) != expected_size:
                errors.append(f"resolution-{clip.size[0]}x{clip.size[1]}")
            if clip.audio is None:
                errors.append("missing-audio-track")
            if number == 1 and not 240.0 <= duration <= 330.0:
                errors.append(f"duration-{duration:.3f}")
            elif number != 1 and abs(duration - 180.0) > 0.15:
                errors.append(f"duration-{duration:.3f}")
            clip.close()
        except Exception:
            errors.append("unreadable-video")

    thumbnail = folder / "thumbnail.png"
    if thumbnail.exists() and thumbnail.stat().st_size:
        try:
            with Image.open(thumbnail) as image:
                if image.size != (1280, 720):
                    errors.append(
                        f"thumbnail-size-{image.size[0]}x{image.size[1]}"
                    )
        except Exception:
            errors.append("unreadable-thumbnail")

    subtitles = folder / "subtitles-ko.srt"
    if subtitles.exists() and subtitles.stat().st_size:
        text = subtitles.read_text(encoding="utf-8")
        if "-->" not in text or not any(
            "\uac00" <= character <= "\ud7a3" for character in text
        ):
            errors.append("invalid-subtitles")

    metadata = folder / "youtube.txt"
    if metadata.exists() and metadata.stat().st_size:
        text = metadata.read_text(encoding="utf-8")
        if number != 1 and ("TITRE" not in text or "DESCRIPTION" not in text):
            errors.append("invalid-metadata")

    if archive.exists() and archive.stat().st_size:
        try:
            with zipfile.ZipFile(archive) as package:
                names = {Path(name).name for name in package.namelist()}
            expected = {
                video_name,
                "thumbnail.png",
                "subtitles-ko.srt",
                "youtube.txt",
                "script-ko-fr.md",
            }
            missing = sorted(expected - names)
            if missing:
                errors.append(f"archive-missing-{'+'.join(missing)}")
        except zipfile.BadZipFile:
            errors.append("invalid-archive")
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
