import argparse
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "ready-to-upload"


def required_paths(number):
    episode = f"EP{number:03d}"
    folder = READY / episode
    video_name = "EP001-lost-star.mp4" if number == 1 else f"{episode}.mp4"
    return [
        folder / video_name,
        folder / "thumbnail.png",
        folder / "subtitles-ko.srt",
        folder / "youtube.txt",
        folder / "script-ko-fr.md",
        READY / f"{episode}-upload-pack.zip",
    ]


def is_complete(number):
    return all(path.exists() and path.stat().st_size > 0 for path in required_paths(number))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=100)
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()

    missing = [
        number
        for number in range(args.start, args.end + 1)
        if not is_complete(number)
    ]
    print("Missing:", " ".join(f"EP{number:03d}" for number in missing) or "none")
    if not args.repair:
        return

    failures = []
    for number in missing:
        if number == 1:
            failures.append(number)
            continue
        success = False
        for attempt in range(1, 3):
            print(f"EP{number:03d}: repair attempt {attempt}", flush=True)
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_episode.py"), str(number)],
                cwd=ROOT,
            )
            if result.returncode == 0 and is_complete(number):
                success = True
                break
            time.sleep(attempt * 5)
        if not success:
            failures.append(number)

    subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_upload_index.py")],
        cwd=ROOT,
    )
    if failures:
        print("Failed:", " ".join(f"EP{number:03d}" for number in failures))
        raise SystemExit(1)
    print("All requested episodes are complete")


if __name__ == "__main__":
    main()
