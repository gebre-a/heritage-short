# CELL 1
!nvidia-smi
!git clone https://github.com/Wan-Video/Wan2.2.git
%cd Wan2.2
# If installing flash_attn fails, delete that line from requirements.txt and re-run.
!pip install -r requirements.txt
!pip install -U "huggingface_hub[cli]"
!huggingface-cli download Wan-AI/Wan2.2-TI2V-5B --local-dir ./Wan2.2-TI2V-5B
# CELL 2: generates one clip per shot, saves each as it finishes, records minutes
import json, time, subprocess, pathlib
IN = "/kaggle/input/heritage-keyframes"          # check the real path under Input
OUT = pathlib.Path("/kaggle/working/shots"); OUT.mkdir(exist_ok=True)
tfile = OUT / "timings.json"
timings = json.load(open(tfile)) if tfile.exists() else {}
for s in json.load(open(f"{IN}/shots.json")):
    dst = OUT / f"{s['id']}.mp4"
    if dst.exists(): continue
    t0 = time.time()
    r = subprocess.run(["python", "generate.py", "--task", "ti2v-5B", "--size", "1280*704",
        "--ckpt_dir", "./Wan2.2-TI2V-5B", "--offload_model", "True", "--convert_model_dtype", "--t5_cpu",
        "--image", f"{IN}/{s['id']}.jpg", "--prompt", s["motion_prompt"],
        "--base_seed", str(s["seed"]), "--frame_num", "49", "--save_file", str(dst)])
    timings[s["id"]] = round((time.time() - t0) / 60, 1)
    json.dump(timings, open(tfile, "w"))
    print(s["id"], "ok" if r.returncode == 0 else "FAILED", timings[s["id"]], "min")