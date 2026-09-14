import os
import json
import glob
import urllib.parse
import urllib.request
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

GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = "gemini-3.1-flash-lite"

WIKIMEDIA_API = (
    "https://commons.wikimedia.org/w/api.php"
)

USER_AGENT = (
    "FBProVisualAgent/4.0 "
    "(GitHub Actions)"
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

print()
print("Production source:")
print(latest_file)

with open(
    latest_file,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)

# ==========================================
# DATA
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
# HTTP JSON
# ==========================================

def get_json(url):

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=40
    ) as response:

        return json.loads(
            response.read().decode(
                "utf-8"
            )
        )


# ==========================================
# DOWNLOAD
# ==========================================

def download_file(
    url,
    destination
):

    try:

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

            content = response.read()

        if len(content) < 10000:
            return False

        with open(
            destination,
            "wb"
        ) as f:

            f.write(content)

        return True

    except Exception as error:

        print(
            "Download error:",
            error
        )

        return False


# ==========================================
# GEMINI:
# BUAT SEARCH KEYWORDS
# ==========================================

def make_search_keywords(
    scene,
    index
):

    visual = scene.get(
        "visual",
        ""
    )

    voice = scene.get(
        "voice_over",
        ""
    )

    screen = scene.get(
        "teks_layar",
        ""
    )

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

    instruction = f"""
You create search keywords for a stock/photo
search engine.

Create 5 different SHORT English search queries
for a real photograph matching this video scene.

Do NOT create an image.
Do NOT explain anything.

Each query must contain only 2-6 simple words.

Avoid abstract words.

Prefer concrete things such as:
person, seller, shop, phone, money,
food, laptop, home, street, family,
morning, office, market, customer,
working, walking, cooking, studying.

Scene visual:
{visual}

Voice:
{voice}

On screen:
{screen}

AI visual prompt:
{prompt}

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
        return []

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": instruction
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json"
        }
    }

    try:

        request = urllib.request.Request(
            url,
            data=json.dumps(
                body
            ).encode(
                "utf-8"
            ),
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

        parsed = json.loads(
            text
        )

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

        for query in queries:

            query = str(
                query
            )

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
            "Gemini keyword error:",
            error
        )

        return []


# ==========================================
# WIKIMEDIA SEARCH
# ==========================================

def search_wikimedia(
    query
):

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "10",
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": "1200"
    }

    url = (
        WIKIMEDIA_API
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )

    try:

        result = get_json(
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

        info_list = page.get(
            "imageinfo",
            []
        )

        if not info_list:
            continue

        info = info_list[0]

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
                "title":
                    page.get(
                        "title",
                        ""
                    ),
                "url":
                    image_url
            }
        )

    if not candidates:
        return None

    return candidates[0]


# ==========================================
# CARI FOTO TERBAIK
# ==========================================

def find_image(
    scene,
    index
):

    queries = make_search_keywords(
        scene,
        index
    )

    print()
    print(
        "Scene",
        index + 1,
        "search queries:"
    )

    for query in queries:

        print(
            " -",
            query
        )

    # ======================================
    # COBA SEMUA QUERY
    # ======================================

    for query in queries:

        result = search_wikimedia(
            query
        )

        if result:

            print(
                "Ditemukan:",
                result["title"]
            )

            return result

    # ======================================
    # FALLBACK DARI VISUAL
    # ======================================

    visual = scene.get(
        "visual",
        ""
    )

    if visual:

        words = re.findall(
            r"[a-zA-Z]{3,}",
            str(visual)
        )

        simple_query = " ".join(
            words[:4]
        )

        if simple_query:

            print(
                "Fallback:",
                simple_query
            )

            result = search_wikimedia(
                simple_query
            )

            if result:
                return result

    return None


# ==========================================
# DOWNLOAD SEMUA GAMBAR
# ==========================================

image_files = []

print()
print("========================================")
print("MENCARI FOTO UNTUK SETIAP ADEGAN")
print("========================================")

for index, scene in enumerate(
    storyboard
):

    number = index + 1

    image_file = (
        f"visual_tmp/"
        f"image_{number}.jpg"
    )

    result = find_image(
        scene,
        index
    )

    if result:

        success = download_file(
            result["url"],
            image_file
        )

        if success:

            image_files.append(
                image_file
            )

            print(
                "OK:",
                image_file
            )

            continue

    print(
        "TIDAK ADA FOTO UNTUK SCENE",
        number
    )

    image_files.append(
        None
    )


# ==========================================
# BUAT VIDEO SCENE
# ==========================================

scene_files = []

print()
print("========================================")
print("MEMBUAT VIDEO DARI FOTO")
print("========================================")

for index, scene in enumerate(
    storyboard
):

    number = index + 1

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

    text = scene.get(
        "teks_layar",
        ""
    )

    if not text:

        text = scene.get(
            "voice_over",
            ""
        )

    if not text:

        text = title

    text = " ".join(
        str(text).split()
    )

    if len(text) > 160:

        text = (
            text[:160]
            + "..."
        )

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
            text
        )

    scene_file = (
        f"visual_tmp/"
        f"scene_{number}.mp4"
    )

    image_file = image_files[
        index
    ]

    # ======================================
    # FOTO DITEMUKAN
    # ======================================

    if image_file:

        print(
            f"Render scene {number}"
        )

        # Foto dibuat memenuhi layar
        # kemudian diberi gerakan zoom.
        filter_video = (

            "scale="
            f"{WIDTH*2}:"
            f"{HEIGHT*2}:"
            "force_original_aspect_ratio=increase,"

            f"crop={WIDTH*2}:{HEIGHT*2},"

            "zoompan="
            "z='min(zoom+0.0018,1.15)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={int(duration * FPS)}:"
            f"s={WIDTH}x{HEIGHT}:"
            f"fps={FPS},"

            # sedikit peningkatan gambar
            "eq="
            "contrast=1.05:"
            "brightness=-0.02:"
            "saturation=1.08,"

            # overlay gelap
            "drawbox="
            "x=0:"
            "y=0:"
            "w=iw:"
            "h=ih:"
            "color=black@0.16:"
            "t=fill,"

            # bagian bawah untuk subtitle
            "drawbox="
            "x=0:"
            "y=ih-560:"
            "w=iw:"
            "h=560:"
            "color=black@0.50:"
            "t=fill,"

            # nomor adegan
            f"drawtext="
            f"fontfile={FONT_BOLD}:"
            f"text='0{number}':"
            "fontcolor=white@0.9:"
            "fontsize=34:"
            "x=60:"
            "y=70:"
            "shadowcolor=black@0.9:"
            "shadowx=2:"
            "shadowy=2,"

            # teks utama
            f"drawtext="
            f"fontfile={FONT_BOLD}:"
            f"textfile={text_file}:"
            "fontcolor=white:"
            "fontsize=58:"
            "line_spacing=20:"
            "x=65:"
            "y=ih-450:"
            "shadowcolor=black@0.95:"
            "shadowx=3:"
            "shadowy=3"
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
                filter_video,
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

    # ======================================
    # JIKA FOTO GAGAL
    # ======================================

    else:

        print(
            "Scene",
            number,
            "tidak memiliki foto."
        )

        # Jangan membuat kotak palsu.
        # Gunakan foto fallback umum.
        fallback_query = (
            "person activity"
        )

        result = search_wikimedia(
            fallback_query
        )

        if not result:

            raise SystemExit(
                "Tidak dapat menemukan "
                "foto untuk scene "
                + str(number)
            )

        fallback_file = (
            f"visual_tmp/"
            f"fallback_{number}.jpg"
        )

        if not download_file(
            result["url"],
            fallback_file
        ):

            raise SystemExit(
                "Gagal download "
                "fallback image."
            )

        image_files[
            index
        ] = fallback_file

        filter_video = (

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
            f"fps={FPS},"

            "drawbox="
            "x=0:"
            "y=0:"
            "w=iw:"
            "h=ih:"
            "color=black@0.12:"
            "t=fill,"

            "drawbox="
            "x=0:"
            "y=ih-560:"
            "w=iw:"
            "h=560:"
            "color=black@0.50:"
            "t=fill,"

            f"drawtext="
            f"fontfile={FONT_BOLD}:"
            f"textfile={text_file}:"
            "fontcolor=white:"
            "fontsize=58:"
            "line_spacing=20:"
            "x=65:"
            "y=ih-450:"
            "shadowcolor=black@0.95:"
            "shadowx=3:"
            "shadowy=3"
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                fallback_file,
                "-vf",
                filter_video,
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

        f.write(
            "file '"
            + os.path.abspath(
                scene_file
            )
            + "'\n"
        )


# ==========================================
# GABUNG
# ==========================================

print()
print(
    "Menggabungkan semua scene..."
)

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
print("FBPRO VISUAL AGENT V4 BERHASIL")
print("========================================")
print()
print()
    "Sumber :",
   
