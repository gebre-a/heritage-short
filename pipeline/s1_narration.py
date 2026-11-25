"""Stage 1: one narration WAV per shot. Cached by hash of text + model + voice + style.
Paces calls to stay under the free-tier rate limit. Safe to re-run: finished shots are skipped."""
import os, pathlib, time
from common import (load_storyboard, h, cached, mark, log_call, gemini_tts, write_wav, need)

MODEL = need("TTS_MODEL")
VOICE = os.environ.get("TTS_VOICE", "Kore")
STYLE = "Speak calmly, warmly and unhurriedly, like telling a family story."
PACE = float(os.environ.get("TTS_PACE", "20"))   # seconds between TTS calls

sb = load_storyboard()
out = pathlib.Path("outputs/narration"); out.mkdir(parents=True, exist_ok=True)

for s in sb["shots"]:
    p = out / f"{s['id']}.wav"
    key = h(s["narration"], MODEL, VOICE, STYLE)
    if cached(p, key):
        print("CACHED", s["id"]); continue
    print("REGEN ", s["id"], "(narration text/voice changed)")
    t0 = time.time()
    try:
        write_wav(p, gemini_tts(s["narration"], VOICE, STYLE, MODEL))
    except Exception as e:
        log_call("narration", MODEL, {"voice": VOICE}, None, time.time() - t0, ok=False, note=str(e)[:200])
        raise
    mark(p, key)
    log_call("narration", MODEL, {"voice": VOICE, "chars": len(s["narration"])}, None, time.time() - t0)
    time.sleep(15)   # stay under the free-tier requests-per-minute limit