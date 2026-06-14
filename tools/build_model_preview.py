import asyncio
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_audioclips,
    concatenate_videoclips,
    vfx,
)

from build_ep001 import SIZE, make_background


ROOT = Path(__file__).resolve().parents[1]
CHARACTERS = ROOT / "assets" / "characters"
POSES = CHARACTERS / "poses"
WORK = ROOT / "production" / "model-preview"
OUTPUT = ROOT / "ready-to-upload" / "MODEL-PREVIEW"
PREVIEW_SIZE = (1280, 720)
FPS = 24

FONT = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 39)
FONT_SMALL = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 25)

DIALOGUE = [
    {
        "speaker": "루니",
        "text": "안녕, 친구들! 나는 달토끼 루니야. 오늘도 신나는 모험을 시작해 볼까?",
        "subtitle": "안녕, 친구들! 오늘도 신나는 모험을 시작해 볼까?",
        "voice": "ko-KR-SunHiNeural",
        "rate": "+9%",
        "pitch": "+1Hz",
        "pose": "luni",
        "action": "welcome",
    },
    {
        "speaker": "별이",
        "text": "루니야, 잠깐! 저쪽에서 이상한 소리가 들려!",
        "subtitle": "루니야, 잠깐! 저쪽에서 이상한 소리가 들려!",
        "voice": "ko-KR-HyunsuMultilingualNeural",
        "rate": "+12%",
        "pitch": "+8Hz",
        "pose": "byeori-worried",
        "action": "warning",
    },
    {
        "speaker": "루니",
        "text": "정말? 조용히 들어 보자. 아, 누군가 우리를 부르고 있어!",
        "subtitle": "조용히 들어 보자. 누군가 우리를 부르고 있어!",
        "voice": "ko-KR-SunHiNeural",
        "rate": "+10%",
        "pitch": "+1Hz",
        "pose": "luni-listening",
        "action": "listen",
    },
    {
        "speaker": "루니",
        "text": "걱정하지 마! 우리가 지금 바로 도와주러 갈게!",
        "subtitle": "걱정하지 마! 우리가 지금 바로 도와주러 갈게!",
        "voice": "ko-KR-SunHiNeural",
        "rate": "+12%",
        "pitch": "+2Hz",
        "pose": "luni-running",
        "action": "run",
    },
]


def pose_path(name):
    if name in {"luni", "byeori"}:
        return CHARACTERS / f"{name}.png"
    return POSES / f"{name}.png"


def make_preview_background():
    source = make_background("forest").convert("RGB")
    source = source.resize(PREVIEW_SIZE, Image.Resampling.LANCZOS)
    path = WORK / "background.jpg"
    source.save(path, quality=92)
    return path


