import asyncio
import math
from pathlib import Path

import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from moviepy import (
    AudioArrayClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    vfx,
)


ROOT = Path(__file__).resolve().parents[1]
EPISODE = ROOT / "production" / "season-01" / "ep001-lost-star"
CHARACTERS = ROOT / "assets" / "characters"
WORK = EPISODE / "build"
OUTPUT = ROOT / "ready-to-upload" / "EP001"
SIZE = (1920, 1080)
FPS = 12

FONT_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 64)
FONT_BODY = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 48)
FONT_SMALL = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 34)

SCENES = [
    {
        "speaker": "루니",
        "voice": "ko-KR-SunHiNeural",
        "text": "안녕, 친구들! 나는 달토끼 루니야. 오늘도 달나라에는 별빛이 반짝반짝 빛나고 있어.",
        "subtitle": "안녕, 친구들!\n나는 달토끼 루니야.",
        "place": "village",
        "characters": [("luni", 0.08, 0.34, 0.46)],
    },
    {
        "speaker": "별이",
        "voice": "ko-KR-HyunsuMultilingualNeural",
        "text": "루니야, 잠깐! 저기서 이상한 소리가 들려.",
        "subtitle": "루니야, 잠깐!\n저기서 이상한 소리가 들려.",
        "place": "village",
        "characters": [("luni", 0.04, 0.39, 0.40), ("byeori", 0.61, 0.27, 0.31)],
    },
    {
        "speaker": "작은 별",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-12%",
        "pitch": "+18Hz",
        "text": "흑, 흑. 친구들과 놀다가 너무 멀리 와 버렸어. 엄마 별이 안 보여.",
        "subtitle": "엄마 별이 안 보여.\n길을 잃어버렸어.",
        "place": "village",
        "characters": [("luni", 0.03, 0.42, 0.36), ("byeori", 0.70, 0.40, 0.20)],
        "small_star": True,
    },
    {
        "speaker": "루니",
        "voice": "ko-KR-SunHiNeural",
        "text": "많이 걱정됐구나. 괜찮아. 우리가 함께 찾아 줄게. 집으로 가는 길에 무엇을 보았니?",
        "subtitle": "괜찮아.\n우리가 함께 찾아 줄게!",
        "place": "village",
        "characters": [("luni", 0.12, 0.33, 0.42), ("byeori", 0.68, 0.37, 0.23)],
        "small_star": True,
    },
    {
        "speaker": "작은 별",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-10%",
        "pitch": "+16Hz",
        "text": "동그란 달빛 돌하고, 파란 꽃 세 송이를 봤어.",
        "subtitle": "동그란 달빛 돌과\n파란 꽃 세 송이!",
        "place": "clues",
        "characters": [("byeori", 0.70, 0.39, 0.22)],
        "small_star": True,
    },
    {
        "speaker": "루니",
        "voice": "ko-KR-SunHiNeural",
        "text": "친구들, 우리도 함께 찾아볼까? 동그란 달빛 돌과 파란 꽃 세 송이야!",
        "subtitle": "친구들, 함께 찾아볼까?",
        "place": "forest",
        "characters": [("luni", 0.08, 0.34, 0.43), ("byeori", 0.66, 0.32, 0.25)],
    },
    {
        "speaker": "루니",
        "voice": "ko-KR-SunHiNeural",
        "text": "여기 동그란 돌이 있어! 그런데 이 돌은 회색이네. 작은 별이 본 돌은 노란빛이었어.",
        "subtitle": "모양은 같지만\n색이 달라요.",
        "place": "forest",
        "characters": [("luni", 0.09, 0.36, 0.40), ("byeori", 0.66, 0.36, 0.23)],
        "stone": "gray",
    },
    {
        "speaker": "별이",
        "voice": "ko-KR-HyunsuMultilingualNeural",
        "text": "모양만 같다고 같은 것은 아니야. 색과 빛도 잘 살펴보자.",
        "subtitle": "색과 빛도\n잘 살펴보자!",
        "place": "forest",
        "characters": [("byeori", 0.37, 0.28, 0.34)],
        "stone": "gray",
    },
    {
        "speaker": "루니",
        "voice": "ko-KR-SunHiNeural",
        "text": "파란 꽃이다! 하나, 둘. 모두 두 송이네. 친구들, 다시 세어 줄래?",
        "subtitle": "하나, 둘!\n꽃이 두 송이예요.",
        "place": "lake",
        "characters": [("luni", 0.06, 0.36, 0.40), ("byeori", 0.69, 0.35, 0.23)],
        "flowers": 2,
    },
    {
        "speaker": "작은 별",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-10%",
        "pitch": "+16Hz",
        "text": "조금 다르지만 길이 가까워진 것 같아. 별빛 호수의 반짝이는 물결이 기억나!",
        "subtitle": "별빛 호수가 기억나!",
        "place": "lake",
        "characters": [("byeori", 0.68, 0.35, 0.23)],
        "small_star": True,
        "flowers": 2,
    },
    {
        "speaker": "루니",
        "voice": "ko-KR-SunHiNeural",
        "text": "저기 봐! 노랗게 빛나는 동그란 돌이야. 그리고 옆에는 파란 꽃이 있어.",
        "subtitle": "노란 달빛 돌을 찾았어요!",
        "place": "lake",
        "characters": [("luni", 0.07, 0.35, 0.42), ("byeori", 0.70, 0.34, 0.23)],
        "stone": "yellow",
        "flowers": 3,
    },
    {
        "speaker": "모두",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-5%",
        "text": "파란 꽃을 함께 세어 보자. 하나, 둘, 셋!",
        "subtitle": "하나, 둘, 셋!",
        "place": "lake",
        "characters": [("luni", 0.05, 0.39, 0.36), ("byeori", 0.70, 0.38, 0.22)],
        "small_star": True,
        "stone": "yellow",
        "flowers": 3,
    },
    {
        "speaker": "작은 별",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-8%",
        "pitch": "+16Hz",
        "text": "맞아! 여기야! 이제 내 별자리가 보여. 엄마 별도 보여!",
        "subtitle": "내 별자리를 찾았어!",
        "place": "constellation",
        "characters": [("luni", 0.04, 0.41, 0.34), ("byeori", 0.70, 0.39, 0.22)],
        "small_star": True,
    },
    {
        "speaker": "루니",
        "voice": "ko-KR-SunHiNeural",
        "text": "길을 잃었을 때는 혼자 있지 말고, 믿을 수 있는 어른에게 도와주세요라고 말해 줘.",
        "subtitle": "길을 잃으면\n믿을 수 있는 어른에게 말해요.",
        "place": "constellation",
        "characters": [("luni", 0.12, 0.31, 0.47), ("byeori", 0.69, 0.37, 0.23)],
    },
    {
        "speaker": "루니와 친구들",
        "voice": "ko-KR-SunHiNeural",
        "rate": "-8%",
        "text": "함께 찾으면 길을 찾을 수 있어! 루니 루니 달토끼, 반짝반짝 웃어요. 친구들과 함께라면 오늘도 괜찮아요.",
        "subtitle": "함께 찾으면 길을 찾을 수 있어!\n친구들과 함께라면 오늘도 괜찮아요.",
        "place": "ending",
        "characters": [
            ("luni", 0.02, 0.40, 0.34),
            ("byeori", 0.36, 0.48, 0.19),
            ("mongi", 0.54, 0.45, 0.20),
            ("kongkong", 0.73, 0.42, 0.24),
        ],
    },
]


def rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def make_background(place):
    w, h = SIZE
    top = np.array([70, 67, 145], dtype=float)
    bottom = np.array([181, 165, 222], dtype=float)
    if place == "forest":
        bottom = np.array([135, 191, 178], dtype=float)
    if place == "lake":
        bottom = np.array([56, 112, 155], dtype=float)
    if place in {"constellation", "ending"}:
        top = np.array([38, 43, 102], dtype=float)
        bottom = np.array([116, 91, 170], dtype=float)

    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = y / (h - 1)
        arr[y, :, :] = top * (1 - t) + bottom * t
    image = Image.fromarray(arr, "RGB").convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    for i in range(90):
        x = (i * 211 + 97) % w
        y = (i * 131 + 53) % 620
        r = 2 + (i % 4)
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 238, 154, 120 + i % 100))

    draw.ellipse((1420, 70, 1600, 250), fill=(255, 225, 126, 230))
    draw.ellipse((1485, 45, 1630, 220), fill=tuple(list(top.astype(int)) + [255]))

    if place in {"village", "ending"}:
        for i, x in enumerate(range(-80, 2000, 280)):
            base_y = 810 + (i % 2) * 35
            draw.rounded_rectangle((x, base_y-210, x+220, base_y), 32, fill=(247, 218, 193, 255))
            draw.polygon([(x-20, base_y-190), (x+110, base_y-310), (x+240, base_y-190)], fill=(116, 91, 167, 255))
            draw.rounded_rectangle((x+85, base_y-95, x+135, base_y), 15, fill=(104, 78, 143, 255))
            draw.ellipse((x+35, base_y-155, x+78, base_y-112), fill=(255, 224, 122, 255))
    elif place == "forest":
        for i, x in enumerate(range(-50, 2000, 220)):
            trunk_y = 790 + (i % 3) * 25
            draw.rounded_rectangle((x+75, trunk_y-160, x+110, trunk_y+40), 18, fill=(133, 95, 79, 255))
            draw.ellipse((x, trunk_y-310, x+190, trunk_y-100), fill=(147, 207, 190, 255))
    elif place in {"lake", "constellation"}:
        draw.ellipse((-200, 640, 2120, 1300), fill=(41, 96, 143, 230))
        for i in range(12):
            y = 700 + i * 27
            draw.arc((120+i*30, y, 1800-i*20, y+80), 185, 350, fill=(190, 219, 235, 90), width=5)
    elif place == "clues":
        rounded_rectangle(draw, (250, 230, 760, 760), 70, (255, 250, 236, 230))
        rounded_rectangle(draw, (1160, 230, 1670, 760), 70, (255, 250, 236, 230))
        draw.ellipse((400, 390, 610, 600), fill=(255, 220, 98, 255))
        for i in range(3):
            x = 1250 + i * 115
            draw.ellipse((x, 420, x+95, 515), fill=(121, 183, 229, 255))
            draw.line((x+48, 510, x+48, 630), fill=(78, 142, 111, 255), width=12)

    if place == "constellation":
        points = [(800, 190), (1010, 120), (1200, 210), (1110, 360), (880, 350), (800, 190)]
        draw.line(points, fill=(255, 226, 105, 220), width=11)
        for x, y in points[:-1]:
            draw.regular_polygon((x, y, 28), 5, rotation=-90, fill=(255, 239, 147, 255))

    return image.filter(ImageFilter.GaussianBlur(0.4))


