import os
import json
import glob
import re
import urllib.parse
import urllib.request
import subprocess
import shutil
import textwrap
from datetime import datetime


# ============================================================
# FBPRO VISUAL AGENT
# V7 - PEXELS VIDEO VERSION
#
# Fungsi:
# Production JSON
#      ↓
# Gemini analisis storyboard
#      ↓
# keyword visual konkret
#      ↓
# Pexels Video
#      ↓
# beberapa klip per scene
#      ↓
# crop 9:16
#      ↓
# teks layar
#      ↓
# credit Pexels
#      ↓
# video final
# ============================================================


WIDTH = 1080
HEIGHT = 1920
FPS = 30

GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    ""
)

PEXELS_API_KEY = os.environ.get(
    "PEXELS_API_KEY",
    ""
)

GEMINI_MODEL = "gemini-3.1-flash-lite"

PEXELS_API = (
    "https://api.pexels.com/v1/videos/search"
)

USER_AGENT = (
    "FBProVisualAgent/7.0 "
    "(GitHub Actions)"
)

FONT_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)


# ============================================================
# FOLDER
# ============================================================

os.makedirs(
    "visuals",
    exist_ok=True
)

# Bersihkan file sementara lama
if os.path.exists("visual_tmp"):
    shutil.rmtree("visual_tmp")

os.makedirs(
    "visual_tmp",
    exist_ok=True
)


# ============================================================
# VALIDASI API
# ============================================================

if not GEMINI_API_KEY:

    print(
        "WARNING: GEMINI_API_KEY tidak ditemukan."
    )

    print(
        "Agent akan menggunakan fallback keyword."
    )


if not PEXELS_API_KEY:

    raise SystemExit(
        "ERROR: PEXELS_API_KEY tidak ditemukan. "
        "Pastikan GitHub Secret bernama "
        "PEXELS_API_KEY sudah dibuat."
    )


# ============================================================
# CARI PRODUCTION TERBARU
# ============================================================

production_files = glob.glob(
    "production/*.json"
)

if not production_files:

    raise SystemExit(
        "ERROR: Tidak ditemukan "
        "file production/*.json"
    )


latest_production = max(
    production_files,
    key=os.path.getmtime
)


print()
print("========================================")
print("FBPRO VISUAL AGENT V7")
print("========================================")
print()

print(
    "Production:",
    latest_production
)


# ============================================================
# BACA PRODUCTION
# ============================================================

with open(
    latest_production,
    "r",
    encoding="utf-8"
) as file:

    production = json.load(file)


video_info = production.get(
    "video",
    {}
)

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
        "ERROR: Storyboard tidak ditemukan."
    )


print(
    "Judul:",
    title
)

print(
    "Jumlah scene:",
    len(storyboard)
)

print()


# ============================================================
# CLEAN TEXT
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
# WRAP TEXT
# ============================================================

def wrap_screen_text(text):

    text = clean_text(
        text
    )

    if not text:

        text = title


    # Batasi agar tidak memenuhi layar
    if len(text) > 130:

        text = (
            text[:127]
            + "..."
        )


    lines = textwrap.wrap(
        text,
        width=34,
        break_long_words=False,
        break_on_hyphens=False
    )


    # Maksimal 4 baris
    lines = lines[:4]


    return "\n".join(
        lines
    )


# ============================================================
# HTTP JSON
# ============================================================

def get_json(
    url,
    headers=None
):

    request_headers = {
        "User-Agent": USER_AGENT
    }


    if headers:

        request_headers.update(
            headers
        )


    request = urllib.request.Request(
        url,
        headers=request_headers
    )


    with urllib.request.urlopen(
        request,
        timeout=90
    ) as response:

        content = response.read()


    return json.loads(
        content.decode("utf-8")
    )


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(
    url,
    destination
):

    try:

        print()
        print(
            "Download video:"
        )

        print(
            url
        )


        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    USER_AGENT
            }
        )


        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            content = response.read()


        if len(content) < 10000:

            print(
                "File video terlalu kecil."
            )

            return False


        with open(
            destination,
            "wb"
        ) as file:

            file.write(
                content
            )


        print(
            "Download berhasil:",
            destination
        )


        return True


    except Exception as error:

        print(
            "Download error:",
            error
        )

        return False


