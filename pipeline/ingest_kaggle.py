"""After downloading clips + timings.json from Kaggle into outputs/shots/, run this."""
import json, pathlib
from common import log_call

p = pathlib.Path("outputs/shots/timings.json")
if not p.exists():
    raise SystemExit("no outputs/shots/timings.json")
for sid, minutes in json.load(open(p)).items():
    log_call("wan_clip", "Wan2.2-TI2V-5B", {"gpu": "Kaggle T4", "frames": 49}, None,
             minutes * 60, gpu_minutes=minutes, note=sid)
    print("logged", sid, minutes, "min")