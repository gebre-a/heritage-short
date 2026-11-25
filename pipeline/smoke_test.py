"""Calls each provider once and logs latency. Run first: python pipeline/smoke_test.py"""
import time
from common import gemini_text, gemini_tts, cf_image, log_call, need

def attempt(name, model, fn):
    t0 = time.time()
    try:
        fn()
        dt = time.time() - t0
        log_call("smoke", model, {"test": name}, None, dt)
        print(f"OK   {name}: {dt:.1f}s")
    except Exception as e:
        log_call("smoke", model, {"test": name}, None, time.time() - t0, ok=False, note=str(e)[:200])
        print(f"FAIL {name}: {e}\n  -> write this in FAILURES.md")

attempt("gemini_text", need("TEXT_MODEL"), lambda: gemini_text("Say hi in one word."))
attempt("gemini_tts", need("TTS_MODEL"), lambda: gemini_tts("Hello.", style="Speak calmly."))
attempt("cloudflare_image", "flux-1-schnell", lambda: cf_image("a red circle on white", seed=1))