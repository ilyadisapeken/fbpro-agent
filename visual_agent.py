import os
import json
import glob
import re
import urllib.parse
import urllib.request
import subprocess
from datetime import datetime


# ============================================================
# FBPRO VISUAL AGENT
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.1-flash-lite"

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

USER_AGENT = (
    "FBProVisualAgent/5.0 "
    "(GitHub Actions)"
)

FONT_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)


# ============================================================
# FOLDER
# ============================================================

os.makedirs("visuals", exist_ok=True)
os.makedirs("visual_tmp", exist_ok=True)


# ============================================================
# CARI FILE PRODUCTION TERBARU
# ============================================================

production_files = glob.glob("production/*.json")

if not production_files:
    raise SystemExit(
        "ERROR: Tidak ditemukan file production/*.json"
    )

latest_production = max(
    production_files,
    key=os.path.getmtime
)

print()
print("========================================")
print("FBPRO VISUAL AGENT")
print("========================================")
print()
print("Production:")
print(latest_production)
print()


# ============================================================
# BACA PRODUCTION
# ============================================================

with open(
    latest_production,
    "r",
    encoding="utf-8"
) as file:
    production = json.load(file)


video_info = production.get("video", {})

title = str(
    video_info.get(
        "judul",
        "FBPro Reels"
    )
)

storyboard = production.get(
    "storyboard",
    []
)

if not storyboard:
    raise SystemExit(
        "ERROR: storyboard tidak ditemukan."
    )


print("Judul:", title)
print("Jumlah scene:", len(storyboard))
print()


# ============================================================
# HTTP GET JSON
# ============================================================

def get_json(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        data = response.read()

    return json.loads(
        data.decode("utf-8")
    )


# ============================================================
# DOWNLOAD FILE
# ============================================================

def download_file(
    url,
    filename
):

    try:

        print("Download:")
        print(url)

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            content = response.read()

        if len(content) < 5000:
            print(
                "File terlalu kecil."
            )
            return False

        with open(
            filename,
            "wb"
        ) as file:

            file.write(content)

        print(
            "Download berhasil:",
            filename
        )

        return True

    except Exception as error:

        print(
            "Download gagal:",
            error
        )

        return False


# ============================================================
# BERSIHKAN TEXT
# ============================================================

def clean_text(text):

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

    return text.strip()


# ============================================================
# GEMINI - BUAT KEYWORD
# ============================================================

def create_keywords(scene):

    visual = clean_text(
        scene.get(
            "visual",
            ""
        )
    )

    voice = clean_text(
        scene.get(
            "voice_over",
            ""
        )
    )

    screen = clean_text(
        scene.get(
            "teks_layar",
            ""
        )
    )

    prompt = f"""
Create search keywords for Wikimedia Commons.

We need REAL PHOTOGRAPHS for a vertical social media
video about Indonesian people, business, daily life,
work, family, food, shopping, money, or other practical
subjects.

Based on this scene:

Visual:
{visual}

Voice:
{voice}

Text:
{screen}

Return exactly 5 short English search queries.

Rules:
- Each query must contain 2 to 5 words.
- Use concrete objects, people, places or activities.
- Do not use abstract motivational words.
- Do not write explanations.
- Do not create image prompts.
- Do not use quotation marks.

Examples:
small business owner
woman using smartphone
local food seller
customer shopping market
person working laptop

Return ONLY JSON:

{{
  "queries": [
    "query one",
    "query two",
    "query three",
    "query four",
    "query five"
  ]
}}
"""

    if not GEMINI_API_KEY:
        print(
            "WARNING: GEMINI_API_KEY tidak tersedia."
        )
        return []

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        + GEMINI_MODEL
        + ":generateContent"
    )

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json"
        }
    }

    try:

        request = urllib.request.Request(
            url,
            data=json.dumps(
                body
            ).encode("utf-8"),
            headers={
                "Content-Type":
                    "application/json",
                "x-goog-api-key":
                    GEMINI_API_KEY,
                "User-Agent":
                    USER_AGENT
            },
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            result = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        text = (
            result
            ["candidates"][0]
            ["content"]["parts"][0]
            ["text"]
        )

        parsed = json.loads(text)

        queries = parsed.get(
            "queries",
            []
        )

        if not isinstance(
            queries,
            list
        ):
            return []

        cleaned = []

        for item in queries:

            query = clean_text(item)

            query = re.sub(
                r"[^a-zA-Z0-9\s-]",
                " ",
                query
            )

            query = " ".join(
                query.split()
            )

            if query:

                cleaned.append(
                    query[:80]
                )

        return cleaned

    except Exception as error:

        print(
            "Gemini keyword error:"
        )

        print(error)

        return []


# ============================================================
# FALLBACK KEYWORD
# ============================================================

def fallback_keywords(scene):

    visual = clean_text(
        scene.get(
            "visual",
            ""
        )
    )

    voice = clean_text(
        scene.get(
            "voice_over",
            ""
        )
    )

    words = re.findall(
        r"[a-zA-Z]{4,}",
        visual + " " + voice
    )

    words = words[:4]

    if words:

        return [
            " ".join(words),
            "person working",
            "small business",
            "business owner",
            "daily activity"
        ]

    return [
        "person working",
        "small business",
        "business owner",
        "daily activity",
        "people working"
    ]


# ============================================================
# WIKIMEDIA SEARCH
# ============================================================

def search_wikimedia(query):

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": "1400"
    }

    url = (
        WIKIMEDIA_API
        + "?"
        + urllib.parse.urlencode(params)
    )

    try:

        result = get_json(url)

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
            "thumburl",
            ""
        )

        if not image_url:

            image_url = info.get(
                "url",
                ""
            )

        if not image_url:
            continue

        return {
            "title": page.get(
                "title",
                ""
            ),
            "url": image_url
        }

    return None


