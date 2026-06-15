import argparse
import json
import math
import shutil
import subprocess
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
READY = ROOT / "ready-to-upload"
REMASTERED = ROOT / "remastered"
ASSETS = ROOT / "assets"
CHARACTERS = ASSETS / "characters"
POSES = CHARACTERS / "poses"
INTRO = READY / "GENERIQUE-INTRO" / "LUNI-GENERIQUE-V6-VRAIMENT-ANIME.mp4"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 30
SIZE = (1920, 1080)
SAMPLE_RATE = 44100
SHOT_TYPES = ("wide", "medium", "close-up", "reaction", "decor")
CAMERAS = ("zoom-in", "pan-right", "zoom-out", "pan-left", "tilt-up")
EMOTIONS = (
    "wonder",
    "mystery",
    "sadness",
    "adventure",
    "hope",
    "resolution",
)


@dataclass
class Dialogue:
    index: int
    speaker: str
    text: str
    voice: Path
    duration: float
    scene: dict


def run(command, *, capture=False):
    return subprocess.run(
        [str(value) for value in command],
        check=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
        text=capture,
    )


def probe_duration(path):
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(path), "-f", "null", "NUL"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    marker = "Duration: "
    position = result.stderr.find(marker)
    if position < 0:
        raise RuntimeError(f"Durée illisible : {path}")
    value = result.stderr[position + len(marker):].split(",", 1)[0]
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def safe_name(value):
    return "".join(character if character.isalnum() else "-" for character in value)


def ep001_data():
    sys.path.insert(0, str(ROOT / "tools"))
    import build_ep001

    work = ROOT / "production" / "season-01" / "ep001-lost-star" / "build"
    dialogues = []
    for index, scene in enumerate(build_ep001.SCENES, start=1):
        voice = work / f"voice-{index:02d}.mp3"
        if not voice.exists():
            raise FileNotFoundError(voice)
        dialogues.append(
            Dialogue(
                index=index,
                speaker=scene["speaker"],
                text=scene["text"],
                voice=voice,
                duration=probe_duration(voice),
                scene=scene,
            )
        )
    return build_ep001, dialogues


def split_duration(duration):
    if duration <= 5.8:
        return [duration]
    count = max(2, math.ceil(duration / 5.2))
    part = duration / count
    return [part] * count


def emotion_for(dialogue_index, total):
    progress = dialogue_index / total
    if progress < 0.14:
        return "wonder"
    if progress < 0.34:
        return "sadness"
    if progress < 0.62:
        return "mystery"
    if progress < 0.80:
        return "adventure"
    if progress < 0.92:
        return "hope"
    return "resolution"


def build_storyboard(dialogues, intro_duration):
    shots = []
    cursor = intro_duration
    shot_index = 1
    total = len(dialogues)
    for dialogue in dialogues:
        reaction_gap = 0.55 if "?" in dialogue.text else 0.34
        block_duration = dialogue.duration + reaction_gap
        parts = split_duration(block_duration)
        for part_index, duration in enumerate(parts):
            shot_type = SHOT_TYPES[(shot_index - 1) % len(SHOT_TYPES)]
            if part_index == len(parts) - 1 and len(parts) > 1:
                shot_type = "reaction"
            emotion = emotion_for(dialogue.index, total)
            shot = {
                "id": f"S{shot_index:03d}",
                "dialogue": dialogue.index,
                "start": round(cursor, 3),
                "duration": round(duration, 3),
                "end": round(cursor + duration, 3),
                "shot_type": shot_type,
                "camera": CAMERAS[(shot_index - 1) % len(CAMERAS)],
                "keyframes": 2,
                "speaker": dialogue.speaker,
                "text": dialogue.text,
                "emotion": emotion,
                "micro_animations": [
                    "blink",
                    "breathing",
                    "head-turn",
                    "ear-or-arm-reaction",
                    "eye-line-to-speaker",
                ],
                "background_motion": [
                    "twinkling-stars",
                    "floating-particles",
                    "soft-light",
                ],
            }
            shots.append(shot)
            cursor += duration
            shot_index += 1
    return {
        "episode": "EP001",
        "version": 1,
        "resolution": "1920x1080",
        "fps": FPS,
        "intro_duration": round(intro_duration, 3),
        "main_duration": round(cursor - intro_duration, 3),
        "outro_duration": 6.0,
        "rules": {
            "shot_duration_seconds": [3, 7],
            "maximum_dialogue_gap_seconds": 0.8,
            "camera_motion_required": True,
            "reaction_required_when_silent": True,
        },
        "shots": shots,
    }


