import os
import json
import glob
import urllib.parse
import urllib.request
import urllib.error
import subprocess
import re
from datetime import datetime

# ==========================================
# KONFIGURASI
# ==========================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

WIKIMEDIA_API = (
    "https://commons.wikimedia.org/w/api.php"
)

USER_AGENT = (
    "FBProVisualAgent/1.0 "
    "(GitHub Actions; educational project)"
)

# ==========================================
# CARI PRODUCTION TERBARU
# ==========================================

files = glob.glob(
    "production/*.json"
)

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
# DATA VIDEO
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

visual_prompts = data.get(
    "visual_prompts",
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
# FUNGSI HTTP
# ==========================================

def http_get_json(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=30
    ) as response:

        return json.loads(
            response.read().decode(
                "utf-8"
            )
        )


# ==========================================
# DOWNLOAD FILE
# ==========================================

def download_file(
    url,
    destination
):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            content = response.read()

        with open(
            destination,
            "wb"
        ) as f:

            f.write(content)

        return True

    except Exception as error:

        print(
            "Download gagal:",
            error
        )

        return False


# ==========================================
# BERSIHKAN QUERY
# ==========================================

def clean_query(text):

    if not text:
        return ""

    text = str(text)

    # Hapus karakter aneh
    text = re.sub(
        r"[^a-zA-Z0-9À-ÿ\s-]",
        " ",
        text
    )

    text = " ".join(
        text.split()
    )

    # Terlalu panjang membuat pencarian buruk
    words = text.split()

    if len(words) > 12:
        words = words[:12]

    return " ".join(words)


# ==========================================
# CARI GAMBAR WIKIMEDIA COMMONS
# ==========================================

def search_wikimedia(query):

    query = clean_query(
        query
    )

    if not query:
        return None

    print()
    print(
        "Mencari visual:",
        query
    )

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": "1080"
    }

    url = (
        WIKIMEDIA_API
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )

    try:

        result = http_get_json(
            url
        )

    except Exception as error:

        print(
            "Wikimedia error:",
            error
        )

        return None

    pages = (
        result
        .get("query", {})
        .get("pages", {})
    )

    candidates = []

    for page in pages.values():

        imageinfo = page.get(
            "imageinfo",
            []
        )

        if not imageinfo:
            continue

        info = imageinfo[0]

        mime = info.get(
            "mime",
            ""
        )

        if not mime.startswith(
            "image/"
        ):
            continue

        image_url = info.get(
            "thumburl"
        )

        if not image_url:
            image_url = info.get(
                "url"
            )

        if not image_url:
            continue

        candidates.append(
            {
                "title": page.get(
                    "title",
                    ""
                ),
                "url": image_url
            }
        )

    if not candidates:
        return None

    return candidates[0]


# ==========================================
# CARI VISUAL UNTUK SCENE
# ==========================================

def find_visual(
    scene,
    index
):

    # --------------------------------------
    # Ambil visual prompt jika tersedia
    # --------------------------------------

    prompt = ""

    if index < len(
        visual_prompts
    ):

        item = visual_prompts[
            index
        ]

        if isinstance(
            item,
            dict
        ):

            prompt = item.get(
                "prompt",
                ""
            )

    # --------------------------------------
    # Visual storyboard
    # --------------------------------------

    visual = scene.get(
        "visual",
        ""
    )

    # --------------------------------------
    # Judul
    # --------------------------------------

    scene_title = title

    # --------------------------------------
    # Prioritas pencarian
    # --------------------------------------

    queries = []

    if prompt:
        queries.append(
            prompt
        )

    if visual:
        queries.append(
            visual
        )

    if theme:
        queries.append(
            theme
        )

    # Tambahkan query sederhana
    # berdasarkan kata penting

    for original_query in queries:

        query = clean_query(
            original_query
        )

        if not query:
            continue

        result = search_wikimedia(
            query
        )

        if result:
            return result

    # --------------------------------------
    # Fallback berdasarkan judul
    # --------------------------------------

    result = search_wikimedia(
        scene_title
    )

    return result


# ==========================================
# DOWNLOAD VISUAL SCENE
# ==========================================

image_files = []

print()
print("========================================")
print("MENCARI VISUAL ASLI")
print("========================================")

for index, scene in enumerate(
    storyboard
):

    number = index + 1

    result = find_visual(
        scene,
        index
    )

    image_file = (
        f"visual_tmp/"
        f"image_{number}.jpg"
    )

    if result:

        print()
        print(
            f"Scene {number}:",
            result["title"]
        )

        success = download_file(
            result["url"],
            image_file
        )

        if success:

            image_files.append(
                image_file
            )

            continue

    print(
        f"Scene {number}: "
        "tidak menemukan gambar."
    )

    image_files.append(
        None
    )


# ==========================================
# BUAT SCENE VIDEO
# ==========================================

scene_files = []