def make_subtitle(text, speaker, index):
    canvas = Image.new("RGBA", PREVIEW_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle(
        (75, 566, 1205, 695),
        radius=34,
        fill=(25, 24, 61, 220),
        outline=(255, 255, 255, 80),
        width=2,
    )
    draw.text((112, 590), speaker, font=FONT_SMALL, fill=(255, 222, 107, 255))
    box = draw.textbbox((0, 0), text, font=FONT)
    x = (PREVIEW_SIZE[0] - (box[2] - box[0])) // 2
    draw.text((x, 625), text, font=FONT, fill="white")
    draw.text((1090, 36), f"MODEL TEST · {index:02d}", font=FONT_SMALL, fill=(255, 255, 255, 210))
    path = WORK / f"subtitle-{index:02d}.png"
    canvas.save(path)
    return path


async def create_voice(item, path):
    import edge_tts

    speech = edge_tts.Communicate(
        item["text"],
        item["voice"],
        rate=item["rate"],
        pitch=item["pitch"],
        volume="-5%" if item["speaker"] == "루니" else "-2%",
    )
    await speech.save(str(path))


async def create_voice_auditions():
    import edge_tts

    line = "안녕, 친구들! 나는 달토끼 루니야. 오늘도 신나는 모험을 시작해 볼까?"
    choices = [
        ("A-sunhi", "ko-KR-SunHiNeural", "+10%", "+2Hz"),
        ("B-hyunsu", "ko-KR-HyunsuMultilingualNeural", "+10%", "+6Hz"),
        ("C-injoon", "ko-KR-InJoonNeural", "+10%", "+6Hz"),
    ]
    tasks = []
    for label, voice, rate, pitch in choices:
        path = OUTPUT / f"voice-{label}.mp3"
        tasks.append(
            edge_tts.Communicate(
                line, voice, rate=rate, pitch=pitch, volume="+0%"
            ).save(str(path))
        )
    await asyncio.gather(*tasks)


def character_layer(item, duration):
    image = pose_path(item["pose"])
    action = item["action"]

    def smoothstep(value):
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def entrance(t, length=0.42):
        return smoothstep(t / min(length, duration))

    def breathe(t, amount=0.012):
        return 1.0 + amount * math.sin(t * 2.8)

    if action == "run":
        clip = ImageClip(str(image), duration=duration).resized(
            lambda t: breathe(t, 0.018) * (0.96 + 0.04 * entrance(t, 0.25))
        ).resized(height=520)

        def run_position(t):
            progress = smoothstep(t / max(duration - 0.28, 0.1))
            x = -360 + (PREVIEW_SIZE[0] + 310) * progress
            stride = abs(math.sin(t * 10.5))
            landing = math.sin(t * 21.0) * 3
            return int(x), int(105 + 16 * stride + landing)

        return clip.with_position(
            run_position
        )

    height = 490 if action != "warning" else 390
    clip = ImageClip(str(image), duration=duration).resized(
        lambda t: breathe(t) * (0.92 + 0.08 * entrance(t))
    ).resized(height=height)
    if action == "welcome":
        return clip.with_position(
            lambda t: (
                int(120 - 34 * (1.0 - entrance(t)) + 5 * math.sin(t * 1.9)),
                int(94 + 5 * math.sin(t * 3.8)),
            )
        )
    if action == "warning":
        return clip.with_position(
            lambda t: (
                int(760 + 42 * (1.0 - entrance(t, 0.32)) + 9 * math.sin(t * 4.2)),
                int(152 + 8 * math.sin(t * 5.4)),
            )
        )
    return clip.with_position(
        lambda t: (
            int(190 + 5 * math.sin(t * 2.0)),
            int(94 + 4 * math.sin(t * 4.0)),
        )
    )


def reaction_layer(item, duration):
    if item["action"] == "warning":
        other = ImageClip(str(POSES / "luni-listening.png"), duration=duration).resized(
            lambda t: 0.96 + 0.018 * math.sin(t * 2.6)
        ).resized(height=420)
        return other.with_position(
            lambda t: (90, int(158 + 4 * math.sin(t * 3.6)))
        ).with_effects([vfx.FadeIn(0.25)])
    if item["action"] == "listen":
        other = ImageClip(str(POSES / "byeori-worried.png"), duration=duration).resized(
            lambda t: 0.97 + 0.025 * math.sin(t * 3.3)
        ).resized(height=310)
        return other.with_position(
            lambda t: (840 + int(5 * math.sin(t * 2.2)), 210 + int(8 * math.sin(t * 4.2)))
        )
    return None


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    background_path = make_preview_background()

    async def audio_setup():
        tasks = []
        for index, item in enumerate(DIALOGUE, start=1):
            voice_path = WORK / f"voice-{index:02d}.mp3"
            if not voice_path.exists():
                tasks.append(create_voice(item, voice_path))
        if tasks:
            await asyncio.gather(*tasks)

    asyncio.run(audio_setup())

    scenes = []
    opened_audio = []
    for index, item in enumerate(DIALOGUE, start=1):
        audio = AudioFileClip(str(WORK / f"voice-{index:02d}.mp3")).with_volume_scaled(
            0.92 if item["speaker"] == "루니" else 0.98
        )
        opened_audio.append(audio)
        duration = audio.duration + 0.48
        background = ImageClip(str(background_path), duration=duration).resized(
            lambda t: 1.0 + 0.018 * min(t / max(duration, 0.1), 1)
        ).with_position("center")
        layers = [
            background,
            character_layer(item, duration),
        ]
        reaction = reaction_layer(item, duration)
        if reaction is not None:
            layers.append(reaction)
        subtitle = ImageClip(
            str(make_subtitle(item["subtitle"], item["speaker"], index)),
            duration=duration,
        )
        layers.append(subtitle)
        scene = CompositeVideoClip(layers, size=PREVIEW_SIZE).with_duration(duration).with_audio(audio)
        scene = scene.with_effects([vfx.FadeIn(0.12), vfx.FadeOut(0.1)])
        scenes.append(scene)

    video = concatenate_videoclips(scenes, method="compose")
    video.write_videofile(
        str(OUTPUT / "luni-model-preview-v2.mp4"),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="2800k",
        threads=4,
    )

    video.close()
    for scene in scenes:
        scene.close()
    for audio in opened_audio:
        audio.close()


if __name__ == "__main__":
    main()
