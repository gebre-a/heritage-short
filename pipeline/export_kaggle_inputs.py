"""python pipeline/export_kaggle_inputs.py s03 s05 s07  -> outputs/kaggle/ (upload this folder as a Kaggle dataset)"""
import json, shutil, sys, pathlib
from common import load_storyboard

ids = sys.argv[1:]
sb = load_storyboard()
dst = pathlib.Path("outputs/kaggle"); dst.mkdir(parents=True, exist_ok=True)
items = []
for s in sb["shots"]:
    if ids and s["id"] not in ids: continue
    shutil.copy(f"outputs/keyframes/{s['id']}.jpg", dst / f"{s['id']}.jpg")
    items.append({"id": s["id"], "motion_prompt": s["motion_prompt"], "seed": s["seed"]})
json.dump(items, open(dst / "shots.json", "w", encoding="utf-8"), indent=2)
print("exported", [i["id"] for i in items], "-> upload outputs/kaggle as dataset 'heritage-keyframes'")