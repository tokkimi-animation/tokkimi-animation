import math
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "assets" / "characters" / "rig" / "luni" / "luni-rig-sheet.png"
VOICE = (
    ROOT
    / "production"
    / "season-01"
    / "ep001-lost-star"
    / "build"
    / "voice-01.mp3"
)
OUTPUT = ROOT / "remastered" / "EP001" / "RIG-TEST"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
SIZE = (1920, 1080)
FPS = 30
SAMPLE_RATE = 44100


REGIONS = {
    "head": (15, 45, 310, 290),
    "ear_floppy": (320, 45, 510, 285),
    "ear_moon": (525, 25, 665, 285),
    "body": (665, 55, 885, 350),
    "arm_left": (905, 50, 1000, 225),
    "arm_right_wave": (1250, 45, 1390, 215),
    "arm_right_open": (1165, 45, 1275, 220),
    "eye_left": (45, 370, 112, 455),
    "eye_right": (128, 370, 192, 455),
    "eye_closed_left": (550, 380, 615, 430),
    "eye_closed_right": (635, 380, 700, 430),
    "mouth_rest": (665, 510, 745, 565),
    "mouth_small": (305, 505, 375, 580),
    "mouth_wide": (1230, 500, 1345, 590),
    "mouth_o": (790, 500, 865, 585),
    "mouth_smile": (540, 500, 640, 585),
}


def trim(image):
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    return image.crop(bbox) if bbox else image


def extract_parts():
    sheet = Image.open(SHEET).convert("RGBA")
    parts = {}
    folder = OUTPUT / "parts"
    folder.mkdir(parents=True, exist_ok=True)
    for name, box in REGIONS.items():
        part = trim(sheet.crop(box))
        parts[name] = part
        part.save(folder / f"{name}.png")
    return parts


def audio_envelope():
    result = subprocess.run(
        [
            FFMPEG,
            "-i",
            str(VOICE),
            "-f",
            "f32le",
            "-acodec",
            "pcm_f32le",
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "pipe:1",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    samples = np.frombuffer(result.stdout, dtype=np.float32)
    duration = len(samples) / SAMPLE_RATE
    window = max(1, SAMPLE_RATE // FPS)
    envelope = []
    for start in range(0, len(samples), window):
        block = samples[start : start + window]
        envelope.append(float(np.sqrt(np.mean(block * block))) if len(block) else 0)
    envelope = np.array(envelope)
    high = np.percentile(envelope, 92) if len(envelope) else 1
    envelope = np.clip(envelope / max(high, 1e-5), 0, 1)
    return envelope, duration


def background(t):
    top = np.array((61, 61, 142), dtype=np.float64)
    bottom = np.array((184, 162, 224), dtype=np.float64)
    array = np.zeros((SIZE[1], SIZE[0], 3), dtype=np.uint8)
    for y in range(SIZE[1]):
        mix = y / (SIZE[1] - 1)
        array[y, :, :] = top * (1 - mix) + bottom * mix
    image = Image.fromarray(array).convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    moon_x = 1480 + int(18 * math.sin(t * 0.35))
    draw.ellipse((moon_x, 80, moon_x + 190, 270), fill=(255, 226, 126, 245))
    draw.ellipse((moon_x + 70, 48, moon_x + 225, 235), fill=(66, 63, 145, 255))
    for index in range(65):
        x = (index * 263 + int(t * (9 + index % 5))) % SIZE[0]
        y = (index * 137 + 43) % 690
        pulse = 80 + int(120 * (0.5 + 0.5 * math.sin(t * 2.4 + index)))
        radius = 2 + index % 4
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 242, 170, pulse))
    draw.ellipse((-180, 790, 2100, 1380), fill=(239, 214, 231, 215))
    for index in range(7):
        x = 90 + index * 280 + int(8 * math.sin(t * 0.7 + index))
        draw.rounded_rectangle((x, 675, x + 200, 850), 28, fill=(249, 221, 194, 235))
        draw.polygon(((x - 14, 700), (x + 100, 600), (x + 214, 700)), fill=(112, 91, 171, 240))
    return image


def scale(image, height):
    width = max(1, round(image.width * height / image.height))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def transformed(image, height, angle=0, scale_x=1.0, scale_y=1.0):
    image = scale(image, height)
    image = image.resize(
        (max(1, round(image.width * scale_x)), max(1, round(image.height * scale_y))),
        Image.Resampling.LANCZOS,
    )
    return image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)


def paste_center(canvas, image, center):
    canvas.alpha_composite(
        image,
        (round(center[0] - image.width / 2), round(center[1] - image.height / 2)),
    )


def mouth_for(parts, level, frame):
    if level < 0.12:
        return parts["mouth_rest"]
    if level < 0.32:
        return parts["mouth_small"]
    if level < 0.60:
        return parts["mouth_o"] if frame % 5 < 2 else parts["mouth_smile"]
    return parts["mouth_wide"]


