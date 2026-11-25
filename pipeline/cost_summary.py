import json, collections
# Fill from each provider's CURRENT public price page. Write the source and date in COSTS.md.
LIST_PRICE_PER_CALL = {"keyframes": 0.0, "keyframes_explore": 0.0, "keyframes_ref": 0.0,
                       "narration": 0.0, "wan_clip": 0.0}
agg = collections.defaultdict(lambda: {"n": 0, "sec": 0.0, "gpu": 0.0, "fail": 0})
for line in open("runs.jsonl", encoding="utf-8"):
    r = json.loads(line); a = agg[r["stage"]]
    a["n"] += 1; a["sec"] += r["latency_s"]; a["gpu"] += r.get("gpu_minutes", 0); a["fail"] += not r["ok"]
print("| stage | calls | failed | total s | avg s | GPU min | list-price equiv $ |\n|---|---|---|---|---|---|---|")
for k, a in agg.items():
    print(f"| {k} | {a['n']} | {a['fail']} | {a['sec']:.1f} | {a['sec']/a['n']:.1f} | {a['gpu']:.1f} | {a['n']*LIST_PRICE_PER_CALL.get(k, 0):.2f} |")