# ============================================================
# GEMINI KEYWORDS
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
You are a professional short-form video editor.

Analyze this Indonesian social media video scene.

Visual description:
{visual}

Narration:
{voice}

On-screen text:
{screen}

Create five SHORT English search queries for
REAL STOCK VIDEO FOOTAGE on Pexels.

The footage must visually represent what the narration
is actually talking about.

Rules:

- 2 to 5 words per query
- concrete people, objects, places or actions
- describe something that can actually be filmed
- prioritize movement/action
- avoid abstract concepts
- avoid motivational phrases
- avoid words like success, inspiration, happiness
  unless there is a concrete visual action
- do not create image-generation prompts
- do not explain anything

Example:

Narration:
"Pedagang online sekarang bisa menerima pesanan
langsung dari smartphone."

Good queries:

online seller smartphone
small business owner phone
person checking orders phone
seller packing online order
woman using smartphone business

Bad queries:

online success
digital transformation
business motivation

Return ONLY valid JSON:

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
        + GEMINI_MODEL
        + ":generateContent"
    )


    body = {

        "contents": [

            {
                "parts": [

                    {
                        "text":
                            prompt
                    }

                ]
            }

        ],

        "generationConfig": {

            "temperature": 0.2,

            "responseMimeType":
                "application/json"

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
            ["content"]
            ["parts"][0]
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


        for item in queries:

            query = clean_text(
                item
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


# ============================================================
# FALLBACK KEYWORDS
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


    combined = (
        visual
        + " "
        + voice
    )


    words = re.findall(
        r"[a-zA-Z]{4,}",
        combined
    )


    queries = []


    if words:

        first_query = " ".join(
            words[:4]
        )

        queries.append(
            first_query
        )


    queries.extend([

        "person using smartphone",

        "small business owner",

        "person working",

        "people daily activity",

        "business activity"

    ])


    return queries


# ============================================================
# PEXELS SEARCH CACHE
# ============================================================

pexels_cache = {}


# ============================================================
# PEXELS SEARCH
# ============================================================

def search_pexels(
    query
):

    query = clean_text(
        query
    )


    if not query:

        return []


    cache_key = query.lower()


    if cache_key in pexels_cache:

        return pexels_cache[
            cache_key
        ]


    params = {

        "query":
            query,

        "per_page":
            "15",

        "orientation":
            "portrait"

    }


    url = (

        PEXELS_API
        + "?"
        + urllib.parse.urlencode(
            params
        )

    )


    print()
    print(
        "Pexels search:",
        query
    )


    try:

        result = get_json(

            url,

            headers={

                "Authorization":
                    PEXELS_API_KEY

            }

        )


    except Exception as error:

        print(
            "Pexels search error:",
            error
        )

        return []


    videos = result.get(
        "videos",
        []
    )


    pexels_cache[
        cache_key
    ] = videos


    print(
        "Video ditemukan:",
        len(videos)
    )


    return videos


# ============================================================
# PILIH FILE VIDEO TERBAIK
# ============================================================

def choose_video_file(
    video
):

    files = video.get(
        "video_files",
        []
    )


    candidates = []


    for item in files:

        link = item.get(
            "link",
            ""
        )

        file_type = item.get(
            "file_type",
            ""
        )

        width = int(
            item.get(
                "width",
                0
            ) or 0
        )

        height = int(
            item.get(
                "height",
                0
            ) or 0
        )


        if not link:

            continue


        if file_type != "video/mp4":

            continue


        if width <= 0 or height <= 0:

            continue


        ratio = (
            height / width
        )


        portrait_bonus = 0


        if ratio >= 1.20:

            portrait_bonus = 100000000


        # Hindari file yang terlalu besar
        if width > 2000:

            size_bonus = -1000000

        else:

            size_bonus = (
                width * height
            )


        score = (
            portrait_bonus
            + size_bonus
        )


        candidates.append(
            (
                score,
                item
            )
        )


    if not candidates:

        return None


    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )


    return candidates[0][1]


# ============================================================
# VIDEO YANG SUDAH DIGUNAKAN
# ============================================================

used_video_ids = set()


# ============================================================
# CARI VIDEO TERBAIK
# ============================================================

def find_video(
    queries,
    scene_number,
    part_number
):

    print()
    print("----------------------------------------")
    print(
        "MENCARI VIDEO SCENE",
        scene_number,
        "PART",
        part_number
    )
    print("----------------------------------------")


    if not queries:

        queries = [

            "person using smartphone",

            "small business owner",

            "person working"

        ]


    for query in queries:

        videos = search_pexels(
            query
        )


        for video in videos:

            video_id = video.get(
                "id"
            )


            if video_id in used_video_ids:

                continue


            video_file = choose_video_file(
                video
            )


            if not video_file:

                continue


            duration = float(
                video.get(
                    "duration",
                    0
                ) or 0
            )


            if duration < 2:

                continue


            used_video_ids.add(
                video_id
            )


            user_info = video.get(
                "user",
                {}
            )


            photographer = clean_text(
                user_info.get(
                    "name",
                    ""
                )
            )


            print()
            print(
                "VIDEO DITEMUKAN"
            )

            print(
                "ID:",
                video_id
            )

            print(
                "Query:",
                query
            )

            print(
                "Durasi:",
                duration,
                "detik"
            )

            print(
                "Ukuran:",
                video_file.get(
                    "width"
                ),
                "x",
                video_file.get(
                    "height"
                )
            )


            return {

                "id":
                    video_id,

                "url":
                    video_file.get(
                        "link"
                    ),

                "duration":
                    duration,

                "photographer":
                    photographer,

                "photographer_url":
                    user_info.get(
                        "url",
                        ""
                    ),

                "pexels_url":
                    video.get(
                        "url",
                        ""
                    )

            }


    return None


# ============================================================
# TEXT FILE
# ============================================================

def create_text_file(
    text,
    number,
    part
):

    filename = (
        "visual_tmp/"
        "text_"
        + str(number)
        + "_"
        + str(part)
        + ".txt"
    )


    text = wrap_screen_text(
        text
    )


    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            text
        )


    return filename


# ============================================================
# CREDIT FILE
# ============================================================

def create_credit_file(
    photographer,
    number,
    part
):

    filename = (
        "visual_tmp/"
        "credit_"
        + str(number)
        + "_"
        + str(part)
        + ".txt"
    )


    if photographer:

        credit = (
            "Footage: Pexels • "
            + photographer
            + " • pexels.com"
        )

    else:

        credit = (
            "Footage: Pexels • pexels.com"
        )


    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            credit
        )


    return filename


