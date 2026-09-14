#!/usr/bin/env python3
import json, os, re, time
from pathlib import Path
from typing import Any, Dict, List
import requests

ROOT = Path(__file__).resolve().parent
PRODUCTION_DIR = ROOT / "production"
CONTENT_DIR = ROOT / "content"
JOBS_DIR = ROOT / "ai_jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"

MAX_SCENES = 8
DEFAULT_SCENE_SECONDS = 5

def read_json_files(folder):
    items = []
    if not folder.exists():
        return items
    for path in sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["_source_file"] = str(path.relative_to(ROOT))
                items.append(data)
        except Exception as exc:
            print(f"[WARN] {path}: {exc}")
    return items

def latest_payload():
    candidates = read_json_files(PRODUCTION_DIR) or read_json_files(CONTENT_DIR)
    if not candidates:
        raise FileNotFoundError("Tidak menemukan JSON di production/ atau content/.")
    return candidates[0]

def recursive_find(obj: Any, keys: set):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in keys:
                return value
        for value in obj.values():
            result = recursive_find(value, keys)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for value in obj:
            result = recursive_find(value, keys)
            if result is not None:
                return result
    return None

def text_value(data, keys, default=""):
    found = recursive_find(data, {k.lower() for k in keys})
    if found is None:
        return default
    if isinstance(found, (str, int, float)):
        return str(found)
    return ""

def normalize_scene(scene, index):
    narration = text_value(scene, ["narration","voiceover","voice_over","vo","script","text","dialogue"])
    visual = text_value(scene, ["visual","visual_description","visual_prompt","scene","description"])
    raw_duration = text_value(scene, ["duration","duration_seconds","seconds","length"])
    nums = re.findall(r"\d+(?:\.\d+)?", raw_duration)
    duration = float(nums[0]) if nums else DEFAULT_SCENE_SECONDS
    duration = max(3.0, min(duration, 8.0))
    return {"scene": index, "duration": duration, "narration": narration.strip(), "visual": visual.strip()}

def extract_scenes(data):
    possible = recursive_find(data, {"scenes","storyboard","scene_list","video_scenes","visual_scenes"})
    scenes = []
    if isinstance(possible, list):
        for idx, item in enumerate(possible[:MAX_SCENES], 1):
            if isinstance(item, dict):
                scenes.append(normalize_scene(item, idx))
    if scenes:
        return scenes

    script = text_value(data, ["voiceover","voice_over","script","narration","caption","content"])
    if not script:
        script = json.dumps(data, ensure_ascii=False)

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
    if not sentences:
        sentences = [script.strip()]
    chunks = [" ".join(sentences[i:i+2]) for i in range(0, len(sentences), 2)]

    for idx, chunk in enumerate(chunks[:MAX_SCENES], 1):
        scenes.append({"scene": idx, "duration": DEFAULT_SCENE_SECONDS, "narration": chunk, "visual": ""})
    return scenes

def title_from_payload(data):
    return text_value(data, ["title","topic","headline","judul","content_title"], "FBPro AI Video").strip()[:200]

def fallback_prompt(scene, title):
    return (
        "Create a cinematic AI-generated animated video scene for a vertical social-media reel. "
        "The scene must visibly communicate the narration through actions, characters and objects. "
        "Polished stylized 3D animated film look, expressive natural movement, cinematic lighting, "
        "believable Indonesian or Southeast Asian setting when relevant, detailed materials, dynamic camera. "
        "No text, subtitles, logos, watermarks or UI. "
        f"Topic: {title}. Narration: {scene.get('narration','')}. "
        f"Visual direction: {scene.get('visual','')}"
    )

def make_prompt(scene, title):
    base = fallback_prompt(scene, title)
    if not GEMINI_API_KEY:
        return base

    prompt = f"""Create ONE concise English text-to-video prompt for Wan2.1 T2V-1.3B.

The video must directly depict the narration with concrete visible actions, objects, characters and camera movement.
Use a polished stylized 3D animated film look.
Use Indonesian/Southeast Asian environments when relevant.
Keep visual continuity across scenes.
No written words, subtitles, logos, watermarks or UI.
Return ONLY the final prompt.

TITLE:
{title}

NARRATION:
{scene.get('narration','')}

VISUAL DIRECTION:
{scene.get('visual','')}

Base concept:
{base}"""

    payload = {"contents":[{"parts":[{"text":prompt}]}],
               "generationConfig":{"temperature":0.75,"maxOutputTokens":450}}
    try:
        r = requests.post(GEMINI_URL, params={"key":GEMINI_API_KEY}, json=payload, timeout=45)
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = re.sub(r"^```(?:text)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        if len(text) >= 40:
            return text
    except Exception as exc:
        print("[WARN] Gemini prompt gagal:", exc)
    return base

def main():
    print("=== FBPro Visual Agent V9 ===")
    payload = latest_payload()
    title = title_from_payload(payload)
    scenes = extract_scenes(payload)
    if not scenes:
        raise RuntimeError("Tidak ada scene.")

    job_id = time.strftime("job_%Y%m%d_%H%M%S")
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=False)

    job_scenes = []
    for scene in scenes:
        job_scenes.append({
            "scene": scene["scene"],
            "duration": scene["duration"],
            "narration": scene["narration"],
            "visual": scene["visual"],
            "prompt": make_prompt(scene, title),
            "negative_prompt": "text, subtitles, captions, watermark, logo, UI, static image, blurry, low quality, flicker, jitter, deformed hands, extra fingers, extra limbs, distorted face"
        })

    job = {
        "job_id": job_id,
        "status": "pending",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_file": payload.get("_source_file",""),
        "title": title,
        "target": {"platform":"Facebook Professional Mode","format":"MP4","aspect_ratio":"9:16","final_resolution":"1080x1920","scene_resolution":"480x832","fps":16},
        "model": {"name":"Wan2.1-T2V-1.3B","mode":"text-to-video","renderer":"Google Colab GPU"},
        "scenes": job_scenes
    }

    (job_dir/"job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Job dibuat: {job_dir}")
    print(f"[OK] Scene: {len(job_scenes)}")

if __name__ == "__main__":
    main()