# ============================================================
# CARI FOTO
# ============================================================

def find_photo(
    scene,
    scene_number
):

    print()
    print("----------------------------------------")
    print(
        "MENCARI FOTO SCENE",
        scene_number
    )
    print("----------------------------------------")

    queries = create_keywords(scene)

    if not queries:

        queries = fallback_keywords(
            scene
        )

    print("Keyword:")

    for query in queries:

        print(
            " -",
            query
        )

    for query in queries:

        result = search_wikimedia(
            query
        )

        if result:

            print()
            print(
                "FOTO DITEMUKAN:"
            )

            print(
                result["title"]
            )

            return result

    print(
        "Tidak ada foto yang ditemukan."
    )

    return None


# ============================================================
# BUAT TEXT FILE UNTUK FFMPEG
# ============================================================

def create_text_file(
    text,
    scene_number
):

    filename = (
        "visual_tmp/"
        f"text_{scene_number}.txt"
    )

    text = clean_text(text)

    if not text:

        text = title

    if len(text) > 180:

        text = text[:177] + "..."

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(text)

    return filename


# ============================================================
# BUAT VIDEO SCENE
# ============================================================

def create_scene(
    image_file,
    text_file,
    duration,
    scene_number
):

    output = (
        "visual_tmp/"
        f"scene_{scene_number}.mp4"
    )

    try:

        duration = float(
            duration
        )

    except Exception:

        duration = 5

    if duration < 2:
        duration = 2

    if duration > 15:
        duration = 15

    frames = int(
        duration * FPS
    )

    # --------------------------------------------------------
    # FOTO MEMENUHI LAYAR
    # --------------------------------------------------------

    filter_complex = (
        "scale="
        + str(WIDTH)
        + ":"
        + str(HEIGHT)
        + ":force_original_aspect_ratio=increase,"
        "crop="
        + str(WIDTH)
        + ":"
        + str(HEIGHT)
        + ","
        "zoompan="
        "z='min(zoom+0.0015,1.12)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d="
        + str(frames)
        + ":"
        "s="
        + str(WIDTH)
        + "x"
        + str(HEIGHT)
        + ":"
        "fps="
        + str(FPS)
        + ","
        "eq="
        "contrast=1.05:"
        "brightness=-0.02:"
        "saturation=1.05,"
        "drawbox="
        "x=0:"
        "y=0:"
        "w=iw:"
        "h=ih:"
        "color=black@0.12:"
        "t=fill,"
        "drawbox="
        "x=0:"
        "y=ih-570:"
        "w=iw:"
        "h=570:"
        "color=black@0.52:"
        "t=fill,"
        "drawtext="
        "fontfile="
        + FONT_BOLD
        + ":"
        "textfile="
        + text_file
        + ":"
        "fontcolor=white:"
        "fontsize=58:"
        "line_spacing=18:"
        "x=65:"
        "y=ih-450:"
        "shadowcolor=black@0.9:"
        "shadowx=3:"
        "shadowy=3"
    )

    print(
        "Membuat scene:",
        scene_number
    )

    command = [
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
        "-movflags",
        "+faststart",
        output
    ]

    subprocess.run(
        command,
        check=True
    )

    return output