# ============================================================
# BUAT VIDEO KLIP
# ============================================================

def create_clip(
    source_file,
    text_file,
    credit_file,
    duration,
    number,
    part
):

    output = (
        "visual_tmp/"
        "clip_"
        + str(number)
        + "_"
        + str(part)
        + ".mp4"
    )


    try:

        duration = float(
            duration
        )

    except Exception:

        duration = 3


    if duration < 2:

        duration = 2


    if duration > 15:

        duration = 15


    print()
    print(
        "Render clip",
        number,
        "-",
        part
    )

    print(
        "Durasi:",
        duration
    )


    # --------------------------------------------------------
    # VIDEO AKTUAL
    # --------------------------------------------------------
    #
    # Tidak menggunakan foto.
    # Tidak menggunakan zoompan.
    # Klip video Pexels langsung digunakan.
    #
    # --------------------------------------------------------

    video_filter = (

        "scale="
        + str(WIDTH)
        + ":"
        + str(HEIGHT)
        + ":"
        "force_original_aspect_ratio=increase,"
        "crop="
        + str(WIDTH)
        + ":"
        + str(HEIGHT)
        + ","
        "eq="
        "contrast=1.04:"
        "brightness=-0.015:"
        "saturation=1.04,"
        "drawbox="
        "x=0:"
        "y=0:"
        "w=iw:"
        "h=ih:"
        "color=black@0.08:"
        "t=fill,"
        "drawbox="
        "x=0:"
        "y=1360:"
        "w=iw:"
        "h=520:"
        "color=black@0.55:"
        "t=fill,"
        "drawtext="
        "fontfile="
        + FONT_BOLD
        + ":"
        "textfile="
        + text_file
        + ":"
        "fontcolor=white:"
        "fontsize=54:"
        "line_spacing=12:"
        "x=65:"
        "y=1410:"
        "shadowcolor=black@0.9:"
        "shadowx=3:"
        "shadowy=3,"
        "drawtext="
        "fontfile="
        + FONT_BOLD
        + ":"
        "textfile="
        + credit_file
        + ":"
        "fontcolor=white@0.70:"
        "fontsize=22:"
        "x=65:"
        "y=1850:"
        "shadowcolor=black@0.7:"
        "shadowx=1:"
        "shadowy=1"
    )


    command = [

        "ffmpeg",

        "-y",

        "-stream_loop",
        "-1",

        "-i",
        source_file,

        "-vf",
        video_filter,

        "-t",
        str(duration),

        "-r",
        str(FPS),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        output

    ]


    result = subprocess.run(
        command,
        check=False
    )


    if result.returncode != 0:

        raise SystemExit(
            "ERROR: FFmpeg gagal membuat "
            "clip "
            + str(number)
            + "-"
            + str(part)
        )


    if not os.path.exists(
        output
    ):

        raise SystemExit(
            "ERROR: Clip tidak ditemukan."
        )


    file_size = os.path.getsize(
        output
    )


    if file_size < 20000:

        raise SystemExit(
            "ERROR: Clip terlalu kecil."
        )


    print(
        "Clip berhasil:",
        output
    )


    return output


