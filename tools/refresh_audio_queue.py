import argparse
import time

from refresh_episode_audio import refresh


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=int, required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--start", type=int, default=2)
    parser.add_argument("--end", type=int, default=97)
    parser.add_argument("--numbers", type=int, nargs="*")
    args = parser.parse_args()

    failures = []
    numbers = args.numbers or list(range(args.start, args.end + 1))
    for index, number in enumerate(numbers):
        if index % args.workers != args.worker:
            continue
        for attempt in range(1, 4):
            try:
                print(
                    f"worker={args.worker} EP{number:03d} refresh-start "
                    f"attempt={attempt}",
                    flush=True,
                )
                refresh(number)
                print(
                    f"worker={args.worker} EP{number:03d} refresh-complete",
                    flush=True,
                )
                break
            except Exception as error:
                print(
                    f"worker={args.worker} EP{number:03d} refresh-failed "
                    f"attempt={attempt}: {error}",
                    flush=True,
                )
                if attempt == 3:
                    failures.append(number)
                else:
                    time.sleep(attempt * 5)
    print(f"worker={args.worker} queue-finished failures={failures}", flush=True)


if __name__ == "__main__":
    main()