# ============================================================
# PROSES SEMUA SCENE
# ============================================================

scene_files = []

print()
print("========================================")
print("MEMPROSES FOTO DAN SCENE")
print("========================================")

for index, scene in enumerate(
    storyboard
):

    scene_number = index + 1

    print()
    print(
        "SCENE",
        scene_number
    )

    # --------------------------------------------------------
    # DURASI
    # --------------------------------------------------------

    duration = scene.get(
        "durasi_detik",
        5
    )

    try:

        duration = float(
            duration
        )

    except Exception:

        duration = 5

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    screen_text = clean_text(
        scene.get(
            "teks_layar",
            ""
        )
    )

    if not screen_text:

        screen_text = clean_text(
            scene.get(
                "voice_over",
                ""
            )
        )

    if not screen_text:

        screen_text = title

    text_file = create_text_file(
        screen_text,
        scene_number
    )

    # --------------------------------------------------------
    # CARI FOTO
    # --------------------------------------------------------

    photo = find_photo(
        scene,
        scene_number
    )

    if not photo:

        # Coba pencarian umum terakhir
        print(
            "Menggunakan foto fallback."
        )

        photo = search_wikimedia(
            "person working"
        )

    if not photo:

        raise SystemExit(
            "ERROR: Tidak dapat menemukan "
            "foto untuk scene "
            + str(scene_number)
        )

    # --------------------------------------------------------
    # DOWNLOAD FOTO
    # --------------------------------------------------------

    image_file = (
        "visual_tmp/"
        f"image_{scene_number}.jpg"
    )

    success = download_file(
        photo["url"],
        image_file
    )

    if not success:

        print(
            "Download foto gagal."
        )

        raise SystemExit(
            "ERROR: Gagal download foto scene "
            + str(scene_number)
        )

    # --------------------------------------------------------
    # BUAT VIDEO
    # --------------------------------------------------------

    scene_video = create_scene(
        image_file,
        text_file,
        duration,
        scene_number
    )

    scene_files.append(
        scene_video
    )


# ============================================================
# CEK SCENE
# ============================================================

if not scene_files:

    raise SystemExit(
        "ERROR: Tidak ada scene video."
    )


print()
print("Jumlah scene berhasil:")
print(len(scene_files))


# ============================================================
# BUAT CONCAT FILE
# ============================================================

concat_file = (
    "visual_tmp/concat.txt"
)

with open(
    concat_file,
    "w",
    encoding="utf-8"
) as file:

    for scene_file in scene_files:

        absolute_path = os.path.abspath(
            scene_file
        )

        file.write(
            "file '"
            + absolute_path
            + "'\n"
        )


# ============================================================
# NAMA VIDEO FINAL
# ============================================================

timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

output_video = (
    "visuals/"
    "FBPro_Visual_"
    + timestamp
    + ".mp4"
)


# ============================================================
# GABUNG SEMUA SCENE
# ============================================================

print()
print("========================================")
print("MENGGABUNGKAN SEMUA SCENE")
print("========================================")
print()

command = [
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
    "-movflags",
    "+faststart",
    output_video
]

subprocess.run(
    command,
    check=True
)


# ============================================================
# VALIDASI VIDEO
# ============================================================

if not os.path.exists(
    output_video
):

    raise SystemExit(
        "ERROR: Video final tidak ditemukan."
    )

file_size = os.path.getsize(
    output_video
)

if file_size < 100000:

    raise SystemExit(
        "ERROR: Ukuran video terlalu kecil."
    )


# ============================================================
# SELESAI
# ============================================================

print()
print("========================================")
print("FBPRO VISUAL AGENT BERHASIL")
print("========================================")
print()

print(
    "Production :",
    latest_production
)

print(
    "Video      :",
    output_video
)

print(
    "Ukuran     :",
    file_size,
    "bytes"
)

print(
    "Resolusi   :",
    str(WIDTH)
    + "x"
    + str(HEIGHT)
)

print(
    "Rasio      : 9:16"
)

print(
    "FPS        :",
    FPS
)

print()
print(
    "Video menggunakan foto nyata "
    "dari Wikimedia Commons."
)

print()
print(
    "Selesai."
)
