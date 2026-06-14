import argparse
import asyncio
import json
import math
import msvcrt
import shutil
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
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
CHARACTERS = ROOT / "assets" / "characters"
POSES = CHARACTERS / "poses"
SIZE = (1280, 720)
FPS = 24
BLEND = 0.16

FONT_BOLD = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 38)
FONT_BODY = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 34)
FONT_SMALL = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 23)

RAINBOW = [
    (239, 87, 92),
    (244, 153, 70),
    (247, 209, 79),
    (105, 188, 111),
    (84, 153, 220),
    (77, 91, 157),
    (157, 104, 190),
]

FRIEND_ASSET = {
    "루니": "luni",
    "별이": "byeori",
    "몽이": "mongi",
    "콩콩": "kongkong",
    "토리": "tori",
    "밤밤": "bambam",
    "루미": "lumi",
    "달할머니": "moon-grandma",
}

THEMES = {
    "달나라 마을": ((91, 82, 161), (228, 205, 205)),
    "구름 숲": ((100, 126, 184), (171, 218, 181)),
    "별빛 호수": ((54, 69, 139), (92, 166, 190)),
    "무지개 언덕": ((119, 112, 192), (195, 231, 210)),
    "별빛 기차역": ((75, 72, 142), (225, 185, 150)),
    "꿈의 정원": ((116, 91, 166), (230, 182, 207)),
    "마법 도서관": ((75, 60, 118), (188, 149, 116)),
    "달의 성": ((45, 47, 105), (139, 110, 177)),
}


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * value * (value * (value * 6 - 15) + 10)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if current and width > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:2]


def episode_paths(number):
    season = (number - 1) // 25 + 1
    episode_dir = ROOT / "production" / f"season-{season:02d}" / f"ep{number:03d}"
    work = episode_dir / "build"
    output = ROOT / "ready-to-upload" / f"EP{number:03d}"
    return episode_dir, work, output


def color_progress(scene_index):
    thresholds = [4, 4, 6, 7, 9, 10, 11]
    return sum(scene_index >= threshold for threshold in thresholds)


