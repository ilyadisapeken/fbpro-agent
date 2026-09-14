import os
import json
import glob
import subprocess
import textwrap
from datetime import datetime

# ==========================================
# KONFIGURASI
# ==========================================

WIDTH = 1080
HEIGHT = 1920

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ==========================================
# CARI FILE PRODUCTION TERBARU
# ==========================================

files = glob.glob("production/*.json")

if not files:
    raise SystemExit(
        "Tidak ada file JSON di folder production/"
    )

latest_file = max(
    files,
    key=os.path.getmtime
)

print("Production source:")
print(latest_file)

with open(
    latest_file,
    "r",
    encoding="utf-8"
) as f:
    data = json.load(f)


# ==========================================
# FOLDER OUTPUT
# ==========================================

os.makedirs("videos", exist_ok=True)
os.makedirs("video_tmp", exist_ok=True)

timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

output_video = (
    f"videos/FBPro_Reels_{timestamp}.mp4"
)


# ==========================================
# AMBIL DATA
# ==========================================

video_info = data.get("video", {})

title = video_info.get(
    "judul",
    "FBPro Reels"
)

storyboard = data.get(
    "storyboard",
    []
)

voice_over = data.get(
    "voice_over",
    ""
)

if not storyboard:
    raise SystemExit(
        "Storyboard tidak ditemukan."
    )

if not voice_over:
    raise SystemExit(
        "Voice-over tidak ditemukan."
    )


# ==========================================
# BUAT VOICE OVER
# ==========================================

voice_file = "video_tmp/voice.wav"

print()
print("Membuat voice-over...")

subprocess.run(
    [
        "espeak-ng",
        "-v",
        "id",
        "-s",
        "145",
        "-p",
        "45",
        "-w",
        voice_file,
        voice_over
    ],
    check=True
)


# ==========================================
# BUAT SCENE
# ==========================================

scene_files = []

colors = [
    "101828",
    "172554",
    "312e81",
    "3f1d38",
    "164e63",
    "365314",
    "4c1d95",
    "7c2d12"
]

print()
print("Membuat scene...")


for index, scene in enumerate(storyboard):

    number = index + 1

    duration = scene.get(
        "durasi_detik",
        5
    )

    try:
        duration = float(duration)
    except:
        duration = 5

    if duration < 2:
        duration = 2

    visual = scene.get(
        "visual",
        ""
    )

    text_screen = scene.get(
        "teks_layar",
        ""
    )

    scene_voice = scene.get(
        "voice_over",
        ""
    )

    # --------------------------------------
    # Gabungkan informasi scene
    # --------------------------------------

    if not text_screen:
        text_screen = scene_voice

    if not text_screen:
        text_screen = visual

    # Batasi panjang teks
    text_screen = str(text_screen)[:220]

    # --------------------------------------
    # Buat file teks untuk FFmpeg
    # --------------------------------------

    text_file = (
        f"video_tmp/text_{number}.txt"
    )

    with open(
        text_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(text_screen)

    scene_file = (
        f"video_tmp/scene_{number}.mp4"
    )

    color = colors[
        index % len(colors)
    ]

    # --------------------------------------
    # FFmpeg scene
    # --------------------------------------

    filter_text = (
        f"drawtext="
        f"fontfile={FONT}:"
        f"textfile={text_file}:"
        f"fontcolor=white:"
        f"fontsize=58:"
        f"line_spacing=18:"
        f"x=(w-text_w)/2:"
        f"y=(h-text_h)/2:"
        f"box=1:"
        f"boxcolor=black@0.45:"
        f"boxborderw=35:"
        f"enable='between(t,0,{duration})'"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=#{color}:s={WIDTH}x{HEIGHT}:r=30",
            "-vf",
            filter_text,
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-an",
            scene_file
        ],
        check=True
    )

    scene_files.append(
        scene_file
    )


# ==========================================
# BUAT CONCAT LIST
# ==========================================

concat_file = "video_tmp/concat.txt"

with open(
    concat_file,
    "w",
    encoding="utf-8"
) as f:

    for scene in scene_files:

        absolute_path = os.path.abspath(
            scene
        )

        f.write(
            f"file '{absolute_path}'\n"
        )


# ==========================================
# GABUNGKAN SCENE
# ==========================================

silent_video = (
    "video_tmp/silent_video.mp4"
)

print()
print("Menggabungkan scene...")


subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        silent_video
    ],
    check=True
)


# ==========================================
# GABUNG VIDEO + VOICE
# ==========================================

print()
print("Menggabungkan voice-over...")


subprocess.run(
    [
        "ffmpeg",
        "-y",
        "-i",
        silent_video,
        "-i",
        voice_file,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-shortest",
        output_video
    ],
    check=True
)


# ==========================================
# SELESAI
# ==========================================

print()
print("========================================")
print("FBPRO VIDEO AGENT BERHASIL")
print("========================================")
print()
print(f"Sumber : {latest_file}")
print(f"Video  : {output_video}")
print()
