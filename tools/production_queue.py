import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def log(worker, message):
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] worker={worker} {message}"
    print(line, flush=True)
    path = ROOT / "production" / f"queue-worker-{worker}.log"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def is_complete(number):
    video = ROOT / "ready-to-upload" / f"EP{number:03d}" / f"EP{number:03d}.mp4"
    pack = ROOT / "ready-to-upload" / f"EP{number:03d}-upload-pack.zip"
    return video.exists() and video.stat().st_size > 1_000_000 and pack.exists()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=int, required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--start", type=int, default=3)
    parser.add_argument("--end", type=int, default=100)
    args = parser.parse_args()

    episodes = [
        number
        for number in range(args.start, args.end + 1)
        if (number - args.start) % args.workers == args.worker
    ]
    log(args.worker, f"queue-start episodes={episodes[0]}..{episodes[-1]}")

    failures = []
    for number in episodes:
        if is_complete(number):
            log(args.worker, f"EP{number:03d} already-complete")
            continue
        log(args.worker, f"EP{number:03d} render-start")
        result = None
        for attempt in range(1, 3):
            result = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_episode.py"), str(number)],
                cwd=ROOT,
            )
            if result.returncode == 0 and is_complete(number):
                break
            log(args.worker, f"EP{number:03d} retry={attempt}")
            time.sleep(attempt * 5)
        if result is not None and result.returncode == 0 and is_complete(number):
            log(args.worker, f"EP{number:03d} render-complete")
        else:
            failures.append(number)
            log(args.worker, f"EP{number:03d} render-failed code={result.returncode}")
        time.sleep(1)

    summary = ROOT / "production" / f"queue-worker-{args.worker}-summary.json"
    summary.write_text(
        json.dumps(
            {"worker": args.worker, "episodes": episodes, "failures": failures},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    log(args.worker, f"queue-finished failures={failures}")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
