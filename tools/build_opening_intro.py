import asyncio
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    concatenate_videoclips,
    vfx,
)
from moviepy.audio.AudioClip import AudioArrayClip

from build_episode import ROOT, create_voice


SIZE = (1280, 720)
FPS = 24
OUTPUT = ROOT / "ready-to-upload" / "GENERIQUE-INTRO"
WORK = ROOT / "production" / "opening-intro"
CHARACTERS = ROOT / "assets" / "characters"
LOGO = ROOT / "assets" / "images" / "tokkimi-logo.png"

FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 64)
FONT_NAME = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 48)
FONT_BODY = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 30)

CAST = [
    ("루니", "LUNI", "달토끼 루니! 함께 모험을 시작해 볼까?", "luni.png", (255, 224, 130)),
    ("별이", "BYEORI", "반짝반짝! 길을 비추는 별이야.", "byeori-pointing.png", (255, 215, 92)),
    ("몽이", "MONGI", "에취! 웃음 가득한 구름 몽이야.", "mongi-sneeze.png", (171, 224, 242)),
    ("콩콩", "KONGKONG", "신나는 모험은 나에게 맡겨!", "kongkong-jump.png", (224, 164, 104)),
    ("토리", "TORI", "새로운 발명품을 만들어 보자!", "tori-inventing.png", (239, 163, 112)),
    ("밤밤", "BAMBAM", "천천히 용기를 내면 할 수 있어.", "bambam-brave.png", (199, 156, 116)),
    ("루미", "LUMI", "좋은 질문이 길을 보여 줄 거야.", "lumi-discovery.png", (183, 166, 222)),
    ("달할머니", "MOON GRANDMA", "마음속 달빛을 따라가 보렴.", "moon-grandma-comfort.png", (236, 199, 145)),
]


def gradient_background(index, duration):
    palettes = [
        ((82, 76, 159), (196, 173, 229)),
        ((91, 84, 175), (246, 193, 187)),
        ((91, 137, 190), (195, 230, 226)),
        ((126, 91, 167), (255, 213, 138)),
    ]
    top, bottom = palettes[index % len(palettes)]
    canvas = np.zeros((SIZE[1], SIZE[0], 3), dtype=np.uint8)
    for y in range(SIZE[1]):
        mix = y / (SIZE[1] - 1)
        canvas[y, :, :] = np.array(top) * (1 - mix) + np.array(bottom) * mix
    image = Image.fromarray(canvas).filter(ImageFilter.GaussianBlur(0.3))
    draw = ImageDraw.Draw(image, "RGBA")
    rng = np.random.default_rng(2026 + index)
    for _ in range(55):
        x = int(rng.integers(20, SIZE[0] - 20))
        y = int(rng.integers(20, SIZE[1] - 60))
        r = int(rng.integers(2, 7))
        draw.ellipse((x-r, y-r, x+r, y+r), fill=(255, 244, 180, int(rng.integers(90, 210))))
    draw.ellipse((70, 515, 1210, 820), fill=(255, 255, 255, 75))
    return ImageClip(np.array(image), duration=duration)


def text_card(korean, latin, line, color, index):
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle(
        (58, 74, 555, 590),
        radius=34,
        fill=(255, 252, 246, 232),
        outline=(255, 255, 255, 190),
        width=3,
    )
    draw.text((100, 125), korean, font=FONT_NAME, fill=(55, 45, 91, 255))
    draw.text((102, 187), latin, font=FONT_BODY, fill=(105, 88, 160, 255))
    draw.rounded_rectangle((99, 242, 175, 250), radius=4, fill=(*color, 255))
    lines = []
    current = ""
    for word in line.split():
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=FONT_BODY) > 385 and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    y = 290
    for text in lines:
        draw.text((100, y), text, font=FONT_BODY, fill=(76, 67, 96, 255))
        y += 50
    draw.text((100, 515), f"달토끼 루니 · FRIEND {index:02d}", font=FONT_BODY, fill=(130, 120, 145, 220))
    return image


def character_layer(path, duration, index):
    source = CHARACTERS / "poses" / path
    if not source.exists():
        source = CHARACTERS / path
    clip = ImageClip(str(source), duration=duration).resized(height=520)

    def position(t):
        entrance = min(1.0, t / 0.55)
        ease = 1 - (1 - entrance) ** 3
        x = 1280 - int(520 * ease)
        bob = int(10 * math.sin(t * 4.2 + index))
        bounce = -int(24 * math.sin(min(1, t / 0.8) * math.pi))
        return x, 132 + bob + bounce

    return clip.with_position(position).with_effects([vfx.FadeIn(0.25), vfx.FadeOut(0.2)])


