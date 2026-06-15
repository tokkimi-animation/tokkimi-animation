import asyncio
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg

from build_episode import ROOT, create_voice


SAMPLES = [
    ("01-luni", "루니", "안녕, 나는 달토끼 루니야. 오늘도 함께 모험을 시작해 볼까?"),
    ("02-byeori", "별이", "반짝반짝 안녕! 나는 작은 별 친구 별이야."),
    ("03-mongi", "몽이", "에취! 나는 말랑말랑 구름 친구 몽이야."),
    ("04-kongkong", "콩콩", "어서 가자! 신나는 모험이라면 내가 먼저 달려갈게!"),
    ("05-tori", "토리", "새로운 생각이 떠올랐어. 멋진 발명품을 만들어 보자."),
    ("06-bambam", "밤밤", "나는 조금 수줍지만 친구들과 함께라면 용기를 낼 수 있어."),
    ("07-lumi", "루미", "천천히 생각해 보렴. 좋은 질문이 길을 보여 줄 거야."),
    ("08-moon-grandma", "달할머니", "우리 아이들, 서두르지 말고 마음속 달빛을 따라가 보렴."),
]


async def build_samples(output):
    tasks = []
    for filename, speaker, text in SAMPLES:
        path = output / f"{filename}.mp3"
        tasks.append(
            create_voice(
                {"speaker": speaker, "text": text, "voice": "ko-KR-SunHiNeural"},
                path,
            )
        )
    await asyncio.gather(*tasks)


def main():
    output = ROOT / "ready-to-upload" / "CONTROLE-VOIX-PERSONNAGES"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    asyncio.run(build_samples(output))

    concat_list = output / "concat.txt"
    lines = []
    silence = output / "silence.mp3"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=stereo",
            "-t",
            "0.8",
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(silence),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for filename, _, _ in SAMPLES:
        lines.append(f"file '{filename}.mp3'")
        lines.append("file 'silence.mp3'")
    concat_list.write_text("\n".join(lines) + "\n", encoding="utf-8")
    combined = output / "ECOUTER-LES-8-VOIX.mp3"
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "160k",
            str(combined),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    silence.unlink()
    concat_list.unlink()
    (output / "LISEZ-MOI.txt").write_text(
        "Échantillons des voix définitives : Luni, Byeori, Mongi, Kongkong, "
        "Tori, Bambam, Lumi et Grand-mère Lune.\n"
        "Ouvrez ECOUTER-LES-8-VOIX.mp3 pour les entendre à la suite.\n",
        encoding="utf-8",
    )
    print(combined)


if __name__ == "__main__":
    main()
