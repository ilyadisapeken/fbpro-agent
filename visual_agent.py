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
# V6 - STABLE VERSION
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30

GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    ""
)

GEMINI_MODEL = "gemini-3.1-flash-lite"

WIKIMEDIA_API = (
    "https://commons.wikimedia.org/w/api.php"
)

USER_AGENT = (
    "FBProVisualAgent/6.0 "
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

os.makedirs(
    "visual_tmp",
    exist_ok=True
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
print("FBPRO VISUAL AGENT V6")
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
# HTTP JSON
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

        print(
            "Download:",
            url
        )

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
            destination,
            "wb"
        ) as file:

            file.write(content)

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
Create five short English search queries for
real photographs on Wikimedia Commons.

Scene visual:
{visual}

Voice:
{voice}

On screen:
{screen}

Rules:
- 2 to 5 words per query
- concrete objects, people or activities
- suitable for a real photograph
- no abstract motivational phrases
- no explanations
- no image generation prompts

Examples:
small business owner
person using smartphone
local food seller
customer shopping market
woman working laptop

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
            "WARNING: GEMINI_API_KEY tidak ditemukan."
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

    words = re.findall(
        r"[a-zA-Z]{4,}",
        visual
    )


    if words:

        words = words[:3]

        first_query = " ".join(
            words
        )

    else:

        first_query = (
            "person working"
        )


    return [

        first_query,

        "small business",

        "business owner",

        "person working",

        "daily activity"

    ]


# ============================================================
# WIKIMEDIA SEARCH
# ============================================================

def search_wikimedia(query):

    params = {

        "action":
            "query",

        "format":
            "json",

        "generator":
            "search",

        "gsrsearch":
            query,

        "gsrnamespace":
            "6",

        "gsrlimit":
            "10",

        "prop":
            "imageinfo",

        "iiprop":
            "url|mime",

        "iiurlwidth":
            "1400"

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
        .get(
            "query",
            {}
        )
        .get(
            "pages",
            {}
        )

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

            "title":
                page.get(
                    "title",
                    ""
                ),

            "url":
                image_url

        }


    return None


# ============================================================
# CARI FOTO
# ============================================================

def find_photo(
    scene,
    number
):

    print()
    print("----------------------------------------")
    print(
        "MENCARI FOTO SCENE",
        number
    )
    print("----------------------------------------")


    queries = create_keywords(
        scene
    )


    if not queries:

        queries = fallback_keywords(
            scene
        )


    print(
        "Search keywords:"
    )


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


    return None


# ============================================================
# BUAT TEXT FILE
# ============================================================

def create_text_file(
    text,
    number
):

    filename = (
        "visual_tmp/"
        "text_"
        + str(number)
        + ".txt"
    )


    text = clean_text(
        text
    )


    if not text:

        text = title


    if len(text) > 180:

        text = (
            text[:177]
            + "..."
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
# BUAT SCENE VIDEO
# ============================================================

def create_scene(
    image_file,
    text_file,
    duration,
    number
):

    output = (
        "visual_tmp/"
        "scene_"
        + str(number)
        + ".mp4"
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


    print()
    print(
        "Render scene",
        number
    )

    print(
        "Durasi:",
        duration,
        "detik"
    )


    # --------------------------------------------------------
    # FILTER STABIL
    #
    # TIDAK MENGGUNAKAN ZOOMPAN
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
        "brightness=-0.02:"
        "saturation=1.05,"
        "drawbox="
        "x=0:"
        "y=0:"
        "w=iw:"
        "h=ih:"
        "color=black@0.10:"
        "t=fill,"
        "drawbox="
        "x=0:"
        "y=ih-560:"
        "w=iw:"
        "h=560:"
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
        "fontsize=58:"
        "line_spacing=18:"
        "x=65:"
        "y=1490:"
        "shadowcolor=black@0.9:"
        "shadowx=3:"
        "shadowy=3"
    )


    command = [

        "ffmpeg",

        "-y",

        "-loop",
        "1",

        "-i",
        image_file,

        "-vf",
        video_filter,

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


    if not os.path.exists(
        output
    ):

        raise SystemExit(
            "ERROR: Scene video tidak "
            "berhasil dibuat."
        )


    print(
        "Scene berhasil:",
        output
    )


    return output


# ============================================================
# PROSES SEMUA SCENE
# ============================================================

scene_files = []


print()
print("========================================")
print("MEMBUAT VIDEO SCENE")
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
    # DURASI
    # --------------------------------------------------------

    duration = scene.get(
        "durasi_detik",
        5
    )


    # --------------------------------------------------------
    # TEXT LAYAR
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
        number
    )


    # --------------------------------------------------------
    # CARI FOTO
    # --------------------------------------------------------

    photo = find_photo(
        scene,
        number
    )


    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not photo:

        print(
            "Foto khusus tidak ditemukan."
        )

        print(
            "Mencoba foto fallback..."
        )


        fallback_queries = [

            "small business",

            "person working",

            "business owner",

            "people working"

        ]


        for query in fallback_queries:

            photo = search_wikimedia(
                query
            )


            if photo:

                break


    if not photo:

        raise SystemExit(

            "ERROR: Tidak ada foto "
            "untuk scene "
            + str(number)

        )


    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    image_file = (

        "visual_tmp/"
        "image_"
        + str(number)
        + ".jpg"

    )


    success = download_file(

        photo["url"],

        image_file

    )


    if not success:

        raise SystemExit(

            "ERROR: Gagal download "
            "foto scene "
            + str(number)

        )


    # --------------------------------------------------------
    # BUAT VIDEO SCENE
    # --------------------------------------------------------

    scene_video = create_scene(

        image_file,

        text_file,

        duration,

        number

    )


    scene_files.append(
        scene_video
    )


# ============================================================
# CEK HASIL SCENE
# ============================================================

if not scene_files:

    raise SystemExit(
        "ERROR: Tidak ada scene."
    )


print()
print(
    "Scene berhasil dibuat:",
    len(scene_files)
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
# GABUNG SCENE
# ============================================================

print()
print("========================================")
print("MENGGABUNGKAN VIDEO")
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
# VALIDASI
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
print("FBPRO VISUAL AGENT V6 BERHASIL")
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
    "Setiap scene menggunakan foto nyata."
)

print(
    "Tidak menggunakan zoompan."
)

print()
print(
    "FBPro Visual Agent selesai."
)