def opening_card(duration):
    bg = gradient_background(0, duration)
    logo = ImageClip(str(LOGO), duration=duration).resized(height=190)
    logo = logo.with_position(
        lambda t: (
            545 + int(7 * math.sin(t * 2.4)),
            90 - int(10 * math.sin(min(1, t / 0.8) * math.pi)),
        )
    )
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    title = "달토끼 루니"
    subtitle = "친구들과 함께 떠나는 달빛 모험"
    box = draw.textbbox((0, 0), title, font=FONT_TITLE)
    draw.text(((1280 - (box[2]-box[0])) / 2, 325), title, font=FONT_TITLE, fill=(255, 252, 224, 255))
    box = draw.textbbox((0, 0), subtitle, font=FONT_BODY)
    draw.text(((1280 - (box[2]-box[0])) / 2, 420), subtitle, font=FONT_BODY, fill=(255, 255, 255, 235))
    return CompositeVideoClip([bg, logo, ImageClip(np.array(image), duration=duration)], size=SIZE)


def finale_card(duration):
    bg = gradient_background(3, duration)
    names = ["luni.png", "byeori.png", "mongi.png", "kongkong.png", "tori.png", "bambam.png", "lumi.png", "moon-grandma.png"]
    layers = [bg]
    for index, name in enumerate(names):
        height = 225 if name != "moon-grandma.png" else 250
        clip = ImageClip(str(CHARACTERS / name), duration=duration).resized(height=height)
        x = 52 + index * 150
        y = 350 - (25 if index % 2 else 0)
        clip = clip.with_position(lambda t, x=x, y=y, i=index: (x, y + int(8 * math.sin(t * 4 + i))))
        layers.append(clip)
    text = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text)
    title = "루니 루니 달토끼!"
    line = "친구들과 함께라면 오늘도 괜찮아요"
    box = draw.textbbox((0, 0), title, font=FONT_TITLE)
    draw.text(((1280-(box[2]-box[0]))/2, 90), title, font=FONT_TITLE, fill=(255, 245, 160, 255))
    box = draw.textbbox((0, 0), line, font=FONT_BODY)
    draw.text(((1280-(box[2]-box[0]))/2, 185), line, font=FONT_BODY, fill=(255, 255, 255, 245))
    layers.append(ImageClip(np.array(text), duration=duration))
    return CompositeVideoClip(layers, size=SIZE)


def pair_card(first, second, index, duration):
    bg = gradient_background(index + 1, duration)
    layers = [bg]
    for side, item in enumerate((first, second)):
        speaker, latin, _, image, color = item
        source = CHARACTERS / "poses" / image
        if not source.exists():
            source = CHARACTERS / image
        height = 385 if speaker != "달할머니" else 420
        clip = ImageClip(str(source), duration=duration).resized(height=height)
        base_x = 145 if side == 0 else 785
        phase = index * 1.2 + side
        clip = clip.with_position(
            lambda t, x=base_x, p=phase: (
                x + int(12 * math.sin(t * 3.4 + p)),
                180 + int(12 * math.sin(t * 4.1 + p)),
            )
        )
        layers.append(clip)
        label = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(label)
        x1 = 85 if side == 0 else 725
        draw.rounded_rectangle(
            (x1, 535, x1 + 470, 650),
            radius=24,
            fill=(255, 252, 246, 235),
        )
        draw.text((x1 + 30, 552), speaker, font=FONT_BODY, fill=(55, 45, 91, 255))
        draw.text((x1 + 30, 600), latin, font=FONT_BODY, fill=(*color, 255))
        layers.append(ImageClip(np.array(label), duration=duration))
    return CompositeVideoClip(layers, size=SIZE)