# ============================================================
# HITUNG JUMLAH KLIP
# ============================================================

def calculate_parts(
    duration
):

    try:

        duration = float(
            duration
        )

    except Exception:

        duration = 5


    if duration >= 12:

        return 3

    if duration >= 7:

        return 2

    return 1


# ============================================================
# PROSES SEMUA SCENE
# ============================================================

clip_files = []


print()
print("========================================")
print("MEMBUAT VIDEO DARI STOCK FOOTAGE")
print("========================================")


for index, scene in enumerate(
    storyboard
):

    number = index + 1


    print()
    print(
        "SCENE",
        number,
        "/",
        len(storyboard)
    )


    # --------------------------------------------------------
    # DURASI SCENE
    # --------------------------------------------------------

    try:

        scene_duration = float(
            scene.get(
                "durasi_detik",
                5
            )
        )

    except Exception:

        scene_duration = 5


    if scene_duration < 2:

        scene_duration = 2


    if scene_duration > 15:

        scene_duration = 15


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


    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    queries = create_keywords(
        scene
    )


    if not queries:

        print(
            "Gemini tidak menghasilkan keyword."
        )

        queries = fallback_keywords(
            scene
        )


    print()
    print(
        "KEYWORD VISUAL:"
    )


    for query in queries:

        print(
            " -",
            query
        )


    # --------------------------------------------------------
    # JUMLAH KLIP
    # --------------------------------------------------------

    parts = calculate_parts(
        scene_duration
    )


    part_duration = (
        scene_duration
        / parts
    )


    print()
    print(
        "Scene duration:",
        scene_duration
    )

    print(
        "Jumlah klip:",
        parts
    )

    print(
        "Durasi tiap klip:",
        round(
            part_duration,
            2
        )
    )


    # --------------------------------------------------------
    # BUAT KLIP
    # --------------------------------------------------------

    for part in range(
        1,
        parts + 1
    ):

        # Rotasi keyword agar visual antar part
        # tidak selalu menggunakan pencarian yang sama

        rotated_queries = (
            queries[
                part - 1:
            ]
            + queries[
                :
                part - 1
            ]
        )


        video = find_video(

            rotated_queries,

            number,

            part

        )


        # ----------------------------------------------------
        # FALLBACK PEXELS
        # ----------------------------------------------------

        if not video:

            print(
                "Video spesifik tidak ditemukan."
            )

            print(
                "Mencoba fallback Pexels..."
            )


            fallback_queries = [

                "person working",

                "small business",

                "business owner",

                "person using phone",

                "daily life"

            ]


            video = find_video(

                fallback_queries,

                number,

                part

            )


        if not video:

            raise SystemExit(

                "ERROR: Tidak menemukan "
                "video Pexels untuk scene "
                + str(number)
                + " part "
                + str(part)

            )


        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        source_file = (

            "visual_tmp/"
            "source_"
            + str(number)
            + "_"
            + str(part)
            + ".mp4"

        )


        success = download_file(

            video["url"],

            source_file

        )


        if not success:

            raise SystemExit(

                "ERROR: Gagal download "
                "video scene "
                + str(number)
                + " part "
                + str(part)

            )


        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        text_file = create_text_file(

            screen_text,

            number,

            part

        )


        # ----------------------------------------------------
        # CREDIT
        # ----------------------------------------------------

        credit_file = create_credit_file(

            video.get(
                "photographer",
                ""
            ),

            number,

            part

        )


        # ----------------------------------------------------
        # RENDER
        # ----------------------------------------------------

        clip = create_clip(

            source_file,

            text_file,

            credit_file,

            part_duration,

            number,

            part

        )


        clip_files.append(
            clip
        )


