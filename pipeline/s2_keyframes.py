"""Stage 2: keyframes with FLUX.1 schnell on Cloudflare.
  python pipeline/s2_keyframes.py            -> one image per shot (outputs/keyframes/sXX.jpg), cached
  python pipeline/s2_keyframes.py --refs     -> 4 character reference candidates
  python pipeline/s2_keyframes.py --explore 3 -> 3 seed options per shot in outputs/keyframes/explore/
"""
import argparse, pathlib, time
from common import load_storyboard, h, cached, mark, log_call, cf_image, CF_MODEL

ap = argparse.ArgumentParser()
ap.add_argument("--refs", action="store_true")
ap.add_argument("--explore", type=int, default=0)
ap.add_argument("--steps", type=int, default=4)
a = ap.parse_args()

sb = load_storyboard()
out = pathlib.Path("outputs/keyframes"); out.mkdir(parents=True, exist_ok=True)
(out / "explore").mkdir(exist_ok=True)
STYLE, CHAR = sb["style_block"], sb["character_sheet"]


def generate(path, prompt, seed, tag):
    t0 = time.time()
    try:
        path.write_bytes(cf_image(prompt, seed, a.steps))
    except Exception as e:
        log_call(tag, CF_MODEL, {"steps": a.steps}, seed, time.time() - t0, ok=False, note=str(e)[:200])
        print("  FAILED (quota? write it in FAILURES.md):", str(e)[:120])
        raise
    log_call(tag, CF_MODEL, {"steps": a.steps}, seed, time.time() - t0)


if a.refs:
    for i in range(4):
        generate(out / f"ref_{'abcd'[i]}.jpg", f"{STYLE}. {CHAR}. portrait, front view, plain background", 100 + i, "keyframes_ref")
        print("wrote ref", 'abcd'[i])
    print("Pick one, then copy its visible traits into character_sheet.")
elif a.explore:
    for s in sb["shots"]:
        for i in range(a.explore):
            seed = s["seed"] + i
            p = out / "explore" / f"{s['id']}_seed{seed}.jpg"
            if p.exists(): continue
            generate(p, f"{STYLE}. {CHAR}. {s['image_prompt']}", seed, "keyframes_explore")
            print("wrote", p.name)
    print("Look at the options, then put the best seed into storyboard.json.")
else:
    for s in sb["shots"]:
        prompt = f"{STYLE}. {CHAR}. {s['image_prompt']}"
        p = out / f"{s['id']}.jpg"
        key = h(prompt, s["seed"], CF_MODEL, a.steps)
        if cached(p, key):
            print("CACHED", s["id"]); continue
        print("REGEN ", s["id"], "(prompt/seed/style changed)")
        generate(p, prompt, s["seed"], "keyframes")
        mark(p, key)