def paste_character(canvas, name, x_ratio, y_ratio, height_ratio):
    character = Image.open(CHARACTERS / f"{name}.png").convert("RGBA")
    target_h = int(SIZE[1] * height_ratio)
    target_w = int(character.width * target_h / character.height)
    character = character.resize((target_w, target_h), Image.Resampling.LANCZOS)
    x = int(SIZE[0] * x_ratio)
    y = int(SIZE[1] * y_ratio)
    canvas.alpha_composite(character, (x, y))


def make_frame(scene, index, include_characters=True):
    frame = make_background(scene["place"])
    draw = ImageDraw.Draw(frame, "RGBA")

    if include_characters:
        for name, x, y, height in scene.get("characters", []):
            paste_character(frame, name, x, y, height)

    if include_characters and scene.get("small_star"):
        paste_character(frame, "byeori", 0.48, 0.52, 0.15)

    if scene.get("stone"):
        color = (135, 137, 150, 255) if scene["stone"] == "gray" else (255, 218, 93, 255)
        draw.ellipse((820, 710, 1040, 900), fill=color, outline=(255, 246, 188, 220), width=10)

    for i in range(scene.get("flowers", 0)):
        x = 1110 + i * 120
        draw.ellipse((x, 730, x+95, 825), fill=(118, 181, 233, 255))
        draw.ellipse((x+20, 700, x+75, 855), fill=(118, 181, 233, 255))
        draw.line((x+48, 820, x+48, 925), fill=(87, 156, 116, 255), width=12)

    rounded_rectangle(draw, (110, 825, 1810, 1030), 46, (24, 24, 57, 205), (255, 255, 255, 40), 2)
    draw.text((160, 855), scene["speaker"], font=FONT_SMALL, fill=(255, 220, 105, 255))

    lines = scene["subtitle"].split("\n")
    y = 900
    for line in lines:
        box = draw.textbbox((0, 0), line, font=FONT_BODY)
        x = (SIZE[0] - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=FONT_BODY, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(30, 25, 60, 220))
        y += 58

    draw.text((1700, 70), f"EP.01 · {index:02d}", font=FONT_SMALL, fill=(255, 255, 255, 180))
    return frame.convert("RGB")


async def create_voice(scene, path):
    communicate = edge_tts.Communicate(
        scene["text"],
        scene["voice"],
        rate=scene.get("rate", "-6%"),
        pitch=scene.get("pitch", "+0Hz"),
        volume="+0%",
    )
    await communicate.save(str(path))


async def build_audio():
    tasks = []
    for index, scene in enumerate(SCENES, start=1):
        path = WORK / f"voice-{index:02d}.mp3"
        if not path.exists():
            tasks.append(create_voice(scene, path))
    if tasks:
        await asyncio.gather(*tasks)


