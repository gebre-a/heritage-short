"""Stage 3: decide per shot whether a Wan clip exists, else Ken Burns on the keyframe.
The actual Ken Burns render happens in stage 5. Wan clips are made on Kaggle (notebooks/)."""
import pathlib
from common import load_storyboard, log_call

sb = load_storyboard()
n_wan = 0
for s in sb["shots"]:
    kf = pathlib.Path(f"outputs/keyframes/{s['id']}.jpg")
    clip = pathlib.Path(f"outputs/shots/{s['id']}.mp4")
    if not kf.exists():
        raise SystemExit(f"missing keyframe for {s['id']}: run stage 2 first")
    mode = "wan" if clip.exists() else "ken-burns"
    n_wan += mode == "wan"
    print(f"{s['id']}: {mode}")
    log_call("shots_plan", "none", {"mode": mode}, s["seed"], 0.0, note=s["id"])
print(f"{n_wan}/{len(sb['shots'])} shots use Wan clips")