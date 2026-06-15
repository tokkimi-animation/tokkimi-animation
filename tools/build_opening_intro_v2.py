import asyncio
import math
import shutil
import subprocess

import imageio_ffmpeg
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

from build_episode import ROOT


SIZE = (1280, 720)
FPS = 60
OUTPUT = ROOT / "ready-to-upload" / "GENERIQUE-INTRO"
WORK = ROOT / "production" / "opening-intro-v2"
CHARACTERS = ROOT / "assets" / "characters"
POSES = CHARACTERS / "poses"
LOGO = ROOT / "assets" / "images" / "tokkimi-logo.png"

FONT_TITLE = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 68)
FONT_NAME = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 50)
FONT_LATIN = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 24)

CAST = [
    ("별이", "BYEORI", "byeori.png", "byeori-pointing.png", (255, 213, 76), "spin"),
    ("몽이", "MONGI", "mongi.png", "mongi-sneeze.png", (161, 220, 241), "sneeze"),
    ("콩콩", "KONGKONG", "kongkong.png", "kongkong-jump.png", (226, 161, 96), "jump"),
    ("토리", "TORI", "tori.png", "tori-inventing.png", (239, 151, 102), "invent"),
    ("밤밤", "BAMBAM", "bambam.png", "bambam-brave.png", (203, 158, 112), "brave"),
    ("루미", "LUMI", "lumi.png", "lumi-discovery.png", (180, 160, 221), "glide"),
    ("달할머니", "MOON GRANDMA", "moon-grandma.png", "moon-grandma-comfort.png", (239, 204, 147), "magic"),
]


def backdrop(index, duration):
    palettes = [
        ((73, 68, 151), (177, 158, 224)),
        ((74, 134, 188), (188, 226, 226)),
        ((123, 84, 168), (248, 193, 149)),
        ((86, 74, 159), (240, 171, 171)),
    ]
    top, bottom = palettes[index % len(palettes)]
    pixels = np.zeros((SIZE[1], SIZE[0], 3), dtype=np.uint8)
    for y in range(SIZE[1]):
        mix = y / (SIZE[1] - 1)
        pixels[y, :, :] = np.array(top) * (1 - mix) + np.array(bottom) * mix
    image = Image.fromarray(pixels).filter(ImageFilter.GaussianBlur(0.4))
    draw = ImageDraw.Draw(image, "RGBA")
    rng = np.random.default_rng(9182 + index)
    for _ in range(45):
        x = int(rng.integers(15, 1265))
        y = int(rng.integers(15, 640))
        radius = int(rng.integers(2, 6))
        draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                     fill=(255, 247, 188, int(rng.integers(90, 210))))
    draw.ellipse((-120, 520, 1400, 900), fill=(255, 255, 255, 75))
    return ImageClip(np.array(image), duration=duration)


def name_plate(name, latin, color, duration, right=False):
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    x = 700 if right else 75
    draw.rounded_rectangle((x, 470, x+470, 625), radius=32,
                           fill=(255, 253, 247, 238))
    draw.rectangle((x+30, 505, x+42, 590), fill=(*color, 255))
    draw.text((x+70, 492), name, font=FONT_NAME, fill=(52, 43, 88, 255))
    draw.text((x+73, 557), latin, font=FONT_LATIN, fill=(112, 98, 151, 255))
    return ImageClip(np.array(image), duration=duration)


