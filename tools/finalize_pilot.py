import shutil
from pathlib import Path

from moviepy import AudioFileClip

from build_ep001 import SCENES


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "production" / "season-01" / "ep001-lost-star"
WORK = SOURCE / "build"
OUTPUT = ROOT / "ready-to-upload" / "EP001"


def timestamp(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def main():
    timeline = 0.0
    entries = []
    for index, scene in enumerate(SCENES, start=1):
        audio = AudioFileClip(str(WORK / f"voice-{index:02d}.mp3"))
        duration = max(audio.duration + 8.0, 18.0)
        audio.close()
        entries.append(
            f"{index}\n"
            f"{timestamp(timeline)} --> {timestamp(timeline + duration)}\n"
            f"{scene['text']}\n"
        )
        timeline += duration

    (OUTPUT / "subtitles-ko.srt").write_text(
        "\n".join(entries),
        encoding="utf-8",
    )
    shutil.copy2(SOURCE / "script-ko-fr.md", OUTPUT / "script-ko-fr.md")
    shutil.copy2(SOURCE / "storyboard.md", OUTPUT / "storyboard.md")
    shutil.make_archive(
        str(ROOT / "ready-to-upload" / "EP001-upload-pack"),
        "zip",
        OUTPUT,
    )
    print(f"EP001 finalized: {timeline:.3f}s")


if __name__ == "__main__":
    main()