def character_pose(name, shot_index, reaction=False):
    variants = {
        "luni": [
            CHARACTERS / "luni.png",
            POSES / "luni-listening.png",
            POSES / "luni-surprised-v2.png",
            POSES / "luni-wink.png",
            POSES / "luni-motion-3.png",
        ],
        "byeori": [
            CHARACTERS / "byeori.png",
            POSES / "byeori-pointing.png",
            POSES / "byeori-worried.png",
            POSES / "byeori-motion-3.png",
            POSES / "byeori-motion-4.png",
        ],
        "mongi": [CHARACTERS / "mongi.png", POSES / "mongi-motion-3.png"],
        "kongkong": [
            CHARACTERS / "kongkong.png",
            POSES / "kongkong-motion-3.png",
        ],
    }
    choices = variants.get(name, [CHARACTERS / f"{name}.png"])
    offset = 1 if reaction else 0
    return choices[(shot_index + offset) % len(choices)]


def scene_character_names(scene):
    names = [item[0] for item in scene.get("characters", [])]
    if scene.get("small_star"):
        names.append("byeori")
    return names or ["luni", "byeori"]


def layout_for(shot_type, names):
    if shot_type == "wide":
        positions = [(130, 410, 430), (1180, 420, 380), (760, 500, 280)]
    elif shot_type == "medium":
        positions = [(170, 290, 610), (1180, 330, 520), (770, 470, 310)]
    elif shot_type == "close-up":
        positions = [(560, 150, 820), (1290, 430, 360), (120, 500, 300)]
    elif shot_type == "reaction":
        positions = [(1070, 190, 750), (180, 390, 460), (760, 500, 280)]
    else:
        positions = [(180, 520, 330), (1360, 520, 300), (820, 550, 230)]
    return positions[: len(names)]


def paste_contain(canvas, asset_path, x, y, height, mirror=False):
    image = Image.open(asset_path).convert("RGBA")
    if mirror:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    width = max(1, round(image.width * height / image.height))
    image = image.resize((width, height), Image.Resampling.LANCZOS)
    canvas.alpha_composite(image, (int(x), int(y)))


def decorate_background(image, shot_index, variant, emotion):
    canvas = image.convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    rng = np.random.default_rng(1200 + shot_index * 13 + variant)
    tint = {
        "wonder": (255, 232, 148),
        "mystery": (169, 188, 255),
        "sadness": (170, 205, 240),
        "adventure": (255, 194, 128),
        "hope": (180, 238, 209),
        "resolution": (255, 221, 151),
    }[emotion]
    for particle in range(34):
        x = int(rng.integers(20, SIZE[0] - 20))
        y = int(rng.integers(30, 720))
        radius = int(rng.integers(2, 7))
        alpha = int(rng.integers(55, 175))
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(*tint, alpha),
        )
    glow_x = 250 + (shot_index * 173 + variant * 95) % 1450
    glow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse(
        (glow_x - 240, 40, glow_x + 240, 520),
        fill=(*tint, 38),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(95))
    return Image.alpha_composite(canvas, glow)


def make_keyframe(builder, dialogue, shot, variant, output):
    base = builder.make_background(dialogue.scene["place"]).convert("RGB")
    base = base.resize(SIZE, Image.Resampling.LANCZOS)
    base = ImageEnhance.Color(base).enhance(1.08)
    canvas = decorate_background(
        base, int(shot["id"][1:]), variant, shot["emotion"]
    )
    names = scene_character_names(dialogue.scene)
    if shot["shot_type"] == "decor":
        names = names[:1]
    positions = layout_for(shot["shot_type"], names)
    for index, (name, position) in enumerate(zip(names, positions)):
        x, y, height = position
        if variant:
            x += 18 * (-1 if index % 2 else 1)
            y += 8 if index % 2 else -10
        pose = character_pose(
            name,
            int(shot["id"][1:]) + index,
            reaction=bool(variant or shot["shot_type"] == "reaction"),
        )
        paste_contain(
            canvas,
            pose,
            x,
            y,
            height,
            mirror=index % 2 == 1,
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, quality=94)