def upbeat_music(duration, sample_rate=44100):
    total = int(duration * sample_rate)
    signal = np.zeros(total, dtype=np.float64)
    chords = [
        (261.63, 329.63, 392.00),
        (293.66, 369.99, 440.00),
        (220.00, 277.18, 329.63),
        (246.94, 311.13, 369.99),
    ]
    melody = [523.25, 659.25, 783.99, 659.25, 587.33, 698.46, 783.99, 880.00]

    def add(start, length, frequency, amplitude, bright=0.18):
        first = int(start * sample_rate)
        last = min(total, int((start + length) * sample_rate))
        if first >= last:
            return
        t = np.arange(last-first) / sample_rate
        envelope = np.minimum(t / 0.04, 1) * np.minimum((length-t) / 0.15, 1)
        wave = np.sin(2*np.pi*frequency*t)
        wave += bright*np.sin(2*np.pi*frequency*2*t)
        signal[first:last] += amplitude*np.clip(envelope, 0, 1)*wave

    for measure in range(math.ceil(duration / 2)):
        start = measure * 2
        chord = chords[measure % 4]
        for f in chord:
            add(start, 1.85, f, 0.022, 0.06)
        for beat in range(4):
            add(start + beat*0.5, 0.30, melody[(measure*4+beat) % len(melody)], 0.030)
        for beat in range(8):
            add(start + beat*0.25, 0.05, 1760, 0.008, 0)
    fade = min(int(sample_rate*0.7), total//2)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    return np.column_stack([signal, signal]).astype(np.float32), sample_rate


async def make_voices():
    WORK.mkdir(parents=True, exist_ok=True)
    scenes = []
    for index, (speaker, _, line, _, _) in enumerate(CAST, start=1):
        scene = {"speaker": speaker, "text": line, "voice": "ko-KR-SunHiNeural"}
        path = WORK / f"voice-{index:02d}.mp3"
        scenes.append(create_voice(scene, path))
    final = {
        "speaker": "노래",
        "text": "루니 루니 달토끼, 친구들과 함께해요. 반짝반짝 웃으며 오늘도 모험을 떠나요!",
        "voice": "ko-KR-HyunsuMultilingualNeural",
    }
    scenes.append(create_voice(final, WORK / "voice-final.mp3"))
    await asyncio.gather(*scenes)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    asyncio.run(make_voices())
    clips = []
    opened_audio = []

    intro_duration = 3.0
    clips.append(opening_card(intro_duration))
    for index, (speaker, latin, line, image, color) in enumerate(CAST, start=1):
        audio = AudioFileClip(str(WORK / f"voice-{index:02d}.mp3")).with_volume_scaled(1.05)
        duration = max(2.45, audio.duration + 0.3)
        bg = gradient_background(index, duration)
        card = ImageClip(np.array(text_card(speaker, latin, line, color, index)), duration=duration)
        character = character_layer(image, duration, index)
        clip = CompositeVideoClip([bg, card, character], size=SIZE).with_duration(duration).with_audio(audio)
        clip = clip.with_effects([vfx.CrossFadeIn(0.18), vfx.CrossFadeOut(0.18)])
        clips.append(clip)
        opened_audio.append(audio)

    final_audio = AudioFileClip(str(WORK / "voice-final.mp3")).with_volume_scaled(1.08)
    final_duration = max(5.0, final_audio.duration + 0.45)
    clips.append(finale_card(final_duration).with_audio(final_audio))
    opened_audio.append(final_audio)

    video = concatenate_videoclips(clips, method="compose", padding=-0.12)
    music, sample_rate = upbeat_music(video.duration)
    music_clip = AudioArrayClip(music, fps=sample_rate).with_volume_scaled(0.68).with_duration(video.duration)
    video = video.with_audio(CompositeAudioClip([music_clip, video.audio]))
    output = OUTPUT / "LUNI-GENERIQUE-INTRO.mp4"
    video.write_videofile(
        str(output),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="3500k",
        threads=4,
    )
    shutil.copy2(LOGO, OUTPUT / "tokkimi-logo.png")

    short_clips = [opening_card(2.1)]
    for pair_index in range(4):
        short_clips.append(
            pair_card(
                CAST[pair_index * 2],
                CAST[pair_index * 2 + 1],
                pair_index,
                2.15,
            ).with_effects([vfx.CrossFadeIn(0.14), vfx.CrossFadeOut(0.14)])
        )
    short_final_audio = AudioFileClip(str(WORK / "voice-final.mp3")).with_volume_scaled(1.08)
    short_clips.append(finale_card(5.0).with_audio(short_final_audio))
    short_video = concatenate_videoclips(short_clips, method="compose", padding=-0.1)
    short_music, short_sample_rate = upbeat_music(short_video.duration)
    short_music_clip = AudioArrayClip(
        short_music, fps=short_sample_rate
    ).with_volume_scaled(0.68).with_duration(short_video.duration)
    short_video = short_video.with_audio(
        CompositeAudioClip([short_music_clip, short_video.audio])
    )
    short_output = OUTPUT / "LUNI-GENERIQUE-COURT-CHAQUE-EPISODE.mp4"
    short_video.write_videofile(
        str(short_output),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="3500k",
        threads=4,
    )
    (OUTPUT / "paroles-ko-fr.txt").write_text(
        "달토끼 루니 - Générique d'ouverture\n\n"
        "루니 루니 달토끼, 친구들과 함께해요.\n"
        "반짝반짝 웃으며 오늘도 모험을 떠나요!\n\n"
        "Luni, Luni, lapin de la Lune, retrouvons tous nos amis.\n"
        "Avec un sourire scintillant, partons aujourd'hui à l'aventure !\n",
        encoding="utf-8",
    )
    (OUTPUT / "LISEZ-MOI.txt").write_text(
        "Pour chaque épisode, utilisez LUNI-GENERIQUE-COURT-CHAQUE-EPISODE.mp4.\n"
        "LUNI-GENERIQUE-INTRO.mp4 est la version complète de présentation.\n"
        "Format : 1280x720, 24 images/seconde, audio AAC.\n",
        encoding="utf-8",
    )
    video.close()
    music_clip.close()
    for audio in opened_audio:
        audio.close()
    for clip in clips:
        clip.close()
    short_video.close()
    short_music_clip.close()
    short_final_audio.close()
    for clip in short_clips:
        clip.close()
    print(output)
    print(short_output)


if __name__ == "__main__":
    main()
