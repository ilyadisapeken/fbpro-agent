import os
import json
import glob
import subprocess
from datetime import datetime

# ==========================================
# KONFIGURASI
# ==========================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

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

# ==========================================
# AMBIL DATA
# ==========================================

video_info = data.get(
    "video",
    {}
)

title = video_info.get(
    "judul",
    "FBPro Reels"
)

theme = video_info.get(
    "tema",
    "Inspirasi"
)

storyboard = data.get(
    "storyboard",
    []
)

if not storyboard:
    raise SystemExit(
        "Storyboard tidak ditemukan."
    )

# ==========================================
# FOLDER
# ==========================================

os.makedirs(
    "visuals",
    exist_ok=True
)

os.makedirs(
    "visual_tmp",
    exist_ok=True
)

timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

output_video = (
    f"visuals/"
    f"FBPro_Visual_{timestamp}.mp4"
)

# ==========================================
# FUNGSI BERSIHKAN TEKS
# ==========================================

def clean_text(text, max_length=180):

    if text is None:
        return ""

    text = str(text)

    text = text.replace(
        "\n",
        " "
    )

    text = text.replace(
        "\r",
        " "
    )

    text = " ".join(
        text.split()
    )

    return text[:max_length]


# ==========================================
# BUAT SCENE
# ==========================================

scene_files = []

print()
print("========================================")
print("MEMBUAT VISUAL REELS PRO")
print("========================================")
print()

total_scenes = len(
    storyboard
)