def character_motion(path, action, duration, index, start=0, base=False):
    source = (CHARACTERS if base else POSES) / path
    clip = ImageClip(str(source), duration=duration).resized(height=530)
    side = -1 if index % 2 else 1
    target_x = 690 if side == -1 else 95

    def pos(t):
        p = min(1.0, t / 0.52)
        ease = p * p * (3 - 2 * p)
        x = target_x + side * int(480 * (1-ease))
        y = 105 + int(5 * math.sin(t * 5.2))
        if action == "jump":
            y -= int(95 * math.sin(min(1, t / 0.9) * math.pi))
        elif action == "sneeze":
            y += int(13 * math.sin(t * 12) * math.exp(-2.2*t))
        elif action == "spin":
            y -= int(20 * math.sin(t * 4))
        elif action == "invent":
            x += int(18 * math.sin(t * 6))
            y -= int(12 * math.sin(t * 5))
        elif action == "brave":
            y -= int(22 * math.sin(min(1, t / 0.7) * math.pi))
        elif action == "glide":
            x += int(22 * math.sin(t * 2.6))
            y += int(12 * math.sin(t * 4.2))
        elif action == "magic":
            y += int(9 * math.sin(t * 3))
        return x, y

    clip = clip.with_position(pos)
    if action == "spin":
        clip = clip.rotated(lambda t: 8 * math.sin(t * 5))
    elif action == "sneeze":
        clip = clip.resized(lambda t: 1.0 + 0.035 * math.sin(t * 11) * math.exp(-2*t))
    elif action == "brave":
        clip = clip.resized(lambda t: 0.94 + 0.06 * min(1, t / 0.8))
    return clip.with_start(start)


def title_scene(duration):
    bg = backdrop(0, duration)
    logo = ImageClip(str(LOGO), duration=duration).resized(height=175)
    logo = logo.with_position(lambda t: (552, 70-int(12*math.sin(min(1,t/.7)*math.pi))))
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    title = "달토끼 루니"
    subtitle = "달빛 친구들을 만나러 가요!"
    box = draw.textbbox((0, 0), title, font=FONT_TITLE)
    draw.text(((1280-(box[2]-box[0]))/2, 305), title, font=FONT_TITLE,
              fill=(255, 245, 155, 255))
    box = draw.textbbox((0, 0), subtitle, font=FONT_LATIN)
    draw.text(((1280-(box[2]-box[0]))/2, 410), subtitle, font=FONT_LATIN,
              fill=(255, 255, 255, 240))
    text = ImageClip(np.array(image), duration=duration)
    return CompositeVideoClip([bg, logo, text], size=SIZE)


def cast_scene(item, index, duration=1.65):
    name, latin, base_path, pose_path, color, action = item
    right = index % 2 == 0
    pose_start = 0.38
    return CompositeVideoClip([
        backdrop(index + 1, duration),
        character_motion(base_path, action, pose_start, index, base=True),
        character_motion(
            pose_path, action, duration - pose_start, index, start=pose_start
        ),
        name_plate(name, latin, color, duration, right=not right),
    ], size=SIZE).with_duration(duration).with_effects(
        [vfx.CrossFadeIn(0.10), vfx.CrossFadeOut(0.10)]
    )


def luni_final(duration):
    bg = backdrop(3, duration)
    position = lambda t: (
        355 + int(8 * math.sin(t * 3.2)),
        92 - int(18 * math.sin(min(1, t / .65) * math.pi))
        + int(4 * math.sin(t * 5.1)),
    )
    normal1 = (
        ImageClip(str(CHARACTERS / "luni.png"), duration=0.72)
        .resized(height=570).with_position(position)
        .with_effects([vfx.FadeIn(0.16), vfx.FadeOut(0.14)])
    )
    surprised = (
        ImageClip(str(POSES / "luni-surprised-v2.png"), duration=0.68)
        .resized(height=570).with_start(0.60).with_position(position)
        .with_effects([vfx.FadeIn(0.14), vfx.FadeOut(0.14)])
    )
    listening = (
        ImageClip(str(POSES / "luni-listening.png"), duration=0.72)
        .resized(height=570).with_start(1.14).with_position(position)
        .with_effects([vfx.FadeIn(0.14), vfx.FadeOut(0.14)])
    )
    wink = (
        ImageClip(str(POSES / "luni-wink.png"), duration=duration-1.70)
        .resized(height=570).with_start(1.70).with_position(position)
        .with_effects([vfx.FadeIn(0.16)])
    )
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((390, 565, 890, 665), radius=32, fill=(255, 252, 242, 235))
    phrase = "안녕! 나는 루니야!"
    box = draw.textbbox((0, 0), phrase, font=FONT_NAME)
    draw.text(((1280-(box[2]-box[0]))/2, 580), phrase, font=FONT_NAME,
              fill=(79, 63, 137, 255))
    phrase_clip = (
        ImageClip(np.array(image), duration=duration - 1.48)
        .with_start(1.48)
        .with_effects([vfx.FadeIn(0.18)])
    )
    return CompositeVideoClip(
        [bg, normal1, surprised, listening, wink, phrase_clip],
        size=SIZE,
    ).with_duration(duration)