def zoom_filter(camera, duration):
    frames = max(1, round(duration * FPS))
    progress = f"on/{max(1, frames - 1)}"
    if camera == "zoom-in":
        z = f"1.02+0.055*{progress}"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "zoom-out":
        z = f"1.085-0.055*{progress}"
        x = "iw/2-(iw/zoom/2)"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "pan-right":
        z = "1.075"
        x = f"(iw-iw/zoom)*{progress}"
        y = "ih/2-(ih/zoom/2)"
    elif camera == "pan-left":
        z = "1.075"
        x = f"(iw-iw/zoom)*(1-{progress})"
        y = "ih/2-(ih/zoom/2)"
    else:
        z = "1.07"
        x = "iw/2-(iw/zoom/2)"
        y = f"(ih-ih/zoom)*(1-{progress})"
    return (
        f"scale=2304:1296:flags=lanczos,"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:"
        f"s={SIZE[0]}x{SIZE[1]}:fps={FPS},"
        f"fps={FPS},settb=AVTB,format=yuv420p,setpts=PTS-STARTPTS"
    )


def render_shot(image_a, image_b, shot, output):
    duration = float(shot["duration"])
    first = max(1.55, duration * 0.53)
    second = duration - first + 0.18
    filter_a = zoom_filter(shot["camera"], first)
    reverse_camera = {
        "zoom-in": "zoom-out",
        "zoom-out": "zoom-in",
        "pan-left": "pan-right",
        "pan-right": "pan-left",
        "tilt-up": "zoom-in",
    }[shot["camera"]]
    filter_b = zoom_filter(reverse_camera, second)
    complex_filter = (
        f"[0:v]{filter_a}[a];"
        f"[1:v]{filter_b}[b];"
        "[a][b]concat=n=2:v=1:a=0,"
        "tmix=frames=3:weights='1 2 1',"
        "unsharp=5:5:0.35:3:3:0.15[v]"
    )
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-t",
            f"{first:.3f}",
            "-i",
            image_a,
            "-loop",
            "1",
            "-t",
            f"{second:.3f}",
            "-i",
            image_b,
            "-filter_complex",
            complex_filter,
            "-map",
            "[v]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-r",
            str(FPS),
            "-t",
            f"{duration:.3f}",
            output,
        ]
    )


def decode_audio(path):
    result = run(
        [
            FFMPEG,
            "-i",
            path,
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-ac",
            "2",
            "-ar",
            str(SAMPLE_RATE),
            "pipe:1",
        ],
        capture=True,
    )
    return np.frombuffer(result.stdout.encode("latin1"), dtype=np.float32)


def read_audio_bytes(path):
    result = subprocess.run(
        [
            FFMPEG,
            "-i",
            str(path),
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-ac",
            "2",
            "-ar",
            str(SAMPLE_RATE),
            "pipe:1",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return np.frombuffer(result.stdout, dtype=np.float32).reshape(-1, 2)


def add_tone(track, start, duration, frequency, volume, kind="soft"):
    first = max(0, int(start * SAMPLE_RATE))
    last = min(len(track), int((start + duration) * SAMPLE_RATE))
    if last <= first:
        return
    t = np.arange(last - first) / SAMPLE_RATE
    attack = np.minimum(t / 0.08, 1)
    release = np.minimum((duration - t) / 0.22, 1)
    envelope = np.clip(attack * release, 0, 1)
    wave = np.sin(2 * np.pi * frequency * t)
    if kind == "magic":
        wave += 0.22 * np.sin(2 * np.pi * frequency * 2 * t)
        wave += 0.08 * np.sin(2 * np.pi * frequency * 3 * t)
    track[first:last, 0] += volume * envelope * wave
    track[first:last, 1] += volume * envelope * wave


def build_audio(dialogues, storyboard, output):
    duration = storyboard["main_duration"]
    count = math.ceil(duration * SAMPLE_RATE)
    voice_mix = np.zeros((count, 2), dtype=np.float64)
    music = np.zeros((count, 2), dtype=np.float64)
    effects = np.zeros((count, 2), dtype=np.float64)
    voice_mask = np.zeros(count, dtype=np.float64)
    cursor = 0.0
    voice_ranges = []
    for dialogue in dialogues:
        samples = read_audio_bytes(dialogue.voice).astype(np.float64)
        start = int(cursor * SAMPLE_RATE)
        end = min(count, start + len(samples))
        voice_mix[start:end] += samples[: end - start] * 0.94
        voice_mask[start:end] = 1.0
        voice_ranges.append((cursor, cursor + len(samples) / SAMPLE_RATE))
        cursor += dialogue.duration + (0.55 if "?" in dialogue.text else 0.34)

    chords = {
        "wonder": (261.63, 329.63, 392.00),
        "mystery": (220.00, 261.63, 329.63),
        "sadness": (196.00, 246.94, 293.66),
        "adventure": (293.66, 369.99, 440.00),
        "hope": (246.94, 329.63, 392.00),
        "resolution": (261.63, 349.23, 440.00),
    }
    beat = 0.72
    for step in range(math.ceil(duration / beat)):
        start = step * beat
        progress = start / max(duration, 0.1)
        emotion = EMOTIONS[min(len(EMOTIONS) - 1, int(progress * len(EMOTIONS)))]
        chord = chords[emotion]
        add_tone(music, start, beat * 0.92, chord[step % 3], 0.016)
        if step % 2 == 0:
            add_tone(music, start, beat * 1.7, chord[0] / 2, 0.010)
        if step % 4 == 0:
            add_tone(effects, start, 0.45, chord[2] * 2, 0.018, "magic")

    ramp = max(1, int(0.18 * SAMPLE_RATE))
    kernel = np.ones(ramp * 2 + 1) / (ramp * 2 + 1)
    smoothed_mask = np.convolve(voice_mask, kernel, mode="same")
    music_gain = 0.88 - 0.58 * np.clip(smoothed_mask, 0, 1)
    mix = music * music_gain[:, None] + effects * 0.62 + voice_mix
    peak = max(np.max(np.abs(mix)), 1e-6)
    mix *= min(1.0, 0.92 / peak)
    pcm = np.clip(mix * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())
    return voice_ranges


def concat_video_files(files, output):
    listing = output.with_suffix(".txt")
    listing.write_text(
        "".join(f"file '{path.as_posix()}'\n" for path in files),
        encoding="utf-8",
    )
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            listing,
            "-c",
            "copy",
            output,
        ]
    )
    listing.unlink(missing_ok=True)


