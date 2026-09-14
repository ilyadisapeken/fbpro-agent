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
FPS = 30

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ==========================================
# CARI PRODUCTION TERBARU
# ==========================================

files = glob.glob("production/*.json")

if not files:
    raise SystemExit(
        "Tidak ada file production/*.json"
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

storyboard = data.get("storyboard", [])

if not storyboard:
    raise SystemExit(
        "Storyboard tidak ditemukan."
    )

# ==========================================
# FOLDER
# ==========================================

os.makedirs("visuals", exist_ok=True)
os.makedirs("visual_tmp", exist_ok=True)

timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

output_video = (
    f"visuals/FBPro_Visual_{timestamp}.mp4"
)

# ==========================================
# BUAT VISUAL SETIAP ADEGAN
# ==========================================

scene_files = []

print()
print("Membuat visual cinematic...")

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

    text_screen = scene.get(
        "teks_layar",
        ""
    )

    visual = scene.get(
        "visual",
        ""
    )

    if not text_screen:
        text_screen = visual

    text_screen = str(text_screen)[:180]

    text_file = (
        f"visual_tmp/text_{number}.txt"
    )

    with open(
        text_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(text_screen)

    scene_file = (
        f"visual_tmp/visual_{number}.mp4"
    )

    # ======================================
    # VARIASI VISUAL
    # ======================================

    colors = [
        "0f172a",
        "172554",
        "312e81",
        "3f1d38",
        "164e63",
        "365314",
        "4c1d95",
        "7c2d12"
    ]

    color = colors[
        index % len(colors)
    ]

    # ======================================
    # BACKGROUND DENGAN GERAKAN
    # ======================================

    zoom = (
        "zoompan="
        "z='min(zoom+0.0008,1.15)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"d={int(duration * FPS)}:"
        f"s={WIDTH}x{HEIGHT}:"
        f"fps={FPS}"
    )

    draw_text = (
        f"drawtext="
        f"fontfile={FONT}:"
        f"textfile={text_file}:"
        f"fontcolor=white:"
        f"fontsize=62:"
        f"line_spacing=20:"
        f"x=(w-text_w)/2:"
        f"y=(h-text_h)/2:"
        f"box=1:"
        f"boxcolor=black@0.48:"
        f"boxborderw=40:"
        f"shadowcolor=black@0.8:"
        f"shadowx=3:"
        f"shadowy=3"
    )

    filter_complex = (
        f"color=c=#{color}:"
        f"s={WIDTH}x{HEIGHT}:"
        f"r={FPS},"
        f"format=yuv420p,"
        f"{zoom},"
        f"{draw_text}"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            filter_complex,
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            scene_file
        ],
        check=True
    )

    scene_files.append(scene_file)

# ==========================================
# CONCAT
# ==========================================

concat_file = (
    "visual_tmp/visual_concat.txt"
)

with open(
    concat_file,
    "w",
    encoding="utf-8"
) as f:

    for scene_file in scene_files:

        path = os.path.abspath(
            scene_file
        )

        f.write(
            f"file '{path}'\n"
        )

# ==========================================
# GABUNG VISUAL
# ==========================================

print()
print("Menggabungkan semua visual...")

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
        output_video
    ],
    check=True
)

# ==========================================
# SELESAI
# ==========================================

print()
print("========================================")
print("FBPRO VISUAL AGENT BERHASIL")
print("========================================")
print()
print(f"Sumber : {latest_file}")
print(f"Visual : {output_video}")
print()
