import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "ready-to-upload"


def complete_folder(number):
    episode = f"EP{number:03d}"
    folder = READY / episode
    video_name = "EP001-lost-star.mp4" if number == 1 else f"{episode}.mp4"
    required = [
        folder / video_name,
        folder / "thumbnail.png",
        folder / "subtitles-ko.srt",
        folder / "youtube.txt",
        folder / "script-ko-fr.md",
    ]
    return folder, all(path.exists() and path.stat().st_size > 0 for path in required)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=100)
    args = parser.parse_args()

    refreshed = []
    skipped = []
    for number in range(args.start, args.end + 1):
        episode = f"EP{number:03d}"
        folder, complete = complete_folder(number)
        if not complete:
            skipped.append(episode)
            continue
        archive = READY / f"{episode}-upload-pack"
        shutil.make_archive(str(archive), "zip", folder)
        refreshed.append(episode)

    print(f"Refreshed {len(refreshed)} packs")
    if skipped:
        print("Skipped:", " ".join(skipped))


if __name__ == "__main__":
    main()