def mux_audio(video, audio, output):
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            video,
            "-i",
            audio,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            output,
        ]
    )


def normalize_intro(output):
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            INTRO,
            "-vf",
            (
                "fps=30,scale=1920:1080:flags=lanczos,"
                "format=yuv420p,unsharp=5:5:0.25"
            ),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            output,
        ]
    )


def make_outro(builder, work):
    scene = {
        "place": "ending",
        "characters": [
            ("luni", 0.10, 0.30, 0.55),
            ("byeori", 0.66, 0.42, 0.28),
            ("mongi", 0.78, 0.52, 0.24),
        ],
    }
    dialogue = Dialogue(99, "", "", Path(), 6.0, scene)
    shot = {
        "id": "S999",
        "duration": 6.0,
        "shot_type": "wide",
        "camera": "zoom-out",
        "emotion": "resolution",
    }
    first = work / "outro-a.jpg"
    second = work / "outro-b.jpg"
    make_keyframe(builder, dialogue, shot, 0, first)
    make_keyframe(builder, dialogue, shot, 1, second)
    video = work / "outro-silent.mp4"
    render_shot(first, second, shot, video)
    audio = work / "outro.wav"
    track = np.zeros((6 * SAMPLE_RATE, 2), dtype=np.float64)
    for step, frequency in enumerate((523.25, 659.25, 783.99, 1046.50)):
        add_tone(track, step * 0.65, 1.5, frequency, 0.035, "magic")
    add_tone(track, 3.0, 2.8, 261.63, 0.018)
    pcm = np.clip(track * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(audio), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())
    result = work / "outro.mp4"
    mux_audio(video, audio, result)
    return result


