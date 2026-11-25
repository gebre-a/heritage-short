import subprocess, sys, time
from common import log_call
STAGES = ["s0_validate", "s1_narration", "s2_keyframes", "s3_shots", "s4_music", "s5_assemble"]
for st in STAGES:
    print(f"\n=== {st} ===")
    t0 = time.time()
    r = subprocess.run([sys.executable, f"pipeline/{st}.py"])
    log_call("stage_total", st, {}, None, time.time() - t0, ok=r.returncode == 0)
    if r.returncode:
        sys.exit(f"stage {st} failed. See FAILURES.md for how to record it.")
print("\nDone: outputs/final/film_vertical.mp4 and film_horizontal.mp4")