def make_background(scene_index, episode_number, title, location):
    w, h = SIZE
    theme_top, theme_bottom = THEMES.get(location, THEMES["달나라 마을"])
    top = np.array(theme_top, dtype=float)
    bottom = np.array(theme_bottom, dtype=float)
    array = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        t = y / (h - 1)
        array[y, :, :] = top * (1 - t) + bottom * t

    image = Image.fromarray(array, "RGB").convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")

    for i in range(48):
        x = (i * 173 + 61) % w
        y = (i * 97 + 29) % 360
        radius = 1 + i % 3
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 244, 188, 145))

    draw.ellipse((1040, 55, 1155, 170), fill=(255, 229, 126, 245))
    draw.ellipse((1078, 38, 1174, 146), fill=(120, 113, 193, 255))

    ground = tuple(np.clip(bottom * 0.88, 0, 255).astype(int)) + (255,)
    draw.polygon([(0, 490), (230, 390), (470, 488)], fill=ground)
    draw.polygon([(340, 500), (650, 340), (960, 500)], fill=tuple(np.clip(bottom * 0.96, 0, 255).astype(int)) + (255,))
    draw.polygon([(760, 500), (1050, 370), (1280, 490)], fill=ground)
    draw.rectangle((0, 490, w, h), fill=tuple(np.clip(bottom * 0.92, 0, 255).astype(int)) + (255,))

    for i in range(18):
        x = 35 + i * 75
        color = RAINBOW[i % len(RAINBOW)]
        draw.ellipse((x, 525 + (i % 2) * 15, x + 22, 547 + (i % 2) * 15), fill=color + (220,))
        draw.line((x + 11, 546, x + 11, 585), fill=(77, 139, 91, 220), width=4)

    if episode_number == 2:
        progress = color_progress(scene_index)
        for band in range(progress):
            inset = 125 + band * 12
            draw.arc(
                (inset, 105 + band * 10, w - inset, 620 - band * 5),
                185,
                355,
                fill=RAINBOW[band] + (225,),
                width=13,
            )

    if episode_number == 2 and scene_index in {3, 4}:
        draw.ellipse((900, 480, 958, 540), fill=RAINBOW[0] + (255,))
        draw.rectangle((925, 530, 935, 590), fill=(102, 147, 84, 255))
        draw.ellipse((1025, 430, 1075, 470), fill=RAINBOW[1] + (255,))
        draw.ellipse((1063, 430, 1113, 470), fill=RAINBOW[1] + (255,))
    if episode_number == 2 and scene_index in {5, 6}:
        draw.ellipse((910, 455, 995, 540), fill=RAINBOW[2] + (255,))
        draw.ellipse((930, 430, 975, 570), fill=RAINBOW[2] + (255,))
        draw.line((952, 535, 952, 610), fill=(83, 145, 89, 255), width=8)
        draw.ellipse((1020, 520, 1100, 565), fill=RAINBOW[3] + (255,))
    if episode_number == 2 and 9 <= scene_index <= 11:
        draw.polygon([(0, 615), (340, 560), (700, 640), (1280, 560), (1280, 720), (0, 720)], fill=(77, 157, 207, 225))
        draw.ellipse((930, 550, 1020, 625), fill=RAINBOW[5] + (255,))
        if scene_index == 11:
            draw.ellipse((1080, 500, 1135, 555), fill=RAINBOW[6] + (255,))
            draw.line((1107, 550, 1107, 605), fill=(80, 139, 91, 255), width=6)

    draw.rounded_rectangle((26, 22, 410, 70), radius=20, fill=(34, 31, 74, 150))
    draw.text((48, 34), f"EP.{episode_number:03d} · {title}", font=FONT_SMALL, fill=(255, 255, 255, 235))

    if episode_number != 2:
        motif = episode_number % 4
        if motif == 0:
            for x in range(110, 1200, 180):
                draw.rounded_rectangle((x, 505, x + 90, 640), 18, fill=(250, 225, 189, 205))
                draw.polygon([(x - 8, 520), (x + 45, 470), (x + 98, 520)], fill=(111, 91, 166, 220))
        elif motif == 1:
            for x in range(90, 1250, 150):
                draw.ellipse((x, 450, x + 120, 570), fill=(144, 205, 180, 220))
                draw.rectangle((x + 52, 540, x + 68, 630), fill=(123, 87, 72, 220))
        elif motif == 2:
            draw.ellipse((-80, 555, 1360, 850), fill=(70, 138, 185, 205))
            for y in range(590, 710, 30):
                draw.arc((80, y, 1190, y + 70), 185, 355, fill=(215, 237, 245, 100), width=4)
        else:
            for x in range(120, 1200, 180):
                draw.ellipse((x, 500, x + 38, 538), fill=RAINBOW[(x // 180) % len(RAINBOW)] + (230,))
                draw.line((x + 19, 535, x + 19, 610), fill=(76, 132, 87, 220), width=5)
    return image.filter(ImageFilter.GaussianBlur(0.25)).convert("RGB")


def subtitle_image(scene, index):
    canvas = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle(
        (45, 570, 1235, 700),
        radius=30,
        fill=(28, 25, 65, 220),
        outline=(255, 255, 255, 65),
        width=2,
    )
    draw.text((78, 588), scene["speaker"], font=FONT_SMALL, fill=(255, 223, 106, 255))
    lines = wrap_text(draw, scene["text"], FONT_BODY, 1040)
    y = 620 if len(lines) == 1 else 606
    for line in lines:
        box = draw.textbbox((0, 0), line, font=FONT_BODY)
        x = (SIZE[0] - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=FONT_BODY, fill="white")
        y += 42
    return canvas


def character_source(name, action):
    if name == "luni" and action in {"collect-colors", "rainbow-appears"}:
        return POSES / "luni-surprised-v2.png"
    if name == "luni" and action == "follow-stream":
        return POSES / "luni-running.png"
    if name == "luni" and action == "audience-search":
        return POSES / "luni-listening.png"
    if name == "byeori" and action in {"point-clues", "show-three"}:
        return POSES / "byeori-pointing.png"
    if name == "mongi" and action in {"sneeze-reaction", "small-sneeze"}:
        return POSES / "mongi-sneeze.png"
    return CHARACTERS / f"{name}.png"


def character_clip(name, action, duration, side, seed):
    source = character_source(name, action)
    target_height = {
        "luni": 390,
        "byeori": 260,
        "mongi": 265,
        "kongkong": 330,
        "tori": 340,
        "bambam": 310,
        "lumi": 320,
        "moon-grandma": 390,
    }[name]
    base_x = {"left": 100, "center": 480, "right": 850}[side]
    base_y = {
        "luni": 145,
        "byeori": 230,
        "mongi": 220,
        "kongkong": 180,
        "tori": 175,
        "bambam": 205,
        "lumi": 190,
        "moon-grandma": 130,
    }[name]
    phase = seed * 0.61

    clip = ImageClip(str(source), duration=duration).resized(height=target_height)

    if action == "follow-stream" and name == "luni":
        return clip.with_position(
            lambda t: (
                int(-250 + 1520 * smooth(t / max(duration - 0.6, 0.1))),
                int(145 + 9 * abs(math.sin(t * 8.8))),
            )
        )

    emphasis = action in {"sneeze-reaction", "small-sneeze", "happy-tears"}
    return clip.with_position(
        lambda t: (
            int(base_x + 5 * math.sin(t * 1.7 + phase)),
            int(base_y + (7 if emphasis else 3) * math.sin(t * (4.6 if emphasis else 2.9) + phase)),
        )
    )


def cast_for(scene):
    speaker = scene["speaker"]
    if speaker == "루니":
        return [("luni", "left"), ("byeori", "right")]
    if speaker in FRIEND_ASSET:
        return [("luni", "left"), (FRIEND_ASSET[speaker], "right")]
    return [("luni", "left"), ("byeori", "center"), ("mongi", "right")]


async def create_voice(scene, path):
    import edge_tts

    speaker = scene["speaker"]
    rate = "+11%"
    pitch = "+1Hz"
    volume = "-5%"
    if speaker == "별이":
        rate, pitch, volume = "+8%", "+3Hz", "-6%"
    elif speaker == "몽이":
        rate, pitch, volume = "+9%", "-1Hz", "-5%"
    elif speaker == "달할머니":
        rate, pitch, volume = "+3%", "-2Hz", "-7%"
    elif speaker in {"모두", "노래"}:
        rate, pitch, volume = "+6%", "+2Hz", "-6%"

    await edge_tts.Communicate(
        scene["text"],
        scene["voice"],
        rate=rate,
        pitch=pitch,
        volume=volume,
    ).save(str(path))


async def build_voices(scenes, work):
    tasks = []
    for index, scene in enumerate(scenes, start=1):
        path = work / f"voice-{index:02d}.mp3"
        if not path.exists():
            tasks.append(create_voice(scene, path))
    if tasks:
        await asyncio.gather(*tasks)


def gentle_music(duration, sample_rate=44100):
    count = int(duration * sample_rate)
    signal = np.zeros(count, dtype=np.float64)
    chords = [
        (130.81, 164.81, 196.00),
        (146.83, 174.61, 220.00),
        (123.47, 164.81, 196.00),
        (110.00, 146.83, 174.61),
    ]
    melody = [261.63, 293.66, 329.63, 392.00, 329.63, 293.66, 261.63, 220.00]

    def tone(start, length, frequency, amplitude):
        first = int(start * sample_rate)
        last = min(count, int((start + length) * sample_rate))
        if first >= last:
            return
        time = np.arange(last - first) / sample_rate
        attack = np.minimum(time / 0.22, 1.0)
        release = np.minimum((length - time) / 0.7, 1.0)
        envelope = np.clip(attack * release, 0, 1)
        wave = np.sin(2 * math.pi * frequency * time)
        wave += 0.08 * np.sin(2 * math.pi * frequency * 2 * time)
        signal[first:last] += amplitude * envelope * wave

    for measure in range(math.ceil(duration / 4)):
        start = measure * 4
        for frequency in chords[measure % len(chords)]:
            tone(start, 3.8, frequency, 0.010)
        for beat in range(4):
            tone(start + beat, 0.6, melody[(measure * 4 + beat) % len(melody)], 0.012)

    fade = min(int(sample_rate * 2), count // 2)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    stereo = np.column_stack([signal, signal]).astype(np.float32)
    return stereo, sample_rate


def srt_time(seconds):
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(scenes, output):
    cursor = 0.0
    blocks = []
    for index, scene in enumerate(scenes, start=1):
        end = cursor + scene["duration"]
        blocks.append(
            f"{index}\n{srt_time(cursor)} --> {srt_time(end)}\n{scene['text']}\n"
        )
        cursor = end
    output.write_text("\n".join(blocks), encoding="utf-8")


def make_thumbnail(data, output):
    canvas = make_background(
        14, data["number"], data["title"], data["location"]
    ).convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    dark = Image.new("RGBA", SIZE, (23, 20, 57, 82))
    canvas = Image.alpha_composite(canvas, dark)

    luni = Image.open(CHARACTERS / "luni.png").convert("RGBA")
    luni.thumbnail((400, 500), Image.Resampling.LANCZOS)
    canvas.alpha_composite(luni, (60, 170))
    friend_name = next(
        (name for name in data.get("characters", []) if name != "루니"),
        "몽이",
    )
    friend_asset = FRIEND_ASSET.get(friend_name, "mongi")
    friend = Image.open(CHARACTERS / f"{friend_asset}.png").convert("RGBA")
    friend.thumbnail((310, 360), Image.Resampling.LANCZOS)
    canvas.alpha_composite(friend, (920, 660 - friend.height))

    draw = ImageDraw.Draw(canvas, "RGBA")
    draw.rounded_rectangle((355, 105, 1050, 275), radius=44, fill=(255, 249, 231, 235))
    title_font = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 58)
    while title_font.getbbox(data["title"])[2] > 590 and title_font.size > 38:
        title_font = ImageFont.truetype(
            r"C:\Windows\Fonts\malgunbd.ttf", title_font.size - 2
        )
    draw.text(
        (410, 130),
        data["title"],
        font=title_font,
        fill=(68, 56, 130, 255),
    )
    draw.text(
        (500, 215),
        f"달토끼 루니 EP.{data['number']:03d}",
        font=FONT_BOLD,
        fill=(106, 90, 172, 255),
    )
    canvas.convert("RGB").save(output, quality=95)


def update_catalog(number, **deliverables):
    path = ROOT / "production" / "catalog.json"
    lock_path = path.with_suffix(".lock")
    lock_path.touch(exist_ok=True)
    with lock_path.open("r+b") as lock:
        while True:
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                time.sleep(0.2)
        try:
            catalog = json.loads(path.read_text(encoding="utf-8"))
            episode = next(
                item for item in catalog["episodes"] if item["number"] == number
            )
            episode["deliverables"].update(deliverables)
            if deliverables.get("animation") and deliverables.get("youtube_pack"):
                episode["status"] = "complete"
            temporary = path.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(path)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def build(number):
    episode_dir, work, output = episode_paths(number)
    data = json.loads((episode_dir / "episode.json").read_text(encoding="utf-8"))
    scenes = data["scenes"]
    work.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)

    asyncio.run(build_voices(scenes, work))

    clips = []
    opened_audio = []
    for index, scene in enumerate(scenes, start=1):
        duration = float(scene["duration"])
        background_path = work / f"background-v2-{index:02d}.jpg"
        subtitle_path = work / f"subtitle-{index:02d}.png"
        if not background_path.exists():
            make_background(
                index, number, data["title"], data["location"]
            ).save(background_path, quality=91)
        subtitle_image(scene, index).save(subtitle_path)

        audio = AudioFileClip(str(work / f"voice-{index:02d}.mp3")).with_volume_scaled(0.96)
        if audio.duration > duration - 0.35:
            audio = audio.with_effects(
                [vfx.MultiplySpeed(final_duration=duration - 0.5)]
            )
        opened_audio.append(audio)

        background = ImageClip(str(background_path), duration=duration)
        layers = [background]
        for seed, (name, side) in enumerate(cast_for(scene), start=index * 4):
            layers.append(character_clip(name, scene["action"], duration, side, seed))
        layers.append(ImageClip(str(subtitle_path), duration=duration))

        clip = CompositeVideoClip(layers, size=SIZE).with_duration(duration).with_audio(audio)
        clip = clip.with_effects([vfx.CrossFadeIn(BLEND), vfx.CrossFadeOut(BLEND)])
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose", padding=-BLEND)
    target = float(data["duration_target"])
    if video.duration < target:
        last_frame = video.get_frame(video.duration - 0.05)
        hold = ImageClip(last_frame, duration=target - video.duration)
        video = concatenate_videoclips([video, hold], method="compose")
    video = video.subclipped(0, target)

    music, sample_rate = gentle_music(target)
    music_clip = AudioArrayClip(music, fps=sample_rate).with_duration(target)
    video = video.with_audio(CompositeAudioClip([music_clip, video.audio]))

    video_path = output / f"EP{number:03d}.mp4"
    video.write_videofile(
        str(video_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        bitrate="2200k",
        threads=4,
    )

    make_thumbnail(data, output / "thumbnail.png")
    write_srt(scenes, output / "subtitles-ko.srt")
    shutil.copy2(episode_dir / "youtube.txt", output / "youtube.txt")
    shutil.copy2(episode_dir / "script-ko-fr.md", output / "script-ko-fr.md")
    archive = ROOT / "ready-to-upload" / f"EP{number:03d}-upload-pack"
    shutil.make_archive(str(archive), "zip", output)

    update_catalog(
        number,
        script=True,
        voices=True,
        animation=True,
        subtitles=True,
        thumbnail=True,
        youtube_pack=True,
    )

    video.close()
    music_clip.close()
    for clip in clips:
        clip.close()
    for audio in opened_audio:
        audio.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("number", type=int)
    args = parser.parse_args()
    build(args.number)


if __name__ == "__main__":
    main()