for index, scene in enumerate(
    storyboard
):

    number = index + 1

    # --------------------------------------
    # DURASI
    # --------------------------------------

    duration = scene.get(
        "durasi_detik",
        5
    )

    try:
        duration = float(
            duration
        )
    except:
        duration = 5

    if duration < 2:
        duration = 2

    # --------------------------------------
    # TEKS
    # --------------------------------------

    screen_text = clean_text(
        scene.get(
            "teks_layar",
            ""
        ),
        160
    )

    scene_visual = clean_text(
        scene.get(
            "visual",
            ""
        ),
        120
    )

    scene_voice = clean_text(
        scene.get(
            "voice_over",
            ""
        ),
        160
    )

    if not screen_text:
        screen_text = scene_visual

    if not screen_text:
        screen_text = scene_voice

    if not screen_text:
        screen_text = title

    # --------------------------------------
    # FILE TEKS
    # --------------------------------------

    text_file = (
        f"visual_tmp/"
        f"text_{number}.txt"
    )

    with open(
        text_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            screen_text
        )

    title_file = (
        f"visual_tmp/"
        f"title_{number}.txt"
    )

    with open(
        title_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            clean_text(
                title,
                70
            )
        )

    theme_file = (
        f"visual_tmp/"
        f"theme_{number}.txt"
    )

    with open(
        theme_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            clean_text(
                theme,
                50
            )
        )

    # --------------------------------------
    # WARNA BERGANTI
    # --------------------------------------

    backgrounds = [
        "0b1020",
        "111827",
        "172554",
        "1e1b4b",
        "312e81",
        "164e63",
        "3f1d38",
        "292524"
    ]

    accent_colors = [
        "38bdf8",
        "60a5fa",
        "818cf8",
        "a78bfa",
        "22d3ee",
        "34d399",
        "f472b6",
        "fb923c"
    ]

    background = backgrounds[
        index % len(backgrounds)
    ]

    accent = accent_colors[
        index % len(accent_colors)
    ]

    # --------------------------------------
    # POSISI VISUAL BERGANTI
    # --------------------------------------

    layout = index % 4

    # ======================================
    # LAYOUT 1
    # ======================================

    if layout == 0:

        text_y = 760

        extra_shape = (
            "drawbox="
            "x='mod(t*180,w+500)-500':"
            "y=260:"
            "w=420:"
            "h=420:"
            "color=#"
            f"{accent}@0.12:"
            "t=fill,"
            
            "drawbox="
            "x='w-mod(t*120,w+600)':"
            "y=1220:"
            "w=520:"
            "h=520:"
            "color=#"
            f"{accent}@0.08:"
            "t=fill"
        )

    # ======================================
    # LAYOUT 2
    # ======================================

    elif layout == 1:

        text_y = 640

        extra_shape = (
            "drawbox="
            "x=70:"
            "y='mod(t*100,h+300)-300':"
            "w=940:"
            "h=14:"
            "color=#"
            f"{accent}@0.55:"
            "t=fill,"
            
            "drawbox="
            "x=70:"
            "y='h-mod(t*80,h+400)':"
            "w=940:"
            "h=10:"
            "color=#"
            f"{accent}@0.25:"
            "t=fill"
        )

    # ======================================
    # LAYOUT 3
    # ======================================

    elif layout == 2:

        text_y = 900

        extra_shape = (
            "drawbox="
            "x='w/2-250':"
            "y=300:"
            "w=500:"
            "h=500:"
            "color=#"
            f"{accent}@0.10:"
            "t=fill,"
            
            "drawbox="
            "x='w/2-180':"
            "y=370:"
            "w=360:"
            "h=360:"
            "color=#"
            f"{accent}@0.08:"
            "t=fill"
        )

    # ======================================
    # LAYOUT 4
    # ======================================

    else:

        text_y = 720

        extra_shape = (
            "drawbox="
            "x='mod(t*150,w+800)-800':"
            "y=1450:"
            "w=700:"
            "h=250:"
            "color=#"
            f"{accent}@0.10:"
            "t=fill,"
            
            "drawbox="
            "x='w-mod(t*100,w+700)':"
            "y=300:"
            "w=600:"
            "h=180:"
            "color=#"
            f"{accent}@0.12:"
            "t=fill"
        )

    # ======================================
    # SCENE FILE
    # ======================================

    scene_file = (
        f"visual_tmp/"
        f"visual_{number}.mp4"
    )

    print(
        f"Scene {number}/{total_scenes} "
        f"({duration:.1f} detik)"
    )

    # ======================================
    # FILTER
    # ======================================

    filter_complex = (

        # Background
        f"drawbox="
        f"x=0:y=0:"
        f"w=iw:"
        f"h=ih:"
        f"color=#{background}:"
        f"t=fill,"

        # Animated shapes
        f"{extra_shape},"

        # Top title bar
        "drawbox="
        "x=55:"
        "y=55:"
        "w=970:"
        "h=115:"
        "color=black@0.30:"
        "t=fill,"

        # Theme
        f"drawtext="
        f"fontfile={FONT_REGULAR}:"
        f"textfile={theme_file}:"
        f"fontcolor=#{accent}:"
        f"fontsize=34:"
        f"x=85:"
        f"y=85:"
        f"shadowcolor=black@0.5:"
        f"shadowx=2:"
        f"shadowy=2,"

        # Main title
        f"drawtext="
        f"fontfile={FONT_BOLD}:"
        f"textfile={title_file}:"
        f"fontcolor=white:"
        f"fontsize=38:"
        f"x=85:"
        f"y=122:"
        f"shadowcolor=black@0.7:"
        f"shadowx=3:"
        f"shadowy=3,"

        # Main text panel
        "drawbox="
        "x=65:"
        f"y={text_y - 55}:"
        "w=950:"
        "h=430:"
        "color=black@0.48:"
        "t=fill,"

        # Accent line
        "drawbox="
        "x=65:"
        f"y={text_y - 55}:"
        "w=14:"
        "h=430:"
        f"color=#{accent}:"
        "t=fill,"

        # Main text
        f"drawtext="
        f"fontfile={FONT_BOLD}:"
        f"textfile={text_file}:"
        f"fontcolor=white:"
        f"fontsize=58:"
        f"line_spacing=22:"
        f"x=105:"
        f"y={text_y}:"
        f"box=0:"
        f"shadowcolor=black@0.85:"
        f"shadowx=3:"
        f"shadowy=3,"

        # Scene number
        f"drawtext="
        f"fontfile={FONT_BOLD}:"
        f"text='0{number}':"
        f"fontcolor=#{accent}:"
        f"fontsize=42:"
        f"x=80:"
        f"y=1670:"
        f"shadowcolor=black@0.7:"
        f"shadowx=2:"
        f"shadowy=2,"

        # Bottom label
        "drawtext="
        f"fontfile={FONT_REGULAR}:"
        "text='FBPRO ORIGINAL':"
        "fontcolor=white@0.75:"
        "fontsize=30:"
        "x=80:"
        "y=1740:"
        "shadowcolor=black@0.6:"
        "shadowx=2:"
        "shadowy=2,"

        # Progress bar background
        "drawbox="
        "x=80:"
        "y=1820:"
        "w=920:"
        "h=12:"
        "color=white@0.18:"
        "t=fill,"

        # Progress bar
        "drawbox="
        "x=80:"
        "y=1820:"
        f"w={max(20, int(920 / total_scenes))}:"
        "h=12:"
        f"color=#{accent}:"
        "t=fill"
    )

    # ======================================
    # BUAT VIDEO SCENE
    # ======================================

    subprocess.run(
        [
            "ffmpeg",
            "-y",

            "-f",
            "lavfi",

            "-i",
            (
                f"color=c=#{background}:"
                f"s={WIDTH}x{HEIGHT}:"
                f"r={FPS}"
            ),

            "-vf",
            filter_complex,

            "-t",
            str(duration),

            "-r",
            str(FPS),

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

    scene_files.append(
        scene_file
    )

# ==========================================
# CONCAT FILE
# ==========================================

concat_file = (
    "visual_tmp/"
    "visual_concat.txt"
)

with open(
    concat_file,
    "w",
    encoding="utf-8"
) as f:

    for scene_file in scene_files:

        absolute_path = os.path.abspath(
            scene_file
        )

        f.write(
            "file '"
            + absolute_path.replace(
                "'",
                "'\\''"
            )
            + "'\n"
        )

# ==========================================
# GABUNG SEMUA SCENE
# ==========================================

print()
print("Menggabungkan semua scene...")

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
# CEK VIDEO
# ==========================================

print()
print("Memeriksa hasil video...")

subprocess.run(
    [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        output_video
    ],
    check=False
)

# ==========================================
# SELESAI
# ==========================================

print()
print("========================================")
print("FBPRO VISUAL AGENT V2 BERHASIL")
print("========================================")
print()
print(f"Sumber : {latest_file}")
print(f"Video  : {output_video}")
print()
print("Format : 1080x1920")
print("Rasio  : 9:16")
print("FPS    : 30")
print()
