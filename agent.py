import os
import json
import glob
import requests
from datetime import datetime

API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-3.1-flash-lite"

# ==========================================
# CARI KONTEN TERBARU
# ==========================================

files = glob.glob("content/*.json")

if not files:
    raise SystemExit("Tidak ada file konten di folder content/")

latest_file = max(files, key=os.path.getmtime)

with open(
    latest_file,
    "r",
    encoding="utf-8"
) as f:
    source_content = json.load(f)

print("Konten sumber:")
print(latest_file)


# ==========================================
# PROMPT AGEN #2
# ==========================================

prompt = f"""
Kamu adalah REELS PRODUCTION AGENT untuk creator
Facebook Professional Indonesia.

Tugas kamu adalah mengubah SATU ide konten menjadi
PAKET PRODUKSI REELS lengkap yang siap diberikan
kepada editor atau mesin pembuat video.

KONTEN SUMBER:

{json.dumps(source_content, ensure_ascii=False, indent=2)}

Buat paket produksi untuk video sekitar 30-60 detik.

ATURAN:

1. Pertahankan inti ide sumber.
2. Jangan menyalin karya creator lain.
3. Buat narasi yang natural seperti manusia.
4. Hook harus kuat dalam 1-3 detik pertama.
5. Jangan menggunakan clickbait yang menipu.
6. Jangan membuat fakta yang tidak diketahui kebenarannya.
7. Jika menyebut fakta, gunakan bahasa yang tidak
   berlebihan jika kepastian faktanya tidak tersedia.
8. Jangan membuat klaim medis, hukum, atau finansial
   yang berisiko.
9. Hindari pengulangan kalimat.
10. Setiap adegan harus mempunyai fungsi.
11. Visual harus bisa dibuat menggunakan stok visual,
    gambar AI, atau video sederhana.
12. Video harus cocok untuk format vertikal 9:16.
13. Teks layar harus singkat dan mudah dibaca di HP.
14. Voice-over harus terdengar natural.
15. CTA harus halus dan tidak memaksa.
16. Jangan menggunakan watermark atau logo milik
    pihak lain.
17. Jangan menyarankan mengambil ulang video orang lain.

BUAT:

A. INFORMASI VIDEO
- judul
- tema
- durasi
- target_penonton
- gaya

B. HOOK
Buat kalimat pembuka 1-3 detik.

C. VOICE OVER
Tulis seluruh naskah voice-over dari awal sampai akhir.

D. STORYBOARD
Buat 6-8 adegan.

Untuk setiap adegan berikan:
- nomor
- durasi_detik
- visual
- voice_over
- teks_layar
- transisi

E. TEKS THUMBNAIL
Buat 3 pilihan teks thumbnail pendek.

F. CAPTION
Buat caption Facebook yang natural.

G. CTA
Buat satu CTA yang relevan.

H. HASHTAG
Buat 5-8 hashtag yang relevan.

I. PROMPT VISUAL
Buat prompt visual untuk setiap adegan
yang bisa digunakan oleh generator gambar/video AI.

J. EDITING NOTES
Berikan arahan:
- format
- rasio
- subtitle
- musik
- tempo
- transisi
- sound effect

K. QUALITY_CHECK
Berikan checklist:
- original
- tidak misleading
- tidak spam
- tidak mengandung klaim berisiko
- layak ditinjau manusia sebelum dipublikasikan

KEMBALIKAN HANYA JSON VALID.

Gunakan struktur:

{{
  "video": {{
    "judul": "",
    "tema": "",
    "durasi_detik": 0,
    "target_penonton": "",
    "gaya": ""
  }},

  "hook": "",

  "voice_over": "",

  "storyboard": [
    {{
      "adegan": 1,
      "durasi_detik": 0,
      "visual": "",
      "voice_over": "",
      "teks_layar": "",
      "transisi": ""
    }}
  ],

  "thumbnail_text": [
    "",
    "",
    ""
  ],

  "caption": "",

  "cta": "",

  "hashtag": [],

  "visual_prompts": [
    {{
      "adegan": 1,
      "prompt": ""
    }}
  ],

  "editing_notes": {{
    "format": "9:16",
    "subtitle": "",
    "musik": "",
    "tempo": "",
    "transisi": "",
    "sound_effect": ""
  }},

  "quality_check": {{
    "original": true,
    "tidak_misleading": true,
    "tidak_spam": true,
    "tidak_berisiko": true,
    "perlu_review_manusia": true
  }}
}}
"""


# ==========================================
# PANGGIL GEMINI
# ==========================================

url = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/"
    f"{MODEL}:generateContent"
)

response = requests.post(
    url,
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": API_KEY
    },
    json={
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
            "temperature": 0.85,
            "responseMimeType": "application/json"
        }
    },
    timeout=120
)


# ==========================================
# CEK RESPONSE
# ==========================================

if response.status_code != 200:

    print("Gemini API ERROR:")
    print(response.text)

    raise SystemExit(1)


data = response.json()

try:

    text = (
        data["candidates"][0]
        ["content"]["parts"][0]["text"]
    )

except Exception:

    print("Response Gemini tidak sesuai:")
    print(json.dumps(data, indent=2))

    raise SystemExit(1)


# ==========================================
# PARSE JSON
# ==========================================

try:

    production = json.loads(text)

except json.JSONDecodeError:

    print("Gemini tidak menghasilkan JSON valid:")
    print(text)

    raise SystemExit(1)


# ==========================================
# SIMPAN HASIL
# ==========================================

os.makedirs("production", exist_ok=True)

timestamp = datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S"
)

filename = (
    f"production/"
    f"{timestamp}.json"
)

with open(
    filename,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        production,
        f,
        ensure_ascii=False,
        indent=2
    )


# ==========================================
# OUTPUT
# ==========================================

print()
print("========================================")
print("FBPRO PRODUCTION AGENT BERHASIL")
print("========================================")
print()
print(f"Sumber   : {latest_file}")
print(f"Hasil    : {filename}")
print()

print(
    json.dumps(
        production,
        ensure_ascii=False,
        indent=2
    )
)