def write_subtitles(dialogues, voice_ranges, intro_duration, output):
    def timestamp(seconds):
        millis = round(seconds * 1000)
        hours, millis = divmod(millis, 3_600_000)
        minutes, millis = divmod(millis, 60_000)
        secs, millis = divmod(millis, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    blocks = []
    for dialogue, (start, end) in zip(dialogues, voice_ranges):
        blocks.append(
            f"{dialogue.index}\n"
            f"{timestamp(intro_duration + start)} --> "
            f"{timestamp(intro_duration + end)}\n"
            f"{dialogue.text}\n"
        )
    output.write_text("\n".join(blocks), encoding="utf-8")


def make_comparison(new_video, intro_duration, output):
    old_video = READY / "EP001" / "EP001-lost-star.mp4"
    font = r"C\:/Windows/Fonts/malgunbd.ttf"
    filters = (
        "[0:v]trim=start=0:duration=45,setpts=PTS-STARTPTS,"
        "fps=30,scale=960:540:flags=lanczos,"
        f"drawtext=fontfile='{font}':text='AVANT':"
        "x=40:y=35:fontsize=44:fontcolor=white:"
        "box=1:boxcolor=black@0.55:boxborderw=14[old];"
        f"[1:v]trim=start={intro_duration}:duration=45,setpts=PTS-STARTPTS,"
        "fps=30,scale=960:540:flags=lanczos,"
        f"drawtext=fontfile='{font}':text='APRÈS':"
        "x=40:y=35:fontsize=44:fontcolor=white:"
        "box=1:boxcolor=black@0.55:boxborderw=14[new];"
        "[old][new]hstack=inputs=2[v]"
    )
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            old_video,
            "-i",
            new_video,
            "-filter_complex",
            filters,
            "-map",
            "[v]",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-t",
            "45",
            "-movflags",
            "+faststart",
            output,
        ]
    )


