"""Shared helpers: paths, hashing/caching, retries, run logging, API calls."""
import base64, functools, hashlib, json, os, pathlib, sys, time, wave
import requests
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)                      # every script runs from the repo root
load_dotenv(ROOT / ".env")

LEAD, TAIL, END_S, FPS = 0.3, 0.5, 3.0, 24   # seconds of padding / end card, frame rate


def need(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return v


# ---------- hashing, caching, logging ----------
def h(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def file_hash(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:16]


def cached(path, key) -> bool:
    path = pathlib.Path(path)
    meta = path.with_suffix(path.suffix + ".key")
    return path.exists() and meta.exists() and meta.read_text() == key


def mark(path, key):
    path = pathlib.Path(path)
    path.with_suffix(path.suffix + ".key").write_text(key)


def log_call(stage, model, params=None, seed=None, latency_s=0.0,
             cost_usd=0.0, ok=True, note="", gpu_minutes=0.0):
    rec = {"ts": round(time.time(), 1), "stage": stage, "model": model,
           "params": params or {}, "seed": seed, "latency_s": round(latency_s, 2),
           "gpu_minutes": gpu_minutes, "cost_usd": cost_usd, "ok": ok, "note": note}
    with open("runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def retry(n=5, base=2):
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*a, **k):
            for i in range(n):
                try:
                    return fn(*a, **k)
                except Exception as e:
                    if i == n - 1:
                        raise
                    wait = 25 * (i + 1) if "429" in str(e) else base ** i
                    print(f"  retry {i+1}/{n-1}: {str(e)[:200]} (wait {wait}s)")
                    time.sleep(wait)
        return wrap
    return deco


def load_storyboard():
    return json.load(open("storyboard.json", encoding="utf-8"))

def check(r):
    """Like raise_for_status, but shows the response body and never prints the URL or key."""
    if not r.ok:
        raise requests.HTTPError(f"{r.status_code}: {r.text[:300]}", response=r)
# ---------- Gemini ----------
GEM = "https://generativelanguage.googleapis.com/v1beta/models"


def _gem_post(model, body):
    """Key goes in a header, so it never appears in URLs or error messages."""
    r = requests.post(f"{GEM}/{model}:generateContent",
                      headers={"x-goog-api-key": need("GEMINI_API_KEY")},
                      json=body, timeout=180)
    if not r.ok:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


@retry()
def gemini_text(prompt, model=None):
    model = model or need("TEXT_MODEL")
    data = _gem_post(model, {"contents": [{"parts": [{"text": prompt}]}]})
    return data["candidates"][0]["content"]["parts"][0]["text"]


@retry()
def gemini_tts(text, voice=None, style="", model=None):
    """Returns raw PCM bytes (16-bit, mono, 24 kHz)."""
    model = model or need("TTS_MODEL")
    voice = voice or os.environ.get("TTS_VOICE", "Kore")
    body = {"contents": [{"parts": [{"text": f"{style}\n\n{text}" if style else text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    data = _gem_post(model, body)
    return base64.b64decode(data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])

def write_wav(path, pcm, rate=24000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)


# ---------- Cloudflare Workers AI (FLUX.1 schnell) ----------
CF_MODEL = "@cf/black-forest-labs/flux-1-schnell"


SEED_OK = True   # flips to False the first time Cloudflare rejects 'seed'


@retry()
def cf_image(prompt, seed=None, steps=4):
    """Returns JPEG bytes. Remembers if the endpoint does not accept 'seed'."""
    global SEED_OK
    url = f"https://api.cloudflare.com/client/v4/accounts/{need('CF_ACCOUNT_ID')}/ai/run/{CF_MODEL}"
    hdr = {"Authorization": f"Bearer {need('CF_API_TOKEN')}"}
    body = {"prompt": prompt, "steps": steps}
    if seed is not None and SEED_OK:
        body["seed"] = seed
    r = requests.post(url, headers=hdr, json=body, timeout=180)
    if r.status_code == 400 and "seed" in body:
        SEED_OK = False
        print("  seed not supported -> generating without it (record in FAILURES.md)")
        body.pop("seed")
        r = requests.post(url, headers=hdr, json=body, timeout=180)
    check(r)
    return base64.b64decode(r.json()["result"]["image"])