def music_track(duration, sample_rate=44100):
    total_samples = int(sample_rate * duration)
    signal = np.zeros(total_samples, dtype=np.float64)
    chords = [
        (196.00, 246.94, 293.66),
        (174.61, 220.00, 261.63),
        (146.83, 196.00, 246.94),
        (164.81, 207.65, 246.94),
    ]
    melody = [392.00, 440.00, 493.88, 587.33, 493.88, 440.00, 392.00, 329.63]
    measure = 4.0

    def add_tone(start, length, frequency, amplitude, harmonic=0.08):
        first = max(0, int(start * sample_rate))
        last = min(total_samples, int((start + length) * sample_rate))
        if last <= first:
            return
        local_t = np.arange(last - first) / sample_rate
        attack = np.minimum(local_t / 0.35, 1.0)
        release = np.minimum((length - local_t) / 0.8, 1.0)
        envelope = np.clip(attack * release, 0, 1)
        wave = np.sin(2 * math.pi * frequency * local_t)
        wave += harmonic * np.sin(2 * math.pi * frequency * 2 * local_t)
        signal[first:last] += amplitude * envelope * wave

    measure_count = math.ceil(duration / measure)
    for measure_index in range(measure_count):
        start = measure_index * measure
        chord = chords[measure_index % len(chords)]
        for frequency in chord:
            add_tone(start, 3.7, frequency, 0.012, harmonic=0.02)
        for beat in range(4):
            note = melody[(measure_index * 4 + beat) % len(melody)]
            add_tone(start + beat, 0.72, note, 0.020, harmonic=0.12)

    fade = min(int(sample_rate * 2), total_samples // 2)
    if fade:
        signal[:fade] *= np.linspace(0, 1, fade)
        signal[-fade:] *= np.linspace(1, 0, fade)
    signal = np.tanh(signal * 1.4) * 0.55
    stereo = np.column_stack([signal, signal]).astype(np.float32)
    return stereo, sample_rate


def character_clip(name, x_ratio, y_ratio, height_ratio, duration, seed):
    base_x = int(SIZE[0] * x_ratio)
    base_y = int(SIZE[1] * y_ratio)
    target_height = int(SIZE[1] * height_ratio)
    phase = seed * 0.83
    amplitude = 7 + (seed % 4) * 2
    clip = ImageClip(str(CHARACTERS / f"{name}.png"), duration=duration)
    clip = clip.resized(height=target_height)
    clip = clip.with_position(
        lambda t: (
            base_x + int(5 * math.sin(t * 0.9 + phase)),
            base_y + int(amplitude * math.sin(t * 1.45 + phase)),
        )
    )
    return clip.with_effects([vfx.FadeIn(0.7), vfx.FadeOut(0.5)])


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    asyncio.run(build_audio())

    clips = []
    audios = []
    for index, scene in enumerate(SCENES, start=1):
        frame_path = WORK / f"animated-bg-{index:02d}.jpg"
        if not frame_path.exists():
            make_frame(scene, index, include_characters=False).save(frame_path, quality=94)
        audio = AudioFileClip(str(WORK / f"voice-{index:02d}.mp3")).with_volume_scaled(1.12)
        duration = max(audio.duration + 8.0, 18.0)
        background = ImageClip(str(frame_path), duration=duration)
        layers = [background]
        for character_index, (name, x, y, height) in enumerate(scene.get("characters", [])):
            layers.append(character_clip(name, x, y, height, duration, index * 5 + character_index))
        if scene.get("small_star"):
            layers.append(character_clip("byeori", 0.48, 0.52, 0.15, duration, index * 7))
        clip = CompositeVideoClip(layers, size=SIZE).with_duration(duration).with_audio(audio)
        clip = clip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
        clips.append(clip)
        audios.append(audio)

    video = concatenate_videoclips(clips, method="compose")
    music, sample_rate = music_track(video.duration)
    music_clip = AudioArrayClip(music, fps=sample_rate).with_duration(video.duration)
    if video.audio is not None:
        video = video.with_audio(CompositeAudioClip([music_clip, video.audio]))
    else:
        video = video.with_audio(music_clip)
    output_path = OUTPUT / "EP001-lost-star.mp4"
    video.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        bitrate="3500k",
        threads=4,
    )

    thumbnail = Image.open(EPISODE / "thumbnail-ep001.png").convert("RGB")
    thumbnail.thumbnail((1280, 720), Image.Resampling.LANCZOS)
    thumb_canvas = Image.new("RGB", (1280, 720), (59, 51, 105))
    thumb_canvas.paste(thumbnail, ((1280-thumbnail.width)//2, (720-thumbnail.height)//2))
    thumb_canvas.save(OUTPUT / "thumbnail.png", quality=95)

    metadata = (EPISODE / "youtube-metadata.md").read_text(encoding="utf-8")
    (OUTPUT / "youtube.txt").write_text(metadata, encoding="utf-8")

    video.close()
    music_clip.close()
    for audio in audios:
        audio.close()
    for clip in clips:
        clip.close()


if __name__ == "__main__":
    main()
