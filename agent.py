import os
import json
import requests
from datetime import datetime

API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-3.1-flash-lite"

PROMPT = """
Kamu adalah Content Brain untuk creator Facebook Professional Indonesia.

Buat SATU ide video Reels ORIGINAL.

Pilih salah satu tema secara acak:
- motivasi
- fakta unik
- cerita kehidupan
- humor
- kisah inspiratif
- teknologi dan AI
- keuangan umum
- relationship
- tren ringan

Target penonton:
pengguna Facebook Indonesia.

Buat konten sekitar 30-60 detik.

Konten harus:
- original
- menarik
- memiliki nilai atau hiburan
- menggunakan bahasa Indonesia natural
- tidak menyalin creator lain
- tidak menggunakan berita palsu
- tidak menggunakan clickbait menipu
- tidak melakukan spam
- tidak membuat klaim medis/hukum/keuangan berisiko

Kembalikan JSON dengan struktur:

{
  "tema": "",
  "judul": "",
  "hook": "",
  "skrip": "",
  "visual": [],
  "caption": "",
  "cta": "",
  "hashtag": []
}
"""

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
                        "text": PROMPT
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "responseMimeType": "application/json"
        }
    },
    timeout=120
)

if response.status_code != 200:
    print("Gemini API ERROR:")
    print(response.text)
    raise SystemExit(1)

data = response.json()

text = (
    data["candidates"][0]
    ["content"]["parts"][0]["text"]
)

content = json.loads(text)

os.makedirs("content", exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

filename = f"content/{timestamp}.json"

with open(
    filename,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        content,
        f,
        ensure_ascii=False,
        indent=2
    )

print("================================")
print("FBPRO AGENT BERHASIL")
print("================================")
print(f"File: {filename}")
print()
print(json.dumps(
    content,
    ensure_ascii=False,
    indent=2
))
