"""Stage 4: take the chosen score (generated on Kaggle) and normalise it to 48 kHz stereo WAV."""
import pathlib, time
from common import log_call, h, file_hash, cached, mark, load_storyboard
from media import run

src = next((p for p in [pathlib.Path(f"outputs/music/score.{e}") for e in ("wav", "mp3", "flac")] if p.exists()), None)
if not src:
    raise SystemExit("No outputs/music/score.(wav|mp3|flac). Generate with ACE-Step, or use a royalty-free "
                     "track and record its licence in ETHICS.md and the reason in FAILURES.md.")
dst = pathlib.Path("outputs/music/score_48k.wav")
key = h(file_hash(src))
if cached(dst, key):
    print("CACHED music")
else:
    t0 = time.time()
    run(["ffmpeg", "-y", "-i", src, "-ar", "48000", "-ac", "2", dst])
    mark(dst, key)
    log_call("music_prepare", "ffmpeg", {"src": src.name}, load_storyboard()["music"]["seed"], time.time() - t0)
    print("music prepared from", src.name)