def write_viewer(episode_dir):
    document = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>EP001 remasterisé · Tokkimi</title>
  <style>
    body{margin:0;padding:28px;background:#f1edff;color:#30294f;
      font-family:"Segoe UI",Arial,sans-serif}
    main{width:min(1180px,96vw);margin:auto}
    h1{margin-bottom:6px} p{color:#665d7c}
    video{display:block;width:100%;margin:18px 0 35px;border-radius:20px;
      background:#171323;box-shadow:0 18px 55px #392d6440}
    a{display:inline-block;padding:12px 16px;border-radius:12px;
      background:#6b5aa6;color:white;text-decoration:none;font-weight:800}
  </style>
</head>
<body><main>
  <h1>EP001 · Pilote remasterisé</h1>
  <p>1080p · 30 FPS · 28 plans dynamiques · générique et outro inclus</p>
  <video controls preload="metadata" src="EP001-REMASTERED-YOUTUBE.mp4"></video>
  <h2>Comparaison avant / après</h2>
  <video controls preload="metadata" src="EP001-AVANT-APRES.mp4"></video>
  <a href="EP001-REMASTERED-YOUTUBE.mp4" download>Télécharger le MP4</a>
</main></body></html>"""
    (episode_dir / "REGARDER-EP001.html").write_text(document, encoding="utf-8")


def build_ep001():
    builder, dialogues = ep001_data()
    episode_dir = REMASTERED / "EP001"
    work = episode_dir / "work"
    shots_dir = work / "shots"
    keyframes_dir = work / "keyframes"
    episode_dir.mkdir(parents=True, exist_ok=True)
    shots_dir.mkdir(parents=True, exist_ok=True)
    keyframes_dir.mkdir(parents=True, exist_ok=True)

    intro_duration = probe_duration(INTRO)
    storyboard = build_storyboard(dialogues, intro_duration)
    storyboard_path = episode_dir / "storyboard.json"
    storyboard_path.write_text(
        json.dumps(storyboard, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    dialogue_map = {dialogue.index: dialogue for dialogue in dialogues}
    shot_files = []
    for shot in storyboard["shots"]:
        dialogue = dialogue_map[shot["dialogue"]]
        image_a = keyframes_dir / f"{shot['id']}-a.jpg"
        image_b = keyframes_dir / f"{shot['id']}-b.jpg"
        video = shots_dir / f"{shot['id']}.mp4"
        make_keyframe(builder, dialogue, shot, 0, image_a)
        make_keyframe(builder, dialogue, shot, 1, image_b)
        render_shot(image_a, image_b, shot, video)
        shot_files.append(video)
        print(
            f"{shot['id']} {shot['shot_type']} {shot['camera']} "
            f"{shot['duration']:.2f}s",
            flush=True,
        )

    silent_main = work / "main-silent.mp4"
    concat_video_files(shot_files, silent_main)
    audio = work / "main-audio.wav"
    voice_ranges = build_audio(dialogues, storyboard, audio)
    main = work / "main.mp4"
    mux_audio(silent_main, audio, main)
    intro = work / "intro.mp4"
    normalize_intro(intro)
    outro = make_outro(builder, work)

    final = episode_dir / "EP001-REMASTERED-YOUTUBE.mp4"
    listing = work / "final.txt"
    listing.write_text(
        f"file '{intro.as_posix()}'\n"
        f"file '{main.as_posix()}'\n"
        f"file '{outro.as_posix()}'\n",
        encoding="utf-8",
    )
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            listing,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            "-af",
            "aresample=async=1:first_pts=0",
            "-movflags",
            "+faststart",
            final,
        ]
    )
    write_subtitles(
        dialogues,
        voice_ranges,
        intro_duration,
        episode_dir / "subtitles-ko.srt",
    )
    comparison = {
        "old_video": str(READY / "EP001" / "EP001-lost-star.mp4"),
        "new_video": str(final),
        "old_duration": probe_duration(
            READY / "EP001" / "EP001-lost-star.mp4"
        ),
        "new_duration": probe_duration(final),
        "old_fps": 12,
        "new_fps": FPS,
        "old_resolution": "1920x1080",
        "new_resolution": "1920x1080",
        "new_shot_count": len(storyboard["shots"]),
        "maximum_silence": 0.55,
    }
    (episode_dir / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    make_comparison(
        final,
        intro_duration,
        episode_dir / "EP001-AVANT-APRES.mp4",
    )
    write_viewer(episode_dir)
    print(f"READY {final}")


def generic_storyboard(episode, duration, intro_duration):
    shots = []
    elapsed = 0.0
    index = 1
    while elapsed < duration:
        shot_duration = min(5.0 + (index % 3) * 0.5, duration - elapsed)
        shots.append(
            {
                "id": f"S{index:03d}",
                "start": round(intro_duration + elapsed, 3),
                "duration": round(shot_duration, 3),
                "shot_type": SHOT_TYPES[(index - 1) % len(SHOT_TYPES)],
                "camera": CAMERAS[(index - 1) % len(CAMERAS)],
                "micro_animations": ["source-reaction", "camera-motion"],
            }
        )
        elapsed += shot_duration
        index += 1
    return {
        "episode": episode,
        "version": 1,
        "resolution": "1920x1080",
        "fps": FPS,
        "intro_duration": round(intro_duration, 3),
        "main_duration": round(duration, 3),
        "outro_duration": 6.0,
        "shots": shots,
    }


def shared_youtube_assets():
    shared = REMASTERED / "_shared"
    shared.mkdir(parents=True, exist_ok=True)
    intro = shared / "intro-1080p30.mp4"
    outro = shared / "outro-1080p30.mp4"
    if not intro.exists():
        normalize_intro(intro)
    if not outro.exists():
        sys.path.insert(0, str(ROOT / "tools"))
        import build_ep001

        outro = make_outro(build_ep001, shared)
    return intro, outro


def remaster_generic(episode):
    number = int(episode[2:])
    source_name = "EP001-lost-star.mp4" if number == 1 else f"{episode}.mp4"
    source = READY / episode / source_name
    if not source.exists():
        raise FileNotFoundError(source)
    output_dir = REMASTERED / episode
    work = output_dir / "work"
    output_dir.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    duration = probe_duration(source)
    intro, outro = shared_youtube_assets()
    storyboard = generic_storyboard(episode, duration, probe_duration(intro))
    (output_dir / "storyboard.json").write_text(
        json.dumps(storyboard, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    body = work / f"{episode}-body.mp4"
    camera = (
        "scale=2112:1188:flags=lanczos,"
        "crop=1920:1080:"
        "x='(iw-ow)/2+((iw-ow)/2)*sin(t*0.45)':"
        "y='(ih-oh)/2+((ih-oh)/2)*sin(t*0.31)',"
        "fps=30,tmix=frames=2:weights='1 2',"
        "unsharp=5:5:0.30,format=yuv420p"
    )
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            source,
            "-vf",
            camera,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "19",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            body,
        ]
    )
    listing = work / "final.txt"
    listing.write_text(
        f"file '{intro.as_posix()}'\n"
        f"file '{body.as_posix()}'\n"
        f"file '{outro.as_posix()}'\n",
        encoding="utf-8",
    )
    output = output_dir / f"{episode}-REMASTERED-YOUTUBE.mp4"
    run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            listing,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "2",
            "-af",
            "aresample=async=1:first_pts=0",
            "-movflags",
            "+faststart",
            output,
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--episode")
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    REMASTERED.mkdir(parents=True, exist_ok=True)
    if args.episode:
        episode = args.episode.upper()
        if episode == "EP001":
            build_ep001()
        else:
            remaster_generic(episode)
        return
    for number in range(1, 101):
        episode = f"EP{number:03d}"
        if episode == "EP001":
            build_ep001()
        else:
            remaster_generic(episode)


if __name__ == "__main__":
    main()