# ============================================================
# VALIDASI CLIP
# ============================================================

if not clip_files:

    raise SystemExit(
        "ERROR: Tidak ada clip."
    )


print()
print(
    "Total clip berhasil:",
    len(clip_files)
)


# ============================================================
# CONCAT FILE
# ============================================================

concat_file = (
    "visual_tmp/"
    "concat.txt"
)


with open(
    concat_file,
    "w",
    encoding="utf-8"
) as file:

    for clip_file in clip_files:

        absolute_path = os.path.abspath(
            clip_file
        )


        # Escape apostrophe
        absolute_path = absolute_path.replace(
            "'",
            "'\\''"
        )


        file.write(
            "file '"
            + absolute_path
            + "'\n"
        )


# ============================================================
# OUTPUT FINAL
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
# GABUNG VIDEO
# ============================================================

print()
print("========================================")
print("MENGGABUNGKAN SEMUA KLIP")
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

    "-an",

    "-c:v",
    "libx264",

    "-preset",
    "veryfast",

    "-crf",
    "23",

    "-pix_fmt",
    "yuv420p",

    "-movflags",
    "+faststart",

    output_video

]


result = subprocess.run(
    command,
    check=False
)


if result.returncode != 0:

    raise SystemExit(
        "ERROR: FFmpeg gagal "
        "menggabungkan video."
    )


# ============================================================
# VALIDASI FINAL
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
        "ERROR: Ukuran video final "
        "terlalu kecil."
    )


# ============================================================
# BUAT INFORMASI CREDIT
# ============================================================

credits_file = (
    "visual_tmp/"
    "credits_used.json"
)


credits = {

    "source":
        "Pexels",

    "website":
        "pexels.com",

    "production":
        latest_production,

    "video":
        output_video,

    "clips":
        []

}


for clip_file in clip_files:

    credits["clips"].append(
        clip_file
    )


with open(
    credits_file,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        credits,
        file,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# SELESAI
# ============================================================

print()
print("========================================")
print("FBPRO VISUAL AGENT V7 BERHASIL")
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
    "Sumber visual: Pexels Video"
)

print(
    "Setiap scene dapat menggunakan "
    "beberapa klip video."
)

print(
    "Visual dianalisis berdasarkan "
    "narasi menggunakan Gemini."
)

print(
    "Tidak menggunakan foto statis."
)

print(
    "Tidak menggunakan zoompan."
)

print(
    "Video dibuat tanpa audio."
)

print()
print(
    "FBPro Visual Agent V7 selesai."
)
