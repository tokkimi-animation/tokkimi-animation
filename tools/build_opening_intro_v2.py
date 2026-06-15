import asyncio
import math
import shutil
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy import (
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
    x = 755 if right else 105
    y = 470
    # An illustrated caption: shadow, sparkle and hand-drawn underline, no box.
    draw.text((x+4, y+5), name, font=FONT_NAME, fill=(37, 28, 70, 90))
    draw.text((x, y), name, font=FONT_NAME, fill=(255, 252, 238, 255),
              stroke_width=2, stroke_fill=(72, 57, 120, 220))
    name_box = draw.textbbox((x, y), name, font=FONT_NAME, stroke_width=2)
    line_y = name_box[3] + 8
    draw.line(
        [(x+2, line_y), (x+92, line_y+4), (x+185, line_y-1)],
        fill=(*color, 245), width=7, joint="curve",
    )
    star_x = x - 32
    star_y = y + 23
    draw.regular_polygon(
        (star_x, star_y, 13), n_sides=4, rotation=45,
        fill=(255, 236, 132, 255),
    )
    draw.text((x+4, line_y+12), latin, font=FONT_LATIN,
              fill=(255, 250, 235, 235),
              stroke_width=1, stroke_fill=(72, 57, 120, 180))
    return ImageClip(np.array(image), duration=duration)


def character_motion(slug, duration, index):
    starts = [0.0, 0.30, 0.66, 1.06]
    ends = [0.42, 0.80, 1.20, duration]
    target_center = 950 if index % 2 else 350
    ground = 590
    clips = []
    for frame in range(1, 5):
        start, end = starts[frame-1], ends[frame-1]
        clip = ImageClip(
            str(POSES / f"{slug}-motion-{frame}.png"), duration=end-start
        ).resized(height=500)
        x = target_center - clip.w / 2
        y = ground - clip.h

        def position(t, x=x, y=y, frame=frame):
            # Tiny breathing follow-through only; the action is in the drawings.
            settle = 2.5 * math.sin(t * 5.2) if frame in {1, 4} else 0
            return x, y + settle

        clip = clip.with_start(start).with_position(position)
        effects = []
        if frame > 1:
            effects.append(vfx.CrossFadeIn(0.10))
        if frame < 4:
            effects.append(vfx.CrossFadeOut(0.10))
        clips.append(clip.with_effects(effects))
    return clips


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
    slug = base_path.removesuffix(".png")
    return CompositeVideoClip([
        backdrop(index + 1, duration),
        *character_motion(slug, duration, index),
        name_plate(name, latin, color, duration, right=not right),
    ], size=SIZE).with_duration(duration).with_effects(
        [vfx.CrossFadeIn(0.10), vfx.CrossFadeOut(0.10)]
    )


def luni_final(duration):
    bg = backdrop(3, duration)
    def keyframe(number, start, end, motion):
        clip = ImageClip(
            str(POSES / f"luni-motion-{number}.png"), duration=end - start
        ).resized(height=520)
        center_x = (SIZE[0] - clip.w) / 2
        base_y = 525 - clip.h

        def position(t):
            if motion == "crouch":
                amount = math.sin(min(1, t / max(end - start, .01)) * math.pi)
                return center_x, base_y + 28 * amount
            if motion == "rise":
                amount = math.sin(min(1, t / max(end - start, .01)) * math.pi)
                return center_x, base_y - 18 * amount
            return center_x, base_y + 3 * math.sin(t * 5)

        clip = clip.with_start(start).with_position(position)
        if motion == "crouch":
            clip = clip.resized(
                lambda t: 1.0 - 0.035 * math.sin(
                    min(1, t / max(end - start, .01)) * math.pi
                )
            )
        elif motion == "rise":
            clip = clip.rotated(lambda t: -2.5 * math.sin(t * 6))
        return clip

    luni_frames = [
        keyframe(1, 0.0, 0.58, "breathe"),
        keyframe(2, 0.58, 1.04, "crouch"),
        keyframe(3, 1.04, 1.76, "rise"),
        keyframe(4, 1.76, duration, "breathe"),
    ]
    image = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    phrase = "나, 루니야!"
    box = draw.textbbox((0, 0), phrase, font=FONT_NAME)
    phrase_x = (1280-(box[2]-box[0]))/2
    draw.text((phrase_x+4, 584), phrase, font=FONT_NAME,
              fill=(44, 30, 78, 100))
    draw.text((phrase_x, 580), phrase, font=FONT_NAME,
              fill=(255, 249, 215, 255),
              stroke_width=2, stroke_fill=(79, 63, 137, 230))
    draw.line((phrase_x+15, 650, phrase_x+box[2]-box[0]-15, 650),
              fill=(255, 207, 91, 235), width=6)
    phrase_clip = (
        ImageClip(np.array(image), duration=duration - 1.48)
        .with_start(1.48)
        .with_effects([vfx.FadeIn(0.18)])
    )
    return CompositeVideoClip(
        [bg, *luni_frames, phrase_clip],
        size=SIZE,
    ).with_duration(duration)


def musical_score(duration, sample_rate=44100):
    total = int(duration * sample_rate)
    signal = np.zeros(total, dtype=np.float64)

    def note(start, length, frequency, amplitude, kind="piano"):
        a = int(start * sample_rate)
        b = min(total, int((start + length) * sample_rate))
        if b <= a:
            return
        t = np.arange(b-a) / sample_rate
        attack = np.minimum(t / 0.018, 1)
        release = np.exp(-2.7 * t / max(length, 0.01))
        env = attack * release
        if kind == "pad":
            attack = np.minimum(t / 0.16, 1)
            release = np.minimum((length - t) / 0.16, 1)
            env = attack * np.maximum(0, release)
            wave = np.sin(2*np.pi*frequency*t)
            wave += .10*np.sin(2*np.pi*frequency*2*t)
        elif kind == "musicbox":
            wave = np.sin(2*np.pi*frequency*t)
            wave += .16*np.sin(2*np.pi*frequency*2*t)
            wave += .04*np.sin(2*np.pi*frequency*3*t)
        elif kind == "ukulele":
            wave = np.sin(2*np.pi*frequency*t)
            wave += .24*np.sin(2*np.pi*frequency*2*t)
            wave += .08*np.sin(2*np.pi*frequency*3*t)
            env *= np.exp(-4.5*t/max(length, .01))
        else:
            wave = (
                np.sin(2*np.pi*frequency*t)
                + .12*np.sin(2*np.pi*frequency*2*t)
            )
        signal[a:b] += amplitude * env * wave

    # Warm C-major children's theme: soft ukulele, piano and music-box melody.
    progression = [
        (261.63, 329.63, 392.00),
        (196.00, 246.94, 293.66),
        (220.00, 261.63, 329.63),
        (174.61, 220.00, 261.63),
        (261.63, 329.63, 392.00),
    ]
    melody_sections = [
        [523.25, 659.25, 783.99, 659.25],
        [587.33, 659.25, 587.33, 493.88],
        [523.25, 659.25, 880.00, 783.99],
        [698.46, 659.25, 587.33, 523.25],
    ]
    beat = .48
    for bar in range(math.ceil(duration / (beat*4))):
        start = bar*beat*4
        chord = progression[bar % len(progression)]
        melody = melody_sections[bar % len(melody_sections)]
        for frequency in chord:
            note(start, beat*4.08, frequency/2, .012, "pad")
        for frequency in chord:
            note(start, beat*3.9, frequency, .012, "piano")
        # Two gentle down-strums per bar, with tiny offsets for a human feel.
        for offset, frequency in enumerate(chord):
            note(start+offset*.018, beat*.9, frequency, .020, "ukulele")
            note(start+beat*2+offset*.016, beat*.8, frequency, .015, "ukulele")
        for step in range(4):
            note(start+step*beat, beat*.72, melody[step], .022, "musicbox")
        note(start, beat*1.6, chord[0]/2, .016, "piano")
        note(start+beat*2, beat*1.6, chord[2]/2, .013, "piano")

    # A short airy bridge before Luni's final line.
    bridge_start = max(0, duration - 4.2)
    bridge_end = min(total, int((bridge_start + 1.2)*sample_rate))
    signal[int(bridge_start*sample_rate):bridge_end] *= np.linspace(1, .35, bridge_end-int(bridge_start*sample_rate))
    fade = min(int(sample_rate*.45), total//2)
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    peak = max(np.max(np.abs(signal)), 1e-6)
    signal *= .22 / peak
    return np.column_stack([signal, signal]).astype(np.float32), sample_rate


def read_voice(path, sample_rate=44100):
    completed = subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(path),
            "-f", "f32le", "-acodec", "pcm_f32le",
            "-ac", "2", "-ar", str(sample_rate), "pipe:1",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return np.frombuffer(completed.stdout, dtype=np.float32).reshape(-1, 2)


def mix_soundtrack(music, voice, voice_start, sample_rate=44100):
    mixed = music.astype(np.float64).copy()
    start = int(voice_start * sample_rate)
    end = min(len(mixed), start + len(voice))
    voice = voice[:end-start].astype(np.float64)

    # Smooth ducking removes the click caused by the old instantaneous cut.
    envelope = np.ones(len(mixed), dtype=np.float64)
    ramp = int(.24 * sample_rate)
    down_start = max(0, start-ramp)
    up_end = min(len(mixed), end+ramp)
    envelope[down_start:start] = np.linspace(1.0, .50, start-down_start)
    envelope[start:end] = .50
    envelope[end:up_end] = np.linspace(.50, 1.0, up_end-end)
    mixed *= envelope[:, None]
    mixed[start:end] += voice * .95

    peak = max(np.max(np.abs(mixed)), 1e-6)
    mixed *= min(1.0, .92 / peak)
    return mixed.astype(np.float32)


async def final_voice(raw_path, soft_path):
    if not raw_path.exists() or raw_path.stat().st_size < 1_000:
        import edge_tts

        await edge_tts.Communicate(
            "나, 루니야!",
            "ko-KR-SunHiNeural",
            rate="+5%",
            pitch="+0Hz",
            volume="-8%",
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
                "stop_threshold=-48dB,highpass=f=90,lowpass=f=11000,"
                "acompressor=threshold=-18dB:ratio=2:attack=20:release=120"
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
    raw_voice_path = WORK / "luni-final-v5-raw.mp3"
    voice_path = WORK / "luni-final-v5-soft.mp3"
    asyncio.run(final_voice(raw_voice_path, voice_path))

    clips = [title_scene(2.0)]
    clips.extend(cast_scene(item, index) for index, item in enumerate(CAST, start=1))
    final_duration = 3.2
    clips.append(luni_final(final_duration))
    video = concatenate_videoclips(clips, method="compose", padding=-0.08)

    music, rate = musical_score(video.duration)
    voice_start = video.duration - 2.02
    voice_samples = read_voice(voice_path, rate)
    soundtrack = mix_soundtrack(music, voice_samples, voice_start, rate)
    music_clip = AudioArrayClip(soundtrack, fps=rate).with_duration(video.duration)
    video = video.with_audio(music_clip)

    output = OUTPUT / "LUNI-GENERIQUE-V6-VRAIMENT-ANIME.mp4"
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
    shutil.copy2(output, OUTPUT / "LUNI-GENERIQUE-V3-FLUIDE-CHAQUE-EPISODE.mp4")
    shutil.copy2(output, OUTPUT / "LUNI-GENERIQUE-V4-ANIME-SANS-GLISSEMENT.mp4")
    shutil.copy2(output, OUTPUT / "LUNI-GENERIQUE-V5-ILLUSTRE.mp4")
    (OUTPUT / "LISEZ-MOI.txt").write_text(
        "Version recommandée : LUNI-GENERIQUE-V6-VRAIMENT-ANIME.mp4\n"
        "Quatre poses d’animation dédiées pour chaque personnage, audio continu, "
        "puis Luni : « 나, 루니야! » avec un clin d’œil.\n",
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
    <p>Chaque personnage possède quatre vraies poses et la piste audio est continue.</p>
    <video controls autoplay preload="auto" poster="tokkimi-logo.png">
      <source src="LUNI-GENERIQUE-V6-VRAIMENT-ANIME.mp4" type="video/mp4">
    </video>
    <nav>
      <a href="LUNI-GENERIQUE-V6-VRAIMENT-ANIME.mp4" download>
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
    for clip in clips:
        clip.close()
    print(output)


if __name__ == "__main__":
    main()