def musical_score(duration, sample_rate=44100):
    total = int(duration * sample_rate)
    signal = np.zeros(total, dtype=np.float64)

    def note(start, length, frequency, amplitude, kind="bell"):
        a = int(start * sample_rate)
        b = min(total, int((start + length) * sample_rate))
        if b <= a:
            return
        t = np.arange(b-a) / sample_rate
        attack = np.minimum(t / 0.025, 1)
        release = np.exp(-3.3 * t / max(length, 0.01))
        env = attack * release
        if kind == "bell":
            wave = np.sin(2*np.pi*frequency*t)
            wave += .32*np.sin(2*np.pi*frequency*2.01*t)
            wave += .12*np.sin(2*np.pi*frequency*3.97*t)
        elif kind == "pluck":
            wave = np.sin(2*np.pi*frequency*t) + .18*np.sin(2*np.pi*frequency*2*t)
        else:
            wave = np.sin(2*np.pi*frequency*t)
        signal[a:b] += amplitude * env * wave

    def drum(start, amplitude, noise=False):
        length = .10 if noise else .16
        a = int(start*sample_rate)
        b = min(total, int((start+length)*sample_rate))
        if b <= a:
            return
        t = np.arange(b-a)/sample_rate
        if noise:
            rng = np.random.default_rng(int(start*1000)+55)
            wave = rng.normal(0, 1, b-a) * np.exp(-30*t)
        else:
            freq = 115*np.exp(-18*t)+48
            wave = np.sin(2*np.pi*freq*t) * np.exp(-22*t)
        signal[a:b] += amplitude*wave

    progression = [
        (261.63, 329.63, 392.00),
        (220.00, 277.18, 329.63),
        (174.61, 220.00, 261.63),
        (196.00, 246.94, 293.66),
        (233.08, 293.66, 349.23),
        (261.63, 329.63, 392.00),
    ]
    melody_sections = [
        [523.25, 659.25, 783.99, 659.25],
        [587.33, 698.46, 880.00, 783.99],
        [659.25, 587.33, 523.25, 493.88],
        [523.25, 622.25, 698.46, 783.99],
        [880.00, 783.99, 698.46, 659.25],
        [659.25, 783.99, 1046.50, 783.99],
    ]
    beat = .42
    for bar in range(math.ceil(duration / (beat*4))):
        start = bar*beat*4
        chord = progression[bar % len(progression)]
        melody = melody_sections[(bar//2) % len(melody_sections)]
        for frequency in chord:
            note(start, beat*3.8, frequency, .014, "sine")
        note(start, beat*.8, chord[0]/2, .027, "pluck")
        note(start+beat*2, beat*.8, chord[1]/2, .024, "pluck")
        for step in range(4):
            note(start+step*beat, beat*.65, melody[step], .028, "bell")
        drum(start, .028)
        drum(start+beat*2, .025)
        drum(start+beat, .009, noise=True)
        drum(start+beat*3, .012, noise=True)

    # A short airy bridge before Luni's final line.
    bridge_start = max(0, duration - 4.2)
    bridge_end = min(total, int((bridge_start + 1.2)*sample_rate))
    signal[int(bridge_start*sample_rate):bridge_end] *= np.linspace(1, .35, bridge_end-int(bridge_start*sample_rate))
    voice_start = duration - 2.8
    signal[int(voice_start*sample_rate):] *= .48

    fade = min(int(sample_rate*.45), total//2)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    peak = max(np.max(np.abs(signal)), 1e-6)
    signal *= .19 / peak
    return np.column_stack([signal, signal]).astype(np.float32), sample_rate


async def final_voice(raw_path, soft_path):
    import edge_tts

    if not raw_path.exists() or raw_path.stat().st_size < 1_000:
        await edge_tts.Communicate(
            "안녕! 나는 루니야!",
            "ko-KR-SunHiNeural",
            rate="-2%",
            pitch="+2Hz",
            volume="-12%",
        ).save(str(raw_path))
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-y",
            "-i",
            str(raw_path),
            "-af",
            (
                "silenceremove=start_periods=1:start_duration=0.03:"
                "start_threshold=-48dB:stop_periods=-1:stop_duration=0.20:"
                "stop_threshold=-48dB,atempo=1.12,lowpass=f=9500,treble=g=-2"
            ),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "128k",
            str(soft_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    raw_voice_path = WORK / "luni-final-raw.mp3"
    voice_path = WORK / "luni-final-soft.mp3"
    asyncio.run(final_voice(raw_voice_path, voice_path))

    clips = [title_scene(2.0)]
    clips.extend(cast_scene(item, index) for index, item in enumerate(CAST, start=1))
    final_duration = 3.2
    clips.append(luni_final(final_duration))
    video = concatenate_videoclips(clips, method="compose", padding=-0.08)

    music, rate = musical_score(video.duration)
    music_clip = AudioArrayClip(music, fps=rate).with_duration(video.duration)
    voice = AudioFileClip(str(voice_path)).with_volume_scaled(0.92)
    voice_start = video.duration - 2.02
    voice = voice.with_start(voice_start)
    video = video.with_audio(CompositeAudioClip([music_clip, voice]))

    output = OUTPUT / "LUNI-GENERIQUE-V3-FLUIDE-CHAQUE-EPISODE.mp4"
    video.write_videofile(
        str(output),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="5200k",
        threads=4,
    )
    shutil.copy2(output, OUTPUT / "LUNI-GENERIQUE-COURT-CHAQUE-EPISODE.mp4")
    shutil.copy2(output, OUTPUT / "LUNI-GENERIQUE-V2-CHAQUE-EPISODE.mp4")
    (OUTPUT / "LISEZ-MOI.txt").write_text(
        "Version recommandée : LUNI-GENERIQUE-V3-FLUIDE-CHAQUE-EPISODE.mp4\n"
        "Animation 60 images/seconde, changements de poses et expressions, "
        "puis Luni : « 안녕! 나는 루니야! » avec un clin d’œil.\n",
        encoding="utf-8",
    )
    (OUTPUT / "REGARDER-LE-GENERIQUE.html").write_text(
        """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Nouveau générique de 달토끼 루니</title>
  <style>
    body { margin:0; padding:30px; color:#30294f; background:#f2edff;
      font-family:"Segoe UI",Arial,sans-serif; text-align:center; }
    main { width:min(1050px,96vw); margin:auto; }
    h1 { margin-bottom:5px; }
    p { color:#6a617c; }
    video { width:100%; margin-top:18px; border-radius:22px; background:#171323;
      box-shadow:0 18px 55px rgba(56,42,95,.25); }
    nav { display:flex; justify-content:center; margin:25px 0; }
    a { padding:12px 17px; border-radius:12px; color:white; background:#6b5aa6;
      text-decoration:none; font-weight:800; }
  </style>
</head>
<body>
  <main>
    <h1>달토끼 루니 · Nouveau générique</h1>
    <p>Animation fluide à 60 images/seconde, expressions vivantes et voix adoucie.</p>
    <video controls autoplay preload="auto" poster="tokkimi-logo.png">
      <source src="LUNI-GENERIQUE-V3-FLUIDE-CHAQUE-EPISODE.mp4" type="video/mp4">
    </video>
    <nav>
      <a href="LUNI-GENERIQUE-V3-FLUIDE-CHAQUE-EPISODE.mp4" download>
        Télécharger le générique final
      </a>
    </nav>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    video.close()
    music_clip.close()
    voice.close()
    for clip in clips:
        clip.close()
    print(output)


if __name__ == "__main__":
    main()