def render():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frames = OUTPUT / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    parts = extract_parts()
    envelope, voice_duration = audio_envelope()
    duration = voice_duration + 1.15
    frame_count = math.ceil(duration * FPS)

    for frame in range(frame_count):
        t = frame / FPS
        canvas = background(t)
        talking = envelope[min(frame, len(envelope) - 1)] if len(envelope) else 0
        entrance = min(1.0, t / 0.65)
        ease = entrance * entrance * (3 - 2 * entrance)
        base_x = 960 + (1 - ease) * 420
        body_y = 700 + 10 * math.sin(t * 2.1)
        breath = 1.0 + 0.012 * math.sin(t * 3.2)
        weight = 5 * math.sin(t * 1.35)
        head_angle = -3 + 4 * math.sin(t * 0.85) + 1.8 * talking

        tail = transformed(parts["arm_left"], 120, angle=-40)
        tail = ImageEnhance.Brightness(tail).enhance(1.02)
        paste_center(canvas, tail, (base_x - 125, body_y + 60))

        body = transformed(parts["body"], 410, angle=weight * 0.25, scale_y=breath)
        paste_center(canvas, body, (base_x, body_y))

        left_arm_angle = 8 + 8 * math.sin(t * 1.9)
        left_arm = transformed(parts["arm_left"], 230, angle=left_arm_angle)
        paste_center(canvas, left_arm, (base_x - 145, body_y - 65))

        wave_phase = math.sin(t * 5.4)
        right_arm = transformed(
            parts["arm_right_wave" if t < 4.3 else "arm_right_open"],
            250,
            angle=-28 + 17 * wave_phase if t < 4.3 else -8 + 7 * math.sin(t * 2.5),
        )
        paste_center(canvas, right_arm, (base_x + 150, body_y - 105))

        floppy_angle = 7 + 10 * math.sin(t * 2.25 + 0.4)
        moon_angle = -2 + 3 * math.sin(t * 1.8)
        floppy = transformed(parts["ear_floppy"], 335, angle=floppy_angle)
        moon_ear = transformed(parts["ear_moon"], 335, angle=moon_angle)
        paste_center(canvas, floppy, (base_x - 130, body_y - 385))
        paste_center(canvas, moon_ear, (base_x + 115, body_y - 405))

        head = transformed(parts["head"], 415, angle=head_angle, scale_y=1 + 0.006 * talking)
        head_center = (base_x + 8 * math.sin(t * 1.2), body_y - 260 + 5 * math.sin(t * 2.1))
        paste_center(canvas, head, head_center)

        blink = any(abs(t - point) < 0.075 for point in (1.85, 1.98, 4.72, 7.15))
        gaze = 7 * math.sin(t * 0.72)
        eye_left = parts["eye_closed_left"] if blink else parts["eye_left"]
        eye_right = parts["eye_closed_right"] if blink else parts["eye_right"]
        eye_left = transformed(eye_left, 76 if not blink else 32, angle=head_angle * 0.15)
        eye_right = transformed(eye_right, 76 if not blink else 32, angle=head_angle * 0.15)
        paste_center(canvas, eye_left, (head_center[0] - 62 + gaze, head_center[1] + 20))
        paste_center(canvas, eye_right, (head_center[0] + 66 + gaze, head_center[1] + 20))

        face_draw = ImageDraw.Draw(canvas, "RGBA")
        face_draw.ellipse(
            (
                head_center[0] - 135,
                head_center[1] + 70,
                head_center[0] - 72,
                head_center[1] + 111,
            ),
            fill=(250, 151, 143, 105),
        )
        face_draw.ellipse(
            (
                head_center[0] + 78,
                head_center[1] + 70,
                head_center[0] + 141,
                head_center[1] + 111,
            ),
            fill=(250, 151, 143, 105),
        )
        nose_x, nose_y = head_center[0] + 3, head_center[1] + 78
        face_draw.polygon(
            (
                (nose_x - 9, nose_y - 5),
                (nose_x + 9, nose_y - 5),
                (nose_x, nose_y + 5),
            ),
            fill=(225, 111, 101, 255),
        )

        mouth = mouth_for(parts, talking, frame)
        mouth_height = 40 + int(18 * talking)
        mouth = transformed(mouth, mouth_height, angle=head_angle * 0.08)
        paste_center(canvas, mouth, (head_center[0] + 3, head_center[1] + 118))

        canvas = canvas.filter(ImageFilter.GaussianBlur(0.12))
        canvas.convert("RGB").save(frames / f"{frame:05d}.jpg", quality=92)

    silent = OUTPUT / "luni-rig-animation-silent.mp4"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            str(FPS),
            "-i",
            str(frames / "%05d.jpg"),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            str(silent),
        ],
        check=True,
    )
    final = OUTPUT / "LUNI-RIG-VIVANT-TEST.mp4"
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(silent),
            "-i",
            str(VOICE),
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
            "-af",
            "apad=pad_dur=1.15",
            "-t",
            f"{duration:.3f}",
            "-movflags",
            "+faststart",
            str(final),
        ],
        check=True,
    )
    print(final)


if __name__ == "__main__":
    render()