print()
print("========================================")
print("MEMBUAT VIDEO DARI VISUAL")
print("========================================")

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

    screen_text = scene.get(
        "teks_layar",
        ""
    )

    if not screen_text:

        screen_text = scene.get(
            "voice_over",
            ""
        )

    if not screen_text:

        screen_text = title

    screen_text = str(
        screen_text
    )

    screen_text = " ".join(
        screen_text.split()
    )

    if len(screen_text) > 180:
        screen_text = (
            screen_text[:180]
            + "..."
        )

    # --------------------------------------
    # FILE TEKS
    # --------------------------------------

    text_file = (
        f"visual_tmp/"
        f"screen_{number}.txt"
    )

    with open(
        text_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            screen_text
        )

    # --------------------------------------
    # SCENE OUTPUT
    # --------------------------------------

    scene_file = (
        f"visual_tmp/"
        f"scene_{number}.mp4"
    )

    image_file = image_files[
        index
    ]

    print(
        f"Scene {number}/{total_scenes}"
    )

    # ======================================
    # JIKA ADA GAMBAR
    # ======================================

    if image_file:

        # ----------------------------------
        # Gerakan kamera
        # ----------------------------------

        # zoom perlahan + sedikit pan
        zoom_filter = (
            "scale="
            f"{WIDTH*2}:"
            f"{HEIGHT*2}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH*2}:{HEIGHT*2},"
            "zoompan="
            "z='min(zoom+0.0015,1.12)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={int(duration * FPS)}:"
            f"s={WIDTH}x{HEIGHT}:"
            f"fps={FPS}"
        )

        # ----------------------------------
        # Overlay gelap
        # ----------------------------------

        filter_complex = (

            f"[0:v]"
            f"{zoom_filter},"
            "eq="
            "contrast=1.04:"
            "brightness=-0.03:"
            "saturation=1.08,"
            "drawbox="
            "x=0:"
            "y=0:"
            "w=iw:"
            "h=ih:"
            "color=black@0.18:"
            "t=fill,"
            
            # top gradient-like panel
            "drawbox="
            "x=0:"
            "y=0:"
            "w=iw:"
            "h=250:"
            "color=black@0.42:"
            "t=fill,"
            
            # bottom panel
            "drawbox="
            "x=0:"
            "y=ih-520:"
            "w=iw:"
            "h=520:"
            "color=black@0.55:"
            "t=fill,"
            
            # teks
            f"drawtext="
            f"fontfile={FONT_BOLD}:"
            f"textfile={text_file}:"
            "fontcolor=white:"
            "fontsize=58:"
            "line_spacing=18:"
            "x=70:"
            "y=h-440:"
            "box=0:"
            "shadowcolor=black@0.9:"
            "shadowx=3:"
            "shadowy=3,"
            
            # nomor scene
            f"drawtext="
            f"fontfile={FONT_BOLD}:"
            f"text='0{number}':"
            "fontcolor=white@0.85:"
            "fontsize=34:"
            "x=70:"
            "y=75:"
            "shadowcolor=black@0.8:"
            "shadowx=2:"
            "shadowy=2,"
            
            # branding kecil
            f"drawtext="
            f"fontfile={FONT_REGULAR}:"
            "text='FBPRO ORIGINAL':"
            "fontcolor=white@0.75:"
            "fontsize=28:"
            "x=70:"
            "y=125:"
            "shadowcolor=black@0.7:"
            "shadowx=2:"
            "shadowy=2"
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                image_file,
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

    # ======================================
    # FALLBACK JIKA GAMBAR TIDAK ADA
    # ======================================

    else:

        filter_complex = (

            "drawbox="
            "x=0:"
            "y=0:"
            "w=iw:"
            "h=ih:"
            "color=#111827:"
            "t=fill,"

            f"drawtext="
            f"fontfile={FONT_BOLD}:"
            f"textfile={text_file}:"
            "fontcolor=white:"
            "fontsize=58:"
            "line_spacing=18:"
            "x=70:"
            "y=(h-text_h)/2:"
            "box=1:"
            "boxcolor=black@0.5:"
            "boxborderw=35:"
            "shadowcolor=black@0.8:"
            "shadowx=3:"
            "shadowy=3"
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                (
                    f"color=c=#111827:"
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
# CONCAT
# ==========================================

concat_file = (
    "visual_tmp/"
    "concat.txt"
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
            f"file '{absolute_path}'\n"
        )


# ==========================================
# GABUNG SEMUA SCENE
# ==========================================

print()
print("========================================")
print("MENGGABUNGKAN VIDEO")
print("========================================")

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
# INFO
# ==========================================

print()
print("========================================")
print("FBPRO VISUAL AGENT V3 BERHASIL")
print("========================================")
print()
print(
    f"Sumber : {latest_file}"
)
print(
    f"Video  : {output_video}"
)
print()
print(
    "Visual : Wikimedia Commons"
)
print(
    "Format : 1080x1920"
)
print(
    "Rasio  : 9:16"
)
print(
    "FPS    : 30"
)
print()
